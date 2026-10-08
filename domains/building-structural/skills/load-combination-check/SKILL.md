# Engineering Skill — Load Combination Check

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `load-combination-check` · Version `0.1.0` · Domain `building-structural` · Lifecycle `pilot`.

## Intent

Produce traceable combined action effects from explicitly supplied load-case effects and explicitly supplied factors for one verified project-rule or standard-derived combination basis.

## Preconditions / inputs

Stable load-case IDs; common effect components and units established upstream; each participating load case has a resolved evidence state; exact combination factors; exact basis source class, record ID/version and clause/rule reference; basis verification state.

## Decision boundary

The skill may perform linear arithmetic and expose provenance/limitations. It **must not** select load factors, invent load cases, choose a governing combination, infer missing effects, or claim that one combination set is code-complete.

## Deterministic checks

- `domains.building_structural.calculations.evaluate_load_combination` validates referenced cases, evidence state, common effect components and factor basis;
- unverified factor basis BLOCKS and emits no combined effects;
- unknown/inferred participating case evidence BLOCKS;
- factors remain caller inputs and are returned in calculation evidence;
- approved-assumption cases remain explicitly limitation-bound.

## Workflow

Freeze load-case ledger → freeze exact combination basis → supply factors → deterministic combination → bind calculation receipt → independent arithmetic/provenance review → hand off combined effects to the next bounded analysis/check stage.

## Software semantics

No native CAD capability is required. Numerical effects normally originate from an accepted analysis/source route; this skill does not create that route.

## QA / outputs

Output combination ID, participating case IDs, exact factors, combined effect components, basis identity/version/rule reference, result and limitations. An independent Checker should reproduce at least one representative arithmetic result from the frozen inputs.

## Negative cases

- factors remembered or guessed instead of supplied from an exact basis;
- one participating load case has unknown evidence;
- a referenced case is absent;
- participating cases omit different effect components;
- arithmetic PASS presented as proof that every required regulatory/project combination was considered.
