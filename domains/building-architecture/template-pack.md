# Building Architecture v1 — Template Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Scope: low-rise residential / design-review baseline.

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

## Execution chunk record

Stage/chunk ID; semantic type; entity/system IDs; dependencies; source/catalog versions; required public capabilities; expected postconditions; transaction/recovery mode; native receipts; read-after-write measurements; checkpoint identity.

## QA record

Rule/requirement ID; expected semantic state; independent measured/query state; unit/tolerance when applicable; artifact hash; inventory coverage; topology/relationship evidence; finding severity/result; reviewer context.

## Handoff record

Native/exchange/document artifacts and hashes; Design Basis/domain/profile/skill/catalog versions; included/excluded/deferred scope; proxies/custom items; unresolved structural/standards dependencies; reopen measurements; Checker verdict; explicit release-class label and limitations.
