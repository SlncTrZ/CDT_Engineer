# Building Structural v0.2 — Benchmark Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.2.0 · Scope: low-rise structural intent, coordination and bounded source-bound calculation evidence.

## Benchmark A — Design-review structural intent

Inputs: frozen architectural levels/openings, specified structural-system intent, explicit grid; materials/loads/standards may remain unknown.

Expected:

- grid validates;
- load-path graph reaches foundation/ground terminals without cycles;
- architecture/member clashes are checked;
- unknown loads/materials/standards remain visible;
- result may support structural coordination/design review only with `structural_adequacy_unclaimed` limitation.

## Benchmark B — Broken load path

Delete a support edge or terminate a loaded branch before foundation/ground.

Expected: STR-04 FAIL with the affected loaded node identified.

## Benchmark C — Architecture clash

Place a column/member inside a frozen architectural opening/required clearance zone.

Expected: STR-05 FAIL/BLOCK until coordinated/dispositioned.

## Benchmark D — Unsupported construction claim

Use the same design-review intent fixture while loads/materials/standards or analysis route are unresolved, then request `fabrication_or_construction_candidate`.

Expected: STR-06 + Release Scope Policy BLOCK. Geometry or visual plausibility cannot override.

## Benchmark E — Native representation

After semantic intent is accepted, create bounded grid/member/coordination representation using public engine capabilities; query back identities/dimensions and verify no semantic relationship loss. This benchmark does not transform intent into final capacity design.

## Benchmark F — Explicit load combination arithmetic / provenance

Inputs: two resolved load cases with common effect components, caller-supplied factors and a verified project-rule or standard-derived basis.

Expected: deterministic **load combination** arithmetic matches hand calculation and receipt binds case IDs, exact factors and basis. Unknown case evidence or unverified factor basis BLOCKS and emits no combined result.

## Benchmark G — Bounded demand/capacity check

Inputs: source-bound member/section/material identities plus independently supplied demand and capacity in one declared unit.

Expected: **demand/capacity** utilization passes below the explicit limit, fails above it, and BLOCKS when capacity provenance is unresolved. The benchmark must not derive resistance or report whole-structure adequacy.

## Benchmark H — Unverified standard / applicability

Inputs: a required standards record using `latest`, metadata-only source evidence, missing clause map or unresolved/conflicting applicability.

Expected: **unverified standard** evidence BLOCKS STR-13; no compliance PASS is emitted. A verified exact edition fixture may pass the applicability evidence gate without implying the design satisfies every clause.

## Benchmark I — Connection/foundation interface boundary

Inputs: semantic connection/foundation interface records with participating member/load-path identities but unresolved connection design or geotechnical/foundation evidence.

Expected: **connection/foundation interface** remains valid coordination evidence at bounded scope but blocks any stronger release that depends on actual resistance/foundation adequacy. Native placeholder geometry cannot override the blocker.

## Evidence and acceptance

Freeze Design Basis/source hashes, architecture handoff revision, structural-system state, grid, load-path graph, typed interface register, domain/profile/skill versions, exact calculation/standards bases and runtime software identity when native work is in scope. Record deterministic guard/calculation outputs and independent Checker evidence.

Structural v0.2 acceptance remains limited to the explicitly evidenced scope. Bounded combination and demand/capacity checks do not establish whole-structure adequacy; final analysis/design, reinforcement, connections and foundations require separately implemented/benchmarked routes with exact loads/materials/standards/geotechnical inputs as applicable.
