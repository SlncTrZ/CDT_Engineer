# Execution Lifecycle Contract

> Documentation class: PUBLIC_CONTRACT
> Contract: 0.1.0 · Status: bounded alpha6 implementation; broader shutdown/restart contract remains a target.

## Scope and ownership

This contract extends Step-0 execution-environment discovery with explicit runtime lifecycle requests. CDT_Engineer may provide the Agent-facing lifecycle entrypoint while a separately authorized execution controller performs host operations. It must not import native engine code or become a hidden CAD mutation proxy.

| Component | Responsibility |
| --- | --- |
| Gateway | Authentication, routing, accepted tool catalog and hot activation |
| CDT_Engineer | Engineering intent, environment assessment and explicit lifecycle requests |
| Execution controller | Approved engine mapping, lifecycle operation coordination and privileged gateway sync |
| Host supervisor | Launch/attach/drain/stop, process ownership and native readiness |
| Generic Engine | Application-specific execution, document guards and recovery |

The lifecycle entrypoint and controller must remain reachable when a requested engine is stopped. Engine registration and controller authority are owner-managed prerequisites; starting an application does not grant authority or register an unknown provider.

## Implemented alpha6 surface

CDT_Engineer 0.1.0a6 exposes 23 tools: 18 engineering tools and the five lifecycle tools below. Exact callable schemas are defined in [MCP Tool Guide](TOOL_GUIDE.md). The configured external controller supports only the approved AutoCAD engine; an unconfigured controller returns a typed blocker.

execution_ensure(engine, operation_id) requests only application_read_only readiness. It delegates fixed host operations to an external controller, persists sanitized operations, converges concurrent ensures, validates the provider contract and activates the approved read surface through the existing gateway control plane. It accepts no caller-selected host, path, task, executable or required write scope.

execution_stop(engine, operation_id, scope) is callable but fails closed with NATIVE_STOP_NOT_CERTIFIED; it performs no shutdown. Generation/ownership-aware drain and shutdown, unsaved-document handling and destructive restart recovery are not implemented by this pilot.

## Agent-facing tools

| Bare name | Purpose |
| --- | --- |
| `execution_list` | List configured engines and permitted lifecycle actions |
| `execution_status` | Report current provider/application/native/document readiness |
| `execution_ensure` | Converge an approved engine to the requested ready state without duplicate launch |
| `execution_stop` | Drain and stop an explicitly selected scope |
| `execution_operation_status` | Observe a long lifecycle operation without keeping one MCP request open |

The broader target contract below is not the alpha6 callable schema. A future ensure request identifies `engine`, configured host, `operation_id`, required capability scope and explicit attach/launch policy. No caller-supplied executable, shell command, task name, arbitrary environment, SSH destination or credential is accepted.

A stop request identifies `engine`, `operation_id`, scope (`provider`, `application`, or `both`) and expected supervisor generation. Save/discard behavior must be explicitly authorized; default behavior refuses to close documents with unsaved changes.

## Ensure flow

```text
authorize engine/action and resolve configured target
→ observe installed software and compatible interactive session
→ acquire engine lifecycle lock and reconcile any previous operation
→ reuse an owned ready runtime or launch through the host supervisor
→ establish provider transport and native application/plugin readiness
→ verify provider contract/version/hash and approved tool surface
→ sync the already-registered gateway provider through an authorized controller
→ verify activation and the intended engine state after activation
→ refresh client tools/list and report READY for the requested capability scope
```

The current gateway sync accepts the discovered tool set. A restricted deployment must validate that set against its approved manifest before sync, or use the gateway's existing explicit tool-set acceptance mechanism. Contract drift blocks activation until reviewed; documentation or a gateway-only profile is not an authorization boundary.

Disabled or missing registrations require an explicit owner-authorized enable/register operation. Sync must not be described as implicitly enabling or creating providers.

Gateway activation may create a new adapter/process generation. For stdio, gateway ownership of the provider process must be preserved: the host supervisor launches the native application and coordinates a single provider launcher instead of starting a competing persistent stdio server. Any discovery/probe process must not launch a second GUI or mutate a document. Final readiness must be checked against the activated generation.

Sync failure is a partial outcome: the application may be running while the gateway is unavailable. Return that truth, keep dependent execution blocked, and reconcile before retrying. Do not claim the application was rolled back merely because gateway configuration rolled back.

## Readiness and identity

Report these dimensions separately:

- software installed and its executable/version/build/edition;
- host reachability and usable user/session/integrity level;
- provider configured, enabled, running and MCP-discoverable;
- application running and its ownership;
- required native plugin/add-in/bridge connected;
- document identity, dirty state and required writer lease;
- gateway activation state and active catalog fingerprint.

Port-open, HTTP health, MCP discovery and catalog presence each prove different facts. None alone proves native readiness or engineering correctness. A missing document may be valid for an application-level ensure; document-dependent mutation still blocks until its document preconditions hold.

Bind readiness to host, provider build/contract hash, application version, process creation identity, session and supervisor generation. A PID alone is not sufficient ownership or Fingerprinting. Never substitute a different backend or application version silently.

## Idempotence, latency and restart behavior

- Same `operation_id` with the same request returns/reconciles the same operation; a different payload under that ID is refused.
- Concurrent ensure calls converge on one approved engine instance; bound admission and waiting.
- Return an operation reference promptly for slow application launch; expose bounded status calls and measured queue/startup/native/sync/total Latency.
- Persist the minimum sanitized lifecycle operation/ownership record needed for restart reconciliation. Gateway in-memory tasks are not a durable lifecycle ledger.
- After controller/supervisor restart, verify process creation identity, session and native state before adopting an instance. Unknown prior mutation or ownership blocks automatic shutdown/replay.
- Lifecycle idempotence never implies that CAD mutations are idempotent. A lost mutation response requires engine-specific reconciliation.

For Scalability, lifecycle coordination is per engine/instance; document mutation authority is separately enforced by the native engine or its authorized execution layer. Gateway per-provider call serialization is not a multi-call document writer lease.

## Windows interactive execution

Use a preconfigured Task Scheduler task or equivalent existing interactive worker under the approved user. SSH is a control channel to that worker, not proof that a process launched directly in an SSH session can access the user's CAD desktop.

Require a usable logged-on interactive session for GUI-dependent engines. Missing or incompatible sessions return `USER_SESSION_REQUIRED` or a typed blocker. A locked/disconnected session is not assumed usable without provider-specific evidence. Use ordinary user privileges by default; compatible elevation must be explicitly configured where required.

## Stop and safety

1. Block new lifecycle transitions and native work for the target instance.
2. Drain owned in-flight work within a bounded deadline.
3. Reconcile uncertain native operations; uncertainty refuses destructive shutdown.
4. Inspect all documents affected by closing the application and their dirty states.
5. Default to `UNSAVED_DOCUMENT` when saving/discarding has not been authorized.
6. Close only supervisor-owned application instances with verified identity.
7. Stop/detach the provider transport as appropriate and update gateway enablement/catalog through the authorized control plane.
8. Verify the resulting process, document and catalog states separately.

Do not kill all processes by image name, auto-dismiss arbitrary modal dialogs, discard unsaved work, force-save to an inferred path, or replay an uncertain CAD mutation. Stopping an application and hiding its tools are separate actions. Do not invoke discover-and-sync on a stopped runtime and imply it will withdraw tools.

## Acceptance criteria

| Scenario | Required result |
| --- | --- |
| Engine cold start | One owned runtime; correct native identity; successful activation and fresh client discovery |
| Concurrent ensure | One launch; deterministic operation results; bounded queue |
| No interactive session | Typed blocker; no invisible GUI launch or duplicate process |
| Contract/tool drift | Refusal before broadening the accepted catalog |
| Sync/activation failure | Truthful partial state; dependent calls blocked; rollback/reconciliation recorded |
| SSH or MCP response loss | No blind replay; ownership and actual native state reconciled |
| Unsaved document / uncertain mutation | Default stop refused; data preserved |
| Controller/PC restart | Durable operation record reconciled against actual process identity |
| Stop owned provider only | User-owned CAD session and documents preserved |
| Multiple Agents / document change | Writer ownership and stale-state guards enforced at the native boundary |

Acceptance binds exact source/build/artifact hashes and real supported host/application/client behavior. The implemented pilot does not certify the broader stop, restart or native-write contract.
