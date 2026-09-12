# Engineering Skill — Building Architecture QA

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `building-qa` · Version `0.1.0` · Domain `building-architecture` · Lifecycle `pilot`.

## Intent

Independently verify that the final architectural artifact satisfies the frozen Design Basis, semantic graph, component/system decisions, feature inventory and declared release class.

## Preconditions / inputs

Frozen Design Basis/source hashes; semantic building graph; applicable rules/standards; feature inventory; component-resolution manifest; final artifact identity; producer receipts; current runtime/application identity.

## Decision boundary

Checker may independently measure/query and issue findings. It must not fill missing producer evidence with assumptions or treat screenshots/generic integrity as proof of architectural correctness.

## Deterministic checks

- rerun `validate_levels`, `evaluate_space`, `evaluate_opening_host`, `evaluate_stair` on frozen inputs/independent measurements where applicable;
- rerun `evaluate_feature_inventory` against the requested release;
- verify semantic IDs/host relationships/component reuse against native query evidence;
- verify required feature/detail inventory completeness;
- verify artifact hash/reopen evidence is current;
- any unresolved BLOCKER/MAJOR finding prevents release through the executable QA Checker.

## Workflow

Freeze artifact → independently query/measure → compare semantic graph/inventory → domain relationship/topology checks → drawing/deliverable review → artifact reopen/hash check → findings → release verdict.

## Software semantics

Use read/query/measure/topology/reopen capabilities of the selected engine. Mutation receipts and screenshots are supplemental and cannot substitute for independent evidence.

## QA / outputs

Output: hash-bound findings, coverage matrix for ARCH-01..10, unresolved dependencies, release limitations and Checker verdict.

## Negative cases

- generic integrity is clean but opening host relation is wrong;
- artifact looks similar to source but required visible details are missing;
- proxy component used above allowed scope;
- producer receipt reused as independent measurement;
- artifact changes after QA but old PASS is reused.
