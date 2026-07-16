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
2. `Current findings`
3. `Current ownership graph`
4. `Target tree-oriented DAG`
5. `Package candidates`
6. `Ports and project adapters`
7. `Ordered phases`
8. `Migration and compatibility risks`
9. `Validation plan`
10. `Confidence and missing evidence`
11. `Deferred or out of scope`

End with the no-write Git-status comparison. Separate confirmed evidence from inference and never claim source-wide compliance, compilation, runtime correctness, or package readiness without proof.
