# Engineering Skill — Storey & Space Plan

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `storey-space-plan` · Version `0.1.0` · Domain `building-architecture` · Lifecycle `pilot`.

## Intent

Create the level/storey/space semantic graph that architectural geometry depends on.

## Preconditions / inputs

Frozen source interpretation; units; level/elevation evidence; spatial requirements; explicit project/standard thresholds when claimed.

## Decision boundary

May derive spatial relationships and calculate geometry from supplied evidence. Must not invent minimum room sizes, circulation widths or jurisdictional criteria without an applicable source.

## Deterministic checks

- `validate_levels` rejects malformed, duplicate or non-ascending level registers;
- `evaluate_space` validates polygon geometry/self-intersection and computes area;
- explicit `minimum_area` and supported clear-dimension requirements are evaluated only when supplied;
- unresolved measurement methods remain `unknown`, never guessed;
- all spaces reference existing levels.

## Workflow

Level register → reference axes → space inventory → boundaries/adjacency intent → explicit dimensional requirements → deterministic checks → semantic checkpoint → 2D planning chunks.

## Software semantics

Technical 2D creation/query may map to AutoCAD or another accepted engine. Native line/polyline entities remain implementations of the approved semantic space/wall plan.

## QA / outputs

Output: level register, space register, geometry/requirement results, unresolved planning requirements and IDs consumed by walls/openings/stairs/drawings.

## Negative cases

- duplicate level elevations;
- self-intersecting room polygon;
- inferred minimum area treated as code requirement;
- space references missing level;
- geometry generated before level/space checkpoint is accepted.
