# Production Domain Contract

> Documentation class: PUBLIC_CONTRACT

Version: 0.2.0 · Status: Engineering OS domain baseline · Updated: 2026-09-12

## Purpose inside Engineering OS

A Production Domain is the discipline-specific professional layer inside CDT_Engineer. It does not represent the whole product and it does not execute native CAD/DCC APIs directly. The Engineering OS selects roles, Design Basis, workflow and software route; the domain owns discipline meaning, deterministic engineering logic, standards-derived rules, templates, benchmarks and review gates.

Site and Mechanical are the original golden verticals used to prove this contract. Building Architecture and Building Structural are newer pilot verticals applying the post-closure semantic-first and fail-closed dependency lessons; their presence does not itself constitute native/discipline production acceptance.

## Required five components

| Component | Required content | Acceptance |
| --- | --- | --- |
| `domain.schema.json` | Typed domain/job input, source inventory, units/reference context, intent and output requirements | Validate structure before execution; unresolved evidence is explicitly representable |
| `rule-pack.md` | Versioned deterministic rules, inputs, decisions, severity, provenance and tests | Rule result is pass/fail/unknown/not_applicable with evidence |
| `template-pack.md` | Intake, interpretation/design, execution record, QA and handoff templates | Mandatory fields resolved or explicitly unresolved with owner/block effect |
| `benchmark-pack.md` | Source provenance, expected results, negative cases, environment and thresholds | Repeatable result bound to exact artifacts and versions |
| `review-rubric.md` | Weighted review plus hard gates and reviewer authority | Score cannot override failed/unknown critical hard gates |

Common-looking fields across domains are specification conventions, not proof that a shared runtime SDK should exist. Keep domain-local implementation until Rule of Two.

## Engineering OS relationships

A domain is consumed together with:

- [Design Basis Contract](DESIGN_BASIS_CONTRACT.md) for purpose, source authority, lifecycle/release class and engineering constraints;
- [Engineering Role Contract](ROLE_CONTRACT.md) for responsibility and review boundaries;
- [Engineering Skill Contract](ENGINEERING_SKILL_CONTRACT.md) for bounded professional work units;
- [Workflow Contract](WORKFLOW_CONTRACT.md) for cross-stage/multi-software composition;
- [Standards Governance](STANDARDS_GOVERNANCE.md) for exact source/edition/applicability and derived rules;
- [QA / Checker Model](QA_CHECKER_MODEL.md) for independent verification and release verdicts;
- [Release Scope & Semantic Dependency Policy](RELEASE_SCOPE_POLICY.md) for missing skill/catalog/standard/interface/evidence states and explicit scope reduction;
- [Engineering Asset Catalog Contract](../catalogs/ENGINEERING_ASSET_CATALOG_CONTRACT.md) when reusable technical systems/components are part of the domain.

The domain five-pack remains the minimum reusable discipline package; skills/workflows may refine and compose it without duplicating rule authority.

## Evidence states

Domain inputs and decisions preserve engineering provenance:

```text
observed
specified
derived
inferred
unknown
approved_assumption
```

`unknown` is a legitimate data state. The schema should be able to represent it where reality is incomplete; domain rules decide whether it blocks a dependent stage. Do not force a fabricated number/string merely to satisfy structural validation.

## Semantic-first invariant

A Production Domain must resolve professional meaning before native primitives. The default order is:

```text
intent/source
→ evidence + Design Basis
→ domain semantic entity/system model
→ Engineering Skill / rule / deterministic calculation
→ approved catalog/custom/proxy decision where applicable
→ capability preflight
→ native implementation
→ semantic read-back / domain relationship QA
```

A domain must not silently replace a missing skill, standard, component/library, cross-discipline dependency or calculation route with generic geometry/tool calls while preserving a stronger release claim. Missing professional dependencies follow the Release Scope Policy.

## Domain production workflow

Within the broader Engineering OS workflow, a domain typically follows:

```text
Design Basis / source inventory
→ discipline interpretation or design plan
→ semantic system/dependency resolution
→ standards/rule applicability
→ capability preflight
→ bounded execution
→ stage measurements/checkpoint
→ independent domain QA
→ documentation/handoff
→ artifact seal
```

Failed or critical unknown gates suspend dependent work.

A run records at least: `run_id`, Design Basis revision, source hashes, domain/five-pack/skill/workflow versions, standards selections, assumptions/approvals, engine software/contract/backend/application versions, tool receipts, checkpoints, measurements, final artifact hashes and reviewer verdict. Release-critical evidence such as verified source hashes, final artifact hash binding, reopen/round-trip verification and seal state must be machine-required inputs/gates in the operational profile or Checker path; prose-only stop conditions are not sufficient release enforcement.

## Capability planning

Maintain a per-run matrix:

```text
domain/workflow step
→ required semantic capability
→ selected software/engine
→ public tool + contract/schema version
→ runtime supported mode/limitations
→ evidence
```

Names in plans are semantic requirements, not claims that a public tool already exists. Missing capability produces a typed blocker and a separately scoped engine backlog item. No silent mesh-for-solid, DXF-for-DWG, screenshot-for-measurement, manual-export or private-script substitution when the deliverable contract requires stronger fidelity.

Software is purpose/capability driven, not hard-coded as a mandatory chain. AutoCAD, SketchUp, Blender and SolidWorks retain native strengths; future tools may join without changing domain ownership.

## Human-readable delivery

When a domain output is intended for fabrication, construction, assembly, inspection, approval or other human use, the domain/skill/rubric must define drawing/document communication requirements in addition to model correctness. These may include views, sections/details, datum/reference system, dimensions/tolerances, notes, legends, schedules/BOM, scale/readability and revision identity.

A correct native model does not automatically constitute an acceptable shop/construction drawing set.

## Recovery and artifact identity

Use engine transaction receipts where available. A multi-engine run is not globally atomic: record stage checkpoints and compensating/restart actions. After an uncertain timeout, reconcile actual document state before retrying.

Resume only when source hashes, Design Basis/domain/skill/workflow versions and checkpoint state remain compatible; otherwise invalidate affected downstream work.

Final save → safe close or proven non-mutating boundary → hash → sealed delivery copy → independent reopen/measurement where required. Changed artifact identity makes earlier hash-bound PASS evidence stale. Hash equality and engineering correctness are distinct checks.

## Versions

Each pack has its own SemVer and a domain release pins all five plus relevant skills/workflows/standards mappings. Breaking schema/rule meaning requires a major change; additive compatible behavior is minor; documentation-only corrections are patch. Record migrations and rerun affected benchmarks.

Engine/application versions and standard editions remain independently pinned.

## Production gate

A domain is production-accepted only for a declared scope/release class when all required elements pass:

```text
adequate Design Basis
+ structurally valid domain input
+ semantic object/system model appropriate to the declared scope
+ executable Engineering Skills and deterministic rule/calculation implementation where applicable
+ required catalog/library/cross-discipline dependencies resolved or explicitly valid for the declared reduced scope
+ verified standards/applicability basis where claimed
+ public engine route for required software work
+ measured relationship/topology/interface, completeness and drawing/domain QA as applicable
+ recovery negative tests
+ sealed required native/exchange/document artifacts
+ independent reviewer acceptance
```

Offline schema/document checks are not native application or engineering acceptance. The strongest CDT_Engineer release target is `ready_for_professional_review`; legal/professional issue/signature remains an external accountable authority action.
