# SketchUp Operating Guide

> Documentation class: PUBLIC_SOFTWARE_GUIDE
Version: 0.5.0 · Source contract: provider `0.1.0`, contract `0.28`, 67 tools · Measured SketchUp 2024 `24.0.594` / Ruby `3.2.2` · Accepted source revision `d9aecb07ecfae9e5ffb969f2314fafe2040c162b`.

## Step-0
Call `system_status` and `system_capabilities`; require a reachable bridge, active model, observed SketchUp/Ruby runtime, matching provider contract/capability fingerprint and the exact required capability descriptors. The source revision and native-acceptance history below establish what has been measured; they are **not current-run runtime proof**. Block if the live runtime cannot reproduce the required capability state.

## Compatibility
SketchUp 2024 `24.0.594` / Ruby `3.2.2` is the measured contract-0.28 baseline. Other major releases remain unclaimed until separately tested. Select paths from machine-readable capability metadata: `read_only`, `strict_mutation`, `external_side_effect` and `deprecated_legacy` have different safety/recovery semantics.

## Semantic capability map
Current integration uses `execute_geometry`, `create_mesh`, `create_component`, `place_instance`, `asset_list`, `place_asset`, strict transforms, `material_assign`, `get_entity_state`, `definition_info`, `measure_distance`, `query_topology`, `query_overlap`, `model_save/model_save_as`, `model_open`, `model_export`, `artifact_seal` and `artifact_verify`.

`component.library_resolve` is now an accepted provider capability: `asset_list` verifies exact file SHA-256 + `native_version`; `place_asset` re-verifies bytes around native load, binds identity to the loaded definition and fails closed on incompatible cache/reuse or later definition-geometry drift. `get_entity_state`/`definition_info` expose the accepted definition identity. The native 0.28 acceptance also exercised CDT_Engineer's catalog resolver with matching evidence (PASS) and mismatched SHA-256 (BLOCK).

This **does not populate product catalog data automatically**. A Building catalog family whose `native_mappings.sketchup` is still `unresolved` continues to block as `native_mapping_unresolved`; QA fixtures must never be promoted into production catalog mappings merely because the provider can resolve strong identities.

`model.measure` now includes exact bounded manifold-solid relation/clearance evidence through `measure_distance`/`query_overlap`, while `create_mesh` is the generic bounded realization primitive for Engineer-planned loft/profile/curved geometry. Shape meaning and tessellation remain Engineer responsibilities.

## Feature chunks
Execute one bounded semantic feature at a time and preserve receipt/context/identity evidence:

```text
Step-0 capability snapshot
→ semantic source + dependency resolution
→ Engineer deterministic geometry/catalog plan
→ strict mutation (if_context / if_match / target_context where applicable)
→ operation receipt + exact affected set
→ independent read-back / measurement
→ checkpoint
→ next dependent feature
```

For complex geometry, CDT_Engineer plans a bounded indexed mesh; `create_mesh` consumes only the vertices/faces and validates provider budgets. For registry-backed assets, resolve the exact catalog mapping first, require matching `asset_key + sha256 + native_version` in current `asset_list`, place through `place_asset`, then independently read back definition/instance identity.

## Lane discipline (mesh coordinates)
`sketchup_mesh` is a 3D lane: every point must carry explicit finite XYZ — 2D points fail the placement gate instead of defaulting Z to 0. Declare `intent_3d` per feature and gate with `verify_execution_placement` before mutation. Strict coordinates are `active_context`/target-local; never assume an implicit world conversion (see `model_world_coordinate_input_unclaimed`).

## Transaction and recovery
Strict mutations use the provider Semantic State Loop and commit only after semantic/affected-set validation. Contract 0.28 native evidence includes:

- three-level nested target edit plus verified caller-context restoration;
- forced mesh expectation failure with verified rollback;
- malformed/over-budget mesh rejection before mutation;
- middle-chunk failure with the prior committed chunk preserved;
- uncertain completion reconciled from actual object identity before action;
- explicit compensation restoring the semantic baseline without duplicate replay.

Never blindly retry non-idempotent placement or creation after timeout/uncertain completion. Reconcile context, PID, definition GUID, semantic fingerprint and expected object count first.

Document/artifact operations are `external_side_effect` or read-only verification, not SketchUp transactions. Their recovery is file/model reconciliation, not undo semantics.

## Chunk budgets
Respect the live capability descriptor. The accepted 0.28 bounds include, among others: nested context depth 32; indexed mesh up to 2048 vertices, 4096 faces, 16 vertices/face and 32768 index references; exact-spatial triangulation/pair-test budgets; registry entry/hash/file-size budgets; bridge frame bounds; semantic fingerprint/object limits; and artifact sealing up to the declared byte cap. Do not raise limits merely to force a benchmark through.

## Read-after-write
For semantic geometry verify persistent ID, context revision, semantic fingerprint, transform/hierarchy, topology/bounds and required exact measurements. Registry placement additionally verifies exact `asset_key`, SHA-256, `native_version`, definition GUID and definition geometry identity. Nested instance-specific edits require `make_unique` first when shared-definition mutation is not intended.

For exact spatial QA, use the provider's manifold-solid `disjoint|touching|penetrating` result and surface clearance rather than AABB overlap. Native acceptance includes a rotated case where bounding boxes overlap but solids are correctly reported disjoint.

Site/Building handoff must save, seal, reopen and independently re-measure the accepted artifact when the release workflow requires those gates.

## UI behavior
Camera/scene and viewport evidence are supplemental. Presentation state must not substitute for semantic geometry, identity or measurement evidence.

## Artifact lifecycle
`model_save`/`model_save_as`, `model_open` and `model_export` provide rooted native lifecycle. Contract 0.28 adds provider-native content-addressed `artifact_seal`/`artifact_verify`:

1. save the active rooted SKP to stable bytes;
2. `artifact_seal` hashes source/copy, creates accepted `<sha256>.skp` + manifest and returns the content identity;
3. mutation makes the prior seal stale until the model is reconciled/saved;
4. if saved bytes change, reseal to a new SHA-256;
5. reopen the exact model and run `artifact_verify` plus independent geometry/identity checks.

Native acceptance proves seal/verify, stale-after-mutation, changed-byte reseal and verify-after-reopen.

## Known blockers
- `source_snapshot_not_runtime_proof` — accepted source/runtime history never replaces Step-0 proof for the current run.
- `model_world_coordinate_input_unclaimed` — strict public coordinates are `active_context` / target-local nested context; no implicit world conversion.
- `legacy_mutation_paths_deprecated` — autonomous workflows use preferred strict paths.
- Per-asset `native_mapping_unresolved` is a catalog-data blocker where a semantic family lacks an actual curated SketchUp mapping; it is **not** a provider identity-capability failure.

## Benchmarks
Contract 0.28 was accepted natively on SketchUp 2024 through the public MCP route. Positive evidence covers nested edit, strong asset identity + Engineer resolver E2E, tetra/frustum/four-section loft/ellipsoid/rounded/open-molding mesh realization, exact clearance/touching/penetration/rotated-disjoint queries, recovery reconciliation, artifact seal and save/reopen. Negative evidence covers wrong hash/version, missing/oversized/changed asset bytes, used-definition identity mismatch, malformed/over-budget mesh, forced rollback, non-manifold spatial input, stale artifact evidence and shared-definition geometry drift.

A production Building benchmark must still provide real native mappings for every required catalog asset. If one is unresolved, block that dependency rather than substituting the acceptance fixture or a visually similar primitive.
