# Engineering Skill — Building Structural QA

> Documentation class: PUBLIC_DOMAIN

`skill_id`: `structural-qa` · Version `0.1.0` · Domain `building-structural` · Lifecycle `pilot`.

## Intent

Independently verify structural intent, load-path connectivity, architecture interfaces and release-boundary evidence for the declared structural scope.

## Preconditions / inputs

Frozen structural Design Basis/source hashes; architecture handoff; grid/member/load-path data; applicable standards/material/load evidence states; final artifacts/producer receipts.

## Decision boundary

Checker may independently query/measure and issue findings. It must not transform a design-review intent model into structural-adequacy evidence by inference.

## Deterministic checks

- rerun `validate_grid` on frozen/independently measured references;
- rerun `validate_load_path` on the accepted graph;
- rerun architecture/member clash checks where applicable;
- rerun `evaluate_release_evidence` for the requested release;
- verify upstream revision/artifact identity remains current;
- unresolved BLOCKER/MAJOR findings block release.

## Workflow

Freeze revisions → independent grid/member measurements → load-path traversal → architecture-interface checks → release-evidence check → drawing/handoff review → findings/verdict.

## Software semantics

Use public read/query/measure capabilities; producer mutation receipts and screenshots are supplementary only.

## QA / outputs

Output: STR-01..08 coverage, independent findings, adequacy limitations, unresolved interfaces and exact release verdict.

## Negative cases

- clean CAD drawing but broken load path;
- structural intent model described as adequate final design;
- unknown loads/materials ignored for construction candidate;
- architecture clash hidden by visual presentation;
- upstream artifact changed after Checker evidence was recorded.
