# Laser 2D-to-3D Assembly — Rule Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.2.0 · Status: LASER-01..06 deterministic guards implemented in `domains.laser_2d3d_assembly.guards`; pilot for decorative laser-cut assemblies · Updated: 2026-10-03.

Scope: two profile variants — `cross-slot` (planar interlocking puzzle, e.g. Pegasus) and `stacked-slice` (parallel contour lamination, e.g. torso). Deliverable is the 2D cut drawing (DWG/DXF + PDF guide); physical construction stays with the requester.

| Rule | Inputs and deterministic decision | Failure/severity | Required evidence |
| --- | --- | --- | --- |
| LASER-01 Session material intake | `material_spec` (material_id, thickness_mm, kerf_mm, slot_clearance_mm, status) must be asked per session before any cut geometry; SUS304 2mm and wood 5mm are different jobs, never a domain default | BLOCK fabrication_candidate/technical_draft cut output on `unknown` triple | Intake record with material answers + approver |
| LASER-02 Source branch | `from_3d` requires hashed 3D source; `from_photo` requires artistic-interpretation stage and proxy label, max `technical_draft` until test-cut | BLOCK stronger release on un-hashed source or unlabeled photo proxy | Source manifest + branch disposition |
| LASER-03 Cross-slot DFM | Slot width = thickness + kerf compensation + clearance; slot depth = 1/2 local width; mating slots coaxial; count parts vs slots | BLOCK on negative clearance, blind slot, or unmated joint | Slot ledger + measurement |
| LASER-04 Closed profiles | Every CUT contour is a closed polyline; no zero-length segments; min bridge/web per material recorded or explicitly unknown | BLOCK on open contour or unmeasurable bridge for requested release | Read-back measurement list |
| LASER-05 Slice step | `stacked-slice` step = sheet thickness; slice order + alignment holes (`+` marks top/bottom) preserved; missing slice count blocks | BLOCK on step mismatch or missing alignment | Slice index + alignment check |
| LASER-06 Nesting | Parts nested inside declared sheet/bed size; grain direction noted for wood; over-bed layout blocks | BLOCK on over-bed or undeclared sheet | Nesting extents vs sheet |
| LASER-07 Exchange export | Required DXF flavor + PDF assembly guide exported; DXF reopened with identified reader; units/scale compared | BLOCK on unavailable exporter or unit drift | Native + DXF hashes + reopen measurements |
| LASER-08 Drawing usability | Views, part labels/quantities, datum, notes (material/thickness/kerf), revision identity, readability verified for human cutting | BLOCK on missing label/BOM/notes for requested release | Independent package check |

## Deterministic implementation

`domains.laser_2d3d_assembly.guards` implements:
- `evaluate_material_intake`: validates material triple (thickness, kerf, clearance); blocks non-concept releases on unknown/missing values (LASER-01);
- `evaluate_cross_slot_dfm`: verifies slot width clearance, depth limits against part severance and mating slot coaxiality (LASER-03);
- `evaluate_cut_contour`: validates closed polyline, non-zero segment lengths, non-self-intersection and positive contour area (LASER-04);
- `evaluate_slice_step`: verifies elevation delta equals sheet thickness and alignment features are present (LASER-05);
- `evaluate_nesting_layout`: checks that nested parts extents fit within the sheet bed size minus safety margins (LASER-06).

Result vocabulary: pass/fail/unknown/not_applicable, linked to rule version and evidence. `unknown` material triple is structurally valid input but a fabrication_candidate drawing remains BLOCK/unknown under LASER-01 until specified or approved_assumption. No construction/manufacturing certification from drawing rules alone.

Negative cases: unspecified thickness; photo slot positions treated as exact; open CUT polyline; slice step != thickness; over-bed nesting; DXF unit drift; missing part labels; changed sealed artifact hash.
