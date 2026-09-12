# Mechanical Reconstruction — Template Pack

> Documentation class: PUBLIC_DOMAIN
Version: 0.2.0 · Status: specification templates.

## Intake
job_id; source drawing/image hashes; view inventory and projection convention; units; scope; native/neutral output requirements; standard records/editions/applicability; acceptance tolerances and reviewer.

## Dimension and interpretation ledger
dimension_id; source view/annotation; nominal value; unit; structured tolerance (`status`, `value`, `unit`, `source_ref`, `approved_by`); explicit/inferred/unknown dimension evidence status; conflicting evidence; decision/approval. Record hidden geometry, holes, radii, tangency and edge treatments separately.

## Feature plan
feature_id; domain purpose; input features; dimension IDs; profile/plane/frame; operation; exact/approximate representation; expected postcondition; selected engine/public capability/version; checkpoint and failure recovery. Store a DAG even when the native engine produces a non-parametric solid.

## QA
Requirement ID; independent measurement method; actual value; tolerance; face/edge/section reference; native body count/validity; uncertainty; rule outcome; artifact hash; verifier and finding disposition. Bbox/volume are supplemental.

## Delivery
Native and required neutral format/hash; exporter and reopening-reader identity; round-trip units/topology/dimension results; unreconstructed features; accepted approximations; standards decisions; review score/hard gates; source/pack/engine versions and replay instructions.

Never fill an unknown radius or manufacturing tolerance from an unstated convention. Record a blocker or approved scope limitation.
