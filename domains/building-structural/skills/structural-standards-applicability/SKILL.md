# Engineering Skill — Structural Standards Applicability

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `structural-standards-applicability` · Version `0.1.0` · Domain `building-structural` · Lifecycle `pilot`.

## Intent

Verify that a required structural compliance basis is pinned to exact, reviewable standards/project-rule evidence before compliance-dependent calculations or release claims proceed.

## Preconditions / inputs

Required standard IDs identified by the Design Basis/responsible authority; registry-like records with exact designation, issuer, edition, record version, source, verification status, applicability decision, clause references, reviewer and decision rationale.

## Decision boundary

The skill may validate evidence completeness and applicability state. It **must not** decide jurisdiction from guesswork, replace an exact edition with `latest`, auto-resolve conflicts, invent clause requirements, reproduce protected normative text, or declare the design compliant merely because the evidence gate passes.

## Deterministic checks

- `domains.building_structural.standards.evaluate_standard_applicability` requires every requested ID to exist uniquely;
- `latest`, `current`, `unspecified` and `unknown` editions BLOCK;
- metadata-only/unavailable source evidence BLOCKS a compliance basis;
- unknown, conflict or required-but-not-applicable state BLOCKS;
- applicable records require clause references, reviewer and rationale.

## Workflow

Freeze Design Basis/jurisdiction inputs → identify required records → verify exact source/edition → record applicability/reviewer decision → map relevant clause/rule references → run deterministic evidence gate → hand off only accepted records to derived calculations/rules.

## Software semantics

No CAD/native capability is involved. Protected standards content remains in authorized storage; public evidence carries permitted metadata/references and original derived logic only.

## QA / outputs

Output applicable record IDs, exact frozen metadata, blocker reason codes and reviewer rationale. Passing this skill means the standards basis is reviewable, not that every technical requirement has passed.

## Negative cases

- edition set to `latest`;
- publisher/source only metadata-verified where source verification is required;
- applicability remains unknown or conflicting;
- required applicable record has no clause mapping;
- model geometry or a generic engineering heuristic reported as code compliance.
