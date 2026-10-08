# Release Scope & Semantic Dependency Policy

> Documentation class: PUBLIC_POLICY

Version: 0.1.0 · Updated: 2026-09-12 · Status: Engineering OS fail-closed baseline.

## Purpose

This policy prevents CDT_Engineer from silently replacing missing professional knowledge, approved assets, standards, calculations, evidence or software semantics with a weaker approximation while preserving a stronger release claim.

A successful primitive/tool execution never upgrades a missing professional dependency.

## Release classes

Ordered from weakest to strongest:

```text
concept
technical_draft
design_review
fabrication_or_construction_candidate
ready_for_professional_review
```

`issued_by_responsible_professional` remains external authority and is not emitted by CDT_Engineer.

## Dependency states

Every required semantic dependency resolves to one of:

```text
resolved
custom_allowed
proxy_allowed_for_scope
reduced_scope
blocked
```

Typical dependencies include:

- production domain/skill implementation;
- approved standard/applicability decision;
- source/evidence package;
- deterministic calculation input;
- engineering asset/component/catalog family;
- cross-discipline handoff;
- required software/runtime semantic.

Missing runtime dependency state is fail-closed and treated as blocked for the requested release.

## Invariants

1. `resolved` may satisfy the dependency for its declared release range.
2. `custom_allowed` means a bounded custom implementation path is explicitly permitted; its actual engineering correctness still requires the stage's normal rules/checks/QA.
3. `proxy_allowed_for_scope` is only valid through the declared maximum release. A stronger request is **BLOCKED** with a recommended lower target; the original request never silently becomes PASS.
4. `reduced_scope` behaves the same way: the caller must deliberately re-plan/re-run at or below the declared maximum release.
5. `blocked` always blocks dependent release.
6. A capability PASS, native mutation PASS, visual similarity, render quality or generic integrity PASS cannot override a dependency blocker.
7. Proxy/custom/reduced-scope limitations are retained as evidence and must be visible to downstream QA/handoff.

## Agent Profile binding

A stage may declare `dependency_requirements`:

```json
[
  {
    "dependency_id": "catalog.window-family",
    "required_from_release": "technical_draft",
    "proxy_allowed_through": "concept"
  }
]
```

Runtime/job evidence supplies the dependency state separately. Profiles define the requirement; they do not hard-code a successful state.

## Primitive/proxy policy

Primitive geometry or analogous low-level implementation is valid only when one of these is true:

- it is the correct native implementation of an already-resolved semantic object/system;
- the declared release is concept/proxy-compatible;
- a bounded custom implementation is explicitly allowed and verified;
- it is auxiliary/non-deliverable construction geometry.

A proxy record should preserve at least:

```text
proxy=true
reason
intended_semantic_family
missing_dependency
allowed_release_class
replacement_required_before
```

## Executable baseline

`execution.release_scope.assess_dependencies` deterministically assesses dependency states. `execution.stage_runner.run_profile` consumes optional per-stage dependency states and makes those facts part of the stage hard gate. If a stronger requested release cannot be supported, the runner may report a `recommended_release_target`, but the original profile result remains blocked.

This policy is domain-neutral. Domain-specific semantics, catalogs and applicability rules remain owned by their production domain/Engineering Skills.
