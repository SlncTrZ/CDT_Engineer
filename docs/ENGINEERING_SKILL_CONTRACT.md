# Engineering Skill Contract

> Documentation class: PUBLIC_CONTRACT

Version: 0.2.0 · Updated: 2026-09-12 · Status: public contract baseline.

## Purpose

An Engineering Skill is a versioned unit of professional engineering practice that tells an Agent how to perform a bounded engineering task with explicit inputs, rules, calculations, software semantics, QA and deliverables. It is not only a prompt and must not rely on hidden expert assumptions.

## Required contents

A production skill defines:

| Area | Requirement |
| --- | --- |
| Identity | `skill_id`, semantic version, owning domain, lifecycle status |
| Intent | What problem it solves and which deliverable purposes it supports |
| Preconditions | Required Design Basis fields, source authority, prerequisite skills/stages and professional dependency states |
| Inputs | Typed inputs, units/frames, evidence status and allowed unresolved states |
| Decisions | Which judgments are allowed, who may approve assumptions and stop conditions |
| Rules | Domain rule IDs, severity, standard/applicability references and deterministic decision logic |
| Calculations | Deterministic algorithms/validators with units, assumptions and tests |
| Workflow | Ordered stages, expected state, Feature-based Chunk Streaming policy for mutation-heavy work, checkpoints, refusal/recovery actions |
| Capabilities | Required semantic software capabilities; mappings live in software/domain maps |
| Assets/dependencies | Required catalog/system/library/cross-discipline/analysis dependencies, substitution/proxy limits and release effect |
| Completeness | Requirement/feature/detail inventory that lets the Checker detect omissions rather than only validate produced objects |
| QA | Positive/negative cases, independent measurements, relationship/interface checks and hard gates |
| Outputs | Required technical artifacts, drawings/models/documents and evidence |
| Benchmark | Golden inputs, expected results, failure cases and environment/version binding |

## Recommended package shape

```text
<domain>/skills/<skill-id>/
  SKILL.md
  inputs.schema.json
  rules.yaml                 # optional machine-readable rules
  workflow.yaml              # optional machine-readable stage profile
  calculations.*             # only deterministic domain logic
  checklist.md
  drawing-requirements.md    # when human-readable drawings are deliverables
  benchmark/
```

Files are introduced only when useful; empty boilerplate directories are not required.

## Skill reasoning boundary

The Agent may perform professional interpretation and judgment only within the skill's declared decision boundary. Values with engineering authority must preserve provenance:

```text
observed | specified | derived | inferred | unknown | approved_assumption
```

The skill must identify which `inferred` values may continue provisionally, which require approval, and which `unknown` values block dependent work.

Do not convert absence into a default merely to make validation pass.

## Deterministic logic rule

Use deterministic code/tests for invariants such as:

- unit conversion and tolerance comparison;
- geometry/coordinate transforms;
- residuals and numerical checks;
- feature/dependency DAG validation;
- electrical/electronic calculations suitable for deterministic evaluation;
- bounded traversal/counting;
- artifact/evidence hash identity;
- formula-based engineering checks.

Use LLM reasoning for interpretation, alternative generation, trade-off explanation and selection under explicit rules. An LLM answer is not a substitute for a deterministic calculation when the calculation can be encoded and tested.

## Standards binding

A skill may reference a standard-derived rule only through a versioned standards record/applicability decision. It records the exact derived rule implementation and source reference needed for review. A standard name without edition/applicability does not activate compliance behavior.

Protected normative text is not required in the public skill package; permitted metadata, clause references and original derived logic are sufficient when full text is access-controlled.

## Semantic dependency and asset boundary

A skill resolves professional meaning before native implementation. If it needs a reusable technical system/component, it selects through the applicable [Engineering Asset Catalog Contract](../catalogs/ENGINEERING_ASSET_CATALOG_CONTRACT.md) or an explicitly bounded custom path. Native files/blocks/components are software representations, not the source of professional applicability.

Missing skill/catalog/standard/interface/calculation/evidence dependencies follow the [Release Scope & Semantic Dependency Policy](RELEASE_SCOPE_POLICY.md). A proxy may be valid for a weaker declared scope, but the skill must not silently substitute primitives or placeholders while retaining a stronger release target.

When the task is source/reconstruction/detail heavy, the skill freezes a requirement/feature/detail inventory before mutation and makes final coverage a Checker input. A plausible output with a required item omitted is not a PASS.

## Software boundary

A skill declares semantic capabilities, for example:

```text
document.open
geometry.measure
feature.create
artifact.export
layout.dimension
render.camera
```

It must not hard-code a native backend as the only business logic. Domain/software mappings choose concrete public engine tools. If a required capability is absent at runtime, the skill returns a typed blocker or an approved reduced-scope path; it does not bypass the public engine contract.

## Feature-based Chunk Streaming requirement

A mutation-heavy skill must define semantic chunk boundaries or chunking rules. It must avoid both monolithic whole-project mutation and primitive-per-command Agent streaming. Each chunk should represent one meaningful, bounded engineering feature or reviewable unit, carry explicit dependencies, and expose measurable postconditions.

The skill defines what belongs together semantically; the selected software guide defines concrete payloads, transaction/checkpoint capabilities, chunk budgets and UI-yield behavior. See [Feature-based Chunk Streaming Contract](FEATURE_CHUNK_STREAMING_CONTRACT.md).

If the selected engine cannot provide truthful recovery/isolation for the requested release class, the skill must block or reduce scope rather than pretend atomic rollback exists.

## Drawing and human-use requirements

When the output is intended for construction, fabrication, assembly, inspection or review by people, the skill defines human-readable communication requirements such as views, sections, details, datum/reference system, dimensions/tolerances, notes, legends, schedules/BOM, revision identity and scale/readability expectations.

For every deliverable family active at the requested release, the skill supplies at least one hard-gate requirement or explicitly defers to an equivalent domain package. Score-only polish cannot account for an active family. N/A dispositions require a reason, approval/reviewer evidence and exact source/artifact revision identity. Missing, unverified or stale hard-gate evidence blocks regardless of quality score; reviewer role and independence requirements are explicit. The reusable executable baseline is `professional_practice.human_deliverables`; discipline skills remain responsible for defining the actual technical requirements and evidence.

A geometrically correct model does not automatically satisfy a drawing-delivery skill.

## Skill lifecycle

Suggested states:

```text
draft → benchmarked → pilot → production → deprecated
```

Production requires implemented deterministic checks where applicable, benchmark evidence, public engine route evidence for required software work, negative cases, independent review and versioned migration behavior.

## Acceptance invariant

A skill is trustworthy only when another competent Agent/Checker can reconstruct why it made each engineering decision from frozen inputs, rules, versions, calculations, evidence and approvals.
