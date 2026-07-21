#!/usr/bin/env python3
"""Locate and run the AI Jira read-only overlap tools for AI Refactor."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PACKAGE_ID = "com.actionfit.ai-jira"
COMMAND_SCRIPTS = {
    "overlap": "list_overlap_work_items.py",
    "detail": "get_work_item.py",
}


def find_project_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "Packages" / "manifest.json").is_file():
            return candidate
    raise SystemExit("Unity project root was not found. Run this command inside a Unity project.")


def find_jira_tools(project_root: Path) -> Path:
    embedded = project_root / "Packages" / PACKAGE_ID / "Tools~"
    if embedded.is_dir():
        return embedded

    cache_root = project_root / "Library" / "PackageCache"
    candidates = sorted(cache_root.glob(f"{PACKAGE_ID}@*/Tools~"))
    if len(candidates) == 1:
        return candidates[0]

    lock_path = project_root / "Packages" / "packages-lock.json"
    if lock_path.is_file():
        try:
            lock = json.loads(lock_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as error:
            raise SystemExit(f"Failed to read Packages/packages-lock.json: {error}") from error
        record = (lock.get("dependencies") or {}).get(PACKAGE_ID) or {}
        version = str(record.get("version", ""))
        revision = str(record.get("hash", ""))
        locked_matches = []
        for candidate in candidates:
            suffix = candidate.parent.name.removeprefix(f"{PACKAGE_ID}@")
            if suffix == version or (revision and revision.startswith(suffix)):
                locked_matches.append(candidate)
        if len(locked_matches) == 1:
            return locked_matches[0]
        if len(locked_matches) > 1:
            raise SystemExit("Multiple AI Jira PackageCache tools matched the active lock record.")

    if candidates:
        raise SystemExit("Multiple AI Jira PackageCache tools were found without one locked match.")
    raise SystemExit(
        "AI Jira package tools were not found. Install the required com.actionfit.ai-jira dependency."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an AI Jira overlap read-only command.")
    parser.add_argument("command", choices=tuple(COMMAND_SCRIPTS))
    parser.add_argument("issue_key", nargs="?")
    args, remainder = parser.parse_known_args()

    if args.command == "detail" and not args.issue_key:
        parser.error("detail requires an issue key")
    if args.command == "overlap" and args.issue_key:
        parser.error("overlap does not accept an issue key")

    root = find_project_root(Path.cwd().resolve())
    script = find_jira_tools(root) / COMMAND_SCRIPTS[args.command]
    command = [sys.executable, str(script)]
    if args.issue_key:
        command.append(args.issue_key)
    command.extend(remainder)
    raise SystemExit(subprocess.call(command, cwd=root))


if __name__ == "__main__":
    main()
