# Engineering Skill — Layered Interpretation

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `layered-interpretation` · Version `0.1.0` · Domain `site-reconstruction` · Lifecycle `pilot`.

## Intent

Think like a multidisciplinary engineer when facing any source: decompose what is seen layer by layer, name what each layer covers, and carry the covered background into every downstream layout-to-3D step. First consumer is site-reconstruction; the executable invariants (`assess_layer_ledger`, `order_layer_chunks`) are domain-neutral so Architecture, Structural, Mechanical and Laser assemblies adopt the same habit without a shared runtime SDK.

## Preconditions and inputs

- Design Basis purpose, requested release, source manifest and target host are explicit.
- Available source layers/files are hash-bound; switched-off and occluded layers remain typed ledger entries, never silent absences.
- `inputs.schema.json` is not required for this pilot; the frozen ledger shape is `item_id / layer_id / visibility / evidence_state / hosted_on / required`.

## Deterministic checks

`execution.completeness_checker.assess_layer_ledger` enforces frozen-to-final carry: dropped required background, unbuilt/unverified items, and occluded required items with `unknown`/`inferred` evidence all block. `professional_practice.layered_interpretation.order_layer_chunks` orders host/base layers before dependents and rejects unknown hosts, self-hosting, and cycles. Neither helper invents hidden content; both fail closed.

## Decision boundary

The owning role may classify layers, tag multidisciplinary families (electrical/mechanical/structural/architectural), declare host/cover relations, and approve assumptions with reason. It may not record an occluded item as absent, drop a required background for visual convenience, or schedule a foreground chunk before its host commits.

## Workflow and recovery

Use stages in order: source closure → layer/occlusion ledger freeze → host-ordered chunk plan → bounded native execution → final-to-frozen comparison → independent QA → handoff. On uncertain completion, reconcile native identities/checkpoint state before any retry; never replay a non-idempotent chunk blindly.

## Software semantics

Typical required semantics are `source.inventory`, `dependency.inspect`, `technical_2d.inspect`, `model.query`, `model.measure` plus the domain-local ledger reasoning. Native implementations remain in CDT-AutoCAD/CDT-SketchUp; this skill never bypasses public engine contracts.

## Completeness and QA

Freeze the layer ledger before mutation and make final coverage a Checker input: every required frozen item must be implemented and verified in the final inventory, or explicitly de-required with a recorded exclusion. A 3D perspective that looks complete while a frozen background layer is missing is not a PASS.

## Positive benchmark

Two-layer layout (foreground cover + background base) frozen, host ordered base-first, final 3D carries both with independent measurements, ledger comparison passes.

## Negative cases

Dropped background layer; occluded required item left unknown/inferred; foreground chunk released before host commit; host cycle; unknown host reference; blind retry after timeout; stale handoff evidence.

## Outputs

Frozen layer/occlusion ledger; host-ordered chunk plan; native receipts/read-back; ledger-comparison evidence; independent measurement evidence; final artifact identity; unresolved limitations; exact release verdict.
