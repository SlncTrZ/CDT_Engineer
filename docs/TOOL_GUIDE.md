# CDT_Engineer MCP Tool Guide

> Documentation class: PUBLIC_INTEGRATION
> Provider contract: `cdt-engineer-v1-alpha1` · Updated: 2026-09-17

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

## Boundary with Generic CAD Executors

CDT_Engineer tools must not expose native primitives such as line/circle creation, extrusion, document save, COM/Ruby/bpy/SolidWorks automation or undocumented executor bypasses.

For AutoCAD, the client performs Step-0 using `cdt-autocad.system_status`, `cdt-autocad.system_capabilities` and, where strong-integrity mutation is required, `cdt-autocad.native_integrity_status`. The client then executes through the public AutoCAD contract and returns measured receipts/state to CDT_Engineer checks.

## Error and safety rules

- Invalid structured engineering input returns `validation_error`.
- Missing canonical source material returns `not_found`.
- Provider runtime failures return `provider_unavailable`.
- Network HTTP transport requires bearer authentication.
- Non-loopback HTTP binding additionally requires explicit `CDT_ENGINEER_ALLOW_REMOTE_HTTP=true`.
- No tool grants gateway authority or changes SlncTrZ policy/provider configuration.
- No mutation is blindly retried after an executor reports timeout or unknown completion; reconcile the executor state first.

## Current scope

This alpha provider slice exposes existing deterministic CDT_Engineer logic. It intentionally does **not** add a project database, hidden orchestration backend, LLM routing layer, universal CAD API, or new professional semantics. Additional tools should be promoted only when backed by public contracts and deterministic behavior.
