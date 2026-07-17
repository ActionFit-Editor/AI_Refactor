# AI Refactor (com.actionfit.ai-refactor)

Read-only Unity project architecture inventory and evidence-backed staged refactoring proposals based on AI Code Convention. The package helps describe an explicitly declared package-owned product composition root, the remaining project shell, a current ownership graph, a tree-oriented target DAG, coherent package candidates, and the narrow ports and project adapters needed to connect them.

This package is distributed from a **Public** repository and has no Runtime assembly, gameplay framework, automatic refactoring engine, asset migration, or publishing workflow. It never applies a proposal. Public visibility makes the source readable but does not embed credentials or grant rights beyond the repository's explicit license terms.

## Install

```json
{
  "dependencies": {
    "com.actionfit.custompackagemanager": "https://github.com/ActionFit-Editor/Custom_Package_Manager.git#1.1.100",
    "com.actionfit.referencebinding": "https://github.com/ActionFit-Editor/ReferenceBinding.git#0.1.2",
    "com.actionfit.ai-codeconvention": "https://github.com/ActionFit-Editor/AI_Code_Convention.git#0.4.4",
    "com.actionfit.ai-refactor": "https://github.com/ActionFit-Editor/AI_Refactor.git#0.2.0"
  }
}
```

Custom Package Manager resolves the declared AI Code Convention and package-manager dependencies from its catalog. Direct Git UPM consumers keep all four root entries because Unity does not resolve transitive Git URLs from semantic-version package dependencies.

## Agent Skills

- `$refactor-help`: explains package outputs, dependencies, menus, related skills, and read-only boundaries.
- `$refactor-plan`: inventories a selected Unity repository, verifies findings against the effective AI Code Convention and installed API-owner guides, and returns an evidence-backed phased proposal.

`$refactor-plan` may execute the bundled `Skills~/Shared/scripts/refactor_inventory.py` read-only inventory. Schema v2 reports candidate signals, installed embedded and source-verified PackageCache assembly/package edges and cycles, recognizes but does not traverse external local-package roots, accepts UTF-8 JSON files with or without a BOM, ignores orphan, stale, or ambiguous cache copies and marker examples inside Markdown fenced/indented code or HTML comments, and reports an explicit product-composition declaration as `absent`, `valid`, or `invalid`. Because an unscanned external local package could contain another declaration, its presence yields `unscanned-local-package` missing evidence and prevents a valid root selection. Invalid or cyclic `file:` references remain bounded diagnostics instead of aborting inventory. A valid declaration must use the exact AI Code Convention marker contract; it does not select the profile, prove that migration occurred, or grant edit authority. Direct source inspection remains required before classifying a convention violation.

Output includes product composition and project shell, current findings, a target ownership tree/DAG, package candidates, ports/adapters, ordered phases, migration and compatibility risks, validation, confidence, and missing evidence. Product nodes may be classified as `Composition`, `Product`, `Reusable`, `Project Shell`, or `Exception` only when evidence supports the classification.

The workflow does not edit source, assets, scenes, prefabs, ScriptableObjects, settings, manifests, Jira, Git refs, packages, or installed skills. It does not run write-capable Unity commands, publish, create repositories, or claim that a candidate signal is automatically a defect.

## Unity Menu

- README: `Tools > Package > AI Refactor > README`.
- The package has no settings asset or executable Unity analysis menu.

## AI Guide

- Read `AI_GUIDE.md` before modifying or diagnosing this package in a consuming project.
- AI Code Convention `0.4.4` owns the stable `AFCC-*` meanings. AI Refactor consumes those rules and owns only inventory and proposal orchestration.

## Assembly

- **Editor** (`com.actionfit.ai-refactor.Editor`): editor-only package assembly.
