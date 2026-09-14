# Building Architecture v1 — Rule Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.2.0 · Scope: low-rise residential / design-review baseline · Status: ARCH-02/03/04/05/07/11 deterministic guards implemented; remaining rules specified.

This pack is standards-neutral unless a job binds an exact standard/project requirement with edition/applicability. No universal room, circulation, stair, fire, accessibility or construction-code numbers are invented here.

| Rule | Deterministic/professional decision | Failure / release effect | Required evidence |
| --- | --- | --- | --- |
| ARCH-01 Source & provenance closure | Freeze source identities/hashes; classify observations as observed/specified/derived/inferred/unknown/approved_assumption; inventory visible/required features before modeling | BLOCK when critical source identity or required feature inventory is unresolved for requested scope | Source manifest, evidence ledger, feature inventory |
| ARCH-02 Levels & references | Level IDs/elevations are finite, unique and ordered; all dependent entities reference valid levels | FAIL on malformed/duplicate/inconsistent levels | Level register and independent elevation check |
| ARCH-03 Spaces & dimensional requirements | Space boundaries are valid; compute area and explicit measurable clear-dimension checks; apply only project/standard thresholds supplied by Design Basis | FAIL on invalid geometry or explicit requirement breach; UNKNOWN where requested measurement method is unsupported | Space polygons, requirement source, measurements |
| ARCH-04 Wall/opening hosting | Opening host identity is explicit; opening bounds must fit host wall in the declared simplified v1 representation; downstream component references the opening/system identity | FAIL on unhosted/out-of-bounds opening | Wall/opening identities and measured bounds |
| ARCH-05 Vertical circulation | Stair total rise must reconcile with connected level elevations; riser/going/width checks use only explicit Design Basis/standard thresholds | FAIL on geometric inconsistency or explicit requirement breach | Level elevations, stair dimensions, requirement source |
| ARCH-06 Semantic/component resolution | Professional intent resolves to a semantic system/component/custom path before native primitives. **Silent primitive substitution** for a missing required component/system is prohibited. Proxy use follows Release Scope Policy | BLOCK or reduce scope when catalog/skill/system dependency is unresolved | Semantic ID, dependency state, catalog/custom/proxy decision, native mapping evidence |
| ARCH-07 Completeness | Compare frozen requirement/visible-feature inventory with implemented + independently verified artifact content | BLOCK on required omission, unverified required item or proxy beyond allowed release | Inventory with source evidence, implementation and verification states |
| ARCH-08 Relationship/topology | Domain relationships (level hierarchy, wall/opening host, component nesting/reuse, stair/slab interface, facade host/support intent) must be checked above generic engine integrity | FAIL/BLOCK on invalid critical relationship; generic integrity PASS cannot override | Engine query/topology facts + domain relationship verdict |
| ARCH-09 Structural/interface boundary | Architecture identifies structural-role state and required cross-discipline interfaces; unknown structural facts remain unknown; design-review dependencies cannot claim structural adequacy | BLOCK stronger claims when structural interface/evidence is missing | Interface register, structural handoff/blocker states |
| ARCH-10 Deliverable & artifact release | Design-review artifact must save/reopen, be independently remeasured and hash-bound; release label/limitations must match evidence | BLOCK/STALE on reopen/hash/measurement failure or scope overclaim | Native artifact, hash, reopen receipt, Checker verdict |
| ARCH-11 Interior casework & equipment fit | For in-scope casework, derive clear carcass envelope only from explicit outer dimensions/panel thicknesses; reconcile compartments; validate orthogonal corner footprint; fit drawers/equipment using explicitly sourced clearances | FAIL/BLOCK on nonphysical carcass/corner geometry, partition-span mismatch, required clearance unknown or item exceeding clear opening; do not invent cabinet/appliance defaults | Fit-out skill input, dimension/clearance sources, deterministic guard results, dependency/catalog state |

## Primitive policy

Primitive geometry is an implementation detail, not a professional object. It is valid only when:

1. it implements an already-resolved semantic feature/system;
2. it is explicitly a concept proxy within the allowed release;
3. a bounded custom component/feature path is approved and verified; or
4. it is auxiliary non-deliverable construction geometry.

A missing door/window/facade/stair/detail family must not become boxes/faces/lines while retaining `design_review`, construction or professional-review semantics.

## Deterministic implementation

`domains.building_architecture.guards` currently implements:

- level identity/elevation ordering;
- simple polygon validity/self-intersection and area;
- explicit space area and rectangular clear-dimension requirements;
- simplified wall/opening hosting bounds;
- stair total-rise consistency and explicit dimension thresholds;
- feature/detail inventory completeness and proxy release enforcement;
- rectangular casework clear-envelope derivation from explicit panel thicknesses;
- compartment/partition span reconciliation;
- orthogonal L-corner casework physical-footprint validation;
- drawer/equipment envelope fit using explicit six-side clearances.

These checks do not determine planning quality, structural adequacy, building-code compliance or construction detail sufficiency by themselves. Those claims require the corresponding skill/standard/domain evidence and independent QA.

## Negative cases

Mandatory Building v1 negative cases include:

- visual source present but critical feature inventory omitted;
- missing component catalog silently substituted with primitives;
- proxy used above its release allowance;
- duplicate/inconsistent levels;
- self-intersecting/degenerate space boundary;
- opening outside its host wall;
- stair total rise inconsistent with levels;
- generic topology/integrity PASS while semantic host relationship fails;
- unknown structural role promoted to structural fact;
- design-review artifact not reopened/remeasured or hash evidence stale;
- compartment widths/partitions do not reconcile to the carcass clear span;
- corner return depth consumes the opposing casework leg;
- drawer/appliance does not fit the clear opening with its sourced clearances;
- image-derived cabinet dimension or manufacturer clearance promoted to exact without an authoritative dimensional/source basis.
