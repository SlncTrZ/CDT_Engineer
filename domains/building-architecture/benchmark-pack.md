# Building Architecture v1 — Benchmark Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.5.0 · Primary negative case: townhouse image reconstruction · Status: benchmark definition with SketchUp contract-0.28 executor acceptance measured; production cases still require current Step-0, real catalog mappings and project evidence.

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
- final native artifact is saved, content-addressed with `artifact_seal`, reopened, independently remeasured and verified against the accepted artifact identity.

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
- opening placed at an absolute sill/head elevation inconsistent with its host wall's level elevation (unresolved level, or measured placement deviating from the resolved reference beyond the declared tolerance);
- component instance whose semantic identity/native mapping does not match the catalog resolution.

Expected: ARCH-04/05/08 FAIL/BLOCK.

## Benchmark E — Structural boundary negative

Leave structural system/load/material/interface state unresolved and request a construction/professional-review claim.

Expected: ARCH-09 and release-scope dependency gate BLOCK; architecture output may still be valid for an explicitly weaker scope.

## Benchmark F — Native failure / recovery

Exercise failure at dependency boundaries without weakening professional gates:

- **early failure:** unknown asset key, missing/mismatched identity, corrupt asset, path escape, unsupported extension or size violation must fail before native placement;
- **middle failure:** force a strict component/geometry chunk failure and verify rollback/reconciliation restores the pre-chunk semantic state before any dependent chunk is released;
- **late failure:** save, seal, reopen, independent-measurement or artifact-verification failure invalidates final artifact evidence and blocks release even when earlier mutation receipts passed;
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

For registry-backed SketchUp placement, `component.library_resolve` must prove exact accepted native identity before a design-review catalog PASS. CDT-SketchUp contract 0.28 now provides and natively verifies that strong identity route (`asset_key + sha256 + native_version`, exact bytes, definition binding, save/reopen read-back). Pilot/product catalog entries that still have no curated SketchUp mapping remain `unresolved`; those dependencies must block as `native_mapping_unresolved` rather than inventing asset keys, hashes or versions.

## Benchmark J — Interior native chunk recovery / duplicate instance negative

Execute semantic chunks such as `casework_module`, `partition_group`, `drawer_group` and `equipment_instance`. Force a middle failure and an uncertain completion. Dependent chunks remain blocked until actual persistent-ID/context/definition state is reconciled. A non-idempotent placement may be retried only after verified rollback/compensation/checkpoint state and a duplicate instance check.

Expected: no blind replay; any unplanned duplicate instance is a hard failure.

## Benchmark K — Profile / molding / loft / curved-shape capability boundary

Freeze the exact profile/curve/loft requirement and source geometry. CDT_Engineer may calculate/profile-plan the shape and chunk it, but native realization is accepted only when current CDT-SketchUp public capabilities can represent and independently query the required geometry within declared budgets. Missing/insufficient capability is a typed blocker or explicit reduced scope; it is not replaced by a visually similar primitive while retaining stronger semantics.

Engineer-side planning is executable through `domains.building_architecture.geometry_planner`: equal-cardinality loft rings and bounded profile sweeps produce indexed-mesh recipes, reject self-intersecting profiles and budget overflow, and fail when declared approximation deviation is exceeded. The matching executor dependency is now measured on CDT-SketchUp contract 0.28: `create_mesh` natively passed tetrahedron, frustum, four-section loft, ellipsoid, rounded closed profile and open curved molding/ribbon cases, plus malformed/budget fail-before-mutation and verified rollback. Every production run must still Step-0 the live descriptor/budgets; this acceptance does not permit a visually similar approximation beyond the Engineer-declared tolerance.

## Benchmark L — Planner-to-native mesh end-to-end (ENG-R03)

Close the planner/executor evidence gap: the native mesh route must consume
real `domains.building_architecture.geometry_planner` recipes, not
self-generated fixtures. Frozen inputs live in `e2e-fixtures/*.json`
(`straight-rect-sweep`, `tapered-quad-loft`, `concave-c-sweep`,
`curved-rect-sweep`, `four-section-loft`); each fixture records the planner
name, its inputs, the byte-exact recipe, the `create_mesh` payload and the
analytically expected oracle values.

Live procedure per case (planner unit = mm, native `unit` explicit):

```text
fixture create_mesh payload
-> CDT-SketchUp create_mesh (expect pins vertex/face counts)
-> get_entity_state read-back (bbox, counts, manifold, volume, unit)
-> domains.building_architecture.plan_oracle.assess_plan_execution
-> envelope / counts / edge-manifold / Euler / manifold-agreement /
   volume / deviation verdict
```

Expected:

- every fixture recipe replays byte-identical from its recorded planner
  inputs (`test_plan_oracle.py` proves this offline);
- straight/tapered/concave/four-section cases reach oracle `pass`
  (envelope within tolerance, counts exact, edge-manifold with Euler 2,
  analytic volume matched);
- `curved-rect-sweep` reports volume `unknown` (tessellation-dependent, no
  exact analytic expectation) while envelope/counts/topology still verify —
  `reduced_scope`, never a silent volume PASS;
- any envelope/count/manifold/volume mismatch verdicts `blocked`;
- missing native read-back verdicts `reduced_scope`, never `pass`.

Status: measured live 2026-09-17 — 4/5 cases oracle `pass` on SketchUp 2024
`24.0.594` / Ruby `3.2.2` via public `execute_geometry`/`get_entity_state`
(`straight-rect-sweep`, `tapered-quad-loft`, `concave-c-sweep`,
`four-section-loft`; envelope worst delta ~1.1e-05 mm against 1e-03 mm run
tolerance; analytic volumes matched, convex cases ~1e-07 relative).
`curved-rect-sweep` stays `reduced_scope` with volume `unknown` by design
(tessellation-dependent, no exact analytic expectation) while its
envelope/counts/topology verify. `concave-c-sweep` carries a case-specific
volume tolerance `2e-04` (measured native deviation `7.9e-05` on re-entrant
cap tessellation, recorded in its fixture). Raw receipts live in ignored
`_test_workspace/live_e2e_evidence_*.json`, never committed; verdicts are
recorded in the private audit SOT with exact revisions.

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

## Current native capability status

CDT-SketchUp source revision `d9aecb07ecfae9e5ffb969f2314fafe2040c162b` (provider `0.1.0`, contract `0.28`, 67 tools) has measured native acceptance on SketchUp 2024 `24.0.594` / Ruby `3.2.2`. Through the public MCP route it passed bounded nested edit/restoration, strong registry identity, CDT_Engineer catalog-resolver positive/mismatched-hash E2E, indexed-mesh realization/rollback/budget negatives, exact manifold-solid spatial queries, recovery reconciliation/compensation, content-addressed artifact seal/staleness/reseal and save/reopen verification.

The previous provider gaps for cryptographic registry identity and provider-native artifact sealing are closed by contract 0.28 native evidence. `execution.catalog_resolver.resolve_catalog_assets` must nevertheless continue returning `blocked` for any semantic asset whose own `native_mappings.sketchup` is unresolved, whose live registry evidence does not exactly match the catalog `asset_key + sha256 + native_version`, or whose current Step-0 capability is not released. That is catalog/runtime evidence completeness, not a missing executor primitive.

No QA fixture from native acceptance is a production catalog mapping. Curated mapping population requires the actual intended asset identity and remains deliberately fail-closed per asset.

## Acceptance

Building Architecture v1 is not production-accepted from offline tests or historical executor evidence alone. A native design-review run requires current Step-0 proof, Benchmark B plus C/D/E/F negative cases on the declared runtime, resolved mappings for every required catalog asset, verified registry evidence, artifact save/seal/reopen evidence and an independent Checker. If a production catalog mapping remains unresolved, only that dependent scope blocks/reduces; the provider identity/mesh/seal capability itself is no longer the blocker. Higher release classes still require the additional structural, standards, detail/document and responsible-review evidence defined elsewhere.
