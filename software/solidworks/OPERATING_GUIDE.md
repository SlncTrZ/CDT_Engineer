# SolidWorks Operating Guide

> Documentation class: PUBLIC_SOFTWARE_GUIDE
Version: 0.3.0 · Source contract: provider 0.1.0, contract 0.1.0, 149 public tools / 125 capability descriptors · Measured SOLIDWORKS 2024 SP0.1 revision 32.0.1 · Accepted source revision ddaef7b60611f8f094f614914e37f9adccc298f3.

## Step-0

Call the public provider discovery surface before any native work: system_status, system_capabilities and application_probe, then connect only through the provider when execution is required. Require the observed SOLIDWORKS version/build, provider/contract identity, required capability descriptors, path-policy roots and exact public tools needed by the selected workflow.

The accepted source revision and native-acceptance history below are not current-run runtime proof. A cached machine inventory, an installed SOLIDWORKS application or this guide cannot promote a required capability to PASS.

## Compatibility

The measured baseline is SOLIDWORKS 2024 SP0.1 / revision 32.0.1 on Windows with CDT-SolidWorks provider 0.1.0 contract 0.1.0. Other SOLIDWORKS releases remain unclaimed until separately accepted.

CDT_Engineer may treat a source-mapped capability as expected, but execution remains fail-closed until the current runtime reports the corresponding dependency/capability as available. Direct COM/.NET automation from CDT_Engineer is never a substitute for a missing public provider capability.

## Semantic capability map

The current provider exposes a callable public MCP surface. Mechanical workflows map to these released routes:

- solid.feature.create: part_create_rect_extrude, part_add_rect_extrude, part_profile_extrude, part_cut_extrude, part_simple_hole, part_revolve, part_fillet, part_chamfer.
- solid.boolean: body_combine, part_combine_all_bodies.
- model.query: document_info, document_list_features, document_list_bodies, part_feature_get, part_feature_parameters_get, body_inspect.
- checkpoint.create: persisted document_save / document_reopen boundaries plus document_reconcile and feature-specific reconcile routes for uncertain completion.
- model_3d.measure: evaluation_measure, evaluation_bounding_box, evaluation_geometry_sanity.
- topology.inspect: topology_query, topology_resolve, topology_inspect.
- artifact.native_save: document_save, document_save_as.
- artifact.reopen: document_open, document_reopen, document_info.
- artifact.exchange_export: export_document plus import_document for a required round-trip check.
- artifact.seal: still blocked because this provider snapshot has no public content-addressed artifact_seal / artifact_verify primitive.

Provider reconstruction tools such as reconstruction_step_to_editable, reconstruction_mesh_to_parametric, reconstruction_assess and reconstruction_compare are bounded engine capabilities. They do not replace CDT_Engineer's source interpretation, feature-plan, tolerance, standards, manufacturability or independent QA responsibilities.

## Feature chunks

Use Feature-based Chunk Streaming. A typical mechanical sequence is: Step-0 runtime discovery → freeze source-linked feature DAG and required dimensions → persisted baseline save → execute one semantic feature/Boolean chunk → query feature/body state → independent measurement/topology read-back → save verified checkpoint → next dependent chunk.

Do not send one opaque whole-part mutation and do not drive primitive geometry one entity per Agent round-trip when those operations form one semantic feature. Bind each chunk to explicit prerequisites, expected feature/body state and measurable postconditions.

## Transaction and recovery

The provider has explicit uncertain-state quarantine/reconciliation, but CDT_Engineer does not claim native transaction atomicity.

- document_save + document_reopen provide a persisted recovery boundary.
- document_reconcile verifies uncertain document mutation state before dependent writes continue.
- part_cut_reconcile, part_simple_hole_reconcile and part_revolve_reconcile verify feature-specific uncertain completion against expected native postconditions.
- Never blindly retry a non-idempotent mutation after timeout or uncertain completion.
- Reconcile the current feature/body/document state first; if the intended postcondition is absent, recover from the last verified persisted baseline or replan according to the declared chunk recovery mode.

exact_transaction_mode_unproven remains a limitation: checkpointed_atomic or whole-chunk rollback may be claimed only after runtime proof that the complete pre-chunk state can be restored and independently verified. Save/reopen/reconcile evidence by itself is a weaker persisted-checkpoint recovery model.

## Chunk budgets

Use current system_capabilities and tool schemas as the source of runtime bounds. Do not invent larger feature, topology, payload or timeout budgets merely to make a benchmark pass. If the current provider rejects an operation as unsupported or over budget, reduce scope/replan or block.

## Read-after-write

Producer receipts are not independent QA evidence. After each accepted mutation, use a separate read path/context as applicable:

- document_list_features, part_feature_get, part_feature_parameters_get for feature identity/parameters;
- document_list_bodies, body_inspect for body state;
- evaluation_measure, evaluation_bounding_box, evaluation_geometry_sanity for deterministic geometry checks;
- topology_query / topology_inspect for bounded analytic topology facts.

The Checker must compare those observations with the frozen Design Basis and approved tolerances. Generic body validity, a screenshot or a successful save cannot establish mechanical correctness.

## UI behavior

SOLIDWORKS visibility/redraw is operational only. Native acceptance uses provider-owned sessions where appropriate and correctness is determined from semantic/native read-back rather than viewport appearance. UI yield may occur only at a verified chunk boundary.

## Artifact lifecycle

Use document_save / document_save_as for native persistence, then reopen the exact artifact and repeat required independent checks. Use export_document only for a format actually supported by the observed runtime; if the workflow requires neutral round-trip, load through import_document or another identified reader and compare units, critical dimensions and required topology.

The provider does not currently expose content-addressed artifact sealing. An externally computed SHA-256 may bind evidence to exact bytes, but it does not satisfy the software semantic artifact.seal. Therefore a profile whose hard gate requires provider-backed artifact.seal remains BLOCKED until that capability or an explicitly revised release policy is accepted.

## Known blockers

- source_snapshot_not_runtime_proof — accepted source/native history does not replace current Step-0 discovery.
- artifact_seal_missing — no public provider-native content-addressed seal/verify route exists at this snapshot.
- exact_transaction_mode_unproven — persisted save/reopen plus explicit reconcile are accepted recovery primitives, but no whole-chunk native rollback/atomicity guarantee is claimed.
- Required neutral exchange format is a Design Basis/runtime decision; do not invent STEP/Parasolid/STL as a universal default.
- Domain-level exactness, tolerances, manufacturability, drawing completeness and professional approval remain CDT_Engineer/reviewer gates even when the provider reports clean native state.

## Benchmarks

CDT-SolidWorks source revision ddaef7b has measured SOLIDWORKS 2024 SP0.1 native evidence for the public provider, including bounded part/assembly/drawing/deployment paths plus STEP and STL reconstruction. Provider-level acceptance establishes the engine routes; it does not by itself establish a CDT_Engineer professional release.

Mechanical SW-07 closed-loop acceptance must therefore exercise the public route from an Engineer-owned frozen feature plan through native mutation, independent measurement/topology read-back and persisted reopen evidence, while preserving producer/Checker separation. Recovery tests must cover early, middle, late and uncertain states without direct COM bypass. Final release remains separately gated by artifact_seal_missing and the domain review rubric.
