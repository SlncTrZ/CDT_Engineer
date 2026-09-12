# Building Architecture v1 — Benchmark Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Primary negative case: townhouse image reconstruction · Status: benchmark definition; native acceptance pending.

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
- native component resolution proves exact `asset_key`, catalog hash/version, current registry availability/hash/version and runtime library capability before placement;
- openings are hosted and bounded;
- visible/required feature inventory is fully accounted for;
- structural-role unknowns remain unknown;
- native chunks preserve semantic IDs and relationships;
- independent QA queries relationships/topology and dimensions;
- final native artifact is saved, reopened, independently remeasured and hash-bound.

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

The current SketchUp public contract can create components and place instances by an existing definition GUID, but the inspected public map has no semantic asset-key/native-library load or registry-resolution route. Therefore `component.library_resolve` is currently mapped `blocked`, and every Building catalog native mapping remains `unresolved`. Generic `create_component`/`place_instance` capability must not be treated as equivalent evidence.

The blocker is cleared only when a public provider route exists and the Building catalog is populated with validated `asset_key`/hash/native-version mappings backed by current registry evidence. `execution.catalog_resolver.resolve_catalog_assets` then must return `resolved` for all required assets.

## Acceptance

Building Architecture v1 is not production-accepted from offline tests alone. Native design-review acceptance requires Benchmark B plus C/D/E negative cases on the declared runtime, with resolved component mappings, verified native registry evidence and an independent Checker. Higher release classes require additional structural, standards, detail/document and responsible-review evidence.
