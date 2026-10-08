# Engineering Skill — Architectural Detail Package

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `architectural-detail-package` · Version `0.1.0` · Domain `building-architecture` · Lifecycle `pilot`.

## Intent

Translate in-scope architectural systems into a release-aware detail/junction inventory so design review cannot PASS with visually plausible but professionally incomplete modeling.

## Preconditions / inputs

Accepted semantic building graph; system families in scope; release target; Design Basis; applicable standards/manufacturer/project data; structural/interface states; component/catalog resolution.

## Decision boundary

May require and organize detail/junction intent according to the domain release matrix. Must not invent exact construction layers, anchors, waterproofing products, structural connections or regulatory dimensions when their source/applicability is unresolved.

## Deterministic checks

- `required_details_for_release` derives required detail IDs from in-scope semantic systems and release class;
- `evaluate_detail_inventory` uses the shared completeness invariant to block missing/unverified required details;
- unrelated decorative/detail content cannot substitute for a required junction;
- stronger release classes activate additional construction-detail IDs;
- technical detail content still fails closed when its standards/material/manufacturer/structural dependencies are unresolved.

## Workflow

Semantic systems → release-aware detail matrix → source/dependency resolution → detail inventory → bounded detail development → independent detail verification → drawing-package handoff.

## Software semantics

Detail drawings may use public technical 2D capabilities. Native geometry is evidence of the detail representation, not proof that an unresolved material/connection/system is technically adequate.

## QA / outputs

Output: required detail IDs, implementation/verification states, dependency limitations, detail drawing references and unresolved owner/actions.

## Negative cases

- facade exists but support/edge detail intent omitted;
- parapet exists but roof junction omitted at design review;
- construction detail drawn with invented anchors/materials;
- extra decorative view used to hide a required missing detail;
- unverified detail counted as complete.
