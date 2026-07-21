#!/usr/bin/env python3
"""Tests for the AI Refactor read-only AI Jira locator."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
LOCATOR_PATH = (
    PACKAGE_ROOT / "Skills~" / "Shared" / "scripts" / "ai_refactor_jira_cli.py"
)


def load_locator():
    spec = importlib.util.spec_from_file_location("ai_refactor_jira_cli_under_test", LOCATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load the AI Refactor Jira locator.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RefactorJiraCliTests(unittest.TestCase):
    def test_embedded_ai_jira_tools_are_preferred(self) -> None:
        locator = load_locator()
        with tempfile.TemporaryDirectory() as directory:
            root = self._project_root(directory)
            embedded = root / "Packages" / "com.actionfit.ai-jira" / "Tools~"
            embedded.mkdir(parents=True)
            cached = root / "Library" / "PackageCache" / "com.actionfit.ai-jira@hash" / "Tools~"
            cached.mkdir(parents=True)

            self.assertEqual(embedded, locator.find_jira_tools(root))

    def test_single_package_cache_ai_jira_tools_are_supported(self) -> None:
        locator = load_locator()
        with tempfile.TemporaryDirectory() as directory:
            root = self._project_root(directory)
            cached = root / "Library" / "PackageCache" / "com.actionfit.ai-jira@hash" / "Tools~"
            cached.mkdir(parents=True)

            self.assertEqual(cached, locator.find_jira_tools(root))

    def test_locked_package_cache_resolves_ambiguous_copies(self) -> None:
        locator = load_locator()
        with tempfile.TemporaryDirectory() as directory:
            root = self._project_root(directory)
            for version in ("old", "current"):
                (root / "Library" / "PackageCache" / f"com.actionfit.ai-jira@{version}" / "Tools~").mkdir(parents=True)
            (root / "Packages" / "packages-lock.json").write_text(
                json.dumps(
                    {"dependencies": {"com.actionfit.ai-jira": {"version": "current"}}}
                ),
                encoding="utf-8",
            )

            expected = root / "Library" / "PackageCache" / "com.actionfit.ai-jira@current" / "Tools~"
            self.assertEqual(expected, locator.find_jira_tools(root))

    def test_git_lock_hash_resolves_ambiguous_package_cache_copies(self) -> None:
        locator = load_locator()
        with tempfile.TemporaryDirectory() as directory:
            root = self._project_root(directory)
            for revision in ("111111111111", "abc123abc123"):
                (root / "Library" / "PackageCache" / f"com.actionfit.ai-jira@{revision}" / "Tools~").mkdir(parents=True)
            (root / "Packages" / "packages-lock.json").write_text(
                json.dumps(
                    {
                        "dependencies": {
                            "com.actionfit.ai-jira": {
                                "version": "https://example.invalid/AI_Jira.git#1.0.28",
                                "source": "git",
                                "hash": "abc123abc123ffffffffffffffffffffffffffff",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            expected = root / "Library" / "PackageCache" / "com.actionfit.ai-jira@abc123abc123" / "Tools~"
            self.assertEqual(expected, locator.find_jira_tools(root))

    def test_commands_dispatch_only_to_ai_jira_read_tools(self) -> None:
        locator = load_locator()
        with tempfile.TemporaryDirectory() as directory:
            root = self._project_root(directory)
            tools = root / "Packages" / "com.actionfit.ai-jira" / "Tools~"
            tools.mkdir(parents=True)
            for script_name in locator.COMMAND_SCRIPTS.values():
                (tools / script_name).write_text("", encoding="utf-8")

            cases = (("overlap", None), ("detail", "MCC-1563"))
            for command_name, issue_key in cases:
                argv = [str(LOCATOR_PATH), command_name]
                if issue_key:
                    argv.append(issue_key)
                argv.extend(("--format", "json"))
                expected = [sys.executable, str(tools / locator.COMMAND_SCRIPTS[command_name])]
                if issue_key:
                    expected.append(issue_key)
                expected.extend(("--format", "json"))

                with self.subTest(command=command_name), patch.object(
                    locator.Path, "cwd", return_value=root
                ), patch.object(locator.subprocess, "call", return_value=0) as subprocess_call, patch.object(
                    sys, "argv", argv
                ):
                    with self.assertRaises(SystemExit) as raised:
                        locator.main()

                self.assertEqual(0, raised.exception.code)
                subprocess_call.assert_called_once_with(expected, cwd=root)

    @staticmethod
    def _project_root(directory: str) -> Path:
        root = Path(directory).resolve()
        packages = root / "Packages"
        packages.mkdir()
        (packages / "manifest.json").write_text("{}", encoding="utf-8")
        return root


if __name__ == "__main__":
    unittest.main()
