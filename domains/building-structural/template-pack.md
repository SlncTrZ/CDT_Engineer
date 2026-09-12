# Building Structural v1 — Template Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Scope: structural intent + architecture coordination / design review.

## Structural basis record

Record: job/revision; architecture handoff/source hashes; release target; structural-system evidence state; materials/loads/standards states; included/excluded analysis/design scope; unresolved interfaces; reviewer.

## Grid/member intent record

```text
grid axes + coordinates
member_id
kind
level/reference
bounds/section state
material state
source/provenance
structural role
```

Unknown member sizes/materials remain explicit; do not infer capacity from geometry.

## Load-path record

```text
loaded nodes
support/load-transfer graph
foundation/ground terminal nodes
cycle/reachability result
source/assumption state
limitations
```

The graph represents structural intent, not numerical analysis or member capacity.

## Architecture interface record

Record opening/member bounds; explicit clearance; stair/slab opening; facade support interface; cantilever/balcony support intent; shafts/penetrations; unresolved clashes; owner/action.

## Execution record

Stage/chunk ID; semantic member/system IDs; required public software capabilities; source/profile/rule versions; native receipts; independent measurements; checkpoint/recovery evidence.

## QA / handoff record

STR rule ID; expected/observed state; independent method; artifact identity; finding severity/result; structural-adequacy limitation; unresolved materials/loads/standards; requested/effective release; downstream responsible reviewer/action.
