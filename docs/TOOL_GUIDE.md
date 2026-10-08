# CDT_Engineer MCP Tool Guide

> Documentation class: PUBLIC_INTEGRATION
> Provider contract: `cdt-engineer-v1-alpha7` · Updated: 2026-10-07 13:45 (Asia/Ho_Chi_Minh)

## Purpose

CDT_Engineer is the **Engineering OS / thinking layer** exposed to AI clients through SlncTrZ-MCP. It owns professional semantics, deterministic engineering checks, workflow/release assessment, QA and traceable evidence. It is not a Generic CAD executor and never substitutes for a native CAD/DCC engine.

The intended client architecture is:

```text
AI model / Agent
  -> SlncTrZ-MCP gateway
     -> cdt-engineer.*   engineering reasoning/checks/state evidence
     -> cdt-autocad.*    Generic CAD execution
     -> cdt-sketchup.*   Generic 3D execution
     -> cdt-solidworks.* Generic parametric CAD execution
```

The client/Agent orchestrates the loop. CDT_Engineer does not secretly call executor providers and executor providers do not absorb engineering-domain rules.

## Operating loop

```text
Design Basis / source facts
-> profile + workflow semantics
-> Step-0 executor capability discovery
-> profile/stage assessment
-> external CDT-* native execution
-> read-after-write measurements/evidence
-> CDT_Engineer completeness/QA/release checks
-> artifact identity + handoff
```

A successful CAD mutation is execution evidence, not an engineering PASS.

## Public tools

### Identity and contract

- `help` — current provider guide, contract fingerprint and capability summary.
- `system_status` — provider runtime identity and available public source packages.
- `system_capabilities` — deterministic Engineering OS capabilities and explicit native-execution refusal.

### Execution environment assessment

- `execution_environment_assess(inventory, requirements, runtime_observation, assessment_at, max_age_seconds=300)` — evaluate caller-collected Step-0 snapshots with exact identity/version/capability and freshness gates. It returns planning facts for `profile_assess`; it never performs discovery or remediation. See [Execution Environment Contract](EXECUTION_ENVIRONMENT_CONTRACT.md) and [assessment context schema](schemas/execution-environment-assessment.schema.json) for strict fields, bounds and unknown-state rules.

### Public source packages

- `profile_get(domain_id)` — retrieve a canonical public Agent Profile.
- `engine_map_get(software_id)` — retrieve a public software engine map. Engine maps are source expectations, never current runtime proof.

### Workflow and release assessment

- `profile_assess(...)` — deterministic stage/release assessment over explicit runtime facts, checks and dependency states.
- `dependency_assess(...)` — apply release-scope dependency policy without silent downgrade.
- `catalog_resolve(...)` — prove semantic asset/native registry resolution from explicit evidence.

### QA and completeness

- `completeness_check(items)` — required-item implementation/verification coverage.
- `layer_ledger_check(frozen, final)` — detect dropped/occluded/background requirements.
- `human_deliverable_check(...)` — release-aware drawing/document communication gates.
- `qa_check(findings, current_artifact_sha256)` — independent finding aggregation with stale-evidence enforcement.

### Artifact evidence

- `artifact_manifest(...)` — create hash-bound artifact evidence metadata; it does not save or modify files.
- `evidence_stale_check(...)` — detect evidence invalidated by artifact mutation/replacement.

### Independent observation and change impact

- `observation_assess(...)` — assess read-back evidence against the expected semantic/native identity, exact observed revision and deterministic state fingerprint. `unavailable`/`unsupported` remains unknown; stale revision, identity substitution, unexpected absence or state mismatch blocks.
- `impact_assess(nodes, changed_ids, evidence?)` — compute exact transitive dependents from explicit revisioned dependency nodes and verify that evidence binds its subject plus every transitive dependency at the current revision. Cycles, dangling dependencies and malformed bindings fail closed.

### Bounded cross-discipline coordination

- `architecture_structural_interface_assess(...)` — assess the implemented Building Architecture↔Building Structural handoff lane against independently supplied current source revisions, project units/reference frame, explicit interface ownership/disposition, and conflict ownership/evidence. A self-declared `verified` handoff becomes blocked when its upstream revision is stale, units/frame disagree, or a conflict remains open/unowned.

This tool is intentionally pair-specific. It does not establish a universal cross-domain SDK; additional pairs require another real implemented consumer before common extraction under the Rule-of-Two policy.

### Final machine release gate

- `release_bundle_check(...)` — fail closed unless frozen verified source hashes still match current source hashes and the final bundle also binds CDT_Engineer source/provider/contract/wheel identity, exact current executor/runtime identity, current artifact hashes, reopen + seal state, SHA-256-bound independent Checker evidence and SHA-256-bound PASS evidence for every declared recovery-negative class. Missing current observations, source/artifact hash drift, runtime identity drift or prose/boolean-only recovery claims block release.

The tool validates caller-supplied current observations; it does not discover or mutate executor/runtime state itself.

The optional `evidence_records` argument accepts a content-addressed mapping
from lowercase SHA-256 to the complete immutable record. Omitting records keeps
release blocked; legacy boolean/hash-only bundles do not gain a weaker PASS.
The independently supplied `current_engineer_identity` contains the current domain,
workflow, Engineer source/provider/contract and wheel bindings; the bundle must
match all six. `current_design_basis_revision` must match the frozen basis. Omitting
these current-context arguments or changing a binding blocks rather than trusts
the bundle's own claim of freshness.
Each required Checker, artifact reopen, artifact seal and recovery reference must
resolve, its canonical UTF-8 JSON hash must match, and its kind/run/Design Basis/
version/source/runtime/artifact bindings must match current observations. Records
include `result`, non-empty `method` and `measurements`. Checker records additionally
bind `reviewer_id` and `reviewer_role`; the reviewer ID must differ from the bundle's
`producer_id`. Recovery records bind the exact `case_id` and `recovery_class`.

The bundle and records explicitly declare `verification_scope` as
`native_application` or `offline_contract_test`. These scopes cannot be mixed.
An offline gate PASS is returned with its offline scope and is never application
acceptance. Record hash verification proves content and binding integrity, not the
truth of measurements or cryptographic reviewer authentication; the caller must
collect trusted independent observations. Synthetic fixtures belong only to tests.

These tools do not execute CAD or mutate project artifacts. They evaluate evidence supplied by the Agent after independent executor read-back and after known source/model/artifact changes.

## Boundary with Generic CAD Executors

CDT_Engineer tools must not expose native primitives such as line/circle creation, extrusion, document save, COM/Ruby/bpy/SolidWorks automation or undocumented executor bypasses.

For AutoCAD, the client performs Step-0 using `cdt-autocad.system_status`, `cdt-autocad.system_capabilities` and, where strong-integrity mutation is required, `cdt-autocad.native_integrity_status`. The client then executes through the public AutoCAD contract and returns measured receipts/state to CDT_Engineer checks.

The same Step-0 preflight applies to the other Generic CAD Executors: discover live capabilities through the executor's own `system_status`/`system_capabilities` surface first, then execute through its pinned public contract. `engine_map_get(software_id)` currently serves `autocad`, `sketchup` and `solidworks` source maps; those maps are source expectations, never current runtime proof.

## Error and safety rules

- Invalid structured engineering input returns `validation_error`.
- Missing canonical source material returns `not_found`.
- Provider runtime failures return `provider_unavailable`.
- Network HTTP transport requires bearer authentication.
- Non-loopback HTTP binding additionally requires explicit `CDT_ENGINEER_ALLOW_REMOTE_HTTP=true`.
- Engineering assessments do not grant gateway/native authority. Host selection, power, prerequisites and gateway/provider deployment belong to the client Agent and independently authorized owner/external tooling.
- No mutation is blindly retried after an executor reports timeout or unknown completion; reconcile the executor state first.
- Producer receipts are not independent observation. Use read-back evidence with explicit identity/revision/method and invalidate affected downstream evidence after dependency changes.

## Current scope

This alpha provider slice exposes existing deterministic CDT_Engineer logic. It intentionally does **not** add a project database, hidden orchestration backend, LLM routing layer, universal CAD API, or new professional semantics. Additional tools should be promoted only when backed by public contracts and deterministic behavior.

Blender is defined in the L2 contract model (`docs/CONTRACTS.md` §6) but is **deferred from this alpha slice**: no `software/blender/` Operating Guide or engine map ships yet, and `engine_map_get` does not serve a `blender` key. A Blender guide/map should be added only with pinned public contract evidence, not as an unverified placeholder.

## Offline PlanSpec planning checks

The Python review/compile helpers enforce the
[Floor-plan Source Completeness Contract](../domains/building-architecture/drawing-completeness.md).
Architectural callers supply a frozen source inventory at every release target; image
sources record context/detail/confirmation review passes. Empty/incomplete plans and
unverified source requirements refuse before CAD execution. Fixtures require a hosted,
explicit rectangular envelope; calibration outputs canonical millimetres.
Compiled chunks carry source/inventory SHA-256 bindings for downstream verification.

Review also blocks plan-view column/opening and fixture/fixture overlaps before
compilation. Opening coordinates are mapped from the host wall's local frame;
rotated rectangular fixtures and circular columns use a narrow geometry check.
Touching boundaries alone are not an overlap. Non-center wall baselines with
unresolved opening clash frames refuse rather than assume a physical side. This
is bounded 2D coordination, not a 3D clash or building-code certificate.

Chunks additionally bind `plan_sha256`, `planning_policy_sha256` and `chunk_sha256`.
`payload_bytes` is the complete canonical JSON UTF-8 size. Defaults are 256 semantic
features and 65,536 bytes per chunk; configurable safety bounds are 1..4096 features
and 1024..1,048,576 bytes. A single feature exceeding the byte budget refuses the
whole compilation without partial chunks. Architectural groups are partitioned by
feature-center spatial cells (default 10 metres expressed in plan units), preserving
whole semantic features and carrying conservative `spatial_bounds`. Callers may set
positive `spatial_cell_size`. Features crossing cells remain whole; cell assignment
does not prove disjoint mutation scopes or authorize concurrent execution.

`assess_provenance_release(..., expected_chunks=compiled.chunks)` checks exact
bindings, complete/unique chunk receipt coverage and verified predecessor ordering.
Omitting `expected_chunks` retains only the narrower provenance assessment; it is
not an execution-plan coverage certificate. The recovery helper treats failed and
malformed receipts as potentially dirty: independent observation must prove a
commit or absence, or compensation must be verified before retry. The default
idempotency key includes the expected semantic state fingerprint.

These helpers are not additional advertised MCP tools. The public completeness/QA tools
still consume independent final artifact evidence; planning approval is not artifact PASS.

## Alpha7 boundary and compatibility

The provider exposes 19 tools: the 18 existing engineering tools and
`execution_environment_assess`. All are read-only assessments or source reads.
Application/native execution remains explicit in Generic CAD executor providers.

Alpha6 names `execution_list`, `execution_status`, `execution_ensure`,
`execution_stop` and `execution_operation_status` are removed without aliases.
The controller configuration/client/executable are no longer product components.
See [Lifecycle Ownership](EXECUTION_LIFECYCLE_CONTRACT.md) for client migration.

Environment assessment returns `verification_scope=caller_supplied_observations`
and `native_execution_authorized=false`. Provider ready does not imply native
application/bridge readiness. Missing, stale, conflicting or unavailable inputs must
not become native planning PASS. Snapshot hashes bind input identity and freshness
policy; they do not authenticate the observation source.

Consumers recollect observations after external remediation and verify the refreshed
provider contract/hash/catalog before using alpha7. Source/package upgrades do not
deploy providers, synchronize the gateway or certify native application acceptance.
