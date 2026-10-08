# Laser 2D-to-3D Assembly — Benchmark Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Status: draft golden cases; native SolidWorks/Blender acceptance blocked by provider implementation.

## Cases
- LZ-01: session intake closes material triple for SUS304 2mm cross-slot job; drawing releases to technical_draft.
- LZ-02: cross-slot Pegasus layout from hashed 2D/3D source; slot ledger matches thickness + kerf + clearance; all CUT polylines closed.
- LZ-03: stacked-slice torso from hashed 3D source; slice step equals thickness; alignment `+` holes present top/bottom; nesting fits sheet.
- LZ-04: single-photo Pegasus reinterpretation; proxy label applied; release capped at technical_draft pending test-cut.
- LZ-05: single-photo torso reinterpretation; proxy label applied; slice count declared as artistic choice, not measured fact.
- LZ-06: DXF + PDF export reopened with identified reader; units/scale and part labels verified.

## Current native blockers
`provider_not_implemented` (CDT-SolidWorks skeleton, no callable MCP) and missing `software/blender/` guide. LZ cases requiring solid/mesh mutation correctly yield typed BLOCKED until providers release; AutoCAD 2D layout cases remain executable.

## Failure / recovery matrix
- **early failure:** unknown material triple, un-hashed source, or missing capability blocks before cut geometry.
- **middle failure:** open contour, slot mismatch, slice-step drift, or over-bed nesting stops dependents; reconcile layout state, compensate from checkpoint, verify no duplicate entities before retry.
- **late failure:** DXF reopen/unit drift or missing labels invalidates release evidence.
- **uncertain completion / timeout:** re-query layout state before retry; never blindly replay a non-idempotent batch.

## Negative ladder
Unspecified thickness treated as exact; photo joints treated as exact; open CUT contour; slot step mismatch; over-bed nesting; DXF unit drift; missing BOM/labels; changed sealed hash.

## Oracle and release
Session requester freezes material triple, source hashes, expected part/joint inventory, and DXF flavor before generation. Drawing PASS means cut-usable drawing, never construction certification. Record exact application, provider/build/contract, pack versions, tool receipts, inspector, output hashes, and unresolved findings.
