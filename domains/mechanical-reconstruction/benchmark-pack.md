# Mechanical Reconstruction — Benchmark Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.3.0 · Status: CDT-SolidWorks public provider available; Engineer-level closed-loop acceptance required before professional release.

## Baseline

The inspected 2026-09-11 mechanical appendix in the engine benchmark report remains historical source evidence: it describes staged ACIS operations and 14 Boolean receipts, sampled radii/profiles, incomplete face-level hole verification and backend calls outside the current public SolidWorks surface. It must not be treated as current CDT-SolidWorks acceptance or as an independent geometry oracle.

The current public provider baseline is CDT-SolidWorks revision ddaef7b60611f8f094f614914e37f9adccc298f3, provider/contract 0.1.0, measured on SOLIDWORKS 2024 SP0.1 revision 32.0.1. That provider exposes 149 public tools and measured native acceptance for bounded part/assembly/drawing/deployment plus STEP/STL reconstruction paths. Step-0 runtime discovery is still mandatory for every run.

The exact reconstruction fixture, source hashes, frozen dimensions/tolerances and expected topology must be bound before replay. Do not manufacture a golden model or promote sampled historical values into approved Design Basis facts.

## Current native state and remaining blocker

The former provider-skeleton blocker is retired for the accepted provider snapshot. MP-03 through MP-06 may now execute through released CDT-SolidWorks public tools when current runtime discovery confirms the required capabilities.

artifact_seal_missing remains a separate release blocker: CDT-SolidWorks currently has no public content-addressed artifact_seal/artifact_verify route. Exact external SHA-256 may bind evidence to bytes, but it does not satisfy the software semantic artifact.seal in a profile that requires provider-backed sealing. Therefore successful native closed-loop evidence does not by itself release ready_for_professional_review.

## Cases

- MP-01: reconcile orthographic views and explicit dimensions; independent interpretation review records unresolved ambiguity.
- MP-02: validate the feature DAG, analytic profiles, required Booleans and exactness/tolerance requirements against the frozen Design Basis.
- MP-03: execute the accepted feature plan only through current CDT-SolidWorks public routes such as part_create_rect_extrude / part_profile_extrude, part_cut_extrude, part_simple_hole, part_revolve and body_combine; verify each dependency-bounded chunk with public model queries before the next mutation.
- MP-04: use a Checker role/context to independently measure holes, radii, depths, placements and body/topology state through evaluation_measure, evaluation_bounding_box, evaluation_geometry_sanity, topology_query and topology_inspect. Producer receipts are not the measurement oracle.
- MP-05: save/reopen the exact native artifact, export the required neutral format through export_document, reopen/import with an identified public reader path and compare units, critical dimensions and required topology. The format is selected by the Design Basis/runtime, not hardcoded globally.
- MP-06: inject early/middle/late/uncertain recovery cases through the public provider; use document_reconcile or feature-specific reconcile tools for uncertain completion and use verified document_save/document_reopen boundaries without claiming whole-chunk transaction atomicity.

## Failure / recovery matrix

- **early failure:** runtime preflight, missing capability, invalid feature prerequisite, cyclic dependency or unsupported exactness blocks before native mutation.
- **middle failure:** force a feature/Boolean mutation failure; query feature/body state, reconcile any uncertain call, prove no duplicate feature/body mutation and recover from the last verified persisted baseline or replan.
- **late failure:** save/reopen, independent measurement/topology, neutral export/import or artifact-identity failure invalidates dependent release evidence.
- **uncertain completion / timeout:** do not replay the mutation; call document_reconcile or the applicable part_*_reconcile route against expected postconditions, then continue only from reconciled state.

No recovery class is accepted from source prose alone. checkpoint.create in this pack means a verified persisted save/reopen boundary plus explicit reconciliation semantics. checkpointed_atomic remains unclaimed unless a separate runtime proof demonstrates complete pre-chunk restoration.

## Negative and scale ladder

Require projection ambiguity, dimension conflict, cyclic feature plan, unsupported required capability, Boolean failure, stale expected revision, missing topology inspection, out-of-tolerance measurement, unsupported exporter, round-trip mismatch, artifact hash drift and early/middle/late/uncertain recovery cases.

Scale testing may increase feature count and topology complexity only after the correctness case passes. Respect live provider limits; an over-budget case must fail closed rather than weaken topology or measurement requirements.

## Independent closed-loop acceptance

A valid SW-07 Engineer→SolidWorks loop separates the producing role from the Checker evidence path:

1. Engineer freezes source identity, feature DAG, dimensions/tolerances and required public semantics.
2. Current runtime Step-0 proves the SolidWorks provider and all required mapped capabilities are available.
3. Producer executes bounded semantic chunks only through public provider tools and records mutation receipts.
4. Checker obtains fresh read-back through model query, evaluation_measure and topology_inspect without reusing producer claims as evidence.
5. Exact native artifact is saved and reopened; required measurements/topology are repeated against the reopened revision.
6. Neutral exchange is exported/imported and compared when required by the Design Basis.
7. Exact artifact hashes, provider/application identities, source revision and finding dispositions are bound to the evidence set.

Any direct COM/.NET bypass from CDT_Engineer invalidates the native public-provider gate. A provider-native PASS still does not establish manufacturability, drawing completeness, standards compliance or professional approval.

## Oracle and release

A responsible reviewer freezes source-linked dimensions, tolerances, expected topology and required exchange format before generation. Generic solid validity, bbox, volume, screenshots or successful save cannot establish critical-hole correctness where a direct measurement/topology route exists.

Record exact SOLIDWORKS version/revision, CDT-SolidWorks provider/build/public contract, CDT_Engineer pack/skill/workflow versions, public tool receipts, independent Checker method, native/neutral artifact hashes and unresolved findings. Missing required runtime capability or failed independent evidence means BLOCKED/FAIL, never a skipped PASS.

Final evidence must satisfy the domain review rubric. artifact_seal_missing remains a hard release limitation until the provider gains an accepted seal route or the release policy is explicitly revised to accept a different sealing authority.
