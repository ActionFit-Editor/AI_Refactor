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
        self.assertEqual(2, result["schemaVersion"])
        self.assertEqual("absent", result["productComposition"]["status"])
        self.assertIsNone(result["productComposition"]["selected"])
        self.assertEqual("absent", result["summary"]["productCompositionStatus"])
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
        self.assertEqual(
            {"com.example.a": "embedded", "com.example.b": "embedded"},
            {item["name"]: item["source"] for item in result["packages"]["items"]},
        )

    def test_text_output_and_candidate_limit_remain_read_only(self) -> None:
        before = self._snapshot()
        completed = self._run("text", "--max-candidates", "1")
        after = self._snapshot()

        self.assertEqual(before, after)
        self.assertIn("AI Refactor read-only inventory", completed.stdout)
        self.assertIn("Assembly cycle: Fixture.A -> Fixture.B -> Fixture.A", completed.stdout)
        self.assertIn("Package cycle: com.example.a -> com.example.b -> com.example.a", completed.stdout)
        self.assertIn("Product composition: none declared", completed.stdout)
        self.assertIn("Candidate details were truncated", completed.stdout)

    def test_valid_embedded_product_composition_has_line_evidence(self) -> None:
        self._write_product_guide("Packages/com.example.a", "com.example.a")

        result = json.loads(self._run("json").stdout)
        composition = result["productComposition"]

        self.assertEqual("valid", composition["status"])
        self.assertEqual(
            {
                "packageName": "com.example.a",
                "root": "com.example.a",
                "target": "package-oriented-product",
                "source": "embedded",
                "guidePath": "Packages/com.example.a/AI_GUIDE.md",
                "manifestPath": "Packages/com.example.a/package.json",
                "rootLine": 5,
                "targetLine": 6,
                "issues": [],
            },
            composition["selected"],
        )
        self.assertEqual([], composition["diagnostics"])
        self.assertIn(
            "Product composition: com.example.a [package-oriented-product] (embedded)",
            self._run("text").stdout,
        )

    def test_valid_package_cache_root_contributes_package_and_assembly_graphs(self) -> None:
        cache_root = "Library/PackageCache/com.example.cache@abc123"
        self._write_json(
            "Packages/packages-lock.json",
            {
                "dependencies": {
                    "com.example.cache": {
                        "version": "1.0.0",
                        "depth": 0,
                        "source": "registry",
                        "dependencies": {"com.example.cache-dependency": "1.0.0"},
                    },
                    "com.example.cache-dependency": {
                        "version": "1.0.0",
                        "depth": 1,
                        "source": "registry",
                        "dependencies": {"com.example.cache": "1.0.0"},
                    },
                }
            },
        )
        self._write_json(
            f"{cache_root}/package.json",
            {
                "name": "com.example.cache",
                "version": "1.0.0",
                "dependencies": {
                    "com.example.cache-dependency": "1.0.0",
                    "com.example.private": "https://user:credential@example.invalid/repo.git#secret",
                },
            },
        )
        dependency_root = "Library/PackageCache/com.example.cache-dependency@def456"
        self._write_json(
            f"{dependency_root}/package.json",
            {
                "name": "com.example.cache-dependency",
                "version": "1.0.0",
                "dependencies": {"com.example.cache": "1.0.0"},
            },
        )
        self._write_product_guide(cache_root, "com.example.cache")
        self._write_json(
            f"{cache_root}/Runtime/Cache.asmdef",
            {"name": "Cache", "references": ["Cache.Dependency"]},
        )
        self._write_json(
            f"{dependency_root}/Runtime/Dependency.asmdef",
            {"name": "Cache.Dependency", "references": ["Cache"]},
        )

        before = self._snapshot()
        first = self._run("json")
        second = self._run("json")
        after = self._snapshot()
        result = json.loads(first.stdout)

        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(before, after)
        self.assertEqual("valid", result["productComposition"]["status"])
        self.assertEqual(
            "package-cache", result["productComposition"]["selected"]["source"]
        )
        self.assertIn(
            "Library/PackageCache", result["productComposition"]["scanRoots"]
        )
        package_sources = {
            item["name"]: item["source"] for item in result["packages"]["items"]
        }
        self.assertEqual("package-cache", package_sources["com.example.cache"])
        cache_package = next(
            item
            for item in result["packages"]["items"]
            if item["name"] == "com.example.cache"
        )
        self.assertEqual("<redacted>", cache_package["dependencies"]["com.example.private"])
        self.assertNotIn("user:credential", first.stdout)
        self.assertNotIn("repo.git#secret", first.stdout)
        self.assertEqual(
            ["com.example.cache", "com.example.cache-dependency"],
            next(
                cycle
                for cycle in result["packages"]["cycles"]
                if "com.example.cache" in cycle
            ),
        )
        self.assertIn(["Cache", "Cache.Dependency"], result["assemblies"]["cycles"])

    def test_orphan_package_cache_declaration_is_not_an_installed_root(self) -> None:
        cache_root = "Library/PackageCache/com.example.orphan@stale"
        self._write_json("Packages/packages-lock.json", {"dependencies": {}})
        self._write_json(
            f"{cache_root}/package.json",
            {"name": "com.example.orphan", "version": "1.0.0"},
        )
        self._write_product_guide(cache_root, "com.example.orphan")

        result = json.loads(self._run("json").stdout)

        self.assertEqual("absent", result["productComposition"]["status"])
        self.assertNotIn(
            "com.example.orphan",
            {item["name"] for item in result["packages"]["items"]},
        )

    def test_duplicate_locked_package_cache_roots_are_ambiguous(self) -> None:
        self._write_json(
            "Packages/packages-lock.json",
            {
                "dependencies": {
                    "com.example.cache": {
                        "version": "1.0.0",
                        "depth": 0,
                        "source": "registry",
                        "dependencies": {},
                    }
                }
            },
        )
        first_root = "Library/PackageCache/com.example.cache@first"
        second_root = "Library/PackageCache/com.example.cache@second"
        for cache_root in (first_root, second_root):
            self._write_json(
                f"{cache_root}/package.json",
                {"name": "com.example.cache", "version": "1.0.0"},
            )
        self._write_product_guide(first_root, "com.example.cache")

        result = json.loads(self._run("json").stdout)
        composition = result["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertIsNone(composition["selected"])
        self.assertIn(
            "ambiguous-package-cache-resolution",
            self._diagnostic_codes(composition),
        )
        self.assertNotIn(
            "com.example.cache",
            {item["name"] for item in result["packages"]["items"]},
        )

    def test_registry_package_cache_version_mismatch_is_invalid(self) -> None:
        self._write_json(
            "Packages/packages-lock.json",
            {
                "dependencies": {
                    "com.example.cache": {
                        "version": "2.0.0",
                        "depth": 0,
                        "source": "registry",
                        "dependencies": {},
                    }
                }
            },
        )
        cache_root = "Library/PackageCache/com.example.cache@stale"
        self._write_json(
            f"{cache_root}/package.json",
            {"name": "com.example.cache", "version": "1.0.0"},
        )
        self._write_product_guide(cache_root, "com.example.cache")

        result = json.loads(self._run("json").stdout)
        composition = result["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertIsNone(composition["selected"])
        self.assertIn("package-cache-lock-mismatch", self._diagnostic_codes(composition))
        self.assertNotIn(
            "com.example.cache",
            {item["name"] for item in result["packages"]["items"]},
        )

    def test_git_package_cache_uses_project_cache_provenance(self) -> None:
        cache_root = "Library/PackageCache/com.example.git@fingerprint"
        commit = "1234567890abcdef1234567890abcdef12345678"
        self._write_json(
            "Packages/packages-lock.json",
            {
                "dependencies": {
                    "com.example.git": {
                        "version": "https://example.invalid/repository.git",
                        "depth": 0,
                        "source": "git",
                        "dependencies": {},
                        "hash": commit,
                    }
                }
            },
        )
        self._write_json(
            f"{cache_root}/package.json",
            {"name": "com.example.git", "version": "3.0.0"},
        )
        self._write_product_guide(cache_root, "com.example.git")
        self._write(
            "Library/PackageManager/ProjectCache",
            "m_UpmPackages:\n"
            "- packageId: com.example.git@https://example.invalid/repository.git\n"
            "  version: 3.0.0\n"
            f"  resolvedPath: {self.root}/{cache_root}\n"
            "  name: com.example.git\n"
            "  git:\n"
            f"    hash: {commit}\n",
        )

        result = json.loads(self._run("json").stdout)

        self.assertEqual("valid", result["productComposition"]["status"])
        self.assertEqual("com.example.git", result["productComposition"]["selected"]["root"])
        self.assertIn(
            "com.example.git",
            {item["name"] for item in result["packages"]["items"]},
        )

    def test_git_project_cache_conflict_beats_hash_prefix_fallback(self) -> None:
        commit = "1234567890abcdef1234567890abcdef12345678"
        cache_root = f"Library/PackageCache/com.example.git@{commit[:12]}"
        self._write_json(
            "Packages/packages-lock.json",
            {
                "dependencies": {
                    "com.example.git": {
                        "version": "https://example.invalid/repository.git",
                        "depth": 0,
                        "source": "git",
                        "dependencies": {},
                        "hash": commit,
                    }
                }
            },
        )
        self._write_json(
            f"{cache_root}/package.json",
            {"name": "com.example.git", "version": "3.0.0"},
        )
        self._write_product_guide(cache_root, "com.example.git")
        self._write(
            "Library/PackageManager/ProjectCache",
            "m_UpmPackages:\n"
            "- packageId: com.example.git@https://example.invalid/repository.git\n"
            "  version: 3.0.0\n"
            f"  resolvedPath: {self.root}/{cache_root}\n"
            "  name: com.example.git\n"
            "  git:\n"
            "    hash: abcdef1234567890abcdef1234567890abcdef12\n",
        )

        composition = json.loads(self._run("json").stdout)["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertIn("package-cache-lock-mismatch", self._diagnostic_codes(composition))

    def test_local_tarball_cache_uses_project_cache_source(self) -> None:
        cache_root = "Library/PackageCache/com.example.local@fingerprint"
        lock_value = "file:../Packages/com.example.local-4.0.0.tgz"
        self._write_json(
            "Packages/packages-lock.json",
            {
                "dependencies": {
                    "com.example.local": {
                        "version": lock_value,
                        "depth": 0,
                        "source": "local-tarball",
                        "dependencies": {},
                    }
                }
            },
        )
        self._write_json(
            f"{cache_root}/package.json",
            {"name": "com.example.local", "version": "4.0.0"},
        )
        self._write_product_guide(cache_root, "com.example.local")
        self._write(
            "Library/PackageManager/ProjectCache",
            "m_UpmPackages:\n"
            f"- packageId: com.example.local@file:{self.root}/Packages/com.example.local-4.0.0.tgz\n"
            "  version: 4.0.0\n"
            f"  resolvedPath: {self.root}/{cache_root}\n"
            "  name: com.example.local\n",
        )

        result = json.loads(self._run("json").stdout)

        self.assertEqual("valid", result["productComposition"]["status"])
        self.assertEqual(
            "com.example.local", result["productComposition"]["selected"]["root"]
        )

    def test_local_tarball_same_filename_different_path_is_invalid(self) -> None:
        cache_root = "Library/PackageCache/com.example.local@fingerprint"
        self._write_json(
            "Packages/packages-lock.json",
            {
                "dependencies": {
                    "com.example.local": {
                        "version": "file:../Expected/com.example.local-4.0.0.tgz",
                        "depth": 0,
                        "source": "local-tarball",
                        "dependencies": {},
                    }
                }
            },
        )
        self._write_json(
            f"{cache_root}/package.json",
            {"name": "com.example.local", "version": "4.0.0"},
        )
        self._write_product_guide(cache_root, "com.example.local")
        self._write(
            "Library/PackageManager/ProjectCache",
            "m_UpmPackages:\n"
            f"- packageId: com.example.local@file:{self.root}/Different/com.example.local-4.0.0.tgz\n"
            "  version: 4.0.0\n"
            f"  resolvedPath: {self.root}/{cache_root}\n"
            "  name: com.example.local\n",
        )

        composition = json.loads(self._run("json").stdout)["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertIn("package-cache-lock-mismatch", self._diagnostic_codes(composition))

    def test_external_local_lock_source_is_valid_but_not_scanned(self) -> None:
        self._write_json(
            "Packages/packages-lock.json",
            {
                "dependencies": {
                    "com.example.local": {
                        "version": "file:../External/com.example.local",
                        "depth": 0,
                        "source": "local",
                        "dependencies": {},
                    }
                }
            },
        )

        result = json.loads(self._run("json").stdout)
        composition = result["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertIsNone(composition["selected"])
        self.assertEqual(
            ["com.example.local"], composition["unscannedLocalPackages"]
        )
        self.assertIn(
            "unscanned-local-package", self._diagnostic_codes(composition)
        )
        self.assertEqual([], result["packages"]["parseErrors"])
        self.assertNotIn(
            "com.example.local",
            {item["name"] for item in result["packages"]["items"]},
        )

        self._write_product_guide("Packages/com.example.a", "com.example.a")
        composition_with_embedded_root = json.loads(self._run("json").stdout)[
            "productComposition"
        ]

        self.assertEqual("invalid", composition_with_embedded_root["status"])
        self.assertIsNone(composition_with_embedded_root["selected"])
        self.assertEqual(1, len(composition_with_embedded_root["declarations"]))
        self.assertIn(
            "unscanned-local-package",
            self._diagnostic_codes(composition_with_embedded_root),
        )

    def test_invalid_file_references_do_not_crash_or_select_product(self) -> None:
        invalid_versions = ["file:\0"]
        loop_a = self.root / "LocalLoopA"
        loop_b = self.root / "LocalLoopB"
        try:
            loop_a.symlink_to(loop_b)
            loop_b.symlink_to(loop_a)
        except OSError:
            pass
        else:
            invalid_versions.append("file:../LocalLoopA/package.tgz")

        for invalid_version in invalid_versions:
            with self.subTest(invalid_version=repr(invalid_version)):
                self._write_json(
                    "Packages/packages-lock.json",
                    {
                        "dependencies": {
                            "com.example.local": {
                                "version": invalid_version,
                                "depth": 0,
                                "source": "local-tarball",
                                "dependencies": {},
                            }
                        }
                    },
                )

                result = json.loads(self._run("json").stdout)
                composition = result["productComposition"]

                self.assertEqual("invalid", composition["status"])
                self.assertIsNone(composition["selected"])
                self.assertIn(
                    "invalid-package-lock", self._diagnostic_codes(composition)
                )

    def test_invalid_package_lock_blocks_generic_product_fallback(self) -> None:
        cache_root = "Library/PackageCache/com.example.cache@unknown"
        self._write("Packages/packages-lock.json", "{ invalid json")
        self._write_json(
            f"{cache_root}/package.json",
            {"name": "com.example.cache", "version": "1.0.0"},
        )
        self._write_product_guide(cache_root, "com.example.cache")

        result = json.loads(self._run("json").stdout)
        composition = result["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertIsNone(composition["selected"])
        self.assertIn("invalid-package-lock", self._diagnostic_codes(composition))

    def test_semantically_invalid_package_lock_blocks_product_selection(self) -> None:
        cache_root = "Library/PackageCache/com.example.cache@unknown"
        self._write_json(
            f"{cache_root}/package.json",
            {"name": "com.example.cache", "version": "1.0.0"},
        )
        self._write_product_guide(cache_root, "com.example.cache")

        for invalid_record in (
            {},
            "invalid",
            {
                "version": "1.0.0",
                "source": "registry",
                "dependencies": {},
            },
            {
                "version": "https://example.invalid/repository.git",
                "depth": 0,
                "source": "git",
                "dependencies": {},
            },
            {
                "version": " ",
                "depth": 0,
                "source": "registry",
                "dependencies": {},
            },
            {
                "version": "file:",
                "depth": 0,
                "source": "embedded",
                "dependencies": {},
            },
            {
                "version": "1.0.0",
                "depth": 0,
                "source": "registry",
                "dependencies": {"com.example.dependency": ""},
            },
        ):
            with self.subTest(invalid_record=invalid_record):
                self._write_json(
                    "Packages/packages-lock.json",
                    {"dependencies": {"com.example.cache": invalid_record}},
                )
                composition = json.loads(self._run("json").stdout)[
                    "productComposition"
                ]

                self.assertEqual("invalid", composition["status"])
                self.assertIsNone(composition["selected"])
                self.assertIn(
                    "invalid-package-lock", self._diagnostic_codes(composition)
                )

    def test_unresolved_cache_manifest_with_marker_is_invalid(self) -> None:
        cache_root = "Library/PackageCache/com.example.cache@broken"
        self._write_json(
            "Packages/packages-lock.json",
            {
                "dependencies": {
                    "com.example.cache": {
                        "version": "1.0.0",
                        "depth": 0,
                        "source": "registry",
                        "dependencies": {},
                    }
                }
            },
        )
        self._write(f"{cache_root}/package.json", "{ invalid json")
        self._write_product_guide(cache_root, "com.example.cache")

        result = json.loads(self._run("json").stdout)
        composition = result["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertIn(
            "unresolved-package-cache-resolution",
            self._diagnostic_codes(composition),
        )
        self.assertTrue(
            any(
                item["path"] == f"{cache_root}/package.json"
                for item in result["packages"]["parseErrors"]
            )
        )

    def test_markers_in_fences_and_comments_do_not_opt_in(self) -> None:
        self._write(
            "Packages/com.example.a/AI_GUIDE.md",
            "# Guide\n\n"
            "## Package Identity\n"
            "```text\n"
            "AI Product Composition Root: com.example.a\n"
            "AI Refactor target: package-oriented-product\n"
            "```\n"
            "<!--\n"
            "AI Product Composition Root: com.example.a\n"
            "AI Refactor target: package-oriented-product\n"
            "-->\n\n"
            "    AI Product Composition Root: com.example.a\n"
            "    AI Refactor target: package-oriented-product\n\n"
            " \tAI Product Composition Root: com.example.a\n"
            " \tAI Refactor target: package-oriented-product\n"
            "  \tAI Product Composition Root: com.example.a\n"
            "  \tAI Refactor target: package-oriented-product\n"
            "   \tAI Product Composition Root: com.example.a\n"
            "   \tAI Refactor target: package-oriented-product\n\n"
            "````text\n"
            "````not-a-commonmark-close\n"
            "AI Product Composition Root: com.example.a\n"
            "AI Refactor target: package-oriented-product\n"
            "````\n\n"
            "    ```text\n"
            "    AI Product Composition Root: com.example.a\n"
            "    AI Refactor target: package-oriented-product\n"
            "    ```\n\n"
            "## Purpose\n",
        )

        composition = json.loads(self._run("json").stdout)["productComposition"]

        self.assertEqual("absent", composition["status"])
        self.assertEqual([], composition["declarations"])

    def test_utf8_bom_json_files_are_parsed_without_errors(self) -> None:
        package_path = "Packages/com.example.bom/package.json"
        assembly_path = "Packages/com.example.bom/Runtime/Bom.asmdef"
        self._write_bytes(
            package_path,
            b"\xef\xbb\xbf"
            + json.dumps(
                {"name": "com.example.bom", "version": "1.0.0"},
                sort_keys=True,
            ).encode("utf-8"),
        )
        self._write_bytes(
            assembly_path,
            b"\xef\xbb\xbf"
            + json.dumps(
                {"name": "Fixture.Bom", "references": []},
                sort_keys=True,
            ).encode("utf-8"),
        )

        result = json.loads(self._run("json").stdout)

        self.assertIn(
            "com.example.bom",
            {item["name"] for item in result["packages"]["items"]},
        )
        self.assertIn(
            "Fixture.Bom",
            {item["name"] for item in result["assemblies"]["items"]},
        )
        self.assertNotIn(
            package_path,
            {item["path"] for item in result["packages"]["parseErrors"]},
        )
        self.assertNotIn(
            assembly_path,
            {item["path"] for item in result["assemblies"]["parseErrors"]},
        )

    def test_embedded_package_shadows_same_id_package_cache_declaration(self) -> None:
        self._write_product_guide("Packages/com.example.a", "com.example.a")
        cache_root = "Library/PackageCache/com.example.a@stale"
        self._write_json(
            f"{cache_root}/package.json",
            {"name": "com.example.a", "version": "0.9.0"},
        )
        self._write_product_guide(
            cache_root, "com.example.a", target="unsupported-stale-target"
        )

        result = json.loads(self._run("json").stdout)
        composition = result["productComposition"]

        self.assertEqual("valid", composition["status"])
        self.assertEqual("embedded", composition["selected"]["source"])
        self.assertEqual(
            ["Library/PackageCache/com.example.a@stale/AI_GUIDE.md"],
            [item["guidePath"] for item in composition["shadowedDeclarations"]],
        )
        package_a = [
            item for item in result["packages"]["items"] if item["name"] == "com.example.a"
        ]
        self.assertEqual(1, len(package_a))
        self.assertEqual("embedded", package_a[0]["source"])

    def test_duplicate_product_roots_are_invalid_without_selection(self) -> None:
        self._write_product_guide("Packages/com.example.a", "com.example.a")
        self._write_product_guide("Packages/com.example.b", "com.example.b")

        composition = json.loads(self._run("json").stdout)["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertIsNone(composition["selected"])
        self.assertEqual(2, len(composition["declarations"]))
        self.assertIn("duplicate-declaration", self._diagnostic_codes(composition))

    def test_mismatch_missing_manifest_and_unsupported_target_are_diagnostic(self) -> None:
        cases = (
            (
                "Packages/com.example.a",
                "com.example.other",
                "package-oriented-product",
                "root-package-mismatch",
            ),
            (
                "Packages/com.example.missing",
                "com.example.missing",
                "package-oriented-product",
                "missing-package-manifest",
            ),
            (
                "Packages/com.example.a",
                "com.example.a",
                "different-product-target",
                "unsupported-target",
            ),
        )
        for package_root, package_name, target, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with tempfile.TemporaryDirectory() as directory:
                    original_root = self.root
                    self.root = Path(directory)
                    try:
                        if expected_code != "missing-package-manifest":
                            self._write_json(
                                "Packages/com.example.a/package.json",
                                {"name": "com.example.a", "version": "1.0.0"},
                            )
                        self._write_product_guide(package_root, package_name, target)
                        composition = json.loads(self._run("json").stdout)[
                            "productComposition"
                        ]
                    finally:
                        self.root = original_root

                self.assertEqual("invalid", composition["status"])
                self.assertIsNone(composition["selected"])
                self.assertIn(expected_code, self._diagnostic_codes(composition))

    def test_misplaced_incomplete_and_unsafe_markers_do_not_leak_values(self) -> None:
        self._write(
            "Packages/com.example.a/AI_GUIDE.md",
            "# Guide\n\n"
            "AI Product Composition Root: credential-secret=value\n"
            "## Package Identity\n"
            "- Package ID: com.example.a\n",
        )

        completed = self._run("json")
        composition = json.loads(completed.stdout)["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertNotIn("credential-secret=value", completed.stdout)
        self.assertTrue(
            {
                "declaration-outside-package-identity",
                "incomplete-declaration",
                "invalid-marker-value",
            }
            <= self._diagnostic_codes(composition)
        )

    def test_duplicate_markers_are_structural_diagnostics(self) -> None:
        self._write(
            "Packages/com.example.a/AI_GUIDE.md",
            "# Guide\n\n"
            "## Package Identity\n"
            "AI Product Composition Root: com.example.a\n"
            "AI Product Composition Root: com.example.a\n"
            "AI Refactor target: package-oriented-product\n"
            "AI Refactor target: package-oriented-product\n",
        )

        composition = json.loads(self._run("json").stdout)["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertTrue(
            {"duplicate-root-marker", "duplicate-target-marker"}
            <= self._diagnostic_codes(composition)
        )

    def test_markdown_list_markers_are_diagnostic_not_valid_opt_in(self) -> None:
        self._write(
            "Packages/com.example.a/AI_GUIDE.md",
            "# Guide\n\n"
            "## Package Identity\n"
            "- AI Product Composition Root: com.example.a\n"
            "- AI Refactor target: package-oriented-product\n",
        )

        completed = self._run("json")
        composition = json.loads(completed.stdout)["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertIsNone(composition["selected"])
        self.assertIn("invalid-marker-value", self._diagnostic_codes(composition))

    def test_invalid_sibling_manifest_is_not_guessed_from_folder_name(self) -> None:
        self._write("Packages/com.example.a/package.json", "{ invalid json")
        self._write_product_guide("Packages/com.example.a", "com.example.a")

        result = json.loads(self._run("json").stdout)
        composition = result["productComposition"]

        self.assertEqual("invalid", composition["status"])
        self.assertIn("invalid-package-manifest", self._diagnostic_codes(composition))
        self.assertIsNone(composition["declarations"][0]["packageName"])
        self.assertTrue(
            any(
                item["path"] == "Packages/com.example.a/package.json"
                for item in result["packages"]["parseErrors"]
            )
        )

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

    def _write_bytes(self, relative: str, contents: bytes) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)

    def _write_product_guide(
        self,
        package_root: str,
        package_name: str,
        target: str = "package-oriented-product",
    ) -> None:
        self._write(
            f"{package_root}/AI_GUIDE.md",
            "# Guide\n\n"
            "## Package Identity\n"
            f"- Package ID: {package_name}\n"
            f"  AI Product Composition Root: {package_name}  \n"
            f"AI Refactor target: {target}\n\n"
            "## Purpose\n",
        )

    @staticmethod
    def _diagnostic_codes(composition: dict[str, object]) -> set[str]:
        diagnostics = composition["diagnostics"]
        assert isinstance(diagnostics, list)
        return {
            item["code"]
            for item in diagnostics
            if isinstance(item, dict) and isinstance(item.get("code"), str)
        }

    def _snapshot(self) -> dict[str, bytes]:
        return {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in sorted(self.root.rglob("*"))
            if path.is_file()
        }


if __name__ == "__main__":
    unittest.main()
