# Building Structural v0.2 — Template Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.2.0 · Scope: structural intent, architecture coordination and bounded calculation evidence.

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


## Calculation evidence record

Record load-case IDs and evidence states; effect components/units; combination ID and **explicit** factors; exact basis source class, record ID/version and clause/rule reference; calculation receipt; assumptions/limitations. Factors are inputs, never guessed by the calculator.

## Material / section evidence record

Record stable `material_id` / `section_id`; source reference; evidence state; property names, values and units; member binding; revision. Geometry alone must not create resistance evidence.

## Demand / capacity check record

Record check/member ID; supplied demand and capacity in the same declared unit; limit; section/material refs; demand/capacity evidence states; exact check basis; utilization/result; independent review. A local PASS is not whole-structure adequacy.

## Connection / foundation interface record

Record semantic interface/catalog ID; connected members or load-path terminal; transfer/reaction intent; owner; design state; geotechnical dependency state where applicable; disposition/evidence. Placeholder geometry must not be promoted to connection/foundation design.

## Standards applicability record

Record exact standard ID/version/designation/issuer/edition/source; source verification state; applicable/not-applicable/unknown/conflict decision; clause refs; reviewer and rationale. Unknown/conflict blocks compliance-dependent checks.

## Execution record

Stage/chunk ID; semantic member/system IDs; required public software capabilities; source/profile/rule versions; native receipts; independent measurements; checkpoint/recovery evidence.

## Layer and occlusion ledger

Freeze every source layer incl. background/covered/switched-off layers with visibility and evidence state; occluded items stay unknown/inferred until re-observed or approved_assumption, never absent. Final inventory is compared with the frozen ledger via `assess_layer_ledger`; host/base layers commit before dependents via `order_layer_chunks`.

## QA / handoff record

STR rule ID; expected/observed state; independent method; artifact identity; finding severity/result; structural-adequacy limitation; unresolved materials/loads/standards; requested/effective release; downstream responsible reviewer/action.
