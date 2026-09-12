# SolidWorks Operating Guide

> Documentation class: PUBLIC_SOFTWARE_GUIDE
Version: 0.2.0 · Status: current CDT-SolidWorks provider skeleton; native MCP execution not yet available.

## Step-0
Discover SolidWorks installation path/version/build/edition, then discover the **CDT-SolidWorks** provider itself: released provider version/contract, callable MCP surface, COM/add-in host readiness and exact runtime capabilities. An installed SolidWorks application or a reference automation repository is not provider readiness.

## Compatibility
Use `compatible` only when the current CDT-SolidWorks public provider exists, the target application/runtime is within its proven range, and every required capability is observed at runtime. With SolidWorks installed but no callable CDT-SolidWorks provider, classification is `guidance_only`/`configuration_required` or a stronger typed provider blocker; native execution remains BLOCKED. Source/reference examples cannot be promoted to runtime evidence.

## Semantic capability map
The current CDT-SolidWorks snapshot is a provider-native skeleton and explicitly exposes no callable MCP server. Therefore `solid.feature.create`, `solid.boolean`, `model.query`, `checkpoint.create`, `model_3d.measure`, `topology.inspect`, `artifact.native_save`, `artifact.reopen`, `artifact.exchange_export` and `artifact.seal` are all source-mapped `blocked` in CDT_Engineer. Earlier names such as `solidworks_create_basic_part` or `solidworks_export_active` came from a reference automation surface and are not public CDT-SolidWorks capabilities.

## Feature chunks
Mechanical work still plans semantic feature chunks — base feature, hole family, boss/cut group, dimension update group and other dependency-bounded feature-tree units — but **native dispatch stops before mutation** while `provider_not_implemented` is active. The feature DAG, expected postconditions and recovery requirements remain useful planning data; they are not evidence that a native tool exists.

When a CDT-SolidWorks public provider is implemented, each chunk must be remapped only to its released MCP tools and verified against current runtime discovery before the guide can publish a concrete native sequence.

## Transaction and recovery
Known blockers: `provider_not_implemented` and `exact_transaction_mode_unproven`. No transaction class (`native_atomic`, `checkpointed_atomic`, `compensating`) may be claimed from the present skeleton. Recovery acceptance starts only after a public mutation/checkpoint route exists and only after runtime proof that early/middle/late failure plus uncertain completion can be reconciled without duplicate or corrupt feature creation.

A future `checkpointed_atomic` claim is valid only after runtime proof that the saved native document restores the complete pre-chunk state and that the restored feature/body/dimension state is independently verified. Otherwise use only the weaker recovery mode actually demonstrated by the provider.

## Chunk budgets
Do not publish numeric SolidWorks mutation budgets before there is a callable provider and measured runtime. Domain chunks should remain dependency-bounded in planning, but entity/operation/time/payload limits are `unknown` until measured on the actual released runtime.

## Read-after-write
Native read-after-write is currently unavailable through CDT-SolidWorks. Once implemented, each feature chunk must independently inspect feature/dimension/body state and measure critical geometry. Generic model validity, screenshots, bounding boxes or inherited AutoCAD/ACIS evidence cannot substitute for SolidWorks-native measurements.

## UI behavior
No SolidWorks UI/redraw behavior is claimed through CDT-SolidWorks at this stage. Future UI yield must occur only after a verified safe chunk boundary and must never define correctness.

## Artifact lifecycle
Native save/reopen and neutral export are currently BLOCKED because the present CDT-SolidWorks provider has no public document lifecycle tools. Installed SolidWorks capabilities do not authorize direct COM/.NET bypass. Future acceptance requires public native save, disposable reopen, independent measurements, required neutral export/reopen, round-trip units/topology/dimensions and final artifact identity. `artifact.seal` remains separately unproven until a content-addressed provider route exists.

## Known blockers
- `provider_not_implemented` — current CDT-SolidWorks repository has no callable MCP server/capability surface
- `source_snapshot_not_runtime_proof` — application installation and reference automation examples are not public provider evidence
- `exact_transaction_mode_unproven`
- `solid.feature.create` blocked
- `solid.boolean` blocked
- `model.query` / `model_3d.measure` / `topology.inspect` blocked
- native save/reopen/export/seal blocked
- required neutral format remains a Design Basis/runtime decision, not an invented default

## Benchmarks
Native Mechanical benchmarks are **not runnable through CDT-SolidWorks yet**. The acceptance sequence remains: provider Step-0 → bounded native feature chunks → independent measurement → save/reopen → neutral export/reopen → failure/recovery injections. Early, middle, late and uncertain-state cases must all be exercised only after the corresponding public routes exist. Until then, `provider_not_implemented` is a typed BLOCKED result, not a skipped PASS.
