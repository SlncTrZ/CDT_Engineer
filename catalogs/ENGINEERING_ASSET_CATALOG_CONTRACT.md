# Engineering Asset Catalog Contract

> Documentation class: PUBLIC_CATALOG

Version: 0.2.0 · Updated: 2026-09-12 · Status: cross-domain metadata + native-resolution baseline.

## Purpose

An Engineering Asset Catalog gives reusable technical systems/components a stable **semantic identity** independent of any one CAD/DCC/EDA/native file format. It lets CDT_Engineer select an approved engineering object/system before asking an engine to resolve or create its native representation.

This is not a generic binary asset dump and it is not a replacement for Production Domains or Engineering Skills.

## Ownership boundary

CDT_Engineer owns:

- semantic identity/family and engineering intent;
- applicability/release maturity;
- provenance;
- parameters and limits;
- host/interface rules;
- substitution policy;
- QA requirements;
- mapping from semantic asset ID to a software-specific native key/state.

A provider/software **native registry** owns the actual native representation and execution mechanics: `.skp` assets, CAD blocks, SolidWorks library features/parts, EDA symbols/footprints or equivalent native artifacts.

CDT_Engineer must not embed provider business/runtime implementation into the catalog. Providers must not decide architectural, mechanical, electrical or other professional applicability merely from an asset file.

## Minimum asset metadata

Each asset records:

```text
asset_id + version
family
semantic_intent
provenance
applicability / release classes
parameters / limits
host/interface rules
allowed transforms
substitution policy
QA checks
native mappings + resolution state
```

A `resolved` native mapping requires a native key, content hash and validated native version. An `unresolved` mapping must not fabricate those values. Catalog metadata alone is never proof that the native registry currently contains the mapped asset.

Schema `0.2.0` makes this invariant machine-enforced: `resolved` requires `asset_key` + SHA-256 + `native_version`; `unresolved`/`blocked` require a reason and reject those native identity fields. This prevents stale or fabricated binary identity from surviving under a non-resolved state.

## Resolution states

Native mappings use:

```text
unresolved
resolved
blocked
```

Job/workflow dependency resolution then maps catalog availability into the Release Scope Policy states (`resolved`, `custom_allowed`, `proxy_allowed_for_scope`, `reduced_scope`, `blocked`). A catalog entry existing in JSON does not by itself mean the required runtime/native asset exists.

## Executable native-resolution invariant

`execution.catalog_resolver.resolve_catalog_assets` is the domain-neutral deterministic baseline for the strong `resolved` path. For every required semantic asset it requires all of:

```text
catalog asset_id exists uniquely
+ software-specific native mapping state == resolved
+ exact asset_key / sha256 / native_version pinned
+ current native registry reports the asset available
+ current registry sha256 equals catalog sha256
+ current registry native_version equals catalog native_version
+ runtime library/registry capability result == pass
```

Any missing asset, unresolved/blocked mapping, absent registry evidence, hash/version drift or non-PASS runtime capability returns a blocking dependency state. The resolver does not decide proxy/custom substitution; that remains a domain/skill + Release Scope Policy decision.

This separation prevents two false positives: (1) a semantic catalog row being mistaken for an installed native component, and (2) a generic component-creation tool being mistaken for a verified catalog/library resolution route.

## Selection invariant

For a required reusable engineering family:

```text
semantic requirement
→ domain/skill applicability decision
→ catalog candidate
→ parameter/interface validation
→ native mapping/runtime resolution
→ native placement/creation
→ read-after-write verification
```

The system must not skip from semantic requirement to arbitrary primitive/native geometry merely because the native mapping is unresolved.

## Substitution

Substitution is explicit and versioned. A substitute must satisfy declared family/interface/parameter/release requirements. If substitution is not allowed or evidence is insufficient, the dependency blocks or scope is reduced.

## Cross-domain examples

Building: doors/windows/louvers/screens/stairs/details. Mechanical: bearings/fasteners/seals/standard parts. Civil: curb/drainage/section templates. Structural: member/connection/detail families. Electrical: protective devices/cables/panels. Electronics: components/symbols/footprints/reference circuits. Embedded: tested interface/protocol/driver profiles where native mapping semantics are appropriate.

Domain-specific catalogs may extend metadata, but they must preserve this identity/provenance/interface/native-mapping boundary.
