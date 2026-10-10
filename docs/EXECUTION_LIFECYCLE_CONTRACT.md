# Execution Lifecycle Ownership

> Documentation class: PUBLIC_CONTRACT
> Contract: 0.2.0 · Updated: 2026-10-07 13:45 (Asia/Ho_Chi_Minh) · Status: alpha7 boundary.

## Ownership

CDT_Engineer owns engineering planning and read-only assessment of execution observations.
The client Agent owns execution-host selection, prerequisite checks and environmental
remediation using independently authorized external skills or operator action.

| Component | Responsibility |
| --- | --- |
| CDT_Engineer | Design Basis, domain/workflow decisions, capability assessment and QA/release evidence |
| Client Agent / external skills | Host selection, power state, prerequisite discovery and environmental remediation |
| Generic Engine provider | Public execution contract, truthful dependency state, native validation and recovery |
| Runtime / native bridge | Application/session attachment, typed dispatch and native identity/state |
| Gateway / owner | Authentication, policy, accepted catalog and provider registration/deployment |

An application being reachable does not grant gateway or document mutation authority.
CDT_Engineer never starts/stops applications, SSHs into hosts, installs vendor software,
or registers/enables/synchronizes providers. Engine/native runtime semantics remain
in their independently assigned repositories.

## Alpha7 compatibility

Provider `0.1.1`, contract `cdt-engineer-v1-alpha7`, exposes 19 tools:
18 existing engineering tools with unchanged callable schemas plus
`execution_environment_assess`.

The following alpha6 tools are removed from the catalog, with no forwarding aliases:

| Retired alpha6 tool | Alpha7 integration |
| --- | --- |
| `execution_list` | Agent reads its configured execution providers and their public contracts |
| `execution_status` | Agent gathers executor status/capabilities and supplies an assessment snapshot |
| `execution_ensure` | Agent resolves prerequisites outside CDT_Engineer; no replacement Engineer action |
| `execution_stop` | Separately authorized engine/runtime lifecycle, subject to ownership/dirty-state guards |
| `execution_operation_status` | Observe the external operation through its owning system |

`CDT_ENGINEER_EXECUTION_CONTROLLER` is no longer consumed; the Settings controller
field and product controller/client are removed. A legacy environment value cannot
reactivate the retired surface. Calls to retired names fail as unknown tools.

Inventory schema `0.1.0` remains unchanged. The assessment context has its own
[JSON Schema](schemas/execution-environment-assessment.schema.json) and
[Execution Environment Contract](EXECUTION_ENVIRONMENT_CONTRACT.md).

Consumers must verify provider version, contract version/hash and the refreshed
accepted catalog before using alpha7. Mixed alpha6/alpha7 assumptions are unsupported.
The gateway's owner-managed deployment/catalog is not changed by a source edit or
wheel build. Historical alpha6 operations must be reconciled in their owning external
system; alpha7 neither resumes nor replays them.

## Planning and native acceptance

An assessment PASS binds supplied snapshots, explicit requirements and assessment
time. It does not prove independent native observations, authenticated reviewer
identity, native application acceptance, document readiness or a writer lease.

An unavailable native dependency must not be confused with a stopped Engineer provider.
After external remediation, the Agent recollects current observations and reassesses;
cached PASS evidence cannot be carried across runtime generation or version changes.
