# Engineering Skill — Member Demand / Capacity Check

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `member-demand-capacity-check` · Version `0.1.0` · Domain `building-structural` · Lifecycle `pilot`.

## Intent

Evaluate a bounded source-bound demand/capacity comparison for one declared member/check when both demand and capacity already exist as engineering evidence.

## Preconditions / inputs

Stable member ID; section/material references; demand value/evidence state; independently established capacity value/evidence state; common declared unit; explicit utilization limit; exact calculation/test/standard/project basis identity and verification state.

## Decision boundary

The skill may compare supplied values and report local utilization. It **must not** derive resistance from CAD geometry, select material properties, create a design equation not already source-bound, size reinforcement/connections/foundations, or upgrade a local PASS into whole-structure adequacy.

## Deterministic checks

- `domains.building_structural.calculations.evaluate_demand_capacity_checks` validates evidence, positive capacity/limit and stable section/material refs;
- unresolved demand or capacity provenance BLOCKS;
- utilization is `abs(demand) / capacity` for the already compatible supplied quantities;
- utilization above the explicit limit FAILS;
- assumption-dependent values remain visible as limitations.

## Workflow

Freeze demand receipt → freeze section/material/source evidence → freeze supplied capacity and exact check basis → deterministic ratio check → independent reproduction → preserve local finding and downstream limitations.

## Software semantics

No native modeling result is accepted as capacity evidence by itself. Native dimensions may support identity/geometry QA only after the engineering property/calculation source is separately established.

## QA / outputs

Output check/member ID, section/material refs, supplied demand/capacity/unit/limit, utilization, exact basis and result. Independent review verifies the source route that produced capacity; this skill only verifies the comparison.

## Negative cases

- capacity missing but inferred from visible member dimensions;
- section or material reference absent;
- capacity provenance unknown;
- demand and capacity semantics/units not already reconciled;
- one passing check reported as structural adequacy, serviceability, stability, connection or foundation approval.
