# Site Reconstruction — Template Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.2.0 · Status: specification templates.

## Intake record
job_id; source manifest with hashes; dependency graph; included/excluded scope; source and target units/frames; desired DWG/SketchUp outputs; standard selections; reviewer and structured acceptance tolerance (`status`, `value`, `unit`, `source_ref`, `approved_by`).

## Interpretation and registration record
Source layer/block → engineering role → target hierarchy/tag → source evidence; control point pairs; fit method; row-major transform; unit scale; determinant/handedness; residuals/holdout; inferred elevations; unresolved XREFs; approved assumptions.

## Layer and occlusion ledger
For every source layer incl. background, switched-off, and covered layers record: layer_id; item_ids on that layer; visibility (visible|occluded|off|absent); evidence_state per item (occlusion is unknown/inferred until re-observed or approved_assumption, never absent); hosted_on host/base ids; required flag; exclusion reason when de-required. The final 3D inventory is compared with this frozen ledger via `assess_layer_ledger`; a dropped background or an unresolved occluded required item blocks release. Host/base layers are ordered before dependents via `order_layer_chunks`.

## Execution plan
Stage ID; prerequisites; domain algorithm/rule version; required public engine capability; actual tool/contract/backend version; bounded query/mutation budget; expected state; checkpoint; refusal and recovery action. Preserve block reuse rather than flattening silently.

## QA record
Rule ID/version; expected value; measured value; unit/tolerance; independent inspector; artifact hash; result; finding severity; excluded/unknown scope; screenshots with explicit reference/display state.

## Handoff record
Native artifacts and hashes; source-to-target registration; model organization map; included/excluded/deferred work; standard applicability decisions; benchmark/rubric result; unresolved findings; reviewer acceptance; reproduction instructions and checkpoint identity.

Every field must be filled or explicitly marked unresolved with an owner. Unknown required evidence blocks acceptance. Raw customer paths and data remain private.
