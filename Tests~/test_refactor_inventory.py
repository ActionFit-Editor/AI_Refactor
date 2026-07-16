#!/usr/bin/env python3
"""Behavior tests for the AI Refactor read-only inventory."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE_ROOT / "Skills~" / "Shared" / "scripts" / "refactor_inventory.py"


class RefactorInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self._write(
            "Assets/Game/Probe.cs",
            "using System.Collections;\n"
            "public sealed class Probe\n"
            "{\n"
            "    private async void Load() { GameObject.Find(\"SecretNode\"); }\n"
            "    private void Update() { PlayerPrefs.SetInt(\"private-key\", 1); }\n"
            "    private IEnumerator Wait() { yield break; }\n"
            "}\n",
        )
        self._write("Library/Ignored.cs", "void Update() { GameObject.Find(\"Ignored\"); }")
        self._write_json(
            "Assets/A/A.asmdef",
            {"name": "Fixture.A", "references": ["Fixture.B"], "includePlatforms": []},
        )
        self._write_json(
            "Assets/B/B.asmdef",
            {"name": "Fixture.B", "references": ["Fixture.A"], "includePlatforms": []},
        )
        self._write_json(
            "Packages/com.example.a/package.json",
            {
                "name": "com.example.a",
                "version": "1.0.0",
                "dependencies": {"com.example.b": "1.0.0"},
            },
        )
        self._write_json(
            "Packages/com.example.b/package.json",
            {
                "name": "com.example.b",
                "version": "1.0.0",
                "dependencies": {"com.example.a": "1.0.0"},
            },
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_json_is_deterministic_redacted_and_reports_cycles(self) -> None:
        before = self._snapshot()
        first = self._run("json")
        second = self._run("json")
        after = self._snapshot()

        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(before, after)
        result = json.loads(first.stdout)
        kinds = {candidate["kind"] for candidate in result["candidateSignals"]}
        self.assertTrue(
            {"scene-wide-discovery", "lifecycle-polling", "detached-async", "coroutine", "persistence"}
            <= kinds
        )
        self.assertNotIn("SecretNode", first.stdout)
        self.assertNotIn("private-key", first.stdout)
        self.assertNotIn("Library/Ignored.cs", first.stdout)
        self.assertEqual([["Fixture.A", "Fixture.B"]], result["assemblies"]["cycles"])
        self.assertEqual(
            [["com.example.a", "com.example.b"]], result["packages"]["cycles"]
        )
        self.assertEqual(1, result["summary"]["assemblyCycleCount"])
        self.assertEqual(1, result["summary"]["packageCycleCount"])

    def test_text_output_and_candidate_limit_remain_read_only(self) -> None:
        before = self._snapshot()
        completed = self._run("text", "--max-candidates", "1")
        after = self._snapshot()

        self.assertEqual(before, after)
        self.assertIn("AI Refactor read-only inventory", completed.stdout)
        self.assertIn("Assembly cycle: Fixture.A -> Fixture.B -> Fixture.A", completed.stdout)
        self.assertIn("Package cycle: com.example.a -> com.example.b -> com.example.a", completed.stdout)
        self.assertIn("Candidate details were truncated", completed.stdout)

    def _run(self, output_format: str, *extra: str) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(self.root),
                "--format",
                output_format,
                *extra,
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=self.root,
            env=environment,
        )

    def _write(self, relative: str, contents: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")

    def _write_json(self, relative: str, value: object) -> None:
        self._write(relative, json.dumps(value, indent=2, sort_keys=True))

    def _snapshot(self) -> dict[str, bytes]:
        return {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in sorted(self.root.rglob("*"))
            if path.is_file()
        }


if __name__ == "__main__":
    unittest.main()
