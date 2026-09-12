# Engineering Skill — Load Path Check

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `load-path-check` · Version `0.1.0` · Domain `building-structural` · Lifecycle `pilot`.

## Intent

Represent and verify structural load-transfer intent as a directed support graph from declared loaded nodes to foundation/ground terminals.

## Preconditions / inputs

Accepted structural-system intent; stable member/support IDs; declared loaded nodes and foundation/ground terminal identities. Numerical loads are not required for the intent graph but are required for later adequacy design.

## Decision boundary

May verify connectivity/acyclic support intent. Must not infer force magnitude, capacity or code compliance from connectivity alone.

## Deterministic checks

- `validate_load_path` validates graph shape and referenced nodes;
- cycles are engineering FAIL evidence;
- every declared loaded node must reach at least one declared terminal;
- orphan/terminated load branches fail;
- graph changes invalidate affected downstream coordination evidence.

## Workflow

Member/support register → loaded nodes → support edges → foundation/ground terminals → deterministic traversal → failure localization → approved graph checkpoint.

## Software semantics

The graph is Engineering OS data. Native model/drawing relations may provide evidence but do not replace deterministic graph validation.

## QA / outputs

Output: versioned load-path graph, loaded/terminal nodes, traversal result, unsupported branches and limitation that this proves path intent rather than capacity.

## Negative cases

- cyclic support graph;
- roof/member load branch terminates before foundation;
- missing referenced member;
- decorative geometry mistaken for structural support;
- graph connectivity presented as a numerical capacity result.
