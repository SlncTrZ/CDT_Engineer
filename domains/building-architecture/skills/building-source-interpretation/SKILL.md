# Engineering Skill — Building Source Interpretation

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `building-source-interpretation` · Version `0.1.0` · Domain `building-architecture` · Lifecycle `pilot`.

## Intent

Convert images/drawings/models/text requirements into a frozen architectural evidence and feature inventory before any native geometry mutation.

## Preconditions / inputs

Design Basis purpose/release; source identities/hashes; units/reference anchors when known; source authority ranking. Every interpretation is tagged `observed|specified|derived|inferred|unknown|approved_assumption`.

## Decision boundary

May classify visible architectural features and propose hypotheses. Must not invent hidden dimensions, structural systems, reinforcement, materials, code compliance or construction details. Critical inferred/unknown items receive an explicit release effect.

## Deterministic checks

- available sources have stable identities/hashes;
- feature inventory IDs are unique;
- every required item carries source evidence, semantic family and resolution state;
- no critical `unknown` is rewritten as specified merely to continue;
- `evaluate_feature_inventory` enforces omission/proxy limits at downstream release.

## Workflow

Source inventory → view/reference assessment → observed feature extraction → uncertainty/provenance ledger → semantic family classification → dimensional-anchor strategy → required/detail inventory → handoff to semantic building plan.

## Software semantics

No native mutation is required. Source inspection may use public read/query capabilities when available; absence of a reader does not authorize private bypass.

## QA / outputs

Output: frozen source manifest, feature inventory, uncertainty map, source-to-semantic traceability and explicit blockers. Checker compares later artifact content against this inventory.

## Negative cases

- visible facade/opening/detail omitted from inventory;
- image-only structural assumption recorded as specified;
- unverified source treated as authoritative;
- missing dimensional anchor silently replaced by guessed construction dimensions;
- execution begins before inventory/provenance closure.
