# Engineering Role Contract

Version: 0.1.0 · Updated: 2026-09-12 · Status: architecture baseline.

## Purpose

Engineering Roles model professional responsibility inside a CDT_Engineer job. A role tells the Agent what it is accountable for, what evidence it must inspect, which decisions it may make, which decisions require escalation/approval, and what it must hand to the next role.

A role does not grant filesystem, software, MCP or legal authority. Tool authority remains external; professional sign-off remains jurisdiction- and person-dependent.

## Required role definition

Each role defines:

- `role_id`, version and owning discipline/family;
- mission and bounded responsibility;
- required Design Basis fields and source package;
- skills the role may invoke;
- permitted professional judgments;
- mandatory deterministic checks;
- standards/applicability responsibilities;
- required inputs from upstream roles;
- deliverables/evidence owed to downstream roles;
- stop/escalation conditions;
- conflicts of responsibility and independence requirements;
- review authority needed for release.

## Initial role families

| Role | Core responsibility |
| --- | --- |
| Chief / Lead Engineer | Resolve purpose, Design Basis, disciplines, interfaces, workflow and release gates |
| Architect / Spatial Designer | Functional/spatial/architectural intent and architectural deliverables |
| Civil / Infrastructure Engineer | Alignment, grading, drainage, roads, utilities and infrastructure engineering |
| Landscape Engineer | Public-space/site circulation, levels, landscape systems and coordination |
| Structural Engineer | Structural system intent, analysis/design inputs and structural deliverables |
| Mechanical Design Engineer | Mechanisms, parts/assemblies, geometry, loads/interfaces and design intent |
| Manufacturing Engineer | Process selection, manufacturability, tolerances, shop/fabrication deliverables |
| Electrical Engineer | Power/distribution/control design and electrical deliverables |
| Electronics Engineer | Schematic/PCB/component/signal/power electronics engineering |
| Embedded Engineer | Firmware architecture, MCU/peripheral/bus/timing behavior and hardware interfaces |
| CAD/BIM Technician | Model/drawing implementation using approved engineering instructions |
| 3D / Visualization Engineer | Visualization-specific model preparation, materials, cameras, lighting/rendering |
| Checker / QA Engineer | Independent verification against frozen requirements/rules/artifacts |
| Documentation Engineer | Drawing/document register, presentation, revisions and issue package |

Roles are introduced as actual verticals are implemented; this table is a responsibility map, not a claim that all roles are production-ready today.

## Role separation and independence

The same Agent may sequentially perform several roles in early product stages, but the run must preserve role transitions and evidence. A production hard gate may require independent checking by a distinct review context, agent/person or verification method as specified by the review rubric.

The Checker must not merely repeat the producing role's conclusions. It works from frozen Design Basis/rules and independently re-measures critical outcomes.

## Chief Engineer routing

Before software selection, the Chief/Lead role resolves:

1. What is being designed or reconstructed?
2. Why is it being produced?
3. Who will use the deliverable?
4. What lifecycle stage applies?
5. Which disciplines/roles are required?
6. Which jurisdiction/standards and project rules may apply?
7. What evidence is missing or uncertain?
8. Which outputs and release class are requested?

Only then is a workflow/software path selected.

## Role handoff contract

A role handoff contains at least:

- upstream artifact/evidence IDs and hashes where applicable;
- decisions made and their provenance;
- calculations/rules completed;
- approved assumptions;
- unresolved/RFI items;
- interface requirements for other disciplines;
- expected downstream action;
- revision/version identity.

A downstream role must not silently reinterpret a frozen upstream assumption; changes are versioned and affected work is revalidated.

## Release classes

Roles distinguish at minimum:

```text
concept
technical_draft
design_review
fabrication_or_construction_candidate
ready_for_professional_review
issued_by_responsible_professional   # external/human authority, not self-issued by CDT_Engineer
```

CDT_Engineer may prepare evidence for the last transition but does not automatically perform it.
