# Execution Environment Contract

> Documentation class: PUBLIC_CONTRACT

Version: 0.2.0 · Updated: 2026-10-07 13:45 (Asia/Ho_Chi_Minh) · Status: Engineering OS Step-0 baseline.

## Purpose

Before CDT_Engineer selects an engineering application, gives version-specific operating guidance, or performs native execution, the Agent must discover the actual execution environment. Installed software, application version/path, and provider readiness are observed facts, not assumptions.

This is **Step 0**. It precedes Design Basis execution planning and software capability mapping; it does not replace engineering intent or Design Basis.

Machine-readable inventory instances conform to [`schemas/execution-environment.schema.json`](schemas/execution-environment.schema.json).

## Two independent inventories

The Agent keeps these facts separate:

1. **Installed Software Inventory** — whether the application exists on the target host, its executable/install path, version/build/edition, OS context and observation method/time.
2. **Execution Capability Inventory** — whether the corresponding public MCP/provider is configured and ready, its provider/contract version, and the capabilities discovered from the current runtime.

`software installed` does not imply `Agent can execute it`. Provider readiness does not prove a compatible application/version exists.

## Mandatory Step-0 flow

```text
identify target host
→ observe OS/architecture
→ discover required application
→ resolve executable/install path + version/build/edition
→ discover provider/runtime contract + capabilities
→ compare with Software Operating Guide support range
→ classify compatibility
→ continue, guide-only, request installation/configuration, or BLOCK
```

Do not infer installation from a remembered path, infer version from a folder name alone when a stronger source exists, or reuse stale runtime capabilities as current proof.

## Required application states

- `installed`: executable/install path and application version are observed.
- `not_installed`: discovery was performed and the application was not found; version/path fields remain null.
- `unknown`: discovery could not establish the state; never silently treat it as installed or absent.

For native execution, `unknown` is fail-closed.

## Provider states

- `ready`: the provider is reachable and its version, contract version and at least one discovered capability are observed. This does not assert native application/bridge readiness.
- `not_ready`: the provider exists but its public service is not ready.
- `not_configured`: no usable provider configuration exists for the target software.
- `unknown`: provider state could not be established.

A machine may validly report `solidworks installed` + `cdt-solidworks ready` + `native bridge unavailable`. Provider readiness and native dependency availability are independent. Missing native readiness blocks execution even while the provider remains callable.

## Version compatibility

Every Software Operating Guide declares its supported application/version range and pinned provider contract. Step 0 compares observed environment facts against that guide before execution.

Compatibility result is one of:

- `compatible` — observed application/provider versions are within the guide's proven range and required runtime capabilities are present;
- `guidance_only` — the application is known well enough for human operating guidance, but native provider execution is unavailable or unproven;
- `installation_required` — required software is explicitly not installed;
- `configuration_required` — software exists but provider/plugin/runtime configuration is missing;
- `version_mismatch` — installed version is outside the guide's proven range or provider contract is incompatible;
- `unknown` — evidence is insufficient; native execution blocks.

Do not silently downgrade a version mismatch into `compatible`.

## Freshness and cache policy

Inventory may be cached to avoid rescanning the host for every prompt. Each observation carries `observed_at` and `discovery_method`.

Before mutation-heavy/native work, revalidate drift-prone facts at minimum:

- target application version/running attachment where relevant;
- provider version and contract version;
- runtime capability surface;
- required plugin/add-in readiness where the Software Operating Guide declares one;
- required writable workspace/output path when execution depends on it.

A cached inventory is context, not runtime proof.

## Safety and user interaction

If required software is not installed, the Agent reports the typed blocker and handles installation/prerequisite remediation through independently authorized external skills or operator action. Vendor installation and host provisioning are outside CDT_Engineer.

If software is installed but execution integration is unavailable, distinguish human guidance from native automation. If version or environment is unknown, ask for or perform permitted discovery instead of guessing.

## Relationship to software guides and workflows

Software Operating Guides consume Step-0 inventory and define application-specific discovery methods, supported versions, required plugins/providers, capability expectations and compatibility rules. Workflows consume the resulting compatibility classification before capability preflight and Feature-based Chunk planning.

Historical runs pin the inventory observation used for execution so later QA can distinguish environment drift from engineering logic changes.

## Read-only assessment surface

`execution_environment_assess(inventory, requirements, runtime_observation,
assessment_at, max_age_seconds=300)` evaluates caller-collected observations.
It never chooses a host, probes the OS/network, invokes a controller or performs
environmental/native remediation. Only the public schemas are read from the source
or installed package. The existing inventory schema `0.1.0` is unchanged.

The separate [assessment context schema](schemas/execution-environment-assessment.schema.json)
defines these inputs:

| Input | Required meaning |
| --- | --- |
| `inventory` | Existing inventory schema; installation/provider facts for the Agent-selected execution host |
| `requirements` | Exact `host_id`, `software_id`, `provider_id`, `application_version`, `provider_version`, `contract_version`, non-empty `required_capabilities`, and `expected_runtime_identity` |
| `runtime_observation` | Snapshot or null; host/software/provider and application/provider/contract versions, `observed_at`, `discovery_method`, `application_state`, `bridge_state`, `runtime_identity`, `observed_capabilities` |
| `assessment_at` | Explicit timezone-aware assessment time supplied by the caller; no hidden wall-clock input |
| `max_age_seconds` | Integer 1..3600; default 300; stale snapshots block and future observations remain unknown |

`application_state` is `running`, `stopped` or `unknown`.
`bridge_state` is `ready`, `unavailable` or `unknown`.
Runtime identity contains `runtime_generation`, `session_id`,
`application_instance_id` (process creation identity, not bare PID) and
`bridge_version`. Expected identity must be supplied from the caller's current
execution context independently of the snapshot. A null expected or observed
identity cannot yield PASS. No credentials or executable actions belong in the payload.

Exact identity/version mismatch, stale evidence, declared unavailable prerequisites
and missing required capabilities block. Missing observations remain unknown rather
than proving software/provider absence. Duplicate application/provider identities
refuse; the assessment must not select whichever duplicate looks ready.
Payloads are bounded to 1 MiB, 64 applications/providers each and 256 capabilities
per provider/runtime/requirement set. Malformed input produces a sanitized
`validation_error` without echoing its values.

Output includes `result`, `compatibility`, `reason_codes`, separate
`provider_state`, `application_installation_state` and `native_state`,
runtime identity, observation ages and canonical `snapshot_sha256`.
This Fingerprinting binds the supplied inputs/time/policy, not their truth or authenticity.

Feed returned `capabilities` and `capabilities_by_software` into the existing
`profile_assess` inputs. The local fact
`execution_environment.compatible_or_typed_blocker` carries the actual assessment
result; discovering a blocker does not count as environment PASS. Per-software facts
are projected only for requested capabilities, and all remain blocked/unknown when
their environment gate is blocked/unknown.

PASS is scoped to `caller_supplied_observations`. The Agent must collect trusted
observations and choose exact requirements from the software guide/contract.
Assessment does not authenticate that collection, approve native writes, validate
document/writer guards, select another backend, or replace independent QA.
`native_execution_authorized` is always false.

## Environmental ownership and compatibility

The [Lifecycle Ownership Contract](EXECUTION_LIFECYCLE_CONTRACT.md) retires the five
alpha6 lifecycle tools in alpha7. Agent/external skills own environmental remediation;
Generic Engines retain their separately declared native runtime/recovery behavior.
After remediation or generation drift, recollect observations before reassessing.
