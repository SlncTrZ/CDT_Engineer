# Skill: cross-slot-dfm

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Owning domain: laser-2d3d-assembly · Status: draft.

## Intent
Design cross-slot interlocking joints for the cross-slot variant so the 2D layout assembles without forcing. Supports SUS304 2mm through wood 5mm+ via per-session material triple.

## Preconditions
LASER-01 intake specified (or approved_assumption); cut_plan features frozen; no open material triple for fabrication_candidate output.

## Inputs
Material triple (thickness_mm, kerf_mm, slot_clearance_mm); part outlines; mating-pair list; sheet/bed size.

## Decisions
Allowed: slot width derivation, slot depth, mating-pair approval within tolerance math. Blocked: zero/negative clearance, blind unmated slot, photo-inferred slot treated as exact without approval.

## Rules
LASER-03, LASER-04. Deterministic slot math: width = thickness + kerf compensation + clearance; depth = 1/2 local width; mating slots coaxial.

## Calculations
Slot-width ledger per joint (deterministic, unit-checked in mm); part-vs-slot count reconciliation; nesting extents vs sheet. LLM proposes layout alternatives; arithmetic stays in tested code/checks.

## Workflow
cut_plan → slot derivation → 2D layout chunks (one part family per chunk) → read-after-write slot measurement → QA. Chunk dependencies follow mating order.

## Capabilities
`technical_2d.create`, `model.query`, `model.measure`, `checkpoint.create` via AutoCAD map; future `solid.feature.create`/`topology.inspect` via SolidWorks only after provider release.

## Assets/dependencies
No catalog family required for first pilot; bounded custom path per job with recorded math.

## Completeness
Joint inventory frozen before mutation; final coverage check detects missing slots, not just validates drawn ones.

## QA
Positive: closed CUT contours, measured slot widths, mated pairs. Negative: open contour, unmated slot, over-bed nest, photo slot as exact.

## Outputs
Nested 2D cut layout + slot ledger + measurement evidence.

## Benchmark
LZ-01/LZ-02 style with SUS304 2mm and wood 5mm session variants.
