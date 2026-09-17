# CDT_Engineer — Engineering OS Architecture

> Documentation class: PUBLIC_ARCHITECTURE
> Version: 1.1.0 · Updated: 2026-09-12
> Scope: stable public product architecture for the Engineering Operating System / Virtual Engineering Office

## 1. Product identity

CDT_Engineer is the engineering operating layer used by AI Agents to perform accountable multi-discipline engineering work. It converts user intent and source evidence into an explicit professional process: establish purpose and Design Basis, select roles/domains/skills, apply verified rules and standards, resolve professional dependencies, choose suitable software capabilities, execute through external Generic Engines, independently verify the result, and hand over traceable artifacts.

CDT_Engineer is **not** a CAD/DCC engine and is not a prompt-only skill collection. It owns professional engineering semantics, deterministic domain logic, standards applicability, engineering workflows, software operating guidance, QA/QC and handoff evidence. Native application mechanics remain in engine/provider repositories.

CDT_Engineer is also a **first-class MCP provider surface** behind SlncTrZ-MCP. The provider exposes engineering semantics, deterministic checks and evidence operations as `cdt-engineer.*` after gateway namespacing. It does not proxy or hide native CAD calls. The client Agent orchestrates CDT_Engineer and independent CDT-* Generic Engine providers side-by-side; SlncTrZ-MCP remains the gateway/authority/routing layer.

## 2. Canonical operating model

```text
User intent / source package
→ Step 0: execution-environment discovery
→ Design Basis + purpose + deliverables + jurisdiction
→ discipline/role selection
→ domain semantic model
→ Engineering Skills + rules + deterministic calculations
→ standards/applicability + professional dependency resolution
→ Engineering Asset Catalog / bounded custom path where applicable
→ workflow + semantic chunk plan
→ public engine capability preflight
→ native execution through CDT-* engines
→ read-after-write evidence + checkpoints + recovery
→ independent domain and cross-discipline QA
→ drawing/document/artifact QA
→ traceable handoff
→ ready_for_professional_review
```

A successful tool call, model save, Boolean, export or render is not an engineering PASS.

## 3. Core product layers

### 3.1 Engineering OS Core

The Core owns discipline-neutral contracts and invariants:

- execution-environment discovery and runtime evidence;
- Design Basis envelope;
- evidence/provenance states;
- roles and review authority;
- Engineering Skill contract;
- workflow/stage contract;
- Agent Operational Profile;
- release-scope and semantic dependency policy;
- Feature-based Chunk Streaming;
- checkpoint/recovery and stale-evidence semantics;
- artifact identity and QA aggregation;
- shared deterministic primitives only after Rule-of-Two evidence.

The Core must remain small enough that discipline meaning stays in domains rather than becoming a universal engineering god-layer.

### 3.2 Engineering Roles

Roles define professional responsibility, required inputs, permitted decisions, checks and handoff boundaries. A single Agent may sequentially act in several roles, or a future multi-agent runtime may assign roles separately, but the responsibility and evidence boundaries remain explicit.

Representative role families include Chief/Lead Engineer, Architect/Spatial Designer, Civil/Infrastructure Engineer, Landscape Engineer, Structural Engineer, Mechanical Design Engineer, Manufacturing Engineer, Electrical Engineer, Electronics Engineer, Embedded Engineer, CAD/BIM Technician, Visualization Engineer, Documentation Engineer and Checker/QA Engineer.

Roles do not grant native tool authority; software authority remains capability-driven.

### 3.3 Production Domains

Domains own discipline semantics, calculations, rules, templates, benchmarks and review rubrics. Every production domain follows the public [Production Domain Contract](PRODUCTION_DOMAIN_CONTRACT.md) and at minimum provides:

1. `domain.schema.json`;
2. `rule-pack.md`;
3. `template-pack.md`;
4. `benchmark-pack.md`;
5. `review-rubric.md`.

A domain may also contain Agent Profiles, Engineering Skills, detail/requirement matrices and deterministic guard implementations. Public domain packages define only the scope they can support with evidence; package existence alone is not native production acceptance.

### 3.4 Engineering Skills

An Engineering Skill is a versioned professional work unit. It binds intent, prerequisites, evidence states, decision boundary, deterministic checks/calculations, required standards, dependency/catalog states, workflow, software semantics, completeness inventory, QA/negative cases and delivery requirements.

Skills are defined by the [Engineering Skill Contract](ENGINEERING_SKILL_CONTRACT.md). They must not silently replace missing professional knowledge with native primitives.

### 3.5 Engineering Asset Catalogs

Reusable technical systems/components have semantic identity independent of native file format. The [Engineering Asset Catalog Contract](../catalogs/ENGINEERING_ASSET_CATALOG_CONTRACT.md) defines provenance, applicability, parameters, interfaces, substitution policy, QA and native mapping evidence.

The selection path is:

```text
semantic requirement
→ domain/skill applicability decision
→ catalog or bounded custom path
→ native mapping/runtime resolution
→ native placement/creation
→ independent read-back verification
```

A semantic catalog record does not prove that a native asset is installed. Exact runtime resolution remains evidence-driven.

### 3.6 Software Operating Guides

CDT_Engineer owns professional guidance for using engineering software; native automation remains external. Public guides live under `software/` and conform to the [Software Operating Guide Contract](SOFTWARE_OPERATING_GUIDE_CONTRACT.md).

A guide may specify feature-tree/drafting/model-organization practice, semantic capabilities, transaction/recovery expectations, read-after-write verification, known limitations and benchmark requirements. It must not embed COM, Ruby, `bpy`, SolidWorks automation backends or private execution bypasses.

### 3.7 Workflows

Workflows compose roles, domains, skills, standards, catalogs and software according to deliverable purpose. They are selected by engineering intent and release class, not by file extension or software preference. The public [Workflow Contract](WORKFLOW_CONTRACT.md) defines the stage model.

## 4. Semantic-first invariant

Professional intent must be resolved before native primitives. The default order is:

```text
intent/source
→ evidence + Design Basis
→ domain semantic entity/system
→ skill/rule/calculation
→ standards/dependency/catalog decision
→ native implementation
→ semantic read-back
→ domain/cross-discipline QA
```

The prohibited shortcut is:

```text
intent/source
→ convenient primitive/tool call
→ visually plausible artifact
→ stronger engineering release claim
```

Missing skills, standards, catalogs, analysis routes, cross-discipline handoffs or critical evidence follow the [Release Scope & Semantic Dependency Policy](RELEASE_SCOPE_POLICY.md): block, explicitly reduce scope, or use an approved proxy only inside its declared release boundary.

## 5. Design Basis first

Every serious engineering job establishes a [Design Basis](DESIGN_BASIS_CONTRACT.md) before production execution. It records purpose, lifecycle/release class, jurisdiction, selected disciplines, authoritative sources, units/reference systems, relevant loads/materials/process/tolerances, required outputs, target consumers, assumptions, unresolved dependencies and reviewer requirements.

Critical missing Design Basis fields may permit bounded concept work but block unsupported compliance, construction, fabrication or professional-review claims.

## 6. Evidence and provenance

Engineering facts preserve provenance states:

```text
observed
specified
derived
inferred
unknown
approved_assumption
```

Unknowns are valid data. They become blockers when a dependent release requires the missing fact. CDT_Engineer must not invent hidden dimensions, loads, materials, standards applicability, XREF content, tolerances, topology or construction/manufacturing facts to keep execution moving.

## 7. Standards architecture

Standards are versioned evidence, not generic names. Exact identity/edition, authoritative source metadata, applicability, derived rules, conflicts and reviewer decisions are governed by [Standards Governance](STANDARDS_GOVERNANCE.md).

Unknown edition/applicability blocks a compliance PASS. Protected normative text remains controlled according to licensing; public rules contain permitted metadata and original derived logic.

## 8. Generic Engine boundary

Native execution remains in independent engines such as CDT-AutoCAD, CDT-SketchUp, CDT-Blender and CDT-SolidWorks. Those engines own document lifecycle, native query/mutation, geometry/topology, transactions/undo, import/export, native save/open and capability declaration.

CDT_Engineer owns why a native operation is needed and whether its result is professionally acceptable. It consumes pinned public contracts and current runtime capability discovery. Missing public capabilities must not be bypassed through undocumented COM/Ruby/bpy/script paths while claiming production acceptance.

The engine contract layering is described in [Contract Model](CONTRACTS.md).

## 9. Capability planning

A job maps:

```text
domain/workflow step
→ required semantic capability
→ selected engine/application
→ pinned public contract/map
→ current runtime support/limitations
→ evidence
```

Source maps and remembered versions are not runtime proof. Step-0 discovery is required by the [Execution Environment Contract](EXECUTION_ENVIRONMENT_CONTRACT.md).

## 10. Feature-based Chunk Streaming

Mutation-heavy work follows the [Feature-based Chunk Streaming Contract](FEATURE_CHUNK_STREAMING_CONTRACT.md). Work is decomposed into bounded semantic features/systems with dependencies and measurable postconditions.

Neither extreme is the default:

- one opaque whole-project mutation;
- one primitive CAD operation per Agent turn.

A dependent chunk is released only after predecessor state is verified. On timeout/uncertain mutation, actual state is reconciled before retry, compensation, checkpoint restart or blocking. Atomicity is never fabricated.

## 11. QA architecture

The public [QA / Checker Model](QA_CHECKER_MODEL.md) separates at least:

1. source/intent correctness;
2. engine integrity;
3. domain engineering correctness;
4. requirement/feature/detail completeness;
5. cross-discipline/interface correctness;
6. standards/applicability;
7. constructability/manufacturability where applicable;
8. drawing/document usability;
9. artifact identity/reopen/staleness;
10. handoff completeness.

Generic engine integrity or visual similarity cannot override a failed professional hard gate. Independent Checker evidence must not merely repeat producer receipts.

## 12. Cross-discipline ownership

Each discipline owns its professional decisions. Interfaces are explicit evidence objects rather than implicit geometry coincidence. Examples include Architecture↔Structural, Structural↔MEP, Mechanical↔Manufacturing, Electrical↔Controls, Electronics↔Embedded and Civil↔Drainage/Utilities.

One discipline may detect a clash or missing dependency but must not silently make another discipline's unresolved professional decision.

## 13. Human-readable deliverables

Machine-correct models do not automatically satisfy human-use requirements. Where the deliverable is intended for design review, fabrication, construction, assembly or inspection, the workflow verifies the required views, sections, details, datum/reference system, dimensions/tolerances, notes, legends, schedules/BOM, revision identity, scale/readability and release limitations.

Human-deliverable acceptance is release-aware and explicit. Every deliverable family active for the requested release must be accounted for by at least one hard-gate requirement; score-only polish cannot satisfy an active family. `not_applicable` is a reviewed disposition with reason, evidence and exact source/artifact revisions, not silent omission. Missing, unverified or stale hard-gate evidence blocks regardless of presentation score, and reviewer role/independence are part of the evidence. `professional_practice.human_deliverables` is the discipline-neutral executable baseline for these invariants; domain skills still own the concrete technical content required in each family.

The M13 Professional Engineering Practice Standard remains development work until calibrated multi-domain benchmark evidence and independent review support public promotion.

## 14. Release and professional boundary

Release strength is evidence-dependent. A stronger requested release never silently degrades into a weaker PASS. CDT_Engineer may recommend a lower release target, but the original stronger request remains blocked until deliberately replanned.

The strongest internal target is `ready_for_professional_review`. CDT_Engineer does not claim legal certification, licensed-professional signature or jurisdictional issue authority.

## 15. Public documentation and development history

Stable product architecture, contracts, policies, domain/skill packages, catalogs, software guides and sanitized benchmark definitions are public product documentation. Roadmaps, ADR history, audits, closure reports, handoffs, provider backlogs, raw evidence and external reference snapshots are development material governed by the [Documentation Policy](DOCUMENTATION_POLICY.md).

Public product semantics must stand alone and must not depend on internal development records.

## 16. Rule of Two

Do not create a speculative shared Domain SDK. Runtime/code extraction requires at least two implemented consumers with equivalent observable behavior, positive/negative tests and migration/version evidence. Shared contracts may exist before shared runtime code.

## 17. Architecture invariants

- CDT_Engineer is the Engineering OS / Virtual Engineering Office; engines remain generic executors.
- Purpose and Design Basis precede software choice.
- Semantic-first professional reasoning precedes native primitives.
- Roles, skills, standards, catalogs and review authority are explicit and versioned.
- Unknown critical evidence remains unknown and fails closed when required by release.
- Deterministic invariants are implemented/tested rather than delegated only to free-form model judgment.
- Professional dependencies cannot be hidden by tool/runtime PASS.
- Mutation-heavy execution uses semantic feature chunks and truthful recovery semantics.
- Cross-discipline workflows preserve ownership and interface evidence.
- Completeness is first-class QA: omitted required content is a failure even when produced content is valid.
- A visually convincing result is not automatically constructible, manufacturable, compliant or complete.
- Final artifacts require independent QA, identity binding and stale-evidence detection.
- Public architecture describes current product invariants; roadmap/audit/history never override it.
