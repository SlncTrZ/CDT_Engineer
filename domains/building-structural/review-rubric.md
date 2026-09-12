# Building Structural v0.2 — Review Rubric

> Documentation class: PUBLIC_DOMAIN
Version: 0.2.0 · Scope: structural intent, coordination and bounded calculation evidence.

| Criterion | Weight | Full-credit evidence |
| --- | ---: | --- |
| Structural basis/provenance | 15 | System/material/load/standard states are explicit and source-bound |
| Grid/member semantic consistency | 10 | Stable grid/member/reference identities independently verified |
| Load-path intent | 15 | Every loaded branch reaches foundation/ground; no cycle |
| Architecture coordination | 15 | Openings/stairs/facade/support interfaces checked and critical clashes dispositioned |
| Calculation / standards provenance | 20 | Any numerical check uses explicit factors, material/section refs, exact source basis and standards applicability evidence |
| Release-boundary honesty | 15 | Local checks never become unsupported global adequacy/construction claims; connection/foundation dependencies stay visible |
| Independent QA/handoff | 10 | Checker evidence, limitations and artifact identity are current |

Hard gates dominate score.

## Design-review hard gates

- STR-01 structural basis/source state sufficient for intent scope;
- STR-02 grid/reference valid;
- STR-03 structural-system intent resolved;
- STR-04 declared load path reaches terminal without cycles;
- STR-05 critical architecture/structure interfaces pass or are explicitly blocked;
- STR-06 unresolved loads/materials/standards are labeled and `structural_adequacy_unclaimed`;
- STR-08 independent Checker evidence current.

## Stronger release hard gates

`fabrication_or_construction_candidate` additionally requires STR-09 through STR-13 where applicable: resolved load cases/combinations, source-bound material/section evidence, accepted demand/capacity calculation route, exact structural standard applicability, and resolved required connection/foundation/geotechnical interfaces. These bounded checks do not by themselves establish final adequacy. Final-design skills/rubrics must also cover the complete analysis model, stability, serviceability, connection/foundation/reinforcement and other applicable gates.

A visual/native member model cannot earn structural adequacy by score. Unknown critical evidence blocks the release class that depends on it.
