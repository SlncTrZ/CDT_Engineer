# Engineering Skill — Architecture / Structural Coordination

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `architecture-structural-coordination` · Version `0.1.0` · Domain `building-structural` · Lifecycle `pilot`.

## Intent

Coordinate structural member/system intent with frozen architectural openings, circulation and support interfaces before downstream modeling/drawing release.

## Preconditions / inputs

Versioned architecture handoff; structural grid/member intent; explicit clearance/project rules where required; stable architecture/structural entity IDs.

## Decision boundary

May identify geometric/interface clashes and request/recommend coordination changes. Must not silently move architecture or resize structural members when the responsible discipline decision is unresolved.

## Deterministic checks

- `domains.building_structural.interfaces.evaluate_architecture_structural_interfaces` requires typed Architecture↔Structural ownership, source revision, disposition, verification state and evidence references;

- `evaluate_architecture_clashes` detects simplified member/opening plan conflicts with explicit clearance;
- grid/level identities across disciplines must be reconciled;
- stair/slab opening, facade support, shaft/penetration and cantilever interfaces remain explicit when in scope;
- unresolved critical conflicts block dependent design-review release;
- any changed upstream architecture revision invalidates affected coordination evidence.

## Workflow

Freeze architecture handoff → map shared levels/grids → member/opening clash checks → interface register → discipline disposition/revision → recheck → coordination checkpoint.

## Software semantics

Use public query/measure capabilities for native evidence when needed. CAD/model overlap facts are inputs to engineering coordination; generic clash geometry alone does not choose the professional resolution.

## QA / outputs

Output: typed cross-discipline interface register, measured clashes/clearances, disposition owner/state, source revisions, evidence refs and downstream blockers.

## Negative cases

- column intersects a required opening;
- architecture revision changes after structural QA;
- stair/slab opening interface omitted;
- facade support assumed without structural interface evidence;
- Agent silently shifts a column/opening and claims both disciplines approved it.
