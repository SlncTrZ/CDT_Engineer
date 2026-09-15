# SolidWorks Operating Guide

> Documentation class: PUBLIC_SOFTWARE_GUIDE
> Version: 0.3.0 · Status: frozen parallel contract mapped; final Agent-7 composition and runtime proof still required.

## Step-0
Discover the live **CDT-SolidWorks** provider before every Mechanical execution: provider/build identity, final composed plugin contract, callable tool surface, capability descriptors, SolidWorks installation/version/build/edition, registration/running state, required dependencies and the strongest available license-readiness evidence. Source mapping is not runtime proof. Missing provider, tool, dependency, license evidence or capability availability is a typed BLOCKED result before mutation.

The Agent-5 map is anchored to frozen base `51e5ecfc6376b4146266811b7cd3f36020a89967` and `inter-agent-contract-v1`. It intentionally does not claim the final post-integration tool count.

## Compatibility
Classify SolidWorks as `compatible` only when runtime discovery confirms the exact tools required by the active stage and their capability descriptors report `available=true`. A mapped source tool name is only an expected route. `parallel_integration_not_accepted`, `tool_missing`, `capability_missing`, `dependency_unavailable`, `license_unverified`, `version_mismatch` or `runtime_unknown` must fail closed.

Direct COM/.NET calls from CDT_Engineer are prohibited as a production bypass. All native work goes through released CDT-SolidWorks public tools after live discovery.

## Semantic capability map
Current frozen-contract mappings include:

- `solid.feature.create` → bounded public routes including `part_create_rect_extrude`, `part_cut_extrude`, `part_revolve`, `part_revolve_cut`, `part_simple_hole`, `part_hole_wizard`.
- `solid.boolean` → `body_combine`, `part_combine_all_bodies`.
- `model.query` → `document_list_features`, `document_list_bodies`, `body_inspect`.
- `model_3d.measure` → `evaluation_measure`, `evaluation_bounding_box`.
- `checkpoint.create` / native persistence → `document_save`; save-as → `document_save_as`; reopen → `document_reopen`.
- neutral exchange → `export_document` for the provider-supported source/format pairs.
- Agent-5 reconstruction → `reconstruction_assess`, `reconstruction_step_to_editable`, `reconstruction_mesh_to_parametric`, `reconstruction_compare`.

`topology.inspect` remains `unproven` at this lane boundary because Agent-5 consumes the frozen injected topology port but does not invent Agent-1's final public tool name. `artifact.seal` also remains unproven.

## Feature chunks
Mechanical execution remains dependency-bounded: source assessment → topology/mesh evidence → base feature → hole/boss/cut groups → edits → independent measurement → persistence/reopen → required exchange validation. Public calls are permitted only after the stage's live runtime gate passes.

For neutral CAD, `reconstruction_assess` records source identity/hash, source class, units/frame confidence, body/topology statistics, provable primitive fits, missing design semantics and a recommended strategy. `reconstruction_step_to_editable` is deliberately limited to controlled prismatic-bracket and turned/shaft cases and ordinary editable SOLIDWORKS features; it does **not** claim arbitrary imported feature-history recovery.

For STL, `reconstruction_mesh_to_parametric` is approximation-only. It requires watertight/manifold evidence, sufficient primitive-fit confidence, explicit fit residuals and a declared millimeter tolerance. Ambiguous fits are refused instead of reporting invented zero deviation.

## Transaction and recovery
`exact_transaction_mode_unproven` remains active. Existing save/reopen and reconciliation routes do not by themselves establish `native_atomic`, `checkpointed_atomic` or compensating semantics. A `checkpointed_atomic` claim is valid **only after runtime proof** that injected early/middle/late/uncertain failures can restore and independently verify the complete pre-chunk feature/body/dimension state without duplicate mutation.

On uncertain completion, query current document/feature/body state before any retry. Never blindly repeat a non-idempotent feature or reconstruction mutation.

## Chunk budgets
Do not publish universal numeric SolidWorks mutation budgets from source inspection. Keep chunks dependency-bounded and use the provider's measured runtime/output limits after final composition. Reconstruction itself is bounded to controlled benchmark classes, explicit critical dimensions and finite tolerance ledgers.

## Read-after-write
Every accepted mutation must use the provider's own native read-back/rebuild gates. Reconstruction adds a quantitative critical-dimension ledger: expected value, measured value, tolerance and non-negative deviation. STEP/STL editable workflows require successful reopen verification; when an intended parametric edit is requested, the edited value must survive reopen/read-back.

Generic solid validity, screenshots, bounding boxes or inherited ACIS evidence cannot substitute for critical SolidWorks-native measurements. `reconstruction_compare` only compares supplied measurements; it does not manufacture measurement provenance.

## UI behavior
UI redraw or visible SolidWorks state is never correctness evidence. Yield UI control only at verified safe boundaries; user-owned SolidWorks processes must not be commandeered or terminated.

## Artifact lifecycle
Use `document_save`/`document_save_as`, `document_reopen` and `export_document` only after runtime discovery verifies those routes. Release evidence should bind native identity, post-reopen measurements, required neutral export/reopen, units/topology/dimensions and output hashes. `artifact.seal` remains separately unproven until a content-addressed provider route is actually released and discovered.

## Known blockers
- `parallel_integration_not_accepted` — Agent-7 must compose all lane plugins and prove the final public surface.
- `runtime_discovery_required` — source mapping and branch SHA are not live provider proof.
- `tool_missing` / `capability_missing` — a mapped route absent or unavailable at runtime blocks that stage.
- `dependency_unavailable` / `license_unverified` — required SolidWorks/runtime dependencies must fail closed when unknown.
- `topology_public_tool_name_unresolved` — Agent-5 consumes the injected topology contract but does not name another lane's final public tool.
- `reconstruction_port_binding_pending` — STEP/STL mutation routes need Agent-7 topology/mesh + editable-part port binding.
- `exact_transaction_mode_unproven` — no atomicity class is claimed from source code alone.
- `artifact_seal_unproven` — final content-addressed sealing is not yet mapped to a released SolidWorks route.

## Benchmarks
Mechanical acceptance remains MP-01 through MP-06. After final composition, run runtime discovery first, then controlled reconstruction through the public surface. MP-03 must exercise the applicable `reconstruction_step_to_editable` or `reconstruction_mesh_to_parametric` route plus ordinary feature tools. MP-04 must independently measure critical geometry, MP-05 must save/reopen and validate the required neutral export, and MP-06 must inject early/middle/late/uncertain failures.

A missing required route is BLOCKED, not skipped PASS. Source-linked dimensions/tolerances and fixture hashes must be frozen before generation; final evidence must record provider/build/contract identity, tool receipts, native application version, measurement provenance, output hashes and unresolved findings.
