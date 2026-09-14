# Skill: photo-to-3d-interpretation

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Owning domain: laser-2d3d-assembly · Status: draft.

## Intent
Reinterpret a single product photo into an explicit proxy 3D/part intent (Blender Sculpt direction or equivalent massing) before any cut planning. Solves the from_photo branch for both cross-slot and stacked-slice variants.

## Preconditions
Session intake closed (material triple may still be unknown); source photo hashed; from_photo branch declared. Never runs silently on a from_3d job.

## Inputs
Photo hash + viewpoint note; target profile variant; known reference dimension if any (else unknown); sculpt/massing tool availability (currently unproven via CDT-Blender, record blocker when required natively).

## Decisions
Allowed: proportion breakup, joint/slice-count proposal, artistic simplification list. Requires approval: treating any photo-inferred joint position, slot width, or slice contour as exact. `unknown` stays unknown; photo inference is `inferred` at best.

## Rules
LASER-02. Proxy record must carry reason, intended semantic family, missing dependency, allowed release (max technical_draft), and replacement condition (test-cut or 3D source).

## Calculations
None deterministic beyond counting proposed parts/slices and listing open unknowns. No pixel-to-mm scaling overrides an explicit dimension.

## Workflow
source_closure → proxy sculpt/massing → joint/slice-count proposal → proxy label → handoff to cut_plan. No native cut mutation in this skill.

## Capabilities
`technical_2d.inspect` (proportion read-back); future Blender sculpt route stays in CDT-Blender provider — this skill only declares intent and evidence, never a private bpy bypass.

## Assets/dependencies
No catalog dependency. Proxy path valid only through technical_draft; stronger release needs from_3d source or test-cut approval.

## Completeness
Proxy record must list every invented joint/contour so the Checker can detect omissions, not just validate drawn items.

## QA
Positive: labeled proxy with capped release. Negative: unlabeled photo trace; photo slot treated as exact; silent bypass to cut layout.

## Outputs
Proxy interpretation record + hash-bound source photo + capped-release disposition.

## Benchmark
LZ-04/LZ-05 style: single photo in, labeled proxy out, release capped.
