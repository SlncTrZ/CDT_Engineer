# Building Structural v1 — Review Rubric

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Scope: structural intent + architecture coordination / design review.

| Criterion | Weight | Full-credit evidence |
| --- | ---: | --- |
| Structural basis/provenance | 20 | System/material/load/standard states are explicit and source-bound |
| Grid/member semantic consistency | 15 | Stable grid/member/reference identities independently verified |
| Load-path intent | 25 | Every loaded branch reaches foundation/ground; no cycle |
| Architecture coordination | 20 | Openings/stairs/facade/support interfaces checked and critical clashes dispositioned |
| Release-boundary honesty | 10 | Adequacy/construction claims blocked unless required analysis/evidence exists |
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

`fabrication_or_construction_candidate` additionally requires, at minimum, resolved materials, loads, exact structural standard applicability and an accepted analysis/capacity route. Future final-design skills/rubrics must add member/serviceability/stability/connection/foundation/reinforcement gates as applicable.

A visual/native member model cannot earn structural adequacy by score. Unknown critical evidence blocks the release class that depends on it.
