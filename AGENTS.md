# AGENTS.md — CDT_Engineer Engineering OS

> Documentation class: PUBLIC_ENTRYPOINT

## Product identity

CDT_Engineer is the Engineering Operating System / Virtual Engineering Office for Agents. It owns professional engineering interpretation, roles, Engineering Skills, deterministic domain calculations, standards/rules, cross-discipline workflows, software operating guidance, QA/QC and engineering handoff evidence.

It is not a native CAD/DCC engine and not a prompt-only skill collection.

Before substantial work, read `README.md`, `docs/README.md`, `docs/ARCHITECTURE.md`, `docs/DOCUMENTATION_POLICY.md`, `docs/EXECUTION_ENVIRONMENT_CONTRACT.md`, `docs/AGENT_PROFILE_CONTRACT.md`, `docs/DESIGN_BASIS_CONTRACT.md`, `docs/ENGINEERING_SKILL_CONTRACT.md`, `docs/ROLE_CONTRACT.md`, `docs/WORKFLOW_CONTRACT.md`, `docs/FEATURE_CHUNK_STREAMING_CONTRACT.md`, `docs/SOFTWARE_OPERATING_GUIDE_CONTRACT.md`, `docs/QA_CHECKER_MODEL.md`, `docs/PRODUCTION_DOMAIN_CONTRACT.md`, `docs/RELEASE_SCOPE_POLICY.md`, `catalogs/ENGINEERING_ASSET_CATALOG_CONTRACT.md` and `docs/STANDARDS_GOVERNANCE.md` as relevant to the task. `docs/ARCHITECTURE.md` is the canonical public architecture; private plans/ADRs/audits/history explain development context only and never override public product semantics.

When working inside a domain, also read its five packs: domain schema, rule pack, template pack, benchmark pack and review rubric, plus any assigned skill/software mapping.

## Professional operating order

For engineering work, reason in this order:

0. Which target host is involved, what engineering software is actually installed there, where is it installed, which version/build is present, and which public provider/runtime capabilities are actually ready?
1. What is being designed/reconstructed?
2. Why is it being produced and who will use the output?
3. What release/lifecycle class applies?
4. Which disciplines/roles are required?
5. What Design Basis fields, sources and dependencies are authoritative or missing?
6. Which standards/project rules apply, at exact version/applicability?
7. Which Engineering Skills and deterministic checks are required?
8. Which software semantic capabilities are needed and actually available?
9. How will each mutation/stage be verified and recovered?
10. What independent QA and handoff evidence is required?

Do not jump directly from user intent to a preferred CAD/3D tool. Never assume an application/provider exists or that remembered version/capability data is current; perform Step-0 discovery and fail closed for native execution when environment state is unknown.

## Evidence and uncertainty

Preserve engineering provenance states explicitly:

- observed;
- specified;
- derived;
- inferred;
- unknown;
- approved_assumption.

Never invent missing XREF content, dimensions, tolerances, elevations, loads, materials, standards applicability, hidden features or manufacturing/constructability facts. An unknown may be structurally valid data while still blocking a dependent release gate.

A successful tool call, Boolean, save/export or render is not by itself an engineering PASS.

## Mandatory engine boundaries

- Generic native execution engines live only in CDT-AutoCAD, CDT-SketchUp, CDT-Blender and CDT-SolidWorks.
- Do not put native backends, COM/Ruby/bpy/SolidWorks automation or MCP server projects here.
- Do not import runtime source from an engine repository. Use pinned public contracts and runtime capability discovery.
- Never replace a missing public capability with an undocumented direct COM/script/native path and claim production acceptance.
- Keep application-specific mappings explicit; do not create a weak universal CAD API.
- Software guides in this repo describe how an engineer should use software; they do not implement the native engine.
- Engine repository changes require a separately assigned task.

## Domain and skill requirements

Every production domain requires at minimum:

1. domain schema;
2. rule pack;
3. template pack;
4. benchmark pack;
5. review rubric.

An Engineering Skill additionally defines intent, prerequisites, inputs/evidence states, decision boundary, deterministic checks, professional dependency/catalog states, workflow/stages, required software semantics, completeness inventory where applicable, QA/negative cases and technical delivery requirements.

For production work, resolve professional semantics before native primitives. Missing skills/catalogs/standards/cross-discipline interfaces/calculation evidence must block, explicitly reduce scope or remain a declared proxy within its allowed release class. Never silently replace a missing professional dependency with primitive geometry/tool calls while retaining a stronger release verdict. Generic engine integrity does not override domain relationship/topology/interface/completeness gates.

Do not build a shared Domain SDK before Rule-of-Two evidence from at least two implemented consumers and an extraction ADR. CDT-Provider-Kit has a separate provider reuse gate.

## Feature-based Chunk Streaming

For mutation-heavy interactive engineering work, the default execution invariant is **Feature-based Chunk Streaming**.

Do not use either unsafe extreme:

- one opaque whole-project mutation;
- one primitive LINE/ARC/face/feature per Agent round-trip when those primitives form one semantic feature.

Instead, decompose the job into bounded semantic chunks with `chunk_id`, scope, dependencies, measurable postconditions, truthful transaction/recovery mode and optional `ui_yield`. Execute and verify one dependency boundary at a time. Do not release dependent chunks until predecessors are verified committed.

If a chunk fails or becomes uncertain, stop dependent work, reconcile actual state, rollback/restore/compensate according to the engine's declared capability, verify recovery, then retry/replan/block. Never blindly replay an uncertain mutation.

`ui_yield` is a presentation hint only. Visual cursor/viewport progress must never weaken transaction boundaries, determinism or QA. Concrete payloads and native transaction/undo/checkpoint semantics live in per-software operating guides/engine maps.

## Standards and compliance

Standards require exact source identity, edition, applicability, clause/derived-rule mapping and reviewer decision. Do not use `latest` as an edition. Unresolved source/edition/applicability blocks a compliance PASS.

Project specifications, manufacturer data and owner requirements may be authoritative and must preserve provenance/precedence. Do not average conflicting tolerances or silently choose a standards family.

Protected normative full text remains in authorized/private storage when required by licensing; public rules contain permitted metadata/references and original derived logic.

## Human-readable deliverables

When drawings/documents are intended for fabrication, construction, assembly, inspection or human review, verify communication quality as engineering content: views, sections/details, datum/reference system, dimensions/tolerances, notes, legends, schedules/BOM, scale/readability and revision identity as applicable.

A correct machine model does not automatically satisfy a shop/construction drawing requirement.

## QA and professional release

Final acceptance binds exact source/artifact hashes, domain/skill/workflow/standards versions, engine/application versions and independent verification. Screenshots supplement measurements.

Rubric scores cannot override hard gates. After final artifact mutation, earlier hash-bound PASS evidence is stale.

CDT_Engineer may prepare `ready_for_professional_review` evidence. Do not claim legal/professional issue, certification or signature authority on behalf of the system.

## Documentation and public/private files

Follow `docs/DOCUMENTATION_POLICY.md`. Every public Markdown file declares one `PUBLIC_*` documentation class near the top. Stable architecture, contracts, policies, domains/skills, catalogs, software guides, integration standards and sanitized benchmark definitions must stand alone without private dependencies.

Internal roadmaps, implementation ADR history, audits/closure reports, session handoffs, provider/product backlogs, customer fixtures, raw evidence, protected references, external reference snapshots and run workspaces belong in ignored `_private/`. They are development evidence, not product authority. When a private decision becomes stable product behavior, promote its normative result into the public architecture/contract/policy/domain/software/catalog surface and leave the private source as history.

Preserve existing private contents unless the task explicitly reorganizes them. Never force-add `_private/`; Git ignore is not backup/access control.

## Change protocol

- Read ground truth and inspect git status before editing.
- Preserve existing uncommitted work; do not reset/clean/rebase it away.
- Preserve pinned spec baselines; provider/engine upgrades require explicit version/sync review.
- Validate document links, schemas and `git diff --check`; run behavioral acceptance for runtime changes.
- Stage only task-owned public changes; never force-add `_private/`.
- No push/deploy without explicit user instruction.
- Record meaningful session evidence through available CyberBrain tools.
