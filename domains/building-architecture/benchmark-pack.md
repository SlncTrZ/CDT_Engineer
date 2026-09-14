# Building Architecture v1 — Benchmark Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.3.0 · Primary negative case: townhouse image reconstruction · Status: benchmark definition; native acceptance pending.

## Scope

The first benchmark targets a low-rise residential/townhouse design-review reconstruction. The original failed townhouse run is retained privately as a negative evidence case; public benchmark semantics contain no customer/raw image dependency.

The benchmark does not claim structural adequacy, code compliance, as-built truth or construction-ready detailing unless those disciplines/evidence are separately supplied and accepted.

## Benchmark A — Concept proxy

Input intentionally lacks approved component/native asset mappings.

Expected:

- source/feature inventory complete;
- semantic building graph exists;
- proxy components may be used only under `concept`;
- requested `design_review` remains BLOCKED with a lower recommended release;
- no silent primitive substitution preserves the stronger release.

## Benchmark B — Semantic design-review reconstruction

Frozen inputs include explicit levels/dimensional anchors, resolved component semantic IDs and verified native catalog mappings/registry evidence for every required reusable component family.

Expected:

- level/space/wall/opening/stair graph validates;
- repeated semantic objects resolve through reusable component definitions/instances where mapped;
- native component resolution proves exact `asset_key`, catalog SHA-256, `native_version`, current registry availability and runtime library capability before placement;
- the accepted public route is registry discovery (`asset_list`) → identity verification → strict native placement (`place_asset`) → independent entity/definition read-back;
- openings are hosted and bounded;
- visible/required feature inventory is fully accounted for;
- structural-role unknowns remain unknown;
- native chunks preserve semantic IDs and relationships;
- independent QA queries relationships/topology and dimensions;
- final native artifact is saved, reopened, independently remeasured and externally hash-bound when provider-native sealing is unavailable.

## Benchmark C — Primitive-substitution negative

Create an artifact that visually resembles the reference but replaces required resolved door/window/facade systems with arbitrary raw boxes/faces or omits major visible features.

Expected: ARCH-06/07 hard gate FAIL/BLOCK regardless of screenshot/render quality or generic engine integrity.

## Benchmark D — Relationship/topology negative

Introduce one or more:

- opening beyond host-wall bounds;
- orphan component/feature;
- duplicate/copanar facade geometry where the declared system forbids it;
- cross-storey semantic leakage;
- stair level-rise mismatch;
- component instance whose semantic identity/native mapping does not match the catalog resolution.

Expected: ARCH-04/05/08 FAIL/BLOCK.

## Benchmark E — Structural boundary negative

Leave structural system/load/material/interface state unresolved and request a construction/professional-review claim.

Expected: ARCH-09 and release-scope dependency gate BLOCK; architecture output may still be valid for an explicitly weaker scope.

## Benchmark F — Native failure / recovery

Exercise failure at dependency boundaries without weakening professional gates:

- **early failure:** unknown asset key, missing/mismatched identity, corrupt asset, path escape, unsupported extension or size violation must fail before native placement;
- **middle failure:** force a strict component/geometry chunk failure and verify rollback/reconciliation restores the pre-chunk semantic state before any dependent chunk is released;
- **late failure:** save, reopen, independent-measurement or external-hash failure invalidates final artifact evidence and blocks release even when earlier mutation receipts passed;
- **uncertain completion / timeout:** reconcile current model/context/entity/definition state before retry; non-idempotent placement must never be blindly replayed and duplicate instances must be detected/prevented.

For every injected case, record predecessor checkpoint/context identity, expected state, observed state, recovery action, recovered state and whether dependent chunks remained blocked.

## Benchmark G — Interior casework box / corner casework

Use the public `interior-casework-layout` skill with frozen dimensions and provenance.

Positive cases:

- **casework box:** explicit outer envelope + panel thicknesses derive the expected clear envelope; optional minimum-clear requirements use only supplied sources;
- **corner casework:** an orthogonal L-footprint has both legs extending beyond the opposing return depth and produces a positive derived footprint area;
- compartment widths plus intervening partition thicknesses reconcile exactly to the carcass clear span.

Negative cases: nonpositive clear envelope, partition-span mismatch, corner return consuming the opposing leg, or an exact dimension inferred only from an unscaled image. Expected: ARCH-11 FAIL/BLOCK before native execution.

## Benchmark H — Drawer fit / appliance fit and edit

Freeze the host opening, item envelope, six-side clearances and their source. Verify a fitting drawer/appliance passes and an oversized item fails. For an edit case, mutate one drawer envelope/position only after the predecessor identity is frozen; re-run fit checks and independently verify the same semantic/native target identity after edit.

Expected negatives: drawer fit failure, appliance fit failure, missing manufacturer/project clearance source, wrong target identity, or an edit that creates/retains a duplicate instance.

## Benchmark I — Interior asset / material / fixing dependency

Resolve the required semantic families `casework_panel_system`, `drawer_system`, `appliance_envelope` and `casework_anchor_system` through the Engineering Asset Catalog or an explicitly bounded custom path. Material/thickness/edge/fixing requirements remain project/manufacturer dependencies, not visual guesses.

For registry-backed SketchUp placement, `component.library_resolve` must prove exact accepted native identity before a design-review catalog PASS. While `native_component_registry_identity_metadata_missing` remains open, these pilot catalog entries intentionally keep SketchUp mappings `unresolved` and the benchmark must block rather than invent `sha256`/`native_version`.

## Benchmark J — Interior native chunk recovery / duplicate instance negative

Execute semantic chunks such as `casework_module`, `partition_group`, `drawer_group` and `equipment_instance`. Force a middle failure and an uncertain completion. Dependent chunks remain blocked until actual persistent-ID/context/definition state is reconciled. A non-idempotent placement may be retried only after verified rollback/compensation/checkpoint state and a duplicate instance check.

Expected: no blind replay; any unplanned duplicate instance is a hard failure.

## Benchmark K — Profile / molding / loft / curved-shape capability boundary

Freeze the exact profile/curve/loft requirement and source geometry. CDT_Engineer may calculate/profile-plan the shape and chunk it, but native realization is accepted only when current CDT-SketchUp public capabilities can represent and independently query the required geometry within declared budgets. Missing/insufficient capability is a typed blocker or explicit reduced scope; it is not replaced by a visually similar primitive while retaining stronger semantics.

This benchmark distinguishes Engineer planning/completeness from the SKP-03 executor dependency. Native molding/loft/curved-shape parity remains pending until the engine-side capability and runtime benchmark are proven.

## Measurement / evidence

Freeze before each run:

- source hashes and exclusions;
- Design Basis revision;
- domain/profile/skill/catalog versions;
- level and dimensional anchors;
- feature inventory;
- required component resolutions;
- applicable explicit project/standard thresholds;
- engine/application/provider versions and runtime capabilities;
- expected hard-gate results.

Record native receipts, semantic IDs, independent measurements, reopen evidence, artifact hashes and Checker findings. Visual comparison is supplemental only.

## Current native blocker

The current SketchUp public contract exposes an owner-curated registry route through `asset_list` plus strict `place_asset`, and native definition/entity identity can be queried after placement. Therefore the old `native_component_registry_route_missing` statement is closed.

Strong Building catalog resolution is still BLOCKED by `native_component_registry_identity_metadata_missing`: the public registry does not yet bind a provider-verified SHA-256 and `native_version` to the exact `.skp` bytes loaded into the native definition. `execution.catalog_resolver.resolve_catalog_assets` already requires those exact fields and must continue returning `blocked` until catalog mapping, registry evidence and current runtime capability all match.

The blocker is cleared only when a public provider route returns/verifies the required asset identity fields, the Building catalog is populated with matching validated mappings, current Step-0 runtime evidence releases `component.library_resolve`, and save/reopen read-back preserves the accepted native identity/instance evidence.

## Acceptance

Building Architecture v1 is not production-accepted from offline tests alone. Native Benchmark B execution remains blocked until the registry identity blocker above is cleared and current SketchUp runtime Step-0 passes. Native design-review acceptance then requires Benchmark B plus C/D/E/F negative cases on the declared runtime, resolved component mappings, verified registry evidence and an independent Checker. Higher release classes require additional structural, standards, detail/document and responsible-review evidence.
