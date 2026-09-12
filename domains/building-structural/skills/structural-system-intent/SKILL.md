# Engineering Skill — Structural System Intent

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `structural-system-intent` · Version `0.1.0` · Domain `building-structural` · Lifecycle `pilot`.

## Intent

Establish a traceable structural-system intent for coordination without pretending image/geometry evidence proves final structural adequacy.

## Preconditions / inputs

Frozen Design Basis; architectural levels/grid/interfaces; structural source evidence; structural-system/material/load/standard evidence states; declared release target.

## Decision boundary

May classify/propose a structural system and preserve member/interface intent within evidence. Must not invent member capacity, reinforcement, material grade, load values, foundation design or compliance.

## Deterministic checks

- `evaluate_release_evidence` enforces structural-system evidence for design review;
- unknown materials/loads/standards remain allowed only with adequacy unclaimed at design-review scope;
- stronger release blocks unresolved adequacy inputs;
- member/system IDs and provenance remain stable;
- assumptions are explicit and versioned.

## Workflow

Source/architecture handoff → evidence ledger → structural-system intent → member/system register → adequacy limitations → grid/load-path handoff.

## Software semantics

No native geometry is required to decide system intent. Later representation may use public CAD/model capabilities, but solids/lines are not capacity evidence.

## QA / outputs

Output: structural basis, system/member intent register, evidence states, exclusions and explicit release limitations.

## Negative cases

- RC frame inferred from facade and recorded as observed;
- material grade invented;
- structural system left unknown but design review released;
- visual columns treated as proof of adequate member sizing;
- construction claim made without loads/standards/analysis route.
