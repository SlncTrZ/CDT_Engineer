# Site Reconstruction — Rule Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.3.0 · Status: SITE-02/03 and bounded SITE-04 guards implemented; remaining rules specified · Origin: internal reconstruction policy.

| Rule | Inputs and deterministic decision | Failure/severity | Required evidence |
| --- | --- | --- | --- |
| SITE-01 Source closure | Check DWG and all relevant XREF/resource dependencies by status/hash; missing source prevents full-fidelity scope | BLOCK for dependent geometry | Dependency graph and explicit exclusions |
| SITE-02 Units and frames | Validate units and affine transform; reject singular transforms, unexplained reflection or duplicate unit scaling | BLOCK | Matrix convention, determinant, scale, source/target units |
| SITE-03 Registration | Require at least 3 non-collinear matched control points for planar registration; full 3D registration requires sufficient independent spatial constraints; compute residual for every point and independent holdout | BLOCK above preapproved tolerance or degenerate controls | Coordinates, fitting method, residuals in target units, holdout result |
| SITE-04 Nested blocks | Compose parent-to-child transforms in declared order; detect cycles and enforce traversal budget; retain source-to-output identity mapping | BLOCK on unresolved transform/cycle/truncation | Nested graph, transformed landmarks and block instance counts |
| SITE-05 Semantic interpretation | Map source layers/blocks to domain roles; every reconstructed item links source evidence or an approved assumption | BLOCK for unsupported critical inference | Classification/assumption ledger |
| SITE-06 Completeness | Compare included objects, extents, axes and repeated instances with frozen oracle; no invented elevations or missing-condition content | BLOCK for required omissions | Independent counts, extents, elevations and exclusions |
| SITE-07 SketchUp handoff | Verify target units, transform, hierarchy/tags and reusable instances after reopening actual output | BLOCK for missing native output or wrong scale | Reopen receipt, identity mapping, measurements |
| SITE-08 Artifact seal | Verify final hashes after close/seal; later changes invalidate result | BLOCK/stale_evidence | Final native artifact manifests |
| SITE-09 Layer carry | Freeze every layer incl. background/occluded/off layers with visibility + evidence state before mutation; final inventory must carry all required frozen items with host/base chunks committed first; occlusion is never absence | BLOCK on dropped background, unresolved occluded required item, or foreground scheduled before its host | Frozen layer ledger, `assess_layer_ledger` result, host-ordered chunk receipts |

Rules yield pass/fail/unknown/not_applicable with rule version and evidence. Registration tolerance is a structured evidence value (`unresolved|proposed|approved|not_applicable`); `unresolved` is structurally valid input but SITE-03 remains BLOCK/unknown until an approved positive tolerance exists. Tolerances are project-approved inputs, not invented standard defaults. No TCVN/ISO/ASME claim is activated by these internal rules.

Mandatory negative cases: unresolved XREF; mixed units; mirrored/nested INSERT; collinear controls; wrong transform order; incomplete paged query; source hash drift; reopened output scale error. Each must fail the relevant gate without claiming a completed reconstruction.

## Deterministic implementation status

`domains.site_reconstruction.guards` is the public deterministic implementation for the geometry-only portions of SITE-02, SITE-03 and SITE-04. It validates row-major affine/homogeneous form, determinant/singularity, handedness/reflection policy, explicit unit scale, `T * R * S` composition, control/holdout residuals, planar non-collinearity, and bounded nested-graph cycle/truncation. It never fits an unknown transform or invents a tolerance.

An unresolved tolerance yields `unknown`, even when measured residual is exactly zero. Source/dependency closure, semantic classification, completeness, native SketchUp handoff and artifact sealing remain separate gates; passing these guards alone is not a reconstruction PASS.
