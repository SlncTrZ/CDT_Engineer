# Site Reconstruction — Benchmark Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.2.0 · Primary case: BeachSquare · Status: inherited evidence, production gate pending.

## Evidence baseline
The inspected 2026-09-11 engine benchmark gap report describes a real AutoCAD 2027 2D skeleton with registration and reusable blocks. It also records direct COM setup/XREF workarounds, side-export source inspection, missing existing-condition XREF content and changed output hashes after the recorded verification. These observations justify this domain; they do not establish an accepted SketchUp reconstruction.

Keep raw source, historic reports and hashes in the private evidence index. Do not publish customer DWG/XREF content. Bind a fresh fixture manifest and current hashes before replay.

## Positive cases
1. BS-01: full source inventory, explicit missing dependencies and bounded nested block/layer query.
2. BS-02: independently checked registration, unit conversion and control-point residuals.
3. BS-03: scoped source reconstruction preserving required axes, extents, block instances and organization.
4. BS-04: native SketchUp output, reopen and independently compare scale, alignment, hierarchy and selected geometry.
5. BS-05: complete a stable native save, compute/bind the final **external hash** when provider-native sealing is unavailable, inspect a disposable reopened copy and verify accepted identity/measurements remain current.

## Failure / recovery matrix

Native acceptance exercises failure by stage, not merely a generic error response:

- **early failure:** unresolved XREF/source dependency, wrong/unknown units, provider/runtime preflight failure or invalid rooted output path must block before dependent mutation;
- **middle failure:** force one bounded registration/reconstruction/SketchUp strict-mutation chunk to fail; reconcile actual state and verify rollback/compensation or restart-from-checkpoint before continuing;
- **late failure:** native save, reopen, independent measurement or external hash mismatch marks dependent QA stale and blocks handoff even when earlier chunks committed;
- **uncertain completion / timeout:** reconcile document/model revision, affected identities and persisted file state before retry; blind replay is forbidden and duplicate geometry/instances must be detected or prevented.

Record the exact recovery mode advertised by the selected engine/provider. A recovery result is accepted only after independent state verification; a successful retry alone is insufficient.

## Negative and scale ladder
Missing/cyclic XREF; wrong unit; nested/mirrored transform; truncated query; unapproved inferred elevation; early/middle/late mutation or artifact failure; uncertain timeout; source/output hash drift. Exercise repeated instances at 20, 100 and 1,000 after correctness is established. Record elapsed time, peak resource use, longest UI block, tool count and response size; freeze acceptance budgets before performance runs.

## Acceptance method
Freeze source hash, expected included objects, landmarks, output formats and numeric tolerances before execution. Registration max residual and holdout error must each meet the approved target-unit tolerance. Every required item is accounted for; no unknown critical geometry. Reopen DWG/SketchUp deliverables independently and compare the actual included scope, not screenshots alone.

Require the public MCP path for all necessary operations. Direct backend access may be diagnostic evidence only. Engine capability gaps are blockers with owner/version/status, not domain-specific engine commands.

Result manifest: run ID, fixture hashes, engine/application/build/contract versions, five pack versions, standards, measurements, receipts, limitations, final native/exchange hashes and reviewer verdict. Production remains blocked until BS-01–05 and the early/middle/late/uncertain recovery gates pass on the declared runtime.
