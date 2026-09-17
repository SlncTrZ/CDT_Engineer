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
- `resolve_opening_elevation` binds sill/head to absolute elevation through the host wall's `level_id` before any native placement — the raw `sill_height` must never be used as a native Z;
- `verify_opening_placement` checks natively measured sill/head elevations against the resolved reference with a caller-declared tolerance;
- widths/heights/offsets/sill values must be finite and physically valid;
- component resolution state is explicit before production-level placement;
- repeated resolved families preserve component identity rather than duplicate raw geometry;
- proxy openings/components obey Release Scope Policy.

## Workflow

Opening requirement → host wall lookup → dimensional/provenance check → absolute elevation resolution (`resolve_opening_elevation`) → component/catalog resolution → semantic opening chunk → native implementation at resolved elevations → query/measure host relationship → placement verification (`verify_opening_placement`) → checkpoint.

## Software semantics

2D opening representation may use technical drafting capabilities; 3D component placement uses public component/instance/create/transform/query capabilities. Engine primitives do not own door/window business meaning.

## QA / outputs

Output: opening register with host IDs, resolved component IDs, measured bounds/orientation and unresolved detail/structural interfaces.

## Negative cases

- door/window merely overlaps a wall without hosted opening semantics;
- opening exceeds host bounds, relatively or absolutely (sill/head placed
  without resolving the host wall level, e.g. window head above wall top);
- missing approved family silently replaced with arbitrary box at `design_review`;
- repeated windows copied as unrelated raw geometry;
- hidden lintel/support detail invented from an image.
