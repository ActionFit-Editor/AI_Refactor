#!/usr/bin/env python3
"""Deterministic, read-only Unity architecture candidate inventory."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


EXCLUDED_PARTS = {
    ".AI",
    ".Codex",
    ".git",
    ".idea",
    ".vs",
    "Build",
    "Builds",
    "Library",
    "Logs",
    "MemoryCaptures",
    "obj",
    "Recordings",
    "Temp",
    "UserSettings",
}

STRING_LITERAL = re.compile(r'@?"(?:""|\\.|[^"\\])*"')
CHAR_LITERAL = re.compile(r"'(?:\\.|[^'\\])'")

CANDIDATE_PATTERNS = (
    (
        "scene-wide-discovery",
        "FindObject",
        re.compile(
            r"\b(?:FindObjectOfType|FindObjectsOfType|FindObjectsByType|FindAnyObjectByType|FindFirstObjectByType|GameObject\.Find)\s*(?:<|\()"
        ),
    ),
    (
        "lifecycle-polling",
        "Update",
        re.compile(
            r"\b(?:public|private|protected|internal)?\s*(?:async\s+)?void\s+(?:Update|LateUpdate|FixedUpdate)\s*\("
        ),
    ),
    ("detached-async", "async void", re.compile(r"\basync\s+void\b")),
    (
        "coroutine",
        "Coroutine",
        re.compile(r"\b(?:StartCoroutine|StopCoroutine|IEnumerator)\b"),
    ),
    (
        "persistence",
        "Persistence API",
        re.compile(
            r"\b(?:PlayerPrefs|DataStore|DatabaseManager|File\.(?:Write|Append|Delete|Move|Copy)|JsonUtility\.ToJson)\b"
        ),
    ),
    (
        "communication-hub",
        "Event hub",
        re.compile(r"\b(?:GameEvents|EventBus|QueryBus|CommandBus)\b|\bstatic\s+event\b"),
    ),
    (
        "serialized-input",
        "SerializeField",
        re.compile(r"\[(?:UnityEngine\.)?SerializeField\]"),
    ),
    (
        "dynamic-loading",
        "Dynamic loading",
        re.compile(r"\b(?:Addressables\.|Resources\.Load(?:Async)?\s*<|Resources\.Load(?:Async)?\s*\()"),
    ),
    (
        "concrete-sdk-coupling",
        "SDK",
        re.compile(
            r"\b(?:Firebase|GameAnalytics|AppsFlyer|ThinkingAnalytics|Playio|Singular|AppLovin|IronSource|Adjust)\b",
            re.IGNORECASE,
        ),
    ),
)

PACKAGE_IDENTITY_HEADING = "## Package Identity"
PRODUCT_ROOT_LABEL = "AI Product Composition Root:"
PRODUCT_TARGET_LABEL = "AI Refactor target:"
SUPPORTED_PRODUCT_TARGET = "package-oriented-product"
MARKER_VALUE = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
SAFE_DEPENDENCY_VALUE = re.compile(r"[0-9A-Za-z][0-9A-Za-z._+-]{0,127}")
MARKDOWN_FENCE = re.compile(r"^(`{3,}|~{3,})")
GIT_COMMIT_HASH = re.compile(r"[0-9a-fA-F]{40}")
SUPPORTED_LOCK_SOURCES = {
    "builtin",
    "embedded",
    "git",
    "local",
    "local-tarball",
    "registry",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory Unity architecture candidates without changing the repository."
    )
    parser.add_argument("--root", default=".", help="Unity repository root")
    parser.add_argument(
        "--format", choices=("json", "text"), default="json", dest="output_format"
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=2000,
        help="Maximum detailed C# candidates to emit; counts still include every match",
    )
    args = parser.parse_args(argv)
    if args.max_candidates < 0:
        parser.error("--max-candidates must be zero or greater")
    return args


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_excluded(path: Path, root: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts)


def iter_scan_files(
    root: Path, suffix: str, additional_roots: Iterable[Path] = ()
) -> Iterable[Path]:
    emitted: set[Path] = set()
    for scan_root_name in ("Assets", "Packages"):
        scan_root = root / scan_root_name
        if not scan_root.is_dir():
            continue
        for path in scan_root.rglob(f"*{suffix}"):
            if path.is_file() and not is_excluded(path, root) and path not in emitted:
                emitted.add(path)
                yield path
    for scan_root in additional_roots:
        if not scan_root.is_dir():
            continue
        for path in scan_root.rglob(f"*{suffix}"):
            if path.is_file() and path not in emitted:
                emitted.add(path)
                yield path


def sanitize_snippet(line: str) -> str:
    redacted = STRING_LITERAL.sub('"<redacted>"', line)
    redacted = CHAR_LITERAL.sub("'<redacted>'", redacted)
    return " ".join(redacted.strip().split())[:200]


def sanitize_dependency_value(value: Any) -> str:
    text = str(value)
    return text if SAFE_DEPENDENCY_VALUE.fullmatch(text) is not None else "<redacted>"


def collect_csharp_candidates(
    root: Path, max_candidates: int
) -> tuple[list[dict[str, Any]], Counter[str], int]:
    candidates: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    scanned_files = 0

    for path in sorted(iter_scan_files(root, ".cs"), key=lambda value: relative_path(value, root)):
        scanned_files += 1
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            for kind, token, pattern in CANDIDATE_PATTERNS:
                if not pattern.search(line):
                    continue
                counts[kind] += 1
                if len(candidates) < max_candidates:
                    candidates.append(
                        {
                            "path": relative_path(path, root),
                            "line": line_number,
                            "kind": kind,
                            "token": token,
                            "snippet": sanitize_snippet(line),
                        }
                    )

    candidates.sort(key=lambda item: (item["path"], item["line"], item["kind"]))
    return candidates, counts, scanned_files


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError:
        return None, "file read failed"
    except (UnicodeError, json.JSONDecodeError) as exception:
        return None, str(exception)
    if not isinstance(value, dict):
        return None, "root JSON value is not an object"
    return value, None


def find_cycles(nodes: Iterable[str], edges: Iterable[tuple[str, str]]) -> list[list[str]]:
    graph = {node: set() for node in nodes}
    for source, target in edges:
        if source in graph and target in graph:
            graph[source].add(target)

    index = 0
    stack: list[str] = []
    indices: dict[str, int] = {}
    low_links: dict[str, int] = {}
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        low_links[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for target in sorted(graph[node]):
            if target not in indices:
                visit(target)
                low_links[node] = min(low_links[node], low_links[target])
            elif target in on_stack:
                low_links[node] = min(low_links[node], indices[target])

        if low_links[node] != indices[node]:
            return
        component: list[str] = []
        while stack:
            target = stack.pop()
            on_stack.remove(target)
            component.append(target)
            if target == node:
                break
        component.sort()
        if len(component) > 1 or node in graph[node]:
            components.append(component)

    for node in sorted(graph):
        if node not in indices:
            visit(node)
    return sorted(components)


def collect_assemblies(
    root: Path, additional_roots: Iterable[Path] = ()
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in sorted(
        iter_scan_files(root, ".asmdef", additional_roots),
        key=lambda value: relative_path(value, root),
    ):
        data, error = read_json(path)
        if data is None:
            errors.append({"path": relative_path(path, root), "error": error or "unknown"})
            continue
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append({"path": relative_path(path, root), "error": "missing assembly name"})
            continue
        references = sorted(
            reference
            for reference in data.get("references", [])
            if isinstance(reference, str)
        )
        items.append(
            {
                "name": name,
                "path": relative_path(path, root),
                "references": references,
                "includePlatforms": sorted(
                    value for value in data.get("includePlatforms", []) if isinstance(value, str)
                ),
                "excludePlatforms": sorted(
                    value for value in data.get("excludePlatforms", []) if isinstance(value, str)
                ),
            }
        )

    items.sort(key=lambda item: (item["name"], item["path"]))
    known_names = {item["name"] for item in items}
    edge_pairs: list[tuple[str, str]] = []
    edges: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []
    for item in items:
        for reference in item["references"]:
            if reference in known_names:
                edge_pairs.append((item["name"], reference))
                edges.append({"from": item["name"], "to": reference, "path": item["path"]})
            elif not reference.startswith(("Unity.", "UnityEngine.", "UnityEditor.")):
                unresolved.append(
                    {"assembly": item["name"], "reference": reference, "path": item["path"]}
                )

    return {
        "items": items,
        "edges": sorted(edges, key=lambda item: (item["from"], item["to"], item["path"])),
        "unresolvedReferences": sorted(
            unresolved,
            key=lambda item: (item["assembly"], item["reference"], item["path"]),
        ),
        "cycles": find_cycles(known_names, edge_pairs),
        "parseErrors": sorted(errors, key=lambda item: item["path"]),
    }


def read_package_lock(root: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    path = root / "Packages" / "packages-lock.json"
    if not path.is_file():
        return {}, []
    data, error = read_json(path)
    relative = relative_path(path, root)
    if data is None:
        return {}, [{"path": relative, "error": error or "unknown"}]
    dependencies = data.get("dependencies")
    if not isinstance(dependencies, dict):
        return {}, [{"path": relative, "error": "missing dependencies object"}]

    resolved: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    for name, value in dependencies.items():
        if not isinstance(name, str) or MARKER_VALUE.fullmatch(name) is None:
            errors.append({"path": relative, "error": "invalid dependency name"})
            continue
        if not isinstance(value, dict):
            errors.append(
                {"path": relative, "error": f"invalid dependency record for {name}"}
            )
            continue
        source = value.get("source")
        version = value.get("version")
        depth = value.get("depth")
        nested_dependencies = value.get("dependencies")
        valid = True
        if source not in SUPPORTED_LOCK_SOURCES:
            errors.append({"path": relative, "error": f"invalid source for {name}"})
            valid = False
        if not isinstance(version, str) or not version.strip():
            errors.append({"path": relative, "error": f"missing version for {name}"})
            valid = False
        if (
            not isinstance(depth, int)
            or isinstance(depth, bool)
            or depth < 0
        ):
            errors.append({"path": relative, "error": f"invalid depth for {name}"})
            valid = False
        if not isinstance(nested_dependencies, dict) or any(
            not isinstance(dependency_name, str)
            or MARKER_VALUE.fullmatch(dependency_name) is None
            or not isinstance(dependency_version, str)
            or not dependency_version.strip()
            for dependency_name, dependency_version in (
                nested_dependencies.items()
                if isinstance(nested_dependencies, dict)
                else ()
            )
        ):
            errors.append(
                {"path": relative, "error": f"invalid dependencies for {name}"}
            )
            valid = False
        if source == "git":
            git_hash = value.get("hash")
            if not isinstance(git_hash, str) or GIT_COMMIT_HASH.fullmatch(git_hash) is None:
                errors.append({"path": relative, "error": f"invalid git hash for {name}"})
                valid = False
        if source in {"embedded", "local", "local-tarball"} and isinstance(version, str):
            if (
                not version.startswith("file:")
                or not version[len("file:") :].strip()
                or resolve_file_reference(version, root / "Packages") is None
            ):
                errors.append(
                    {"path": relative, "error": f"invalid file source for {name}"}
                )
                valid = False
        if valid:
            resolved[name] = value
    return resolved, errors


def read_project_cache(
    root: Path,
) -> tuple[dict[str, list[dict[str, str]]], list[dict[str, str]]]:
    path = root / "Library" / "PackageManager" / "ProjectCache"
    if not path.is_file():
        return {}, []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}, [
            {"path": relative_path(path, root), "error": "project cache read failed"}
        ]

    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    def finish_current() -> None:
        if current is not None and current.get("name") and current.get("rootName"):
            records.append(dict(current))

    for line in lines:
        if line.startswith("- packageId: "):
            finish_current()
            current = {"packageId": line[len("- packageId: ") :].strip()}
            continue
        if current is None:
            continue
        if line.startswith("  resolvedPath: "):
            resolved_path = line[len("  resolvedPath: ") :].strip()
            if resolved_path:
                current["rootName"] = Path(resolved_path).name
        elif line.startswith("  name: "):
            current["name"] = line[len("  name: ") :].strip()
        elif line.startswith("  version: "):
            current["version"] = line[len("  version: ") :].strip()
        elif line.startswith("    hash: "):
            current["gitHash"] = line[len("    hash: ") :].strip()
    finish_current()

    by_name: dict[str, list[dict[str, str]]] = {}
    for record in records:
        by_name.setdefault(record["name"], []).append(record)
    return by_name, []


def cache_record_matches_lock(
    root: Path,
    record: dict[str, Any],
    lock_entry: dict[str, Any],
    project_cache: dict[str, list[dict[str, str]]],
) -> bool:
    manifest = record["_manifest"]
    package_name = record["packageName"]
    if manifest is None or package_name is None:
        return False
    manifest_version = manifest.get("version")
    if not isinstance(manifest_version, str):
        return False

    source = lock_entry.get("source")
    lock_version = lock_entry.get("version")
    if source in {"registry", "builtin"}:
        return isinstance(lock_version, str) and manifest_version == lock_version

    root_project_records = [
        value
        for value in project_cache.get(package_name, [])
        if value.get("rootName") == record["_root"].name
    ]
    matching_project_records = [
        value
        for value in root_project_records
        if value.get("version") == manifest_version
    ]
    if source == "git":
        lock_hash = lock_entry.get("hash")
        if isinstance(lock_hash, str) and lock_hash and isinstance(lock_version, str):
            expected_package_id = package_name + "@" + lock_version
            if root_project_records:
                return any(
                    value.get("gitHash") == lock_hash
                    and value.get("packageId") == expected_package_id
                    for value in matching_project_records
                )
            return record["_root"].name.endswith("@" + lock_hash[:12])
        return False
    if source == "local-tarball":
        if not isinstance(lock_version, str):
            return False
        expected_file = resolve_file_reference(lock_version, root / "Packages")
        if expected_file is None:
            return False
        return any(
            resolve_file_reference(
                value.get("packageId", "").removeprefix(package_name + "@"),
                root / "Packages",
            )
            == expected_file
            for value in matching_project_records
        )
    if source == "local":
        return False
    return len(matching_project_records) == 1


def resolve_file_reference(value: str, base: Path) -> Path | None:
    try:
        if not value.startswith("file:"):
            return None
        path_value = value[len("file:") :].strip()
        if not path_value:
            return None
        path = Path(path_value)
        if not path.is_absolute():
            path = base / path
        return path.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None


def discover_package_roots(
    root: Path,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[str],
]:
    package_lock, lock_errors = read_package_lock(root)
    project_cache, project_cache_errors = read_project_cache(root)
    records: list[dict[str, Any]] = []
    for source, parent in (
        ("embedded", root / "Packages"),
        ("package-cache", root / "Library" / "PackageCache"),
    ):
        if not parent.is_dir():
            continue
        for package_root in sorted(parent.iterdir(), key=lambda value: value.as_posix()):
            if not package_root.is_dir():
                continue
            manifest_path = package_root / "package.json"
            guide_path = package_root / "AI_GUIDE.md"
            if not manifest_path.is_file() and not guide_path.is_file():
                continue

            manifest: dict[str, Any] | None = None
            manifest_error: str | None = None
            package_name: str | None = None
            if manifest_path.is_file():
                manifest, manifest_error = read_json(manifest_path)
                if manifest is not None:
                    value = manifest.get("name")
                    if isinstance(value, str) and MARKER_VALUE.fullmatch(value) is not None:
                        package_name = value
                    else:
                        manifest_error = "missing or invalid package name"

            records.append(
                {
                    "source": source,
                    "rootPath": relative_path(package_root, root),
                    "manifestPath": (
                        relative_path(manifest_path, root)
                        if manifest_path.is_file()
                        else None
                    ),
                    "guidePath": (
                        relative_path(guide_path, root) if guide_path.is_file() else None
                    ),
                    "packageName": package_name,
                    "manifestError": manifest_error,
                    "active": source == "embedded",
                    "resolution": "active" if source == "embedded" else "unresolved",
                    "resolutionIssue": None,
                    "_root": package_root,
                    "_manifest": manifest,
                }
            )

    embedded_names = {
        record["packageName"]
        for record in records
        if record["source"] == "embedded" and record["packageName"] is not None
    }
    cache_groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record["source"] != "package-cache" or record["packageName"] is None:
            continue
        cache_groups.setdefault(record["packageName"], []).append(record)

    locked_cache_names = {
        name
        for name, value in package_lock.items()
        if value.get("source") != "embedded"
    }
    for package_name, group in cache_groups.items():
        if package_name in embedded_names:
            for record in group:
                record["resolution"] = "embedded-shadow"
            continue
        if package_name not in locked_cache_names:
            for record in group:
                record["resolution"] = "not-installed"
            continue
        matching = [
            record
            for record in group
            if cache_record_matches_lock(
                root, record, package_lock[package_name], project_cache
            )
        ]
        if len(matching) > 1:
            for record in group:
                record["resolution"] = "ambiguous"
                record["resolutionIssue"] = "ambiguous-package-cache-resolution"
            continue
        if not matching:
            for record in group:
                record["resolution"] = "lock-mismatch"
                record["resolutionIssue"] = "package-cache-lock-mismatch"
            continue
        matching[0]["active"] = True
        matching[0]["resolution"] = "active"
        for record in group:
            if record is not matching[0]:
                record["resolution"] = "not-resolved"

    unscanned_local_packages = sorted(
        package_name
        for package_name, lock_entry in package_lock.items()
        if lock_entry.get("source") == "local"
    )
    return (
        records,
        lock_errors + project_cache_errors,
        lock_errors,
        unscanned_local_packages,
    )


def collect_packages(
    package_roots: list[dict[str, Any]], lock_errors: list[dict[str, str]]
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = list(lock_errors)
    for record in package_roots:
        if record["resolutionIssue"] is not None and record["manifestPath"] is not None:
            errors.append(
                {
                    "path": record["manifestPath"],
                    "error": record["resolutionIssue"],
                }
            )
        if (
            record["source"] == "package-cache"
            and record["resolution"] == "unresolved"
            and record["manifestPath"] is not None
            and record["manifestError"] is not None
        ):
            errors.append(
                {
                    "path": record["manifestPath"],
                    "error": record["manifestError"],
                }
            )
        if not record["active"] or record["manifestPath"] is None:
            continue
        data = record["_manifest"]
        name = record["packageName"]
        if data is None or name is None:
            errors.append(
                {
                    "path": record["manifestPath"],
                    "error": record["manifestError"] or "unknown",
                }
            )
            continue
        dependencies = data.get("dependencies", {})
        if not isinstance(dependencies, dict):
            dependencies = {}
        items.append(
            {
                "name": name,
                "version": sanitize_dependency_value(data.get("version", "")),
                "path": record["manifestPath"],
                "source": record["source"],
                "dependencies": {
                    key: sanitize_dependency_value(value)
                    for key, value in sorted(dependencies.items())
                    if isinstance(key, str) and MARKER_VALUE.fullmatch(key) is not None
                },
            }
        )

    items.sort(key=lambda item: (item["name"], item["path"]))
    known_names = {item["name"] for item in items}
    edge_pairs: list[tuple[str, str]] = []
    edges: list[dict[str, str]] = []
    external: list[dict[str, str]] = []
    for item in items:
        for dependency, version in item["dependencies"].items():
            record = {
                "from": item["name"],
                "to": dependency,
                "version": version,
                "path": item["path"],
            }
            if dependency in known_names:
                edge_pairs.append((item["name"], dependency))
                edges.append(record)
            else:
                external.append(record)

    sort_key = lambda item: (item["from"], item["to"], item["path"])
    return {
        "items": items,
        "edges": sorted(edges, key=sort_key),
        "externalDependencies": sorted(external, key=sort_key),
        "cycles": find_cycles(known_names, edge_pairs),
        "parseErrors": sorted(errors, key=lambda item: item["path"]),
    }


def markdown_indent_columns(line: str) -> int:
    columns = 0
    for character in line:
        if character == " ":
            columns += 1
        elif character == "\t":
            columns += 4 - (columns % 4)
        else:
            break
    return columns


def markdown_visible_line_indices(lines: list[str]) -> set[int]:
    visible: set[int] = set()
    fence_character: str | None = None
    fence_length = 0
    in_comment = False

    for index, line in enumerate(lines):
        trimmed = line.strip()
        is_indented_code = markdown_indent_columns(line) >= 4
        fence = MARKDOWN_FENCE.match(trimmed)
        if fence_character is not None:
            if not is_indented_code and re.fullmatch(
                re.escape(fence_character) + "{" + str(fence_length) + ",}",
                trimmed,
            ):
                fence_character = None
                fence_length = 0
            continue
        if is_indented_code:
            continue
        if not in_comment and fence is not None:
            token = fence.group(1)
            fence_character = token[0]
            fence_length = len(token)
            continue

        comment_touched = in_comment
        cursor = 0
        while cursor < len(line):
            if in_comment:
                end = line.find("-->", cursor)
                if end < 0:
                    cursor = len(line)
                else:
                    in_comment = False
                    comment_touched = True
                    cursor = end + 3
            else:
                start = line.find("<!--", cursor)
                if start < 0:
                    cursor = len(line)
                else:
                    in_comment = True
                    comment_touched = True
                    cursor = start + 4
        if not comment_touched:
            visible.add(index)

    return visible


def identity_section_lines(
    lines: list[str], visible_lines: set[int]
) -> tuple[set[int], int]:
    section_lines: set[int] = set()
    heading_indices = [
        index
        for index, line in enumerate(lines)
        if index in visible_lines and line.strip() == PACKAGE_IDENTITY_HEADING
    ]
    for heading_index in heading_indices:
        end_index = len(lines)
        for index in range(heading_index + 1, len(lines)):
            if index in visible_lines and lines[index].strip().startswith("## "):
                end_index = index
                break
        section_lines.update(
            index
            for index in range(heading_index + 1, end_index)
            if index in visible_lines
        )
    return section_lines, len(heading_indices)


def parse_marker_line(line: str, label: str) -> tuple[bool, str | None]:
    trimmed = line.strip()
    if trimmed.startswith("- " + label):
        return True, None
    if not trimmed.startswith(label):
        return False, None
    prefix = label + " "
    if not trimmed.startswith(prefix):
        return True, None
    value = trimmed[len(prefix) :]
    if MARKER_VALUE.fullmatch(value) is None:
        return True, None
    return True, value


def parse_product_declaration(
    root: Path, record: dict[str, Any]
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    guide_path_value = record["guidePath"]
    if guide_path_value is None:
        return None, []
    guide_path = root / guide_path_value
    try:
        lines = guide_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None, [{"code": "guide-read-error", "path": guide_path_value}]

    visible_lines = markdown_visible_line_indices(lines)
    identity_lines, identity_heading_count = identity_section_lines(
        lines, visible_lines
    )
    roots: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        if index not in visible_lines:
            continue
        root_match, root_value = parse_marker_line(line, PRODUCT_ROOT_LABEL)
        if root_match:
            roots.append(
                {
                    "line": index + 1,
                    "value": root_value,
                    "inIdentity": index in identity_lines,
                }
            )
        target_match, target_value = parse_marker_line(line, PRODUCT_TARGET_LABEL)
        if target_match:
            targets.append(
                {
                    "line": index + 1,
                    "value": target_value,
                    "inIdentity": index in identity_lines,
                }
            )

    if not roots and not targets:
        return None, []

    diagnostics: list[dict[str, Any]] = []

    def add_diagnostic(code: str, line: int | None = None) -> None:
        diagnostic: dict[str, Any] = {"code": code, "path": guide_path_value}
        if line is not None:
            diagnostic["line"] = line
        diagnostics.append(diagnostic)

    if identity_heading_count != 1:
        add_diagnostic("invalid-package-identity-section")
    if not roots or not targets:
        add_diagnostic("incomplete-declaration")
    if len(roots) > 1:
        add_diagnostic("duplicate-root-marker")
    if len(targets) > 1:
        add_diagnostic("duplicate-target-marker")
    for marker in roots + targets:
        if not marker["inIdentity"]:
            add_diagnostic("declaration-outside-package-identity", marker["line"])
        if marker["value"] is None:
            add_diagnostic("invalid-marker-value", marker["line"])

    if record["manifestPath"] is None:
        add_diagnostic("missing-package-manifest")
    elif record["_manifest"] is None or record["packageName"] is None:
        add_diagnostic("invalid-package-manifest")

    root_marker = roots[0] if len(roots) == 1 else None
    target_marker = targets[0] if len(targets) == 1 else None
    root_value = root_marker["value"] if root_marker is not None else None
    target_value = target_marker["value"] if target_marker is not None else None
    if (
        root_value is not None
        and record["packageName"] is not None
        and root_value != record["packageName"]
    ):
        add_diagnostic("root-package-mismatch", root_marker["line"])
    if target_value is not None and target_value != SUPPORTED_PRODUCT_TARGET:
        add_diagnostic("unsupported-target", target_marker["line"])

    diagnostics.sort(
        key=lambda item: (item["code"], item["path"], item.get("line", 0))
    )
    declaration = {
        "packageName": record["packageName"],
        "root": root_value,
        "target": target_value,
        "source": record["source"],
        "guidePath": guide_path_value,
        "manifestPath": record["manifestPath"],
        "rootLine": root_marker["line"] if root_marker is not None else None,
        "targetLine": target_marker["line"] if target_marker is not None else None,
        "issues": sorted({item["code"] for item in diagnostics}),
    }
    return declaration, diagnostics


def collect_product_composition(
    root: Path,
    package_roots: list[dict[str, Any]],
    lock_errors: list[dict[str, str]],
    unscanned_local_packages: list[str],
) -> dict[str, Any]:
    declarations: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = [
        {"code": "invalid-package-lock", "path": path}
        for path in sorted({error["path"] for error in lock_errors})
    ]
    diagnostics.extend(
        {
            "code": "unscanned-local-package",
            "path": "Packages/packages-lock.json",
            "packageName": package_name,
        }
        for package_name in unscanned_local_packages
    )
    shadowed: list[dict[str, Any]] = []
    scanned_guide_count = 0

    for record in package_roots:
        if record["guidePath"] is None:
            continue
        declaration, declaration_diagnostics = parse_product_declaration(root, record)
        if record["active"]:
            scanned_guide_count += 1
            if declaration is not None:
                declarations.append(declaration)
            diagnostics.extend(declaration_diagnostics)
        elif declaration is not None and record["resolution"] == "embedded-shadow":
            shadowed.append(
                {
                    "packageName": record["packageName"],
                    "source": record["source"],
                    "guidePath": record["guidePath"],
                    "manifestPath": record["manifestPath"],
                }
            )
        elif declaration is not None and record["resolutionIssue"] is not None:
            resolution_code = record["resolutionIssue"]
            declaration["issues"] = sorted(
                set(declaration["issues"]) | {resolution_code}
            )
            declarations.append(declaration)
            diagnostics.extend(declaration_diagnostics)
            diagnostic: dict[str, Any] = {
                "code": resolution_code,
                "path": declaration["guidePath"],
            }
            if declaration["rootLine"] is not None:
                diagnostic["line"] = declaration["rootLine"]
            diagnostics.append(diagnostic)
        elif (
            declaration is not None
            and record["source"] == "package-cache"
            and record["resolution"] == "unresolved"
        ):
            resolution_code = "unresolved-package-cache-resolution"
            declaration["issues"] = sorted(
                set(declaration["issues"]) | {resolution_code}
            )
            declarations.append(declaration)
            diagnostics.extend(declaration_diagnostics)
            diagnostic = {
                "code": resolution_code,
                "path": declaration["guidePath"],
            }
            if declaration["rootLine"] is not None:
                diagnostic["line"] = declaration["rootLine"]
            diagnostics.append(diagnostic)

    declarations.sort(key=lambda item: (item["guidePath"], item["source"]))
    shadowed.sort(key=lambda item: (item["guidePath"], item["source"]))
    if len(declarations) > 1:
        for declaration in declarations:
            declaration["issues"] = sorted(
                set(declaration["issues"]) | {"duplicate-declaration"}
            )
            diagnostic: dict[str, Any] = {
                "code": "duplicate-declaration",
                "path": declaration["guidePath"],
            }
            if declaration["rootLine"] is not None:
                diagnostic["line"] = declaration["rootLine"]
            diagnostics.append(diagnostic)
    diagnostics.sort(
        key=lambda item: (
            item["code"],
            item["path"],
            item.get("packageName", ""),
            item.get("line", 0),
        )
    )

    selected: dict[str, Any] | None = None
    if not declarations and not diagnostics:
        status = "absent"
    elif len(declarations) == 1 and not diagnostics:
        status = "valid"
        selected = dict(declarations[0])
    else:
        status = "invalid"

    return {
        "status": status,
        "supportedTarget": SUPPORTED_PRODUCT_TARGET,
        "selected": selected,
        "declarations": declarations,
        "diagnostics": diagnostics,
        "shadowedDeclarations": shadowed,
        "unscannedLocalPackages": unscanned_local_packages,
        "scannedGuideCount": scanned_guide_count,
        "scanRoots": [
            name
            for name, path in (
                ("Packages", root / "Packages"),
                ("Library/PackageCache", root / "Library" / "PackageCache"),
            )
            if path.is_dir()
        ],
    }


def build_inventory(root: Path, max_candidates: int) -> dict[str, Any]:
    candidates, counts, scanned_csharp_files = collect_csharp_candidates(
        root, max_candidates
    )
    (
        package_roots,
        package_resolution_errors,
        package_lock_errors,
        unscanned_local_packages,
    ) = discover_package_roots(root)
    packages = collect_packages(package_roots, package_resolution_errors)
    cached_package_roots = [
        record["_root"]
        for record in package_roots
        if record["active"]
        and record["source"] == "package-cache"
        and record["_manifest"] is not None
        and record["packageName"] is not None
    ]
    assemblies = collect_assemblies(root, cached_package_roots)
    product_composition = collect_product_composition(
        root,
        package_roots,
        package_lock_errors,
        unscanned_local_packages,
    )
    total_candidate_matches = sum(counts.values())
    scan_roots = [name for name in ("Assets", "Packages") if (root / name).is_dir()]

    return {
        "schemaVersion": 2,
        "root": root.as_posix(),
        "scanRoots": scan_roots,
        "candidateSignals": candidates,
        "candidateCounts": dict(sorted(counts.items())),
        "candidateDetailsTruncated": total_candidate_matches > len(candidates),
        "assemblies": assemblies,
        "packages": packages,
        "productComposition": product_composition,
        "summary": {
            "scannedCSharpFiles": scanned_csharp_files,
            "candidateMatches": total_candidate_matches,
            "candidateDetails": len(candidates),
            "assemblyCount": len(assemblies["items"]),
            "assemblyCycleCount": len(assemblies["cycles"]),
            "packageCount": len(packages["items"]),
            "packageCycleCount": len(packages["cycles"]),
            "productCompositionStatus": product_composition["status"],
        },
    }


def render_text(inventory: dict[str, Any]) -> str:
    summary = inventory["summary"]
    lines = [
        "AI Refactor read-only inventory",
        f"Root: {inventory['root']}",
        f"Scan roots: {', '.join(inventory['scanRoots']) or 'none'}",
        f"C# files: {summary['scannedCSharpFiles']}",
        f"Candidate matches: {summary['candidateMatches']} (details: {summary['candidateDetails']})",
        f"Assemblies: {summary['assemblyCount']} (cycles: {summary['assemblyCycleCount']})",
        f"Packages: {summary['packageCount']} (cycles: {summary['packageCycleCount']})",
    ]
    product_composition = inventory["productComposition"]
    if product_composition["status"] == "absent":
        lines.append("Product composition: none declared")
    elif product_composition["status"] == "valid":
        selected = product_composition["selected"]
        lines.append(
            "Product composition: "
            f"{selected['packageName']} [{selected['target']}] ({selected['source']}) "
            f"at {selected['guidePath']}:{selected['rootLine']}"
        )
    else:
        diagnostic_codes = sorted(
            {item["code"] for item in product_composition["diagnostics"]}
        )
        lines.append(
            "Product composition: invalid ("
            + ", ".join(diagnostic_codes or ["unknown"])
            + ")"
        )
    if inventory["candidateDetailsTruncated"]:
        lines.append("Candidate details were truncated; counts include all matches.")
    for cycle in inventory["assemblies"]["cycles"]:
        lines.append("Assembly cycle: " + " -> ".join(cycle + [cycle[0]]))
    for cycle in inventory["packages"]["cycles"]:
        lines.append("Package cycle: " + " -> ".join(cycle + [cycle[0]]))
    for candidate in inventory["candidateSignals"]:
        lines.append(
            f"{candidate['path']}:{candidate['line']} [{candidate['kind']}] {candidate['snippet']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Repository root does not exist: {root}", file=sys.stderr)
        return 2
    inventory = build_inventory(root, args.max_candidates)
    if args.output_format == "json":
        print(json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(inventory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
