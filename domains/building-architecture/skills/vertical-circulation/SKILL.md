# Engineering Skill — Vertical Circulation

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `vertical-circulation` · Version `0.1.0` · Domain `building-architecture` · Lifecycle `pilot`.

## Intent

Plan and verify stairs/vertical circulation as level-connected semantic systems with explicit dimensional requirements.

## Preconditions / inputs

Accepted level elevations; stair location/intent; rise/going/width evidence; applicable project/standard thresholds and source references when compliance is claimed; structural opening/support interface state.

## Decision boundary

May derive riser count/geometry from approved level and stair data. Must not invent regulatory limits, structural support, headroom or guard/handrail requirements without an applicable source.

## Deterministic checks

- `evaluate_stair` reconciles riser count × riser height with connected level delta;
- supplied maximum riser/minimum going/minimum width requirements are checked deterministically;
- riser count must be a positive integer and dimensions finite/positive;
- stair/slab opening and support interfaces remain explicit dependencies for stronger release classes.

## Workflow

Level connection → stair intent → requirement source → dimensional plan → deterministic check → opening/support coordination → semantic chunk → native execution → independent measurement.

## Software semantics

Native stair geometry may be constructed from bounded component/custom semantic chunks. Primitive steps are not by themselves proof of compliant vertical circulation.

## QA / outputs

Output: stair register, connected level IDs/elevations, dimensional calculations, applicable requirements, unresolved headroom/guard/support/interface items and independent measurements.

## Negative cases

- stair rise does not match levels;
- arbitrary riser/going values treated as code compliant;
- structural opening/support omitted but construction scope claimed;
- visually plausible stair passes without independent dimensions;
- railing/guard details silently assumed.
