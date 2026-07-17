# AI Refactor (com.actionfit.ai-refactor)

Read-only Unity project architecture inventory and evidence-backed staged refactoring proposals based on AI Code Convention. The package helps describe a current ownership graph, a tree-oriented target DAG, coherent package candidates, and the narrow ports and project adapters needed to connect them.

This package is distributed from a **Public** repository and has no Runtime assembly, gameplay framework, automatic refactoring engine, asset migration, or publishing workflow. It never applies a proposal. Public visibility makes the source readable but does not embed credentials or grant rights beyond the repository's explicit license terms.

## Install

```json
{
  "dependencies": {
    "com.actionfit.custompackagemanager": "https://github.com/ActionFit-Editor/Custom_Package_Manager.git#1.1.97",
    "com.actionfit.referencebinding": "https://github.com/ActionFit-Editor/ReferenceBinding.git#0.1.1",
    "com.actionfit.ai-codeconvention": "https://github.com/ActionFit-Editor/AI_Code_Convention.git#0.4.2",
    "com.actionfit.ai-refactor": "https://github.com/ActionFit-Editor/AI_Refactor.git#0.1.2"
  }
}
```

Custom Package Manager resolves the declared AI Code Convention and package-manager dependencies from its catalog. Direct Git UPM consumers keep all four root entries because Unity does not resolve transitive Git URLs from semantic-version package dependencies.

## Agent Skills

- `$refactor-help`: explains package outputs, dependencies, menus, related skills, and read-only boundaries.
- `$refactor-plan`: inventories a selected Unity repository, verifies findings against the effective AI Code Convention and installed API-owner guides, and returns an evidence-backed phased proposal.

`$refactor-plan` may execute the bundled `Skills~/Shared/scripts/refactor_inventory.py` read-only inventory. It reports candidate signals, assembly/package edges and cycles, then requires direct source inspection before classifying a convention violation. Output includes current findings, a target ownership tree/DAG, package candidates, ports/adapters, ordered phases, migration and compatibility risks, validation, confidence, and missing evidence.

The workflow does not edit source, assets, scenes, prefabs, ScriptableObjects, settings, manifests, Jira, Git refs, packages, or installed skills. It does not run write-capable Unity commands, publish, create repositories, or claim that a candidate signal is automatically a defect.

## Unity Menu

- README: `Tools > Package > AI Refactor > README`.
- The package has no settings asset or executable Unity analysis menu.

## AI Guide

- Read `AI_GUIDE.md` before modifying or diagnosing this package in a consuming project.
- AI Code Convention `0.4.2` owns the stable `AFCC-*` meanings. AI Refactor consumes those rules and owns only inventory and proposal orchestration.

## Assembly

- **Editor** (`com.actionfit.ai-refactor.Editor`): editor-only package assembly.
