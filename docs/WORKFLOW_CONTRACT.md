# Engineering Workflow Contract

Version: 0.1.0 · Updated: 2026-09-12 · Status: architecture baseline.

## Purpose

A workflow composes Engineering Roles, Domain Skills, standards decisions, software semantics and QA into a purpose-dependent engineering delivery sequence. Workflows are selected from the Design Basis, not from a preferred software package.

## Required stage fields

Each workflow stage defines:

- `stage_id` and purpose;
- owning role/discipline;
- required Design Basis fields and upstream artifacts;
- Engineering Skills/rules invoked;
- required semantic capabilities;
- expected state/output;
- bounded query/mutation budget where relevant;
- Feature-based Chunk Streaming policy, semantic chunk boundaries and dependency order for mutation-heavy stages;
- checkpoint and artifact identity;
- read-after-write/measurement verification;
- stop/block conditions;
- timeout/uncertain-state reconciliation;
- recovery/resume/compensation action;
- handoff to downstream stage;
- QA gate and release effect.

## Canonical professional flow

```text
Intake
→ Step-0 execution-environment discovery
→ Design Basis
→ discipline/role selection
→ source closure
→ interpretation/design
→ standards applicability
→ capability preflight
→ bounded execution
→ stage verification/checkpoint
→ independent QA
→ documentation/handoff
→ artifact seal
→ ready_for_professional_review
```

Stages may be omitted only when the selected deliverable purpose makes them not applicable and the workflow records that decision.

## Capability semantics

A workflow consumes a Step-0 environment compatibility result before requiring semantic capabilities; software maps then bind those capabilities to public engine tools. Cached inventory is not runtime proof for mutation-heavy work. Example:

```text
technical_2d.create
technical_2d.dimension
model_3d.measure
solid.feature.create
artifact.native_save
artifact.exchange_export
render.camera.configure
```

Capability mapping is explicit per software/application. Do not create a weak universal CAD API and do not use private native bypasses to close a public acceptance gate.

## Multi-software workflow

The Agent may move work across AutoCAD, SketchUp, Blender, SolidWorks or future engines when the Design Basis and deliverable purpose justify it. Each transfer defines:

- source and target artifact identity;
- units/frame/scale convention;
- semantic fidelity expected;
- information intentionally lost/deferred;
- receiving software capability preflight;
- transfer/reopen verification.

A format conversion is not automatically a valid engineering handoff.

## Example classes

### Building / architecture

```text
requirements
→ architectural Design Basis
→ site/constraints
→ 2D technical planning
→ dimension/circulation/rule checks
→ sections/elevations basis as required
→ SketchUp or other 3D model
→ optional Blender visualization
→ drawing/model/render package
→ Checker
```

### Mechanical / manufacturing

```text
requirements/source drawing
→ mechanical/manufacturing Design Basis
→ feature/dimension/tolerance plan
→ native part/assembly edit or reconstruction
→ manufacturability + dimension/topology verification
→ drawing views/sections/dimensions/notes/BOM
→ native + neutral/shop outputs
→ Checker
```

### Civil / infrastructure

```text
survey/source package
→ civil Design Basis
→ alignment/levels/grading/drainage interpretation
→ technical plan/profile/sections/details
→ constructability/interface checks
→ drawing package
→ Checker
```

## Feature-based Chunk Streaming

Mutation-heavy stages default to [Feature-based Chunk Streaming](FEATURE_CHUNK_STREAMING_CONTRACT.md). The Agent decomposes work into semantic engineering units rather than sending an entire project in one opaque mutation or one primitive LINE/ARC/face/feature per Agent turn.

Each chunk is planned, preflighted, executed within the strongest truthful transaction/checkpoint mode supported by the selected engine, reconciled, independently queried/measured, committed, optionally yielded to the UI, then releases its dependent chunks. A failed/uncertain chunk stops dependent work and is locally recovered/replanned before continuation.

Concrete payloads, transaction primitives, chunk budgets and redraw/UI-yield behavior remain software-specific and are documented by each software guide/engine map.

## Retry and recovery

After timeout or uncertain mutation, never retry blindly. Query/reopen/reconcile actual state, compare with checkpoint and choose one of:

```text
resume
compensate
restart_from_checkpoint
block_for_review
```

The workflow records the decision and new evidence.

## Workflow versioning

Breaking changes to stage meaning, required evidence or release behavior require a major workflow version. Additive stages/capabilities may be minor when old job semantics remain reproducible. Historical runs pin exact workflow/domain/skill/software-map versions.
