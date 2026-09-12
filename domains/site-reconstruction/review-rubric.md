# Site Reconstruction — Review Rubric

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Proposed release policy; apply only with frozen project tolerances.

| Criterion | Weight | Full-credit evidence |
| --- | ---: | --- |
| Source and dependency fidelity | 20 | All included-source dependencies identified, hashed and interpreted |
| Coordinates and registration | 25 | Units, controls, residuals and independent holdout pass |
| Reconstruction completeness | 25 | Required geometry, instances and source mapping independently measured |
| SketchUp organization and output | 15 | Reopened native output with correct scale, hierarchy/tags and reuse |
| Recovery and reproducibility | 15 | Failure tests, checkpoints, sealed artifacts and replay identity |

Rate each 0–4: 0 absent/failed; 1 major gaps; 2 partial evidence; 3 meets declared scope; 4 complete evidence including adverse cases. Weighted score = sum(weight × rating/4), out of 100.

Release requires score ≥95 AND every hard gate passes: source sufficient for included scope; registration within approved tolerance; required geometry accounted for; actual SketchUp output reopened; public MCP path; recovery verified; hashes match; applicable standards resolved where compliance is claimed. Unknown/unmeasured gates block regardless of score.

Reviewer must be independent of the generation decision, record evidence and disposition every critical finding. A scope-reduced acceptance must say exactly what was excluded and may not be reported as full BeachSquare reconstruction. Screenshots cannot override measurements.
