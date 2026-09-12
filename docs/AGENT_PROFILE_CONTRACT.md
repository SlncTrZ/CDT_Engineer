# Agent Operational Profile Contract

> Documentation class: PUBLIC_CONTRACT

Version: 1.1.0 · Updated: 2026-09-12 · Status: Engineering OS execution-profile baseline.

## Purpose

An Agent Operational Profile converts a production domain into an executable professional sequence without embedding native CAD/DCC implementation. It binds domain stages to roles, rule IDs, semantic capabilities, software candidates, stop conditions, checkpoints, recovery actions and QA gates.

Machine-readable profiles conform to [`schemas/agent-profile.schema.json`](schemas/agent-profile.schema.json).

## Required invariants

Every profile:

- starts with `environment_preflight` and consumes the [Execution Environment Contract](EXECUTION_ENVIRONMENT_CONTRACT.md);
- targets a declared release class and exact profile version;
- assigns at least one accountable role to every stage;
- links applicable domain rule IDs rather than reproducing rule logic in the profile;
- asks for semantic capabilities, never private/native implementation details;
- identifies software candidates explicitly when software execution is needed;
- declares stage dependencies and uses Feature-based Chunk Streaming for mutation-heavy work;
- declares professional/semantic `dependency_requirements` when a stage depends on a domain skill, catalog/library, standard/applicability decision, cross-discipline handoff, analysis route or other non-tool evidence;
- provides a checkpoint/evidence identity for each stage;
- declares non-empty stop conditions, recovery actions and QA gates;
- stops dependent stages when predecessor evidence is failed, unknown or stale.

## Capability resolution

A profile capability can be either:

1. an Engineering OS/domain-local semantic such as environment classification, dimension-ledger reasoning or feature-DAG validation; or
2. a software semantic that must resolve through one of the stage's software `engine-map.yaml` files.

A software semantic is not considered available merely because it appears in source code or an engine map. Engine maps describe expected public capability and known blockers. Step-0 runtime discovery must prove the selected application's/provider's current version and capability surface.

If no selected software map covers a required software semantic, profile validation fails before execution planning. If the map marks the semantic `blocked` or `unproven`, execution yields a typed blocker unless current runtime evidence legitimately upgrades that state under the applicable Software Operating Guide.

## Semantic dependency and release-scope resolution

Software capability availability is only one dependency class. A stage may also require professional dependencies such as an implemented Engineering Skill, approved Engineering Asset Catalog family, standards/applicability decision, cross-discipline interface or analysis/evidence route.

Profiles declare those requirements with `dependency_requirements` and the job/runtime supplies one explicit state from the [Release Scope & Semantic Dependency Policy](RELEASE_SCOPE_POLICY.md):

```text
resolved
custom_allowed
proxy_allowed_for_scope
reduced_scope
blocked
```

Missing dependency state fails closed. A proxy or reduced-scope dependency may recommend a weaker release target, but the requested stronger release remains blocked until the workflow is explicitly replanned/rerun at that weaker target. Native capability PASS, visual similarity or generic integrity PASS cannot override this gate.

## Stage lifecycle

```text
preconditions
→ Step-0/runtime capability resolution
→ semantic/professional dependency resolution
→ stage plan
→ optional semantic feature chunks
→ execute
→ read-after-write / independent measurement
→ checkpoint
→ QA gate
→ release dependents
```

On timeout or uncertain mutation, do not release dependents. Reconcile actual state and choose only from the profile's declared recovery actions.

### Runtime stage applicability

A stage is `applicable` by default. Whole-stage omission is allowed only through an explicit runtime applicability disposition recorded separately from the stage Checker result. The executable baseline accepts a `stage_applicability` record keyed by `stage_id`; `not_applicable` requires a non-empty reason and yields stage release `not_applicable`, which is dependency-neutral.

A Checker result of `not_applicable` is **not** a stage-applicability decision. For an applicable stage, a required capability reported `not_applicable` is a typed blocker, and a stage Checker result of `not_applicable` also blocks because the required verification was not performed. If every stage is explicitly not applicable, the profile result is `not_applicable`, never `pass`.

## Profile vs workflow vs software map

- **Workflow Contract:** defines reusable professional flow semantics across jobs/disciplines.
- **Agent Profile:** instantiates the domain's operational stages, rules, roles and blockers.
- **Software engine map:** resolves software semantics to expected public engine surfaces and records source-level support/blockers.
- **Software Operating Guide:** explains version-specific professional operation, transaction/recovery behavior and measured runtime acceptance.

None of these grants tool authority or replaces runtime discovery.

## Initial profiles

- [`domains/site-reconstruction/agent-profile.json`](../domains/site-reconstruction/agent-profile.json)
- [`domains/mechanical-reconstruction/agent-profile.json`](../domains/mechanical-reconstruction/agent-profile.json)
- [`domains/building-architecture/agent-profile.json`](../domains/building-architecture/agent-profile.json)
- [`domains/building-structural/agent-profile.json`](../domains/building-structural/agent-profile.json)

These are operational baselines/pilots, not production PASS evidence for the mapped engines or discipline release classes.

## Software capability resolution

Runtime capability facts are bound to the selected `software_id`; equal semantic names from different engines must not be flattened into one global truth value. For a stage with multiple `software_candidates`, candidates are alternatives only for semantics that the stage genuinely allows any one candidate to satisfy. A BLOCKED capability on one alternative must not poison a runtime-proven PASS on another alternative. Conversely, requirements that apply to distinct artifacts/engines must be represented in separate dependency stages or explicit local evidence gates rather than hidden inside a multi-engine union.

Source-derived engine maps remain fail-closed: `expected` is not runtime PASS, even if source metadata contains a historical/runtime-looking flag. Step-0/runtime evidence supplies the actual per-software capability facts consumed by the Stage Runner. `blocked` and `unproven` are typed blockers at source-map projection; only current runtime evidence accepted under the Software Operating Guide may upgrade them. Global/domain-local facts must not override a semantic that is explicitly software-bound for the selected stage. A multi-candidate stage selects one candidate that satisfies the stage's software-bound requirements as a set; the runner must not synthesize PASS by mixing different engines per semantic.

The executable runner keeps Engineering-OS/domain-local semantic names in the explicit `execution.stage_runner.LOCAL_CAPABILITIES` registry. Any required semantic on a stage with `software_candidates` that is not in this registry is treated as software-bound and resolves through one candidate, including when the runtime fact is missing. New local semantics must therefore be registered deliberately, and local names must not collide with engine-map semantics. This prevents an accidental global PASS fact from bypassing a missing or blocked software capability.

A predecessor released as `not_applicable` is dependency-neutral; `fail`, `unknown` or `blocked` predecessors stop dependent release. When an actually released stage fails and later stages become blocked by that failure, the profile-level result remains `fail` rather than being masked by the derived downstream block.
