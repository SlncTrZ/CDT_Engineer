# Engineering Skill — Building Drawing Package

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `building-drawing-package` · Version `0.1.0` · Domain `building-architecture` · Lifecycle `pilot`.

## Intent

Assemble a human-reviewable architectural drawing package whose views, dimensions, notes, details, schedules and revision identity match the declared release scope and frozen semantic model.

## Preconditions / inputs

Accepted semantic building graph; frozen feature/detail inventories; Design Basis/release target; exact applicable standards where compliance is claimed; final model/drawing artifact identities.

## Decision boundary

May compose and check drawings from accepted engineering data. Must not promote missing model/detail/structural/standard evidence through annotations or presentation quality.

## Deterministic checks

- required view/detail/schedule inventory is explicit for the job and evaluated through `execution.completeness_checker.assess_inventory`;
- dimensions/labels reference stable semantic entities or independently measured geometry;
- revision/package identity is present and hash-bound when required;
- required details from `architectural-detail-package` are represented and verified;
- a model PASS does not automatically produce a drawing-package PASS.

## Workflow

Deliverable requirements → drawing inventory → plans/elevations/sections/detail references → dimensions/notes/schedules → readability/revision review → independent completeness check → final artifact/hash handoff.

## Software semantics

Use public layout/dimension/plot/export/query capabilities where available. Manual/private bypasses cannot substitute for missing required public capabilities in production acceptance.

## QA / outputs

Output: versioned drawing inventory, view/detail/schedule coverage, independent dimension evidence, readability/revision findings and final package identity.

## Negative cases

- model is correct but section/detail required by release is absent;
- drawing dimension disagrees with independently measured model geometry;
- stale drawing set references a newer model revision;
- unreadable scale/text or missing revision identity;
- render/screenshot substituted for a required technical drawing.
