# Building Architecture v1 — Template Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.2.0 · Scope: low-rise residential / design-review baseline.

## Intake / Design Basis record

Record: job/revision; intended use and release class; source manifest/hashes; jurisdiction; exact standards/applicability decisions; units/reference frame; included/excluded disciplines; required 2D/3D/drawing outputs; reviewer; unresolved dependencies.

## Source interpretation record

For every observed or required feature record:

```text
item_id
source_evidence
observation
semantic_family
evidence_status: observed|specified|derived|inferred|unknown|approved_assumption
resolution_state
release_effect
```

Do not convert a missing dimension, hidden construction system or structural fact into a specified value.

## Semantic building plan

```text
levels
spaces / circulation
wall systems
openings
doors/windows
stairs/railings
roof/parapet
facade systems/modules
materials/finish intent
interior fit-out/casework systems when in scope
structural-role/interface state
feature/detail inventory
```

Each entity preserves stable identity and provenance. Dependencies are planned before native geometry.

## Component resolution record

```text
semantic entity id
engineering asset/catalog family
resolution: resolved|custom_allowed|proxy_allowed_for_scope|reduced_scope|blocked
component/asset id + version if resolved
native mapping state
host/interface rules
allowed transforms/parameters
proxy/custom rationale
maximum allowed release
replacement requirement
```

## Interior casework record

When interior fit-out is in scope, record: system/module IDs; source/scale basis; module kind; box or orthogonal-corner geometry; panel-system/material semantic reference; explicit panel thicknesses; compartment widths/partition thickness; drawer/equipment envelopes; six-side clearance values plus source; host/fixing dependency state; catalog/custom/proxy resolution; release effect; deterministic ARCH-11 results.

Unknown manufacturer/project clearances or fixing adequacy stay unknown and block dependent stronger claims rather than receiving a default.

## Execution chunk record

Stage/chunk ID; semantic type; entity/system IDs; dependencies; source/catalog versions; required public capabilities; expected postconditions; transaction/recovery mode; native receipts; read-after-write measurements; checkpoint identity. Interior native chunks additionally preserve semantic ID, persistent ID/definition GUID where applicable, predecessor context/fingerprint and duplicate-instance checks so uncertain non-idempotent placement is never blindly replayed.

## QA record

Rule/requirement ID; expected semantic state; independent measured/query state; unit/tolerance when applicable; artifact hash; inventory coverage; topology/relationship evidence; finding severity/result; reviewer context.

## Layer and occlusion ledger

Freeze every source layer incl. background/covered/switched-off layers with visibility and evidence state; occluded items stay unknown/inferred until re-observed or approved_assumption, never absent. Final inventory is compared with the frozen ledger via `assess_layer_ledger`; host/base layers commit before dependents via `order_layer_chunks`.

## Handoff record

Native/exchange/document artifacts and hashes; Design Basis/domain/profile/skill/catalog versions; included/excluded/deferred scope; proxies/custom items; unresolved structural/standards dependencies; reopen measurements; Checker verdict; explicit release-class label and limitations.
