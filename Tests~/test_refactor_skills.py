#!/usr/bin/env python3
"""Contract tests for the AI Refactor package and skills."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PACKAGE_ROOT / "Skills~"
ANALYSIS_CONTRACT = (
    SKILLS_ROOT / "Shared" / "references" / "refactor-analysis-contract.md"
)
INVENTORY = SKILLS_ROOT / "Shared" / "scripts" / "refactor_inventory.py"
SKILL_NAMES = ("refactor-help", "refactor-plan")


class RefactorSkillTests(unittest.TestCase):
    def test_manifest_registers_read_only_schema_v2_skills(self) -> None:
        manifest = json.loads((SKILLS_ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(2, manifest["schemaVersion"])
        self.assertEqual("refactor", manifest["skillPrefix"])
        self.assertEqual("refactor-help", manifest["helpSkill"])
        self.assertEqual(
            [
                {
                    "name": "refactor-help",
                    "agents": ["codex", "claude"],
                    "includeShared": False,
                    "access": "read-only",
                },
                {
                    "name": "refactor-plan",
                    "agents": ["codex", "claude"],
                    "includeShared": True,
                    "access": "read-only",
                },
            ],
            manifest["skills"],
        )

    def test_help_uses_inventory_and_explains_dependency_and_boundaries(self) -> None:
        for agent in ("Codex", "Claude"):
            help_skill = self._read_skill(agent, "refactor-help")
            self.assertIn("`PACKAGE_SKILLS.md`", help_skill)
            self.assertIn("com.actionfit.ai-codeconvention@0.4.2", help_skill)
            self.assertIn("candidate inventory", help_skill)
            self.assertIn("not automatic violations", help_skill)
            self.assertIn("never edits source, assets, scenes", help_skill)
        self.assertEqual([], list(SKILLS_ROOT.rglob("PACKAGE_SKILLS.md")))

    def test_plan_requires_evidence_target_dag_phases_and_no_write_proof(self) -> None:
        required = (
            "git status --short --untracked-files=all",
            "references/refactor-analysis-contract.md",
            "scripts/refactor_inventory.py --root <repository-root> --format json",
            "path:line",
            "`AFCC-TRE-001`",
            "`AFCC-PKG-001`",
            "`AFCC-PRT-001`",
            "`AFCC-INT-001`",
            "tree-oriented DAG",
            "Package count is not a goal",
            "DI containers",
            "Ordered phases",
            "Migration and compatibility risks",
            "Confidence and missing evidence",
            "byte-for-byte",
            "no-write contract failed",
            "A proposal never authorizes implementation",
        )
        for agent in ("Codex", "Claude"):
            plan = self._read_skill(agent, "refactor-plan")
            for phrase in required:
                self.assertIn(phrase, plan)
            for prohibited_operation in (
                "Do not edit",
                "install or refresh packages or skills",
                "change Jira",
                "create repositories",
                "publish",
            ):
                self.assertIn(prohibited_operation, plan)

    def test_codex_and_claude_instruction_sources_are_equivalent(self) -> None:
        for name in SKILL_NAMES:
            self.assertEqual(self._read_skill("Codex", name), self._read_skill("Claude", name))

    def test_shared_contract_and_inventory_define_bounded_evidence(self) -> None:
        self.assertTrue(ANALYSIS_CONTRACT.is_file())
        self.assertTrue(INVENTORY.is_file())
        contract = ANALYSIS_CONTRACT.read_text(encoding="utf-8")
        inventory = INVENTORY.read_text(encoding="utf-8")
        for status in ("Observed", "Candidate", "Violation", "Missing evidence", "Deferred"):
            self.assertIn(f"`{status}`", contract)
        for section in (
            "Current ownership graph",
            "Target tree-oriented DAG",
            "Package candidates",
            "Ports and project adapters",
            "Ordered phases",
        ):
            self.assertIn(section, contract)
        self.assertIn("standard-library", (PACKAGE_ROOT / "AI_GUIDE.md").read_text(encoding="utf-8"))
        self.assertIn("EXCLUDED_PARTS", inventory)
        self.assertIn("candidateDetailsTruncated", inventory)
        self.assertNotIn("write_text", inventory)
        self.assertNotIn("write_bytes", inventory)

    def test_package_metadata_is_public_editor_only_and_dependency_pinned(self) -> None:
        package = json.loads((PACKAGE_ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual("0.1.2", package["version"])
        self.assertEqual(
            {
                "com.actionfit.ai-codeconvention": "0.4.2",
                "com.actionfit.custompackagemanager": "1.1.97",
            },
            package["dependencies"],
        )
        self.assertFalse((PACKAGE_ROOT / "Runtime").exists())
        asmdef = json.loads(
            (PACKAGE_ROOT / "Editor" / "com.actionfit.ai-refactor.Editor.asmdef").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(["Editor"], asmdef["includePlatforms"])
        package_info = (
            PACKAGE_ROOT / "Editor" / "PackageInfo" / "ActionFitPackageInfo_SO.asset"
        ).read_text(encoding="utf-8")
        self.assertIn("_repositoryVisibility: 0", package_info)
        self.assertIn("com.actionfit.ai-codeconvention@0.4.2", package_info)
        self.assertIn("com.actionfit.custompackagemanager@1.1.97", package_info)

    def test_docs_and_metadata_have_no_placeholders_or_machine_paths(self) -> None:
        paths = [
            PACKAGE_ROOT / "README.md",
            PACKAGE_ROOT / "AI_GUIDE.md",
            ANALYSIS_CONTRACT,
            *[SKILLS_ROOT / agent / name / "SKILL.md" for agent in ("Codex", "Claude") for name in SKILL_NAMES],
            *list((SKILLS_ROOT / "Codex").glob("*/agents/openai.yaml")),
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        for forbidden in ("TODO", "/Users/", "/Volumes/", "...\""):
            self.assertNotIn(forbidden, combined)
        self.assertIn("Repository visibility: Public", combined)
        self.assertIn("This `0.1.2` candidate targets the Public", combined)
        self.assertIn("Tools > Package > AI Refactor > README", combined)

    @staticmethod
    def _read_skill(agent: str, name: str) -> str:
        return (SKILLS_ROOT / agent / name / "SKILL.md").read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
