# Documentation Policy

> Documentation class: PUBLIC_POLICY
> Version: 1.0.0 · Updated: 2026-09-12

## Purpose

CDT_Engineer separates stable product semantics from development history. Public documentation must describe what the product **is**, what contracts it enforces, how a domain/software package behaves, or how a contributor validates the public package. Internal planning, audits, implementation history and customer/runtime evidence are development material and are not public product authority.

## Public documentation classes

| Class | Purpose | Canonical examples | Normative? |
| --- | --- | --- | --- |
| `PUBLIC_ENTRYPOINT` | Repository/product entrypoints and agent-facing operating rules | `README.md`, `AGENTS.md` | Yes for stated operating rules |
| `PUBLIC_NAVIGATION` | Documentation index/navigation | `docs/README.md` | No; points to normative docs |
| `PUBLIC_ARCHITECTURE` | Stable product architecture, ownership boundaries and invariants | `docs/ARCHITECTURE.md` | Yes |
| `PUBLIC_CONTRACT` | Versioned interfaces and required data/behavior | `docs/*_CONTRACT.md`, `docs/CONTRACTS.md`, provider standard | Yes |
| `PUBLIC_POLICY` | Cross-cutting governance, release, QA and standards policy | this file, QA/release/standards docs | Yes |
| `PUBLIC_DOMAIN` | Domain rules, templates, skills, benchmarks and review rubrics | `domains/**` | Yes within declared scope/lifecycle |
| `PUBLIC_CATALOG` | Engineering asset catalog semantics and reusable public metadata | `catalogs/**` | Yes within declared scope/lifecycle |
| `PUBLIC_SOFTWARE_GUIDE` | Professional software use, capability mapping and known public limitations | `software/**` | Yes for the pinned guide/map version; runtime proof remains separate |
| `PUBLIC_CONTRIBUTOR` | Reproducible validation/contributor procedure | `docs/FOUNDATION_VALIDATION.md` | No product semantics; yes for validation procedure |
| `PUBLIC_INTEGRATION` | Public integration/provider standards that CDT_Engineer depends on | `MCP_PROVIDER_STANDARD.md` | Yes for integration boundary |

Every public Markdown file declares exactly one `> Documentation class: PUBLIC_*` marker near the top. Public product semantics must never depend on a private document.

## Private development classes

Private files are grouped by purpose rather than treated as architecture authority:

| Class | Purpose | Location pattern |
| --- | --- | --- |
| `PRIVATE_DEV_PLAN` | roadmap, milestone plan, future sequencing | `_private/development/**/PLAN*.md`, project-direction plans |
| `PRIVATE_DEV_AUDIT` | gap analysis, stress-test findings, closure/re-audit reports | `_private/development/*audit*.md`, closure reports |
| `PRIVATE_DEV_ADR` | implementation/project-direction decision history | `_private/development/project-direction/adr/**` |
| `PRIVATE_HANDOFF` | session/agent handoff and current work notes | `_private/development/*HANDOFF*.md` |
| `PRIVATE_BACKLOG` | unresolved engine/provider/product backlog and acceptance tasks | `_private/development/*gap*.md`, backlog records |
| `PRIVATE_EVIDENCE` | customer/source fixtures, locked benchmark evidence, runtime outputs | `_private/fixtures`, `_private/tests`, `_private/runs` |
| `PRIVATE_REFERENCE` | external/reference repositories and protected research sources | `_private/reference/**` |
| `PRIVATE_HISTORY` | superseded snapshots preserved for traceability | `_private/history/**`, `_private/development/archive/**` |

Private ADRs and plans explain **why/how we developed the product**, but do not define current public semantics. When a private decision becomes stable product behavior, its normative result is promoted into `docs/ARCHITECTURE.md`, a public contract/policy, domain pack, catalog contract or software guide. The private source remains historical evidence only.

## Promotion rule

A development document may be promoted to public only when all of the following are true:

1. content is stable enough to be a product invariant or reproducible public procedure;
2. customer/private/runtime-specific evidence is removed or sanitized;
3. no protected standards text, secrets, local paths or private dependencies remain;
4. the public document stands alone and has an explicit documentation class;
5. relevant code/tests/contracts support the claim;
6. roadmap language, temporary status, personal handoff notes and speculative implementation details are removed.

## Demotion rule

Move or rewrite a public document into private development space when its primary value is one of:

- temporary implementation status or test-count snapshot;
- roadmap/milestone sequencing;
- internal audit or postmortem;
- engine/provider backlog;
- experiment notes;
- raw benchmark/customer evidence;
- historical decision narrative that is no longer needed to understand the public contract.

## Source-of-truth hierarchy

When documents disagree, use this order:

```text
public contract/policy/domain schema
→ public canonical architecture
→ public domain/skill/software/catalog package
→ public contributor documentation
→ private ADR/plan/audit/history
```

Private development material may motivate a change, but it cannot silently override a public contract.
