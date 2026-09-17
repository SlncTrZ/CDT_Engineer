# AutoCAD Operating Guide

> Documentation class: PUBLIC_SOFTWARE_GUIDE
Version: 0.4.0 · Source contract: `0.4.0rc2 / autocad-generic-v1-rc2 / 86 tools` · Runtime proof required per run.

## Step-0
Call `system_status` and `system_capabilities`; when strong-integrity native mutation is required also call `native_integrity_status`. Confirm AutoCAD build, provider/contract identity, backend, allowed roots and the exact runtime-supported capability path. For native strong-integrity writes, capture the active `document_pid` and predecessor fingerprint from the state actually used for planning; RC2 requires caller-supplied `document_pid` + `expected_parent_fp` and refuses wrong/stale planning state before mutation. The pinned source contract is integration evidence, not proof that the current runtime is ready.

## Compatibility
Use `compatible` only from observed runtime facts. Unobserved source expectations are `guidance_only/unknown`; absent software is `installation_required`; provider/path setup gaps are `configuration_required`; incompatible builds are `version_mismatch`.

## Semantic capability map
`engine-map.yaml` binds CDT_Engineer semantics to current public tools. Prefer `feature_execute` for production Feature-based Chunks Streaming where its accepted action families fit. Broader drafting/document/XREF/ACIS tools remain useful but are not all promoted to the same G3 integrity semantics.

## Feature chunks
One engineering feature maps to one bounded provider feature where possible:
```text
system/native preflight
→ feature_execute(document_pid, expected_parent_fp, feature_id, sequence, correlation_id, actions)
→ verify receipt + object/query/measurement state
→ release next dependent feature
```
Use raw `batch_*` only when their lower-level primitive is intentionally required. Compatibility mutations must retain their advertised weaker recovery class.

## Transaction and recovery
For accepted G3/`feature_execute` families, the provider owns one immutable predecessor checkpoint across bounded native micro-chunks and verifies exact feature-local recovery. RC2 additionally binds caller planning state through `document_pid` + `expected_parent_fp`; do not refresh the predecessor merely to make a stale mutation succeed. Do not wrap that path in a second long-lived client transaction. For broad COM/legacy paths, use only their advertised transaction/recovery semantics; timeout/unknown completion requires reconciliation and forbids blind replay. A known deferred RC2 operational debt can leave a stale COM application proxy after AutoCAD restart; after `RPC server is unavailable`, recover a clean Session-1 supervisor/worker, re-run read-only preflight, and only then resume new mutation.

## Chunk budgets
Current accepted native lane: micro-chunk max 32, semantic capacity 12,288, logical feature/batch cap 10,000, with live graduation through 10,000 entities. These numbers apply only to the accepted lane and current certified runtime; runtime capability metadata remains authoritative.

## Read-after-write
A committed receipt is execution evidence, not engineering PASS. Query affected PIDs/objects and independently measure required extents, dimensions, registration, solids or other domain invariants.

## UI behavior
The provider may recommend ~300 ms presentation pacing between completed features. UI yield never changes commit/recovery boundaries and screenshots never replace semantic measurements.

## Artifact lifecycle
Use `document_save`/`document_save_as` for persisted checkpoints. `artifact_seal` saves a clean active DWG, creates a content-addressed accepted copy and SHA-256 manifest/provenance. For human-readable drawing delivery, `artifact.drawing_export` maps to `document_export_pdf` plus the public layout/viewport routes and requires independent package/readability verification. `artifact.exchange_export` is separate: SAT is the verified native ACIS 3D exchange path; STEP/STL are not implied. CDT_Engineer must still mark prior QA stale if an accepted artifact changes after review.

## Known blockers
- `source_snapshot_not_runtime_proof`
- `broad_com_surface_not_full_g3`
- `acis_topology_not_authoritative`
- `post_seal_staleness_external`
- `stale_com_proxy_after_autocad_restart`

## Benchmarks
Positive: live Step-0, Feature-based Chunk commit/recovery, XREF/dependency inspection, bounded read-back, artifact seal, and SAT export where required. Negative: unresolved XREF, stale parent fingerprint, timeout uncertainty, rollback failure, unsupported topology, seal drift or unsupported exchange format.
