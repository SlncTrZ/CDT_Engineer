# Skill: contour-slicing-nesting

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Owning domain: laser-2d3d-assembly · Status: draft.

## Intent
Slice a stacked-slice form into parallel cut contours at sheet-thickness step with alignment holes, then nest for the laser bed. Works for any per-session thickness (cardboard through thick wood).

## Preconditions
LASER-01 intake specified (or approved_assumption); slice axis and direction declared; 3D source hashed or proxy labeled.

## Inputs
3D source or approved proxy; thickness_mm as slice step; alignment-hole positions; sheet/bed size; DXF flavor.

## Decisions
Allowed: slice order, alignment placement, nest arrangement. Blocked: step != thickness without recorded approval; missing alignment; photo contour treated as exact.

## Rules
LASER-05, LASER-04, LASER-06. Step equals thickness; every slice contour closed; `+` alignment top/bottom preserved; nesting fits declared sheet.

## Calculations
Slice count = extent / step reconciliation; contour-closure check; extents-vs-sheet check. Deterministic counting/measurement; artistic shape stays in source/proxy.

## Workflow
cut_plan → slice derivation → layout chunks (slice batches in order) → alignment verification → nest → QA. Slice order is the chunk dependency chain.

## Capabilities
`technical_2d.create`, `model.query`, `model.measure`, `checkpoint.create` via AutoCAD map; future mesh slicing via CDT-Blender only after its guide/provider release.

## Assets/dependencies
No catalog family required for first pilot; bounded custom path per job.

## Completeness
Slice index frozen before mutation; final coverage detects missing slices, not just validates drawn ones.

## QA
Positive: ordered closed slices, alignment holes, fitted nest. Negative: step drift, missing alignment, open contour, over-bed nest.

## Outputs
Ordered slice layout + alignment record + nesting evidence + stacking guide content.

## Benchmark
LZ-03/LZ-05 style: hashed-3D deterministic slices and single-photo proxy slices.
