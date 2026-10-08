# Mechanical Reconstruction — Rule Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.3.0 · Status: MECH-02/03/04/07 deterministic guards implemented; remaining rules specified · Origin: internal reconstruction policy.

| Rule | Inputs and deterministic decision | Failure/severity | Required evidence |
| --- | --- | --- | --- |
| MECH-01 Orthographic interpretation | Resolve first/third-angle convention, view alignment and hidden/section evidence before 3D interpretation | BLOCK on unresolved critical ambiguity | View mapping and source references |
| MECH-02 Dimensions | Reconcile explicit dimensions and tolerances in canonical units; detect contradictory constraints; never use pixel scale to override an explicit dimension | BLOCK on conflict/missing critical values | Dimension ledger, source references, reviewer decisions |
| MECH-03 Feature dependency | Unique feature IDs; all references exist; DAG acyclic; operands created before use; no self-dependency | BLOCK | Topological build order and preconditions |
| MECH-04 Exactness | Distinguish exact analytic geometry from sampled approximation; required radii/tangencies cannot silently become polygonal profiles | BLOCK unless explicitly scoped approximation | Geometry representation and deviation evidence |
| MECH-05 Solids/Boolean | Check pre/post native body state and expected operation result; reconcile uncertain failures before retry | BLOCK | State receipts, expected body count, verified checkpoint/recovery |
| MECH-06 Holes/dimensions | Independently measure required diameters, positions, axes and depths after final Boolean; construction success is insufficient | BLOCK outside tolerance or unmeasurable | Face/section/topology measurement, not only bbox/volume |
| MECH-07 Topology | Compare expected connected solid count and validity; reject unintended cavities/non-solid output and missing required treatments | BLOCK | Native topology inspection and issue list |
| MECH-08 Neutral export | Confirm required format supported; reopen with identified reader; compare units, bodies, dimensions/topology within frozen tolerances | BLOCK on unavailable exporter, wrong format or lossy substitute | Native and neutral hashes plus round-trip measurements |

Result vocabulary: pass/fail/unknown/not_applicable, linked to rule version and evidence. Dimension tolerance is a structured evidence value (`unresolved|specified|derived|approved|not_applicable`); `unresolved` is structurally valid input but a critical dimension remains BLOCK/unknown under MECH-02/06 until dispositioned. No manufacturing or standards compliance claim from these internal reconstruction rules alone.

Negative cases: ambiguous projection; inconsistent dimensions; cyclic DAG; missing operand; mid-Boolean failure; unmeasured hole; sampled arc represented as exact; unsupported neutral format; export unit drift; changed accepted artifact hash.

## Deterministic implementation status

`domains.mechanical_reconstruction.guards` implements the domain-only deterministic portions of MECH-02, MECH-03, MECH-04 and MECH-07: independent dimension/tolerance evaluation, feature-DAG identity/dependency/cycle validation with build order, exact-vs-sampled representation enforcement, and final solid topology/body-state acceptance.

The guards never infer hidden geometry, projection convention, manufacturing tolerance, Boolean success, hole measurements or neutral-export correctness. `unresolved` critical tolerance returns `unknown`; sampled geometry cannot satisfy an `exact` requirement; generic one-solid success cannot substitute for independent dimension/topology evidence. MECH-01, MECH-05, MECH-06 and MECH-08 still require source/native/runtime evidence outside these pure guards.
