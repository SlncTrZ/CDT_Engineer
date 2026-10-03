# Floor-plan Source Completeness Contract

> Documentation class: PUBLIC_DOMAIN

Version: 0.2.0 · Applies to architectural PlanSpec review/compilation at every release target.

## Purpose

A valid object or a successful CAD call does not prove a complete floor plan. Before
execution, freeze source requirements independently of the proposed output. Never
generate a production source inventory from the output PlanSpec: doing so hides omissions.

`execution.plan_review.review_plan_spec` checks this planning contract.
`execution.plan_compiler.compile_plan_spec` refuses failed review and emits no chunks.
Final artifact completeness still requires independently measured native evidence.

## Reading images

Read each source image in three ordered passes:

1. `context`: identify the view, floors/levels, included scope, units/scale anchors
   and what cannot be seen.
2. `detail`: inspect each region and record every visible/requested feature,
   including small junctions, offsets, opening subdivisions, furniture and annotations.
3. `confirmation`: independently revisit the source against the inventory;
   account for missing, ambiguous and occluded content before execution.

An image source requires `review_passes: ["context", "detail", "confirmation"]`.
These fields record the Agent's review evidence; the pure checker cannot itself
prove that an image was visually read or discover details absent from the inventory.

A perspective facade photo is not an authoritative floor plan. Hidden columns,
load-bearing roles, room partitions and exact dimensions remain unknown until
additional sources or explicit approved assumptions resolve them. Do not invent them.

## Frozen source inventory

Architectural PlanSpec includes `source_inventory` with:

| Field | Meaning |
| --- | --- |
| `source_id` | Stable source-package identity |
| `source_sha256` | Exact source or frozen source-package manifest digest |
| `source_type` | `image`, `drawing`, `model` or `specified` |
| `review_passes` | Ordered image review records; non-image sources may use an empty list |
| `items` | Non-empty frozen requirement inventory |

Each item records `item_id`, `semantic_family`, `required`, `feature_refs`,
`evidence_state` and non-empty `source_evidence`. IDs are unique.
Required references must exist in the correct PlanSpec family; every planned feature
must also be accounted for by the frozen inventory. Unknown/inferred
source requirements block execution; a required item without feature references
also blocks. A structurally valid PlanSpec without this inventory does not pass review.

Every family below must be explicitly accounted for, even when absent:

| Family | Planned content |
| --- | --- |
| `axes` | Reference axes/grid |
| `walls` | Wall systems |
| `bearing_walls` | Source-established load-bearing walls |
| `partition_walls` | Partition walls |
| `columns` | Columns |
| `doors` | Door openings |
| `windows` | Window openings |
| `spaces` | Named room/space boundaries |
| `fixtures` | Furniture/equipment/sanitary fixtures in scope |
| `dimensions` | Required dimension annotations |

A non-required item needs `exclusion_reason`, `reviewed_by` and source evidence.
Its feature references must be empty and it must not contradict geometry already
in that family. N/A means a reviewed scope decision; lack of information is unknown,
not N/A. A family may contain multiple separately identified required items.

Additional required semantics that this floor-plan IR cannot represent must remain
blocked or be separately planned through a supported domain workflow. They must not
be discarded or replaced by an unsupported field that the compiler ignores.

At minimum a floor plan contains walls and spaces. An empty or axes-only payload
cannot be released as a floor plan. Explicitly excluded families may have no chunks;
this differs from silently deleting required source features.

## Fixture envelope

For fixtures, `position` is the footprint center and `dimensions: [width, depth]`
is a positive rectangular envelope in PlanSpec length units. `rotation` follows
PlanSpec angle units (`deg` or `rad`); absent rotation means zero.
`host_space_id` must resolve to the containing room/space.

Containment checks the rotated envelope vertices and every edge interval against
the room polygon, including concave notches. Boundary contact is permitted;
project clearance requirements remain separate. A center point alone is insufficient.
Missing dimensions/host or an envelope outside the room blocks review.
This contract does not claim arbitrary furniture shape, furniture-furniture collision,
door-swing clearance or circulation/accessibility compliance.

## Units and source binding

Source calibration supports `mm`, `cm`, `m`, `in` and `ft` anchors.
Unsupported units fail before calibration. Original anchor values/units remain in
the evidence ledger; calibrated `coords_mm`, frame scale and frame unit are canonical
millimetres. Mixed anchor units remain refused by the current calibration contract.

Every architectural compiled chunk carries `source_sha256` and
`source_inventory_sha256` (SHA-256 of canonical UTF-8 JSON with sorted keys,
compact separators, no NaN, and unescaped Unicode). The receipt builder preserves both hashes and refuses partial/invalid bindings.
The executor/checker must bind its measurements to these identities and invalidate evidence after drift.

These are caller-supplied source observations, not native image/file verification.
The Agent must independently observe current source bytes/manifest and compare
their identity before execution. The existing final release-bundle gate still
requires current source/artifact/runtime observations.

## Final acceptance and migration

After execution, compare the frozen items with actual persistent native identities,
positions, quantities and measurements; run final completeness, drawing readability,
save/reopen and stale-evidence gates. Pre-CAD review is planning approval only.

Existing architectural callers must supply a source inventory and fixture envelopes
before requesting review/compilation. Inventory omission is not accepted at concept,
technical-draft or design-review scope. Schema validation alone remains a separate,
weaker result. Generic `assess_inventory([])` may represent a domain with no required
items; it must never be interpreted as proof of floor-plan completeness.

Regression acceptance covers complete plans, omission of each required family,
unreviewed N/A, incomplete image reads, unknown requirements, wrong/duplicate identity,
empty plans, rotated/concave/boundary fixture containment and canonical unit conversion.
Native AutoCAD/SketchUp acceptance remains a separate runtime check.

## Numeric safety and bounded review

PlanSpec validation rejects non-finite numbers anywhere in the input before schema,
topology or compilation. Values with absolute magnitude above `1e100` are outside
this floating-point computational envelope; this is a numerical safety bound,
not an engineering design limit. Source calibration also verifies every computed
coordinate before returning `CALIBRATED`; overflow returns `INVALID_SOURCE`
without usable features.

The current implementation declares these fixed limits in
`execution.planspec.PLAN_INPUT_LIMITS`:

| Limit | Value |
| --- | --- |
| Traversed input nodes | 50,000 |
| Nested depth | 48 |
| String length | 65,536 characters |
| Architectural features | 1,024 |
| Vertices per room polygon | 256 |
| Chunk dependency records | 256 |
| Conservative review work estimate | 250,000 |

The work estimate includes wall joins, axis/column comparisons, every room polygon
and repeated hosted-fixture containment. Duplicate space IDs cannot hide large
polygons from the estimate. Exceeding a limit refuses before pairwise geometric
review and emits no chunks; callers must partition/replan the job with explicit
cross-partition checks, or use a separately validated scalable implementation.
Increasing the chunk size does not bypass the review limit. This gate is not a
wall-clock Latency guarantee.

## Independent installation verification

Run `python3 scripts/smoke_installed_wheel.py` from the source checkout.
The verifier builds the current working tree using an isolated builder, installs
the wheel plus its declared dependencies into a fresh virtual environment, runs
`pip check`, and exercises valid/invalid planning behavior from that installed
wheel outside the source tree. The report binds the wheel SHA-256 and source
fingerprint and separately records source-foundation checks with those newly
resolved dependencies. Source tests and installed-wheel behavior are distinct
evidence. Neither proves AutoCAD/SketchUp native acceptance.
