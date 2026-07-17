---
name: refactor-help
description: Explain AI Refactor, its AI Code Convention dependency, installed related skills, inventory and proposal outputs, setup, menu, and read-only safety boundaries. Use when the user asks how architecture refactoring planning works or which refactor skill applies.
---

# AI Refactor Help

Keep this workflow read-only. Do not edit files, invoke Unity, refresh packages or skills, change Git state, create Jira work, publish, or deploy.

1. Read `PACKAGE_SKILLS.md` first. Treat its generated package identity, complete related-skill inventory, invocations, descriptions, agents, and access values as authoritative.
2. Resolve the package from `Packages/com.actionfit.ai-refactor`; otherwise use exactly one `Library/PackageCache/com.actionfit.ai-refactor@*` without editing it. Read its `README.md` and `AI_GUIDE.md`.
3. Explain that `com.actionfit.ai-codeconvention@0.4.4` owns the stable `AFCC-*` rules, including `AFCC-PCR-001`, while AI Refactor owns only deterministic candidate inventory and evidence-backed proposal orchestration.
4. Explain that inventory reports an explicit package-owned product composition declaration as `absent`, `valid`, or `invalid` after embedded-before-PackageCache resolution. The marker never selects the profile, proves a migration, or authorizes a change.
5. Explain `$refactor-plan` output: product composition and project shell, current findings, target ownership tree/DAG, package candidates, ports and project adapters, ordered phases, migration and compatibility risks, validation, confidence, and missing evidence.
6. State that inventory signals are candidates, not automatic violations, and that direct path-and-line evidence plus an effective convention rule is required before a violation can be reported.
7. Explain the README-only Unity menu and direct Git UPM root dependencies when relevant. State that no Runtime assembly, settings asset, or automatic refactoring menu exists.
8. State that the workflow never edits source, assets, scenes, prefabs, ScriptableObjects, settings, manifests, Jira, Git refs, packages, or installed skills and never publishes or creates repositories.
