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


def iter_scan_files(root: Path, suffix: str) -> Iterable[Path]:
    for scan_root_name in ("Assets", "Packages"):
        scan_root = root / scan_root_name
        if not scan_root.is_dir():
            continue
        for path in scan_root.rglob(f"*{suffix}"):
            if path.is_file() and not is_excluded(path, root):
                yield path


def sanitize_snippet(line: str) -> str:
    redacted = STRING_LITERAL.sub('"<redacted>"', line)
    redacted = CHAR_LITERAL.sub("'<redacted>'", redacted)
    return " ".join(redacted.strip().split())[:200]


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
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exception:
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


def collect_assemblies(root: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in sorted(iter_scan_files(root, ".asmdef"), key=lambda value: relative_path(value, root)):
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


def collect_packages(root: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    packages_root = root / "Packages"
    if packages_root.is_dir():
        for path in sorted(packages_root.glob("*/package.json"), key=lambda value: relative_path(value, root)):
            data, error = read_json(path)
            if data is None:
                errors.append({"path": relative_path(path, root), "error": error or "unknown"})
                continue
            name = data.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append({"path": relative_path(path, root), "error": "missing package name"})
                continue
            dependencies = data.get("dependencies", {})
            if not isinstance(dependencies, dict):
                dependencies = {}
            items.append(
                {
                    "name": name,
                    "version": str(data.get("version", "")),
                    "path": relative_path(path, root),
                    "dependencies": {
                        key: str(value)
                        for key, value in sorted(dependencies.items())
                        if isinstance(key, str)
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


def build_inventory(root: Path, max_candidates: int) -> dict[str, Any]:
    candidates, counts, scanned_csharp_files = collect_csharp_candidates(
        root, max_candidates
    )
    assemblies = collect_assemblies(root)
    packages = collect_packages(root)
    total_candidate_matches = sum(counts.values())
    scan_roots = [name for name in ("Assets", "Packages") if (root / name).is_dir()]

    return {
        "schemaVersion": 1,
        "root": root.as_posix(),
        "scanRoots": scan_roots,
        "candidateSignals": candidates,
        "candidateCounts": dict(sorted(counts.items())),
        "candidateDetailsTruncated": total_candidate_matches > len(candidates),
        "assemblies": assemblies,
        "packages": packages,
        "summary": {
            "scannedCSharpFiles": scanned_csharp_files,
            "candidateMatches": total_candidate_matches,
            "candidateDetails": len(candidates),
            "assemblyCount": len(assemblies["items"]),
            "assemblyCycleCount": len(assemblies["cycles"]),
            "packageCount": len(packages["items"]),
            "packageCycleCount": len(packages["cycles"]),
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
