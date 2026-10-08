# Engineering Skill — Architecture / Structural Coordination

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `architecture-structural-coordination` · Version `0.3.0` · Domain `building-structural` · Lifecycle `pilot`.

## Intent

Coordinate structural member/system intent with frozen architectural openings, circulation and support interfaces before downstream modeling/drawing release.

## Preconditions / inputs

Versioned architecture handoff; structural grid/member intent; explicit clearance/project rules where required; stable architecture/structural entity IDs.

## Decision boundary

May identify geometric/interface clashes and request/recommend coordination changes. Must not silently move architecture or resize structural members when the responsible discipline decision is unresolved.

## Deterministic checks

- `domains.building_structural.interfaces.evaluate_architecture_structural_interfaces` requires typed Architecture↔Structural ownership, handoff/source revision, project unit/frame identity, disposition, conflict state/owner and evidence references;

- `evaluate_architecture_clashes` detects simplified member/opening plan conflicts with explicit clearance;
- grid/level identities across disciplines must be reconciled;
- stair/slab opening, facade support, shaft/penetration and cantilever interfaces remain explicit when in scope;
- unresolved critical conflicts block dependent design-review release;
- a required interface marked `not_applicable` is a reviewed disposition, not an omission: it requires `verification_state=verified`, a declared `source_revision` and nonempty evidence references;
- the caller supplies the independently discovered current Architecture/Structural revisions plus expected project unit/frame identity; the guard compares them directly with each handoff rather than trusting its self-declared verification state;
- any changed upstream source revision invalidates the affected handoff even when its previous `verification_state` was `verified`;
- unit/reference-frame disagreement is a hard coordination blocker;
- an open conflict blocks release; a resolved conflict requires an owning participating discipline plus nonempty resolution evidence.

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
