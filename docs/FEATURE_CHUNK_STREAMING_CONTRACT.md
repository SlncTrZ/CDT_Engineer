# Feature-based Chunk Streaming Contract

> Documentation class: PUBLIC_CONTRACT

Version: 0.1.0 · Updated: 2026-09-12 · Status: Engineering OS execution invariant.

## 1. Purpose

CDT_Engineer forbids two dangerous execution extremes for interactive engineering software:

1. **Monolithic project mutation** — sending the whole project as one large operation is difficult to inspect, recover, debug and isolate when one semantic part fails.
2. **Primitive command streaming** — sending every LINE/ARC/face/feature as a separate Agent round-trip is slow, token-expensive, fragile and increases application/runtime failure exposure.

The default execution strategy is **Feature-based Chunk Streaming**: the Agent decomposes a design into bounded semantic units, executes one committed unit at a time, verifies it, yields UI when appropriate, then advances according to dependencies.

This is both an engineering-safety rule and a presentation-quality rule. Safety always takes precedence over visual effect.

## 2. Semantic chunk

A chunk is the smallest **professionally meaningful and independently recoverable** unit of work for the active domain/software context.

Examples:

- architecture: one wall system, room core, stair, facade bay, grid/column group, annotation group;
- civil: one road segment, curb system, drainage reach, culvert, intersection, profile/section group;
- landscape: one plaza zone, kiosk group, path network branch, planting/hardscape region;
- mechanical: one base feature, hole pattern, shaft step group, pocket, bracket feature group, drawing-view package;
- electrical/electronics: one feeder/circuit group, schematic function block, PCB functional region where the target tool supports bounded mutation;
- visualization: one material family, lighting rig, camera set, scene/asset group.

A chunk is not defined by a fixed entity count. Domain logic decides which operations belong together because they form one engineering feature, dependency unit or reviewable scope.

## 3. Chunk planning before mutation

Before execution, the Agent creates a chunk DAG or ordered plan. Each chunk records at least:

```json
{
  "batch_session_id": "road_project_01",
  "chunk_id": "chunk_curb_d1",
  "semantic_type": "road_curb_segment",
  "scope": "station_0+000_to_0+120_left",
  "depends_on": ["chunk_alignment_d1"],
  "expected_outputs": ["curb_geometry", "curb_dimensions"],
  "required_capabilities": ["geometry.create", "geometry.measure"],
  "transaction_policy": "native_atomic",
  "verification_policy": "read_after_write",
  "ui_yield": true
}
```

Concrete MCP payloads are software-specific and belong in the corresponding software operating guide/engine map. CDT_Engineer owns the semantic envelope and safety rules, not native request syntax.

## 4. Chunk size rule

A valid chunk must satisfy all of these:

- one coherent engineering purpose;
- bounded mutation size/time/entity count appropriate to the engine;
- independently identifiable outputs;
- deterministic or measurable postconditions;
- explicit dependencies;
- independently recoverable or compensatable failure scope;
- small enough that failure diagnosis is local;
- large enough to avoid primitive-per-command Agent round-trips.

Anti-patterns:

```text
BAD: entire building / entire road project / entire machine in one mutation
BAD: one LINE or ARC per Agent turn when they form one semantic feature
GOOD: one wall/room/road segment/hole-pattern/feature group per chunk
```

Software guides may define hard budgets such as maximum entities, operations, estimated execution time, payload size or complexity for one chunk. The Agent must subdivide further when a budget would be exceeded.

## 5. Transaction honesty

Every software map declares the strongest truthful chunk isolation mode it supports:

```text
native_atomic          # engine/application supports real transaction/undo-group rollback
checkpointed_atomic    # safe snapshot/checkpoint can restore the complete pre-chunk state
compensating           # no true atomic rollback; explicit compensating actions are verified
nonrecoverable         # unacceptable for production mutation unless explicitly approved/reduced scope
```

CDT_Engineer must never label a chunk `native_atomic` merely because an MCP call returned successfully.

For `checkpointed_atomic` or `compensating`, the workflow records the recovery mechanism and validates the recovered state before continuing.

`nonrecoverable` mutation is a hard blocker for release classes that require rollback-safe execution unless a domain-specific approved exception exists.

## 6. Commit barrier and flow control

Chunk execution is sequential at dependency boundaries:

```text
plan chunk
→ preflight capabilities + preconditions
→ establish transaction/checkpoint
→ execute chunk
→ reconcile actual state
→ verify postconditions
→ COMMIT chunk
→ emit receipt/checkpoint
→ optional UI yield
→ release dependent chunks
```

A dependent chunk must not be sent until every required predecessor is in a verified committed state.

Independent chunks may later be scheduled concurrently only when the engine/document transaction model proves that concurrency is safe. Parallelism is not assumed by default.

## 7. Failure behavior

If Chunk X fails or enters uncertain state:

1. stop all dependent chunks;
2. query/reconcile the actual document/model state;
3. rollback, restore checkpoint or execute compensating recovery according to the declared transaction mode;
4. verify that recovery actually restored the intended state;
5. record the error with `chunk_id`, operation/receipt, expected state, observed state and recovery evidence;
6. choose `retry`, `replan`, `skip_with_approved_scope_reduction` or `block`;
7. never blindly replay an uncertain mutation.

Chunks already committed and independent of the failed scope remain valid if their evidence/artifact identity is unaffected.

## 8. Read-after-write verification

A successful mutation response is necessary but insufficient. Each chunk defines measurable postconditions such as:

- expected object/entity/feature IDs or bounded counts;
- dimensions/coordinates/levels;
- topology/feature-tree relationships;
- layer/tag/material/property assignments;
- dependency/constraint state;
- document/model revision/checkpoint identity.

The Agent verifies these through query/measurement capabilities before marking the chunk committed.

## 9. Visual streaming / demo effect

`ui_yield: true` requests that the engine/application expose the committed chunk visually before the next chunk begins when safely supported.

Desired experience:

```text
feature appears
→ application redraws / cursor or viewport visibly progresses when available
→ short yield at a safe committed boundary
→ next feature appears
```

Rules:

- visual yield happens **after** a safe chunk boundary, never mid-transaction merely for animation;
- redraw/cursor motion is not correctness evidence;
- visual pacing must not add unbounded delays or force primitive command streaming;
- headless/batch environments may ignore visual hints while preserving the same semantic chunk plan;
- demo mode and production mode share engineering chunk semantics; only pacing/presentation hints may differ.

The system must never make geometry less safe or less deterministic just to create a better demo.

## 10. Chunk receipt

Every committed chunk produces a traceable receipt conceptually containing:

```json
{
  "batch_session_id": "road_project_01",
  "chunk_id": "chunk_curb_d1",
  "status": "committed",
  "transaction_mode": "native_atomic",
  "engine_receipt_id": "...",
  "created_or_modified_ids": ["..."],
  "verification": {
    "status": "pass",
    "evidence_ids": ["..."]
  },
  "checkpoint_id": "...",
  "artifact_revision": "..."
}
```

Exact fields/tool syntax are adapted per engine. The invariant is semantic traceability from design intent → chunk → native operations → verification → committed state.

## 11. Dependency and ordering logic

Production Domain/Engineering Skills own semantic decomposition and ordering. Typical rules include:

- references/grids/datums before dependent geometry;
- primary alignment before curb/drainage/road furniture;
- base feature before dependent cuts/holes/fillets;
- architectural base before downstream 3D/detailing where the workflow depends on it;
- model geometry before annotations that reference that geometry;
- source/import/setup before transformations that assume its coordinate frame.

The Agent must not order chunks solely for visual spectacle when engineering dependencies require a different sequence.

## 12. Software operating guide requirement

Every interactive engineering software guide must document:

- native chunk/transaction primitive or checkpoint strategy;
- rollback/undo semantics and known limitations;
- recommended semantic chunk types for that application;
- chunk budgets;
- public MCP tools used for begin/execute/query/commit/rollback where available;
- uncertain timeout/recovery behavior;
- redraw/UI-yield capability and limitations;
- engine-specific payload examples;
- negative cases proving rollback/reconciliation.

A provider capability gap is recorded explicitly; CDT_Engineer must not bypass it with undocumented native automation and still claim production acceptance.

## 13. Production acceptance invariant

A mutation-heavy workflow is not production-ready until its benchmark proves:

1. semantic chunk plan is deterministic/reviewable for the benchmark scope;
2. chunk dependencies prevent invalid downstream execution;
3. per-chunk verification detects wrong/partial mutation;
4. a forced chunk failure is isolated and recovered according to the declared transaction mode;
5. uncertain-state retry does not duplicate or corrupt geometry;
6. committed earlier chunks remain traceable;
7. UI streaming, when enabled, does not change the final engineering result;
8. the final sealed artifact independently passes domain QA.
