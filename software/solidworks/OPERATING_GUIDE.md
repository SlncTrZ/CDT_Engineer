# SolidWorks Operating Guide
Version: 0.1.0 · Status: source-derived baseline; mechanical runtime acceptance pending.

## Step-0
Discover SolidWorks installation path/version/build/edition, required COM/add-in host readiness, provider version/contract, and exact runtime public capability surface. The inspected dirty source snapshot is not runtime proof.

## Compatibility
Runtime-observed app/provider/version/capabilities are required for `compatible`. Source-map expectations without runtime evidence are `guidance_only`/`unknown`; absent software is `installation_required`; unloaded host/add-in/provider is `configuration_required`; incompatible version is `version_mismatch`.

## Semantic capability map
Expected from source: `solid.feature.create`, `model.query`, `checkpoint.create`, `model_3d.measure`, `artifact.native_save`, `artifact.reopen`, `artifact.exchange_export`. `solid.boolean`, `topology.inspect`, and `artifact.seal` remain unproven.

## Feature chunks
Use semantic native feature groups: base feature, hole family, boss/cut group, dimension update group, or other dependency-bounded feature-tree unit. Preserve the domain feature DAG and do not collapse an entire part into one opaque mutation.

Illustrative public sequence:
```text
solidworks_create_basic_part / solidworks_create_hole_feature
→ solidworks_review_active / solidworks_inspect_hole_features
→ solidworks_update_dimension as required
→ inspect again
→ solidworks_save_document checkpoint
```
Export occurs only after independent measurement/QA gates for the native model.

## Transaction and recovery
Known blocker: `exact_transaction_mode_unproven`. Do not claim native atomicity. `checkpointed_atomic` may be used only after runtime proof that the saved native document can restore the complete pre-chunk state and that restoration is independently verified. Otherwise use compensating/restart-from-checkpoint behavior appropriate to proven runtime semantics.

Timeout or uncertain feature creation requires feature-tree/model reconciliation before retry; blind duplicate feature creation is prohibited.

## Chunk budgets
Prefer small dependency-bounded feature groups rather than long Boolean/feature chains. Numeric operation/time budgets must be measured on the actual runtime before production qualification. A historical 14-Boolean AutoCAD benchmark is not a SolidWorks budget.

## Read-after-write
After each native feature chunk, inspect feature/dimension state and independently measure critical geometry. Hole correctness requires hole/face/section evidence where the runtime exposes it; generic body validity or visual plausibility is insufficient.

## UI behavior
Feature-tree growth/redraw may be yielded after a safe committed checkpoint. UI activity is supplementary and must not weaken recovery semantics.

## Artifact lifecycle
Native save/reopen and exchange export are source-expected but require runtime proof for the selected version. Final acceptance requires native save, disposable reopen, independent measurements, required neutral export, reopening reader identity, round-trip units/topology/dimension checks, and content identity. `artifact.seal` is unproven.

## Known blockers
- `source_snapshot_not_runtime_proof`
- `exact_transaction_mode_unproven`
- `solid.boolean` unproven
- `topology.inspect` unproven
- `artifact.seal` unproven
- Required neutral format remains a Design Basis/runtime decision, not an invented default.

## Benchmarks
Positive: native feature creation, dimension update, save/reopen, independent hole measurement, neutral export/reopen when runtime-proven. Negative: feature failure mid-chain, duplicate retry, unresolved tolerance, sampled geometry presented as exact, topology inspection unavailable, neutral exporter unavailable, round-trip unit/topology drift.
