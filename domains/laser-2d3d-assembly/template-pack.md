# Laser 2D-to-3D Assembly — Template Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Status: specification templates.

## Session intake (asked every session, no defaults)
job_id; profile_variant (cross-slot | stacked-slice); source_branch (from_3d | from_photo); source photo/3D hashes; material_id (e.g. SUS304 | plywood | MDF | acrylic); thickness_mm (e.g. 2.0 | 5.0); kerf_mm for this laser; slot_clearance_mm; sheet/bed size; units; scope included/excluded; output formats (DWG + DXF flavor + PDF guide); reviewer.

## Material and cut ledger
material_id; thickness_mm + status (specified | unknown | approved_assumption); kerf_mm + source; slot_clearance_mm + approver; per-part slot width derivation (thickness + kerf + clearance); slice step check for stacked-slice; conflicting evidence; decision/approval. Never fill thickness/kerf from an unstated convention.

## Cut plan
feature_id; kind (profile | slot | slice | alignment-hole | nest); input features; dimension IDs; evidence_status (observed | specified | derived | inferred | unknown | approved_assumption); expected postcondition; selected engine/public capability/version; checkpoint and recovery. Photo-derived joints stay `inferred` until test-cut approves them.

## QA
Requirement ID; independent measurement method; actual value; tolerance; contour/slot/slice reference; closed-profile result; nesting extents; uncertainty; rule outcome; artifact hash; verifier and finding disposition. Bounding box alone is supplemental.

## Layer and occlusion ledger
Freeze every source layer incl. background/covered content with visibility and evidence state; photo-occluded joints stay unknown/inferred until re-observed or approved_assumption, never absent. Final layout is compared with the frozen ledger via `assess_layer_ledger`; host/base parts commit before dependents via `order_layer_chunks`.

## Delivery (drawing only)
Native DWG + required DXF hash; exporter and reopening-reader identity; round-trip units/scale check; PDF assembly guide with part labels/quantities; unresolved joints; accepted approximations; review score/hard gates; source/pack/engine versions and replay instructions. Construction method remains the requester's responsibility.
