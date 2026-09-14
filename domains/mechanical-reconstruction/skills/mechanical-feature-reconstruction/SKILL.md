# Engineering Skill — Mechanical Feature Reconstruction

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `mechanical-feature-reconstruction` · Version `0.1.0` · Domain `mechanical-reconstruction` · Lifecycle `pilot`.

## Intent

Translate hash-bound mechanical drawing/source evidence into a versioned feature DAG and bounded native part-execution plan while preserving exact-vs-approximate geometry intent, tolerances and independent inspection evidence. The skill does not invent projection conventions, missing dimensions, tolerances, material/process requirements or manufacturing authority.

## Preconditions and inputs

- Design Basis, release target, source identities/hashes and target runtime are explicit.
- Projection/dimension evidence is frozen and critical ambiguity is typed.
- Critical tolerances preserve source/provenance and remain unresolved when absent.
- Feature IDs/dependencies and exactness requirements are explicit.
- `inputs.schema.json` validates the bounded feature package.

## Deterministic checks

`domains.mechanical_reconstruction.guards` provides:

- `evaluate_dimension` — compare independent measurement to nominal under an explicit resolved tolerance;
- `validate_feature_dag` — unique feature identity, dependency closure and deterministic build order;
- `evaluate_exactness` — exact analytic versus sampled representation and approved deviation;
- `evaluate_topology` — final body/topology/treatment evidence.

## Decision boundary

Mechanical/Manufacturing roles may interpret source features and choose an implementation strategy compatible with declared exactness and available public engine semantics. They may not infer missing manufacturing tolerances, fits, material/process properties or substitute sampled geometry where exact analytic geometry is required.

## Workflow and recovery

Use `workflow.yaml`: source/dimension closure → feature DAG/exactness → native feature chunks → independent dimension/topology QA → neutral/native handoff. Native work follows Feature-based Chunk Streaming. On timeout/uncertain completion, reconcile feature/body identity and checkpoint state before retry; dependent features remain blocked.

## Software semantics

Typical semantics include `technical_2d.inspect`, `dimension.ledger`, `feature.plan`, `solid.feature.create`, `solid.boolean`, `model.query`, `checkpoint.create`, `model_3d.measure`, `topology.inspect`, artifact export/reopen/seal and round-trip evidence. Native SolidWorks automation belongs only in CDT-SolidWorks.

## Completeness and QA

Freeze the dimension ledger and required feature/treatment inventory including holes, cuts, chamfers/fillets, datums, tolerances, surface/process notes and required neutral outputs where applicable. Independent QA measures critical dimensions/topology and rejects omitted required features even when a body exists and opens successfully.

## Positive benchmark

A source-frozen part with an acyclic feature DAG, resolved critical tolerances, exactness-compatible representations, verified native chunks, independent measurements/topology, and successful round-trip handoff.

## Negative cases

Critical projection/dimension conflict; unresolved tolerance promoted to PASS; missing/cyclic feature dependency; sampled substitute for exact geometry; approximation deviation above approval; Boolean/feature completion uncertain; omitted required treatment; topology/body-count mismatch; stale round-trip evidence.

## Outputs

Frozen dimension/feature inventory; deterministic DAG/exactness checks; semantic feature chunks; native receipts/checkpoints; independent measurement/topology evidence; round-trip artifact identity; unresolved manufacturing dependencies; exact release verdict.
