# AI Guide - AI Refactor

This file is the package-local authority for AI Refactor's read-only inventory and proposal workflow. AI Code Convention owns the stable `AFCC-*` meanings; this package consumes those meanings without duplicating or overriding them.

## Package Identity

- Package ID: `com.actionfit.ai-refactor`
- Display name: AI Refactor
- Repository: `https://github.com/ActionFitGames/AI_Refactor.git`
- Repository visibility: Private
- Current package version at generation time: `0.1.1`
- Unity version: `6000.2`
- AI Code Convention dependency: published `0.4.1`
- Custom Package Manager dependency: published `1.1.96`

## Purpose And Boundary

Use this package when a user explicitly asks for a project-wide or scoped architecture audit and a staged refactoring proposal. It inventories candidate source signals and dependency edges, resolves the consuming repository's effective AI Code Convention profile and installed API-owner guides, verifies evidence directly, and proposes a progressive tree-oriented ownership DAG whose coherent reusable nodes can become packages with narrow project-bound ports.

This package owns no gameplay state, Runtime assembly, framework, automated fix, source analyzer verdict, migration executor, Jira workflow, Git workflow, package publisher, repository creator, or global skill installer. It never edits source, assets, scenes, prefabs, ScriptableObjects, ProjectSettings, manifests, installed skills, Git state, or external systems. A proposal is evidence for a later decision; it never creates implementation authority.

## Convention Dependency

- Resolve `com.actionfit.ai-codeconvention` from the embedded `Packages/` directory or exactly one PackageCache installation.
- Read its `AI_GUIDE.md`, shared authoring reference, exact profile selector, selected profile reference, owner routing, and relevant installed owner guides before classifying findings.
- AI Code Convention owns `AFCC-TRE-001`, `AFCC-PKG-001`, `AFCC-PRT-001`, `AFCC-INT-001`, and every other stable rule meaning. Do not restate a broader or incompatible meaning here.
- The desired architecture is a tree-oriented ownership view backed by an acyclic DAG. Shared services can have multiple consumers. It is not a strict Transform hierarchy, inheritance tree, package-count target, DI-container mandate, or whole-project rewrite.

## Analysis Contract

`Skills~/Shared/references/refactor-analysis-contract.md` defines evidence statuses, path-and-line citation, target-tree notation, package candidate fields, phase planning, confidence, missing evidence, and the final output schema. Candidate inventory signals are never violations by themselves. The skill must inspect the relevant source and map a finding to an effective `AFCC-*` rule before using `Violation`.

## Read-Only Inventory

`Skills~/Shared/scripts/refactor_inventory.py` is a deterministic Python standard-library inventory. It scans `Assets` and `Packages`, ignores Git/worktree and Unity-generated directories, redacts string literals from candidate snippets, and reports:

- C# candidate signals such as scene-wide discovery, lifecycle polling, detached async, coroutines, persistence, communication hubs, serialization, dynamic loading, and concrete SDK coupling;
- asmdef names, references, known edges, unresolved references, and cycles;
- immediate embedded package metadata, dependency edges, and cycles;
- deterministic counts and repository-relative paths.

The tool writes nothing and emits JSON or text only to standard output. Its result is a bounded discovery aid, not source-compliance proof.

## Project Router Registration

This package should be listed in `Packages/com.actionfit.custompackagemanager/PACKAGE_AI_GUIDE_ROUTER.md`.

Requested router entry:

- `Packages/com.actionfit.ai-refactor/AI_GUIDE.md` - AI Refactor owns read-only Unity architecture inventory and evidence-backed staged refactoring proposals based on the installed AI Code Convention. Read before planning project-wide package extraction or architecture refactoring.

If the router is not included in the consuming assistant's default reading sequence, connect it through an existing primary project entry point such as `PROJECT.md`, `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`. Do not silently create a new documentation hierarchy.

Read this guide when:

- changing files under `Packages/com.actionfit.ai-refactor/`;
- invoking, diagnosing, or explaining `$refactor-help` or `$refactor-plan`;
- changing the analysis contract, deterministic inventory, package metadata, or release notes;
- preparing this package for a later manual release.

## How To Work On This Package

- Treat `package.json` as the source for package ID, version, Unity version, and package dependencies.
- Treat `Editor/PackageInfo/ActionFitPackageInfo_SO.asset` as the source for catalog metadata, owner, status, description, release note, repository name, and dependency override.
- Keep `README.md` focused on human usage and setup and this guide focused on AI-facing ownership, safety, validation, and release contracts.
- When behavior changes, update this guide and the package tests together so consuming projects receive the same contract.

## Agent Skills

- `Skills~/manifest.json` registers schema v2 read-only `refactor-help` and `refactor-plan` for Codex and Claude with prefix `refactor`.
- `refactor-help` reads generated `PACKAGE_SKILLS.md`, README, and this guide and explains dependencies, outputs, invocation, menu, and safety without changing state.
- `refactor-plan` proves the exact repository and baseline Git state, resolves the effective convention and owner guides, runs the read-only inventory, inspects direct evidence, emits the required staged proposal, and compares final Git state byte-for-byte.
- Custom Package Manager installs project-local copies and preserves unknown, modified, file-backed, linked, or conflicting targets. Do not author `PACKAGE_SKILLS.md` inside package skill sources.

## Routing And Validation

- Use `$code-convention-help` for convention explanation, `$code-convention-check` for documented-contract comparison and retirement readiness, and `$code-convention-apply` only after a concrete implementation has separate edit authority.
- Use `$refactor-plan` for source-backed architecture inventory and a no-write staged proposal. Do not route it to Jira, PR, publication, or implementation operations.
- Run `Tests~/run-tests.sh` for inventory determinism, no-write behavior, metadata, shared resources, skill parity, and safety contracts.
- Run Custom Package Manager contract validation and Unity compilation after package metadata, Editor menu, asmdef, or guide-router changes.

## Package Tools Menu

- Unity menu root: `Tools/Package/AI Refactor/`.
- `README` opens this package README.
- The package has no settings asset and no executable Unity analysis menu. Keep the README entry in the README-only priority band.

## Release Note Rules

- `ActionFitPackageInfo_SO.ReleaseNote` is Korean and contains only the candidate version being prepared. Keep identifiers and paths unchanged.
- Do not copy older changelog entries into the release note. Custom Package Manager composes history from separate catalog rows.

## Release And Distribution Boundary

- This `0.1.0` candidate is Private. Repository creation and package publication have not been performed by this implementation.
- Publishing is manual through Custom Package Manager and requires separate authorization.
- Before reusing a version, check remote Git tags. Published tags are immutable.
- If the package changes after a version is tagged, bump to the next unused version before publishing.
- Do not create a repository, push a package repository, tag, append a catalog row, publish, change visibility, or install into global/home skill directories without separate authorization.
