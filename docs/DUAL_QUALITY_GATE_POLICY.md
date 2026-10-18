# Dual Technical & Visual Quality Gate Policy

> Documentation class: PUBLIC_POLICY

Version: 1.0.0 · Scope: authored graphical, drawing, model and visual engineering deliverables.

## Normative invariant

**A technically correct but visually unfinished drawing/model is not ready for delivery, and a beautiful but technically defective artifact is not ready for delivery.** All CDT_Engineer workflows which create or revise a visual artifact MUST independently resolve `technical_gate` and `visual_gate` for the exact final artifact revision.

The visual gate means **professional, purpose-appropriate visual quality**, not decoration everywhere. A mechanical shop drawing prioritizes clarity, dimension layout and line weights; a circuit schematic prioritizes readable signal flow, symbols and annotations; an architectural/concept 3D scene additionally prioritizes composition, silhouette, credible materials and finish. Geometry detail must be real and editable where the deliverable requires actual 3D, not a 2D stroke masquerading as thickness.

A purpose that genuinely has no human-readable/visual artifact may explicitly mark the visual gate `not_applicable`, but only with a reviewed reason, responsible role, revision-bound evidence and approval. No N/A solely to accelerate delivery.

## Quality sequence (per deliverable)

1. Freeze the source/Design Basis, output purpose, expected visual language, required views and detail inventory. Separate **observed**, **specified**, **derived**, **inferred** and **unknown** dimensions/materials.
2. Build valid primary geometry/topology at the declared scale, units and coordinate system. Preserve the source and make meaningful features editable.
3. Complete **purposeful detailing**: physical depth/volume, assemblies, junctions, trims and tolerances as appropriate; layered line weights or functional annotations in 2D; hardware and joinery in furniture; material/UV/lighting/scene finish when relevant. Do not maximize primitive count as a proxy for quality.
4. Inspect the actual artifact in its intended native software. Use relevant overall, orthographic/front and close-up views, plus required section/detail and comparison with the source. Inspect cropping, occlusion, readability, color/contrast, rhythm, proportion, unwanted outlines, material continuity, clash/overlap and real thickness.
5. Run independent technical checks (dimensions, tolerances, topology, relations, completeness, units, editable hierarchy, supported format, saved/reopened state) **and** visual checks. Fix defects then re-measure the final revision; screenshots alone are not a technical measurement.
6. Deliver the editable native file and required exchange/render/drawing files plus verifiable evidence. If either gate fails, is unknown or stale, the claimed completed/finished release is **BLOCKED**.

## Mandatory evidence (where applicable)

| Gate | Evidence | Failure examples |
| --- | --- | --- |
| `technical_gate` | exact native artifact revision/hash; source linkage; dimensions/scale; hierarchy; valid solids/topology/constraints; independent readback; save/reopen; domain hard gates | flattened 3D geometry, missing dimensions, invalid solids, broken assemblies, wrong units |
| `visual_gate` | exact same artifact revision/hash; native viewport or equivalent render with complete overall view, principal view and detail close-up; source-to-output comparison; legibility/material/finish review by accountable role | unfinished look, fake texture lines, severe outline clutter, unreadable drafting, missing intentional detailing, disproportionate features |
| `scope/assumptions` | basis for inferred dimensions/materials; concept-versus-production label; reviewer identity; approved exclusions | claiming construction-ready from one perspective photograph |

If a view/category is truly not applicable, record a reviewed reason. An image/photo cannot prove unseen geometry, material specification or manufacturing suitability. A visually convincing model cannot override any technical blocker. A native geometry/saving PASS cannot override a visual blocker.

## Quality statuses and acceptance

Each gate has `pass | fail | unknown | not_applicable` with gate-specific evidence. `not_applicable` is invalid without documented authorization and is normally **not allowed** for a visually presented deliverable. For an authored drawing/model, release as complete only when **both** gates pass, independent of any numeric rubric score. Scores may rank *already conforming* alternatives but cannot waive hard gates.

At every revision or post-QA change, review evidence becomes stale until rebound to the new artifact identity. Production and professional-review scope still requires exact source/drawing/standards/domain measurements and independent Checker rules under [QA/Checker](QA_CHECKER_MODEL.md) and [Release Scope](RELEASE_SCOPE_POLICY.md). This policy does not claim signature/certification authority.

## Rework loop and benchmark

`source+purpose → precise base → real detail → technical inspection → native visual inspection → rework until both pass → saved/reopened independent QA → handoff`.

Benchmark a few representative jobs across software, and include **negative cases**: a complete but unattractive model, a beautiful but non-manifold model, insufficient close-up evidence, false/2D thickness, mismatched source dimension, stale screenshot and blurred/unreadable plan. All must block the corresponding gate. Include rework/corrected-result tests; do not equate additional tests or number of primitives with visual excellence.

## Integration boundary

CDT_Engineer owns requirements, QA decisions and evidence semantics. Its [Engineering Workflow Contract](WORKFLOW_CONTRACT.md), [Engineering Skill Contract](ENGINEERING_SKILL_CONTRACT.md), [Software Operating Guide Contract](SOFTWARE_OPERATING_GUIDE_CONTRACT.md) and individual guides implement this policy. Native executors remain separate providers. Do not introduce arbitrary script or private-COM/Ruby/bpy execution through CDT_Engineer; concept one-shot generation is only usable via an approved/tested execution route, with native evidence and separately declared scope.

## Observable incremental construction is a separate hard gate

For interactive drawing/modeling work, visual craftsmanship is evaluated **during execution**, not only at the final screenshot. A single native call that constructs the whole cabinet/building/part/scene before the user can see its semantic features violates the workflow even when both final QA gates pass. Real execution is \`plan → create feature → verify → commit/save checkpoint → optional visible viewport yield → next dependent feature\`. For repeated doors/legs/hardware, a small coherent repeated assembly or individually important element is a valid feature; never manufacture one primitive per network request solely to imitate progress. Capture receipt and appropriate stage screenshot/viewport evidence from the native application when a visible-progress experience is requested. Aesthetic polishing and detailing are separate chunks with the same recovery standards. No retrospective fade-in/reveal of finished geometry may masquerade as staged construction. This execution invariant is additional to technical and visual quality gates.
