# SketchUp Operating Guide

> Documentation class: PUBLIC_SOFTWARE_GUIDE
Version: 0.3.0 · Source contract: provider `0.1.0`, contract `0.21`, 64 tools · Measured SketchUp 2024 `24.0.594` / Ruby `3.2.2`.

## Step-0
Call `system_status` and `system_capabilities`; require a reachable bridge, active model, observed SketchUp/Ruby runtime, matching contract/capability fingerprint and the exact required tool descriptors. Source/live-acceptance history does not replace current runtime proof.

## Compatibility
Use the measured 2024 runtime as the current accepted baseline. Other major releases remain unclaimed until separately tested. Prefer capability descriptors over prose: `read_only`, `strict_mutation`, and `deprecated_legacy` are materially different execution classes.

## Semantic capability map
Current strict/public integration uses `execute_geometry`, `create_component`, `place_instance`, `transform_entity`/move/rotate/scale/mirror, `material_assign`, `get_entity_state`, `measure_distance`, `query_topology`, `model_save/model_save_as`, `model_open`, and `model_export`. Native save/open/export are no longer blockers. A true content-addressed `artifact.seal`/provider hash primitive is still absent. The current public contract also has no semantic asset-key/native-library load or registry-resolution route, so Building catalog resolution is a separate blocker from generic component creation.

## Feature chunks
Execute one bounded semantic feature at a time and preserve receipt context:
```text
get_entity_state / context query
→ strict mutation with if_context + if_match where applicable
→ operation receipt (affected PIDs, fingerprints, validation, rollback)
→ independent query/measurement
→ next feature
```
For component systems, compose/create once then place instances by exact definition GUID and absolute transforms. `create_component` may implement an explicitly approved bounded custom component recipe; it must not be treated as proof that an Engineering Asset Catalog entry was resolved. `place_instance` consumes an existing definition GUID, not a CDT_Engineer semantic `asset_key`.

## Transaction and recovery
Strict mutations use the provider Semantic State Loop with native operation, semantic validation before commit, and verified rollback/compensation according to the capability descriptor. Do not treat deprecated legacy mutations as equivalent. On uncertain client state, query current context/entity fingerprints before retrying.

## Chunk budgets
Respect capability metadata bounds: active-context object/fingerprint budgets, 1..500 entity composition sets, arrays up to 100 with projected-load limits, geometry point/segment limits and bridge frame limits. Re-measure on another SketchUp version/hardware before advertising stronger budgets.

## Read-after-write
Verify persistent ID, context revision, semantic fingerprint, transform/hierarchy/material and explicit-unit geometry. Site handoff must re-open the saved SKP with `model_open` and independently re-measure scale/alignment/hierarchy before release.

## UI behavior
Camera/scene and viewport evidence are supplemental. Presentation state must not substitute for semantic state or geometry verification.

## Artifact lifecycle
`model_save`/`model_save_as` and `model_open` provide rooted native SKP lifecycle; `model_export` provides rooted DAE/KMZ (plus raster view export). These paths are live-accepted on the measured runtime but still require Step-0 proof per run. CDT_Engineer may compute an external file hash after a stable save, but the provider currently has no content-addressed `artifact.seal`/manifest primitive; do not claim sealed SKP provenance from save/open alone.

## Known blockers
- `source_snapshot_not_runtime_proof`
- `artifact_seal_missing`
- `native_component_registry_route_missing` — no public semantic asset-key/native-library load or registry-resolution route; Building `design_review` catalog mappings stay blocked until a validated native route exists
- `model_world_coordinate_input_unclaimed`
- `legacy_mutation_paths_deprecated`

## Benchmarks
Positive: strict create/component/transform/material receipts, explicit-unit read-back, save → open → independent measurement, bounded export. Negative: stale context/entity guards, wrong unit/coordinate space, deprecated path use, save/open path escape, failed reopen verification, or release that requires a provider-native content-addressed seal.
