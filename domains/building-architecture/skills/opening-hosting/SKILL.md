# Engineering Skill — Opening Hosting

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `opening-hosting` · Version `0.1.0` · Domain `building-architecture` · Lifecycle `pilot`.

## Intent

Create and verify door/window/void openings as hosted architectural semantics rather than overlapping primitive geometry.

## Preconditions / inputs

Accepted level/wall system identities; wall dimensions; opening evidence/dimensions; component/catalog resolution state; applicable clearance requirements where supplied.

## Decision boundary

May place openings and selected resolved/custom components within approved host geometry. Must not invent lintel/structural support, frame/jamb/sill construction or performance ratings from visual appearance alone.

## Deterministic checks

- `evaluate_opening_host` validates host identity and opening bounds against wall length/height;
- widths/heights/offsets/sill values must be finite and physically valid;
- component resolution state is explicit before production-level placement;
- repeated resolved families preserve component identity rather than duplicate raw geometry;
- proxy openings/components obey Release Scope Policy.

## Workflow

Opening requirement → host wall lookup → dimensional/provenance check → component/catalog resolution → semantic opening chunk → native implementation → query/measure host relationship → checkpoint.

## Software semantics

2D opening representation may use technical drafting capabilities; 3D component placement uses public component/instance/create/transform/query capabilities. Engine primitives do not own door/window business meaning.

## QA / outputs

Output: opening register with host IDs, resolved component IDs, measured bounds/orientation and unresolved detail/structural interfaces.

## Negative cases

- door/window merely overlaps a wall without hosted opening semantics;
- opening exceeds host bounds;
- missing approved family silently replaced with arbitrary box at `design_review`;
- repeated windows copied as unrelated raw geometry;
- hidden lintel/support detail invented from an image.
