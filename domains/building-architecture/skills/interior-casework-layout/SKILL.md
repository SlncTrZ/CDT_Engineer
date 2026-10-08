# Engineering Skill — Interior Casework Layout

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `interior-casework-layout` · Version `0.2.0` · Domain `building-architecture` · Lifecycle `pilot`.

## Intent

Translate an explicitly sourced interior fit-out requirement into a semantic casework/equipment system that can be executed through a Generic CAD Executor such as CDT-SketchUp without inventing dimensions, clearances, material properties, joinery or installation facts.

Supported pilot scope: box carcasses, orthogonal L-corner casework, compartment partitions, drawer/equipment fit envelopes, reusable panel/drawer/appliance/anchor semantic assets, bounded SketchUp feature chunks, independent read-back and design-review evidence.

This skill does not claim fabrication-ready joinery, structural anchorage adequacy, manufacturer compliance, MEP coordination or concealed-site truth unless those dependencies are separately resolved.

## Preconditions / inputs

- Design Basis purpose and release target are explicit.
- Source identities/hashes and dimensional anchors are frozen.
- `inputs.schema.json` v0.2.0 validates the casework/equipment input package. Critical numeric geometry, panel, compartment, envelope and clearance values carry field-level evidence (`status`, `value`, `source_ref`, approval where applicable); package-level provenance alone is insufficient.
- Every dimension, panel thickness and required clearance preserves `observed|specified|derived|inferred|unknown|approved_assumption` provenance through its source record.
- Required catalog/custom/proxy decisions are resolved under ARCH-06 and the Release Scope Policy.
- Step-0 confirms the selected SketchUp runtime/provider and exact required public capabilities before native execution.

Unknown panel thickness, appliance envelope, drawer clearance, anchor requirement or critical dimension is not replaced with a convenience default. `validate_casework_input_package` also enforces source membership, unique semantic IDs, evidence-state release ceilings and resolved/proxy/reduced-scope cross-field invariants before the requested release can pass.

## Decision boundary

The Architect / Spatial Designer may derive compartment geometry and fit from supplied dimensions and may choose between an applicable catalog asset and a bounded custom casework path. Manufacturer-specific clearances, hardware behavior, material performance, anchorage, services and fabrication tolerances require their authoritative source or responsible discipline decision.

A visual image may establish observed/inferred arrangement intent, but it must not be used to assert exact real-world dimensions without an independent dimensional source/scale basis.

## Deterministic checks

`domains.building_architecture.guards` provides:

- `evaluate_casework_box`: derives clear width/height/depth from explicit outer dimensions and panel thicknesses; tests only supplied minimum-clear requirements;
- `evaluate_casework_compartments`: reconciles compartment widths plus partition thicknesses against the clear span;
- `evaluate_corner_casework`: validates a simple orthogonal L-footprint and rejects nonphysical return geometry;
- `evaluate_rectangular_fit`: checks drawer/appliance envelopes against an opening using explicitly supplied six-side clearances.

No function embeds universal cabinet dimensions, drawer gaps, appliance clearances, panel thickness or code/manufacturer values. `domains.building_architecture.geometry_planner` additionally provides bounded indexed-mesh planning for equal-ring lofts and profile sweeps, including self-intersection rejection, executor-aligned mesh budgets and explicit approximation-deviation gates.

## Rules / release effects

- ARCH-01: source/provenance closure remains mandatory.
- ARCH-06: semantic component/custom-path resolution precedes native primitives.
- ARCH-07: every required cabinet, compartment, drawer, appliance, panel/finish intent and anchor dependency is present in the frozen feature inventory and independently accounted for.
- ARCH-08: module adjacency, nesting, component identity and host/interface relationships are independently queried/checked.
- ARCH-10: final accepted artifact must be saved, reopened, remeasured and hash-bound according to release policy.
- ARCH-11: interior casework dimensions, subdivisions and fit envelopes must pass the deterministic casework checks or carry a typed blocker; primitive geometry cannot erase a failed semantic check.

## Asset / dependency policy

The Building Engineering Asset Catalog includes pilot semantic families for `casework_panel_system`, `drawer_system`, `appliance_envelope` and `casework_anchor_system`. These records describe professional identity and required parameters; they are not proof that a native SketchUp asset exists.

CDT-SketchUp contract 0.28 now provides and natively verifies exact registry identity binding for loaded bytes (`asset_key` + `sha256` + `native_version`) plus definition read-back. Strong registry-backed design-review resolution therefore depends on the **actual semantic asset mapping and current registry/runtime evidence**, not on a missing provider primitive. If the selected catalog entry still has `native_mappings.sketchup` unresolved, the dependency blocks as `native_mapping_unresolved`; do not substitute a QA fixture or invent identity metadata. An explicitly bounded custom casework system may still be used when release policy permits it, with geometry/material/identity evidence independently verified.

## Workflow

Use `workflow.yaml`. Required order:

source/scale basis → semantic fit-out inventory → deterministic casework checks → catalog/custom dependency resolution → Feature-based Chunk Streaming plan → capability preflight → SketchUp bounded native execution → independent identity/geometry read-back → save/reopen/remeasure → Checker verdict.

Mutation chunks are semantic units, not primitive LINE/face operations: one carcass/module, one partition group, one drawer group, one equipment instance, one bounded profile/finish feature. A dependent chunk is released only after predecessor postconditions pass.

## Recovery / retry

For every native chunk record predecessor context/fingerprint, semantic IDs, expected postconditions and the strongest truthful provider recovery mode. On failure or uncertain completion:

1. stop dependent chunks;
2. reconcile current context/entity/definition state;
3. verify rollback/compensation/checkpoint state;
4. detect duplicate/non-idempotent placements;
5. retry only from a verified state or block/replan.

Never blindly replay a non-idempotent asset/component placement after timeout.

## Software semantics

Required semantics depend on the case but commonly include `model_3d.create`, `model_3d.transform`, `model.query`, `model.measure`, `topology.inspect`, `artifact.native_save` and `artifact.reopen`. Registry-backed components additionally require `component.library_resolve` at the release strength being claimed.

For bounded profile/molding/loft/curved work, the Engineer produces a generic indexed-mesh recipe through `plan_loft_mesh` / `plan_profile_sweep`; the selected engine must expose a compatible bounded mesh primitive. Native Ruby/SketchUp API implementation remains in CDT-SketchUp. This skill must not bypass the public engine contract with direct Ruby scripts.

## Completeness / QA

Freeze an inventory covering, where applicable:

- casework runs/modules and stable IDs;
- box/corner geometry and panel thickness sources;
- compartment partitions;
- drawer groups and required clearances;
- appliance/equipment envelopes and required clearances;
- panel/material/finish semantic references;
- anchor/host dependency state;
- custom vs catalog resolution;
- molding/profile/curved-feature requirements and whether the selected engine can represent them truthfully;
- intended edit operations and identity that must survive edit/read-back;
- final saved/reopened artifact identity.

Independent QA remeasures critical envelopes, checks component/definition identity, detects duplicates and verifies feature coverage. Screenshot/render similarity is supplemental only.

## Positive benchmark cases

- rectangular casework box with explicit panel thickness and clear envelope;
- orthogonal corner casework with physically valid L-footprint;
- compartment subdivision whose widths + partitions exactly reconcile;
- drawer edit whose new envelope still satisfies explicit clearances;
- appliance placement whose envelope and manufacturer/project clearances fit;
- bounded custom panel system created once and reused by exact native identity when the engine route supports it.

## Negative cases

- image-derived dimensions treated as exact without scale/source basis;
- compartment widths do not reconcile to carcass clear span;
- drawer or appliance exceeds the clear opening;
- corner return depth consumes the entire opposing leg;
- required anchor/material/equipment dependency silently omitted;
- unresolved registry asset represented as resolved or populated with invented hash/version;
- timeout followed by blind non-idempotent placement replay causing a duplicate instance;
- visual result accepted despite failed semantic fit/identity/read-back;
- save/reopen changes identity or critical measurement while stale prior QA is retained.

## Outputs

Semantic fit-out inventory; validated casework/equipment input package; deterministic guard results; dependency/catalog manifest; chunk DAG/evidence records; native receipts and independent measurements; save/reopen/hash evidence; unresolved dependencies/limitations; Checker verdict and exact release label.
