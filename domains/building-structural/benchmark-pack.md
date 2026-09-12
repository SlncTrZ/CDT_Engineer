# Building Structural v1 — Benchmark Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Scope: low-rise structural intent + architecture coordination.

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

## Evidence and acceptance

Freeze Design Basis/source hashes, architecture handoff revision, structural-system state, grid, load-path graph, interface register, domain/profile versions and runtime software identity. Record deterministic guard outputs and independent Checker evidence.

Structural v1 production acceptance is limited to the declared intent/coordination scope until native positive/negative benchmarks pass. Final member design, reinforcement, connections and foundations require separately implemented/benchmarked skills with exact loads/materials/standards/geotechnical inputs.
