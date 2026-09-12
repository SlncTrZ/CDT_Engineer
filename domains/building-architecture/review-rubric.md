# Building Architecture v1 — Review Rubric

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Scope: low-rise residential / design-review baseline.

| Criterion | Weight | Full-credit evidence |
| --- | ---: | --- |
| Source/provenance + feature inventory | 15 | Required/visible features frozen with source evidence and uncertainty state |
| Semantic building graph | 20 | Levels, spaces, walls, openings, stairs/facade systems have stable identities and valid dependencies |
| Component/system fidelity | 20 | Resolved systems use approved semantic assets/custom paths; no silent primitive substitution |
| Geometry + relationship/topology correctness | 20 | Independent host/level/dimension/topology checks pass |
| Completeness + detail coverage | 10 | Required inventory items implemented and independently verified for declared scope |
| Cross-discipline boundary honesty | 5 | Structural/standards unknowns remain explicit and block stronger claims |
| Native artifact/handoff evidence | 10 | Save/reopen/remeasure/hash evidence and limitations are bound to the final artifact |

Rate 0–4 per criterion. Score is secondary: hard gates always dominate.

## Hard gates

Design-review release requires all of:

- ARCH-01 source/provenance closure;
- ARCH-02–05 applicable deterministic semantic/geometry checks;
- ARCH-06 component/system dependency resolution with no silent primitive substitution;
- ARCH-07 required feature/detail inventory complete and verified;
- ARCH-08 critical semantic relationships/topology pass independently;
- ARCH-09 structural/interface state is explicit; no unsupported adequacy claim;
- ARCH-10 final artifact save/reopen/remeasure/hash evidence current;
- exact standards/applicability resolved for any compliance claim;
- public engine route and current runtime capability evidence.

A proxy that is legal for `concept` cannot earn `design_review` by score. Generic engine integrity or visual similarity cannot override a hard gate.

## Reviewer independence

Checker evidence must be produced from the frozen Design Basis/inventory and independent queries/measurements, not by restating producer receipts. Every BLOCKER/MAJOR finding must be resolved or represented as a blocking verdict before release.
