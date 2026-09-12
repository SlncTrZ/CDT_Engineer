# Building Structural v1 — Rule Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Scope: low-rise structural intent + architecture coordination / design-review baseline.

This vertical does **not** perform or claim final structural member/capacity design. Exact materials, loads, load combinations, analysis model, geotechnical inputs and standards/applicability are required before stronger adequacy/construction claims.

| Rule | Decision | Failure / release effect | Required evidence |
| --- | --- | --- | --- |
| STR-01 Structural source/basis closure | Freeze structural-source identity, architecture handoff and provenance of system/material/load/standard states | BLOCK when design-review system intent or required source identity unresolved | Source hashes, Design Basis, evidence states |
| STR-02 Grid/reference validity | Grid axes are finite, unique and ordered; member/reference identities must be stable | FAIL on malformed/duplicate/inconsistent grid | Grid register and measurements |
| STR-03 Structural system intent | Record frame/wall/slab/foundation-interface intent and evidence state; unknown hidden facts remain unknown | BLOCK design-review when structural-system intent unresolved | System register, provenance, limitations |
| STR-04 Load-path intent | Every declared loaded node must have an acyclic path to a declared foundation/ground terminal | FAIL on cycle or missing terminal reachability | Load-path graph and independent traversal result |
| STR-05 Architecture ↔ structural coordination | Detect declared member/opening/interface clashes and preserve stair/slab/facade-support coordination state | FAIL/BLOCK critical unresolved clash/interface | Architecture handoff, bounds/clearance evidence, interface register |
| STR-06 Release-evidence boundary | `design_review` may preserve unknown materials/loads/standards only with `structural_adequacy_unclaimed`; fabrication/construction candidate requires those inputs plus an accepted analysis/capacity route | BLOCK when requested release exceeds evidence | Material/load/standard states, analysis route, release target |
| STR-07 Member/system representation | Native/drawing member geometry must preserve semantic member IDs/grid/level/system relationships; native solids/lines are implementation, not proof of capacity | FAIL/BLOCK on identity/relationship mismatch | Read-after-write queries and dimensions |
| STR-08 QA/handoff | Independent Checker verifies grid/load-path/coordination/release limitations and artifact identity as applicable | BLOCK/STALE on unresolved critical finding or stale evidence | Checker findings, final artifacts/hashes, limitations |

## Structural adequacy boundary

CDT_Engineer **must not** claim structural adequacy, code compliance, member capacity, reinforcement sufficiency, connection adequacy or foundation adequacy from architectural imagery or geometric plausibility alone.

For `fabrication_or_construction_candidate` and stronger internal release targets, unresolved materials, loads or structural standards are hard blockers in the current v1 guard. A future capacity/design skill additionally requires exact analysis assumptions, combinations, section/material properties, stability/serviceability rules and benchmarked calculations.

## Deterministic implementation

`domains.building_structural.guards` implements:

- finite/unique/ordered orthogonal grid coordinates;
- deterministic load-path graph cycle/reachability validation;
- simplified plan-view column/opening clash checks with explicit clearance;
- release evidence policy separating design-review intent from adequacy/construction claims.

These guards are necessary but insufficient for final structural design.

## Negative cases

- structural system left unknown but design-review claimed;
- load path terminates before foundation/ground;
- cyclic support/load graph;
- column conflicts with architectural opening;
- loads/materials/standards unknown but construction candidate requested;
- visual/native member model treated as capacity proof;
- hidden reinforcement/foundation dimensions invented from an image;
- producer claims reused as independent structural QA.
