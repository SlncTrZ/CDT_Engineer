# Engineering Skill — Facade Component Layout

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `facade-component-layout` · Version `0.1.0` · Domain `building-architecture` · Lifecycle `pilot`.

## Intent

Resolve and lay out repeated facade systems/components such as louvers, screens, breeze-block panels, railings and facade modules without degrading them into anonymous repeated primitives.

## Preconditions / inputs

Accepted facade/host geometry; frozen visible-feature inventory; semantic family; module/profile dimensions when known; approved catalog/custom/proxy state; support/interface evidence appropriate to release class.

## Decision boundary

May select and repeat approved semantic components within parameter limits. Must not invent hidden anchors/subframes, manufacturer properties, structural capacity, waterproofing or installation details from appearance alone.

## Deterministic checks

- required facade inventory items have explicit resolution/implementation/verification states;
- repeated resolved families preserve one semantic/component definition identity and bounded transforms;
- pitch/spacing/start/end offsets are checked when explicitly specified;
- proxy systems are rejected above their allowed release class;
- host/support/interface state is explicit for design-review and stronger scopes;
- missing catalog mapping is a dependency blocker, not a reason for silent primitive substitution.

## Workflow

Observed/required facade item → semantic family → host/interface → catalog/custom/proxy resolution → module parameters → feature chunk plan → native instances/geometry → query transforms/counts → independent inventory/topology QA.

## Software semantics

CDT_Engineer chooses semantic family/component. SketchUp/other engines only resolve/create/place/transform/query native representations. Arrays are execution primitives, not facade-system intelligence.

## QA / outputs

Output: facade system register, component IDs/versions, host/support intent, module parameters, instance identities/transforms, proxy/custom limitations and missing detail requirements.

## Negative cases

- louver/screen/breeze-block family replaced by solid boxes at `design_review`;
- instance copies lose semantic/material/property identity;
- facade system has no host/support state;
- edge/corner/opening conditions omitted from required inventory;
- visual similarity used to override missing component/detail evidence.
