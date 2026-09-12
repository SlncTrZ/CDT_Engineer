# Building Structural v0.2 — Rule Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.2.0 · Scope: low-rise structural intent, architecture coordination and bounded source-bound calculation evidence.

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
| STR-09 Load-case / combination evidence | Numerical effects may be combined only from explicitly supplied load cases, exact caller-supplied factors and a verified source basis | BLOCK when factor basis or participating load-case evidence is unresolved; never select factors implicitly | Load-case ledger, combination ID/factors, exact basis record/version/rule reference, calculation receipt |
| STR-10 Material / section provenance | Material and section properties used by a check must preserve stable identity and source/evidence state | BLOCK dependent capacity checks when required material/section property evidence is unknown, inferred without approval or source-unbound | Material/section register, source refs, units/properties, evidence state |
| STR-11 Bounded demand/capacity verification | Compare explicitly supplied demand and explicitly supplied capacity under one source-bound check basis; utilization is local evidence only | FAIL when supplied demand exceeds supplied limit; BLOCK when demand/capacity provenance is unresolved; must not derive resistance from geometry | Demand/capacity values + units, section/material refs, calculation method/standard basis, utilization receipt |
| STR-12 Connection / foundation interface boundary | Preserve semantic connection/foundation interface ownership and dependency state without inventing connection, footing, pile or soil resistance | BLOCK stronger release when a required connection/foundation/geotechnical dependency is unresolved | Interface/catalog identity, participating members/terminal nodes, reaction/design/geotechnical evidence state, owner/disposition |
| STR-13 Standards applicability closure | A compliance-dependent structural check requires exact standard identity/edition, verified source, applicable decision, clause/rule mapping and reviewer rationale | BLOCK on missing/`latest` edition, metadata-only source, unknown/conflicting applicability or missing clause mapping | Standards record/version, edition/source verification, applicability decision, clause refs, reviewer/rationale |

## Structural adequacy boundary

CDT_Engineer **must not** claim structural adequacy, code compliance, member capacity, reinforcement sufficiency, connection adequacy or foundation adequacy from architectural imagery or geometric plausibility alone.

For `fabrication_or_construction_candidate` and stronger internal release targets, unresolved materials, loads, structural standards, calculation basis or required connection/foundation dependencies are hard blockers. v0.2 adds bounded evidence checks for combinations and supplied demand/capacity values; it still **must not** claim whole-structure adequacy. Final design additionally requires the complete applicable analysis model, stability/serviceability, connection/foundation/reinforcement design routes, geotechnical evidence where relevant and independent benchmarks.

## Deterministic implementation

Domain-local deterministic implementations include:

- finite/unique/ordered orthogonal grid coordinates;
- deterministic load-path graph cycle/reachability validation;
- simplified plan-view column/opening clash checks with explicit clearance;
- release evidence policy separating design-review intent from adequacy/construction claims;
- `domains.building_structural.calculations.evaluate_load_combination` for explicit source-bound linear combinations;
- `domains.building_structural.calculations.evaluate_demand_capacity_checks` for supplied demand/capacity comparisons only;
- `domains.building_structural.interfaces.evaluate_architecture_structural_interfaces` for typed Architecture↔Structural interface ownership/evidence;
- `domains.building_structural.standards.evaluate_standard_applicability` for exact edition/source/applicability/clause evidence.

These guards are necessary but insufficient for final structural design.

## Negative cases

- structural system left unknown but design-review claimed;
- load path terminates before foundation/ground;
- cyclic support/load graph;
- column conflicts with architectural opening;
- loads/materials/standards unknown but construction candidate requested;
- visual/native member model treated as capacity proof;
- hidden reinforcement/foundation dimensions invented from an image;
- producer claims reused as independent structural QA;
- load factors silently selected from memory/defaults;
- member capacity inferred from visible/native section geometry;
- a connection/foundation placeholder treated as design evidence;
- a standard marked `latest`, source-unverified or applicability-conflicted but reported compliant.
