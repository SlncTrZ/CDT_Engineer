# Design Basis Contract

Version: 0.1.0 · Updated: 2026-09-12 · Status: architecture baseline.

## Purpose

The Design Basis is the frozen engineering context that defines what a job is for, which evidence and constraints are authoritative, what standards/assumptions apply, what outputs are required and what release class is being pursued. It is the technical contract between user intent and downstream engineering execution.

No serious fabrication, construction, compliance or professional-review claim may be made without an adequate Design Basis for the relevant discipline.

## Required envelope

A Design Basis records:

| Area | Required information |
| --- | --- |
| Identity | `job_id`, project, revision/version, owner/requestor |
| Purpose | Business/engineering purpose and intended downstream user |
| Lifecycle | concept, development, reconstruction, fabrication/construction candidate, visualization, as-built, etc. |
| Deliverables | Native models, exchange files, drawings, schedules/BOM, calculations, renders, reports |
| Disciplines | Selected domains/roles and discipline interfaces |
| Jurisdiction | Country/authority/project jurisdiction and known regulatory context |
| Standards | Selected standard records, applicability status and reviewer decisions |
| Sources | Source manifest, hashes, dependency status and authority ranking |
| Geometry/reference | Units, coordinate systems, datums, levels, orientation/reference frames |
| Engineering inputs | Loads, operating conditions, materials, process/manufacturing constraints as applicable |
| Tolerances | Project/standard/manufacturing tolerance policy and unresolved state |
| Assumptions | Approved, inferred and unresolved assumptions with owner/authority |
| Outputs | Required formats, issue purpose, human/machine consumers and acceptance class |
| QA | Required checker independence, hard gates and acceptance thresholds |

Discipline-specific extensions add fields rather than weakening this core envelope.

## Evidence states

Design Basis values preserve one of:

```text
observed
specified
derived
inferred
unknown
approved_assumption
```

`unknown` is a valid representation of incomplete reality, not a validation failure by itself. Domain rules decide whether the unknown blocks a dependent stage. An Agent must never replace a critical `unknown` with a fabricated numeric/string value merely to satisfy a schema.

## Purpose-dependent rigor

The same source may support several deliverable purposes with different gates.

Examples:

- **concept:** incomplete engineering inputs may be acceptable when limitations are explicit;
- **visualization:** geometry/material/camera requirements may dominate, but output must not be labeled fabrication-ready;
- **design review:** critical dimensions/interfaces and applicable rules must be sufficiently frozen for review;
- **fabrication/construction candidate:** manufacturability/constructability, dimensions/tolerances, human-readable drawings and stronger QA become mandatory;
- **ready for professional review:** unresolved critical findings are dispositioned and evidence is sealed for accountable review.

## Source authority

The Design Basis ranks sources and dependencies. Example classes include:

```text
owner-specified requirement
approved drawing/model
survey/measurement
manufacturer data
verified standard/project specification
historic/reference evidence
inference/concept sketch
```

Conflicts are recorded and resolved by declared authority; an Agent must not silently choose whichever source is easiest to execute.

## Change control

Any change to critical Design Basis inputs creates a new revision and invalidates affected downstream evidence. The run must identify which calculations, rules, drawings/models and QA checks require rerun.

Examples of critical changes include:

- source hash/dependency change;
- units/frame/datum change;
- material/process change;
- load/operating condition change;
- tolerance/standard edition change;
- deliverable purpose/release-class change.

## Minimum release gate

Before production execution, the Agent checks that all mandatory Design Basis fields for the selected workflow are either resolved or explicitly unresolved with a known blocker/owner. A missing critical requirement must stop the dependent workflow stage with a typed reason.
