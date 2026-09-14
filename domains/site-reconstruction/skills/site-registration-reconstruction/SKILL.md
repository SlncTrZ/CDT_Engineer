# Engineering Skill — Site Registration Reconstruction

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `site-registration-reconstruction` · Version `0.1.0` · Domain `site-reconstruction` · Lifecycle `pilot`.

## Intent

Reconstruct a bounded site/base model from frozen source evidence by resolving coordinate frames, units, registration controls and holdouts before native mutation. The skill preserves source truth and produces measurable registration/reconstruction evidence; it does not invent missing XREFs, survey controls, project tolerances or hidden existing conditions.

## Preconditions and inputs

- Design Basis purpose, requested release, source manifest and target host are explicit.
- Available source files are hash-bound; missing sources remain typed dependencies.
- Source/target units and coordinate frames are declared.
- Registration controls and independent holdouts are supplied from authoritative or approved sources.
- Registration tolerance is `approved` with source/approver before SITE-03 can PASS.
- `inputs.schema.json` validates the bounded skill input.

## Deterministic checks

`domains.site_reconstruction.guards` provides the executable invariants used by this skill: `inspect_affine`, `compose_affine`, `apply_affine_point`, `evaluate_registration` and `validate_nested_graph`. These checks do not fit a transform or choose a tolerance on behalf of the responsible engineer.

## Decision boundary

The Site/Landscape role may classify sources, select an applicable declared transform model, plan semantic reconstruction chunks and evaluate supplied registration evidence. It may not fabricate survey authority, omitted XREF content, geodetic transformations, acceptance tolerance or as-built truth.

## Workflow and recovery

Use `workflow.yaml` in order: source closure → registration → semantic feature plan → native bounded reconstruction → independent QA → handoff. Native mutations use Feature-based Chunk Streaming. On uncertain completion, reconcile native identities/checkpoint state before any retry; never replay a non-idempotent chunk blindly.

## Software semantics

Typical required semantics are `source.inventory`, `dependency.inspect`, `model.measure`, `coordinate.transform.inspect`, `technical_2d.create`, `technical_2d.modify`, `model.query`, `model_3d.create`, `model_3d.transform`, native save/reopen and independent artifact evidence. Native implementations remain in CDT-AutoCAD/CDT-SketchUp; this skill never bypasses public engine contracts.

## Completeness and QA

Freeze an inventory of required source files/XREFs, registration controls, holdouts, semantic layers/features, output artifacts and excluded scope. Independent QA re-evaluates transform/unit invariants, residuals, feature coverage and final artifact identity. Missing authoritative inputs may permit an explicitly reduced scope but cannot be hidden by visually plausible geometry.

## Positive benchmark

Available/hash-bound sources, nondegenerate controls plus independent holdouts, approved tolerance with residuals inside limit, bounded nested graph, native feature read-back and final reopen/remeasure evidence.

## Negative cases

Missing required source; unverified hash; singular/reflected/double-scaled transform; degenerate controls; unresolved tolerance; excessive holdout residual; nested-reference cycle/budget overflow; blind retry after timeout; stale handoff evidence.

## Outputs

Frozen source/dependency manifest; coordinate/registration decision; deterministic guard evidence; semantic feature/chunk plan; native receipts/read-back; independent residual/measurement evidence; final artifact identity; unresolved limitations; exact release verdict.
