# SketchUp Operating Guide

> Documentation class: PUBLIC_SOFTWARE_GUIDE
Version: 0.4.0 · Source contract: provider `0.1.0`, contract `0.25`, 64 tools · Measured SketchUp 2024 `24.0.594` / Ruby `3.2.2`.

## Step-0
Call `system_status` and `system_capabilities`; require a reachable bridge, active model, observed SketchUp/Ruby runtime, matching contract/capability fingerprint and the exact required tool descriptors. Source/live-acceptance history does not replace current runtime proof.

## Compatibility
Use the measured 2024 runtime as the current accepted baseline. Other major releases remain unclaimed until separately tested. Prefer capability descriptors over prose: `read_only`, `strict_mutation`, `external_side_effect` and `deprecated_legacy` are materially different execution classes.

## Semantic capability map
Current strict/public integration uses `execute_geometry`, `create_component`, `place_instance`, `asset_list`, `place_asset`, `transform_entity`/move/rotate/scale/mirror, `material_assign`, `get_entity_state`, `definition_info`, `measure_distance`, `query_topology`, `model_save/model_save_as`, `model_open`, and `model_export`. Native save/open/export are no longer source blockers. A true content-addressed `artifact.seal`/provider hash primitive is still absent.

The owner-curated component registry route now exists: `asset_list` enumerates allowlisted `asset_key` entries and `place_asset` loads the bound `.skp` through the native definition library before placing an instance. `get_entity_state`/`definition_info` can read back the resulting native definition identity. This closes the old **route-missing** statement, but it does **not** yet satisfy strong Engineering Asset Catalog resolution. The public registry metadata exposes key/name/file/size, not a provider-verified SHA-256 plus `native_version` bound to the exact bytes loaded. Therefore `component.library_resolve` remains `unproven` for release classes that require exact catalog-native identity, with blocker `native_component_registry_identity_metadata_missing`.

## Feature chunks
Execute one bounded semantic feature at a time and preserve receipt context:
```text
get_entity_state / context query
→ strict mutation with if_context + if_match where applicable
→ operation receipt (affected PIDs, fingerprints, validation, rollback)
→ independent query/measurement
→ next feature
```
For explicitly approved custom component systems, compose/create once then place instances by exact definition GUID and absolute transforms. For registry-backed assets, query `asset_list` first, require the intended `asset_key`, then use `place_asset` only when the workflow's identity evidence requirement is satisfied. `place_asset` is valid generic native placement; it must not be promoted to a strong catalog-resolution PASS until SHA-256/`native_version` identity is proven by an accepted public route.

## Transaction and recovery
Strict mutations, including `place_asset`, use the provider Semantic State Loop with native operation, semantic validation before commit, and verified rollback according to the capability descriptor. Unknown asset keys, invalid registry paths, unsupported file types and oversized assets must fail before native placement. On a middle-operation failure, verify rollback by reconciling context/entity fingerprints. On uncertain client state, query current context/entity/definition state before retrying; never blindly replay non-idempotent `place_asset`.

Document save/open/export are `external_side_effect`, not native transactions. A late save/reopen error therefore requires explicit file/model reconciliation and cannot be described as transactional rollback.

## Chunk budgets
Respect capability metadata bounds: active-context object/fingerprint budgets, 1..500 entity composition sets, arrays up to 100 with projected-load limits, geometry point/segment limits, bridge frame limits and registry asset size caps. Re-measure on another SketchUp version/hardware before advertising stronger budgets.

## Read-after-write
Verify persistent ID, context revision, semantic fingerprint, transform/hierarchy/material and explicit-unit geometry. Registry placement additionally verifies `asset_key` receipt metadata and the resulting definition GUID. These facts still do not substitute for a missing SHA-256/`native_version` binding. Site/Building handoff must reopen the saved SKP with `model_open` and independently re-measure required geometry/relationships before release.

## UI behavior
Camera/scene and viewport evidence are supplemental. Presentation state must not substitute for semantic state or geometry verification.

## Artifact lifecycle
`model_save`/`model_save_as` and `model_open` provide rooted native SKP lifecycle; `model_export` provides rooted DAE/KMZ (plus raster view export). These paths have historical live acceptance on the measured runtime but still require Step-0 proof per run. CDT_Engineer may compute an external SHA-256 after a stable save when the workflow permits, but the provider currently has no content-addressed `artifact.seal`/manifest primitive; do not claim sealed SKP provenance from save/open alone.

## Known blockers
- `source_snapshot_not_runtime_proof`
- `artifact_seal_missing`
- `native_component_registry_identity_metadata_missing` — `asset_list`/`place_asset` exist, but strong catalog release still lacks provider-verified SHA-256 and `native_version` identity for the loaded registry asset
- `model_world_coordinate_input_unclaimed`
- `legacy_mutation_paths_deprecated`

## Benchmarks
Positive source/runtime route: Step-0 → `asset_list` → bounded `place_asset` → definition/entity read-back → native save → reopen → independent measurement, when all required identity evidence is available. Negative: unknown asset, corrupt/mismatched identity, registry path escape, oversized asset, stale context/entity guards, middle-operation rollback, uncertain timeout without blind retry, wrong unit/coordinate space, save/open path escape, failed reopen verification, or a release requiring provider-native content-addressed sealing. Strong Building catalog acceptance remains BLOCKED until the registry identity metadata blocker is closed.
