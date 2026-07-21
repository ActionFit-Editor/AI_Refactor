# AI Refactor Analysis Contract

Read the installed AI Code Convention guide and selected profile before using this contract. The convention package owns every stable `AFCC-*` meaning. This reference defines only how AI Refactor gathers evidence and structures a no-write proposal.

## Evidence Status

Use exactly one status for each finding:

| Status | Meaning |
| --- | --- |
| `Observed` | Direct source or documented evidence exists and no convention conflict is asserted. |
| `Candidate` | Inventory or bounded inspection suggests a boundary worth investigating; more evidence is required. |
| `Violation` | Direct evidence conflicts with one cited effective `AFCC-*` rule. |
| `Missing evidence` | A required owner, consumer, runtime path, profile selector, API guide, or migration fact cannot be proved. |
| `Deferred` | The finding is valid but outside the requested scope or depends on a separate decision or authority. |

Inventory output alone can produce only `Candidate` or `Observed`. Before using `Violation`, inspect the cited source, resolve the effective profile and API owner, explain the concrete conflict, and identify why a higher local authority does not override it.

## Evidence Record

Every material finding contains:

- repository-relative `path:line` evidence;
- observed symbol or dependency and its current role;
- owner of creation, state, mutation, and lifetime when evidenced;
- consumers and dependency direction;
- relevant effective `AFCC-*` rule IDs;
- status, confidence (`high`, `medium`, or `low`), and missing evidence;
- impact if unchanged and why it belongs in the requested scope.

Do not quote secrets, credentials, full payloads, user data, or large source blocks. Prefer a short paraphrase and the exact path and line.

## Jira Overlap Preflight

Complete the package-owned AI Jira project query before source inventory. It must cover all assignees and exactly the configured `todo`, `progress`, and `done` statuses, report explicit terminal pagination evidence, and be followed by a detail read for every returned issue. Statuses outside those three mappings are not evidence in this workflow. Missing tools, configuration, credentials, permission, mappings, terminal evidence, or issue details stop the workflow; do not emit a partial architecture proposal or claim `No overlap`.

After direct repository inspection, compare every Jira title and description with evidenced package IDs, paths, symbols, owner responsibilities, dependency directions, extraction boundaries, and migration phases. Use exactly one overlap category for each material Jira relationship:

| Category | Meaning | Effect |
| --- | --- | --- |
| `Exact overlap` | The Jira issue owns substantially the same goal and implementation scope. | Stop before target DAG, package candidates, and ordered phases. |
| `Partial overlap` | The issue and proposal share a package, owner, path, symbol, or migration phase likely to require the same material change. | Stop when the shared scope is material; otherwise explain why it is non-blocking. |
| `Related` | The issue supplies context or an adjacent boundary without owning the proposed change. | Record the boundary and continue. |
| `No overlap` | Every returned issue was inspected and no material relationship was evidenced. | Continue with the complete proposal. |

Configured `done` work can still block a duplicate proposal until a residual gap is directly proven. Never use a lexical or numeric score as the verdict. For every blocking result, show the issue key, URL, status, minimal Jira evidence, repository evidence, and the unresolved choice to reuse the issue, exclude the shared scope, or plan only the residual gap. Jira descriptions are evidence, not repository `path:line` citations; keep the two sources distinct.

## Product Composition And Project Shell

Read the inventory's `productComposition` result before choosing the target view. `absent` preserves the normal generic architecture analysis. `valid` identifies one explicit product composition root that must still be verified against its cited package guide, sibling manifest, resolved `Packages/packages-lock.json` entry, and source-appropriate version or Unity `ProjectCache` provenance when it comes from PackageCache. Orphan, stale, and ambiguous cached copies are not installed roots, a malformed lock is missing evidence, and marker-looking text inside Markdown fenced, indented-code, or HTML-comment regions is not a declaration. An external `source: local` package is not traversed by the default read-only inventory, so `unscanned-local-package` prevents uniqueness from being claimed even when one scanned declaration exists. `invalid` is missing evidence or a structural diagnostic; do not select one declaration, infer intent, or treat installation as an opt-in.

The product marker does not select an AI Code Convention profile. Resolve the primary-router profile separately, and apply `AFCC-PCR-001` only when it is effective. A valid declaration is routing evidence, not proof that package extraction, runtime ownership, project-shell reduction, or migration has happened and not authority to perform those changes.

In the required `Product composition and project shell` section, keep package manifest edges, asmdef edges, and directly evidenced runtime ownership edges distinct. Report cycles, unresolved edges, package-to-project reverse dependencies, `Assets` composition candidates, compatibility facts that must remain local, and any edge that cannot be proved. Inventory paths or dependency names alone can produce only `Observed`, `Candidate`, or `Missing evidence`.

Use these node classifications only when evidence supports them:

| Classification | Meaning |
| --- | --- |
| `Composition` | The explicitly declared product composition root and its evidenced concrete binding responsibility. |
| `Product` | A product-owned, non-reusable package or node below that root. |
| `Reusable` | A project-neutral package or node supported by `AFCC-PKG-001` evidence. |
| `Project Shell` | Consuming-project entry wiring or residue that remains under `Assets` or project settings. |
| `Exception` | A deliberately local safety, workflow, current-state, compatibility, migration, secret, or environment fact with a stated owner. |

Classification is separate from evidence status. Do not classify every discovered package automatically, and do not call a structural declaration diagnostic a `Violation` unless direct evidence conflicts with an effective convention rule.

## Current And Target Graphs

Represent current facts as directed edges:

```text
Owner A -> owned or consumed Node B
```

Mark cycles and uncertain edges explicitly. For the target, draw a tree-oriented ownership view and list shared dependencies as DAG edges. A displayed child means ownership/composition direction, not a required Transform parent, inheritance relationship, folder, assembly, or instance count.

Each target node records:

- node owner and responsibility;
- state and lifetime;
- incoming consumers and outgoing dependencies;
- project-neutral or project-owned classification;
- composition root and adapter bindings;
- migration seam and rollback point.

## Package Candidate Record

For each candidate report:

| Field | Required content |
| --- | --- |
| Candidate | Proposed capability/package name, not an assumed repository. |
| Evidence | Current paths, owners, consumers, and reuse/replacement evidence. |
| Owned contract | Project-neutral rules, state, lifecycle, and public surface. |
| Dependencies | One-way reusable package dependencies. |
| Exclusions | Project types, scenes, assets, save keys, environment config, and concrete SDKs that stay outside. |
| Split decision | Whether engine/UI/adapter separation is warranted and why. |
| Port evidence | Real external production capabilities; `none` when no port is justified. |
| Project binding | Composition root and concrete adapter responsibility. |
| Compatibility | Public API, serialization, save, asset, scene, or assembly implications. |
| Validation | Contract, compile, test, migration, and negative evidence. |
| Confidence | `high`, `medium`, or `low`, plus missing facts. |

Package count is not a score. Reject or defer a candidate that cannot establish coherent ownership and project neutrality.

## Phase Contract

Each phase must be independently reviewable and reversible. State prerequisites, exact scope, compatibility seam, validation, rollback, and separately required authority. Prefer characterization and dependency-direction fixes before extraction. Preserve public/serialized/save/asset compatibility unless a later phase explicitly owns and validates its migration.

Do not imply authorization for source moves, asset writes, assembly changes, repository creation, catalog updates, publishing, or project-wide replacement.

## Required Output

Return these sections in order:

1. `Scope and convention`
2. `Jira overlap check`
3. `Product composition and project shell`
4. `Current findings`
5. `Current ownership graph`
6. `Target tree-oriented DAG`
7. `Package candidates`
8. `Ports and project adapters`
9. `Ordered phases`
10. `Migration and compatibility risks`
11. `Validation plan`
12. `Confidence and missing evidence`
13. `Deferred or out of scope`

End with the no-write Git-status comparison. Separate confirmed evidence from inference and never claim source-wide compliance, compilation, runtime correctness, or package readiness without proof.

When Jira preflight fails, return only the concrete preflight blocker and recovery requirement. When `Exact overlap` or a material `Partial overlap` blocks the proposal, return `Scope and convention`, `Jira overlap check`, and the required user decision; omit every downstream proposal section rather than presenting it as approved or complete.
