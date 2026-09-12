# Building Architecture v1 — Detail Requirement Matrix

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Scope: release-documentation completeness, not universal construction-code content.

This matrix answers **which junction/detail intent must be accounted for** when a semantic system is in scope. It does not invent dimensions, materials, waterproofing products, anchors, loads or standard requirements. Exact technical content still comes from Design Basis, standards, manufacturer/project data and responsible discipline decisions.

| Semantic system | Design review | Fabrication / construction candidate |
| --- | --- | --- |
| Opening | head/jamb/sill junction intent | dimensioned head/jamb/sill construction detail |
| Door | threshold intent | threshold/waterproofing/accessibility detail as applicable |
| Facade system | host/support + edge/corner intent | anchor/subframe/termination detail with technical evidence |
| Parapet / roof edge | roof-junction intent | waterproofing/termination/drainage detail as applicable |
| Railing / guard | base/top support intent | anchor/connection detail + exact governing requirements |
| Stair | landing/handrail/interface intent | landing/handrail/guard/support construction details |
| Balcony | edge/support intent | edge/waterproofing/drainage/support detail |

`domains.building_architecture.detailing.required_details_for_release` is the executable v1 mapping. `evaluate_detail_inventory` compares required detail IDs with implemented/independently verified detail inventory.

## Hard invariant

Extra decorative modeling cannot substitute for a missing required junction/detail. A render/model can be visually complete and still be blocked by detail completeness.

## Release boundary

`concept` has no mandatory v1 construction-junction details. `design_review` requires critical system/junction intent. `fabrication_or_construction_candidate` adds construction-detail IDs but still cannot PASS until the exact materials/standards/structural/manufacturer dependencies required by those details are resolved.
