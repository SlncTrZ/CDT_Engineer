# CDT_Engineer Documentation Map

> Documentation class: PUBLIC_NAVIGATION

This index separates stable public product architecture/contracts from contributor documentation and private development evidence. See [Documentation Policy](DOCUMENTATION_POLICY.md) for classification and promotion rules.

## Start here

- [Product README](../README.md) — what CDT_Engineer is and its product boundaries.
- [Canonical Architecture](ARCHITECTURE.md) — stable Engineering OS architecture and invariants.
- [Documentation Policy](DOCUMENTATION_POLICY.md) — what is public product authority vs private development material.
- [AGENTS.md](../AGENTS.md) — operating rules for agents working in this repository.

## Public normative architecture and contracts

- [Contract Model](CONTRACTS.md)
- [Execution Environment Contract](EXECUTION_ENVIRONMENT_CONTRACT.md)
- [Design Basis Contract](DESIGN_BASIS_CONTRACT.md)
- [Engineering Role Contract](ROLE_CONTRACT.md)
- [Engineering Skill Contract](ENGINEERING_SKILL_CONTRACT.md)
- [Engineering Workflow Contract](WORKFLOW_CONTRACT.md)
- [Agent Operational Profile Contract](AGENT_PROFILE_CONTRACT.md)
- [Production Domain Contract](PRODUCTION_DOMAIN_CONTRACT.md)
- [Feature-based Chunk Streaming Contract](FEATURE_CHUNK_STREAMING_CONTRACT.md)
- [Software Operating Guide Contract](SOFTWARE_OPERATING_GUIDE_CONTRACT.md)
- [Release Scope & Semantic Dependency Policy](RELEASE_SCOPE_POLICY.md)
- [QA / Checker Model](QA_CHECKER_MODEL.md)
- [Standards Governance](STANDARDS_GOVERNANCE.md)
- [Engineering Asset Catalog Contract](../catalogs/ENGINEERING_ASSET_CATALOG_CONTRACT.md)
- [SlncTrZ-MCP Provider Standard](../MCP_PROVIDER_STANDARD.md)

## Public production packages

Domain packages under `domains/` contain the public five-pack minimum plus optional Agent Profiles and Engineering Skills. Current public packages include Site Reconstruction, Mechanical Reconstruction, Building Architecture and Building Structural. Their benchmark/rubric lifecycle labels define the scope actually claimed; presence in the repository does not itself mean native production acceptance.

Software packages under `software/` contain public Operating Guides and semantic engine maps for AutoCAD, SketchUp and SolidWorks. Source mappings are not runtime proof.

Catalog packages under `catalogs/` contain reusable Engineering Asset Catalog metadata and schemas. A semantic catalog entry is not proof that a native asset is currently installed or resolved.

## Public contributor documentation

- [Foundation Validation](FOUNDATION_VALIDATION.md) — reproducible offline validation of public docs/contracts/schemas/profiles/catalogs/tests.

Contributor documentation describes how to validate or work on the public package; it is not itself product architecture.

## Private development material

Roadmaps, internal ADRs, audits, closure reports, handoffs, provider backlogs, private benchmark evidence, external reference repositories and historical snapshots live under ignored `_private/`. They are intentionally excluded from public semantics and are not linked as product dependencies.
