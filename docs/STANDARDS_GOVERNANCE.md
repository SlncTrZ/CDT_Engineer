# Versioned Standards Governance and Registry

> Documentation class: PUBLIC_POLICY

Version: 0.2.0 · Updated: 2026-09-12 · Scope: TCVN / QCVN / ISO / IEC / ASME and other normative or project-controlled sources.

This policy defines standards identity, access, applicability, derived engineering rules and historical reproducibility. It does not assert that any particular edition applies or that a design/model complies merely because a standard is present in the registry.

## 1. Standards are first-class evidence

A production compliance conclusion requires an explicit chain:

```text
project purpose/jurisdiction
→ exact normative source + edition
→ applicability decision
→ clause/requirement mapping
→ derived rule/calculation implementation
→ measurement/evidence
→ reviewer disposition
```

A standard family name alone is never enough.

## 2. Registry structure

Target logical structure:

```text
standards/
  registry/
    <issuer-or-family>/
      <standard-record>.*
  applicability/
    <project-or-domain-policy>.*
  derived-rules/
    <domain>/
```

Only introduce files/directories when an actual verified standard/rule is added. Protected normative full text belongs in controlled storage when license/access terms require it; public repository records contain permitted metadata, clause references and original derived logic.

## 3. Required standard record

| Field | Requirement |
| --- | --- |
| `standard_id`, designation, title, issuer | Exact identity, not merely TCVN/ISO/IEC/ASME |
| edition/date | Exact edition; never implicit `latest` |
| amendments/corrigenda | Explicit selected changes |
| jurisdiction/status | Regulatory/project/industry context and legal/normative status where known |
| source | Authoritative publisher/catalog locator and authorized document locator |
| source_hash/retrieved_at | Bind consulted content when full text is available |
| verification_status | metadata_only / source_verified / content_verified / superseded / unavailable |
| applicability_scope | Disciplines, artifact/process, project conditions and exclusions |
| clauses | Applicable clause IDs/sections mapped to derived rule IDs |
| units | Source unit conventions and conversion requirements |
| license_access | Access/reproduction constraints |
| supersedes/record_version | Historical version lineage |
| selected_by/reviewed_by | Responsible selection/review authority |
| decision_reason | Why this edition/source applies or does not apply |

A registry record is immutable in historical meaning: corrections/evolution produce a new record/version rather than silently changing an old run's compliance basis.

## 4. Applicability decision

Applicability is project- and deliverable-specific. The decision records:

- jurisdiction/authority;
- discipline and lifecycle stage;
- project/customer specifications;
- artifact/process being evaluated;
- inclusion/exclusion and precedence rules;
- effective dates/conditions where relevant;
- conflicts with other selected requirements;
- responsible reviewer and rationale.

Unknown source, edition, required clause or applicability results in `unknown/blocked` compliance assessment. Bounded concept/reconstruction work may continue only when the workflow explicitly allows it and does not emit a compliance PASS.

## 5. Derived engineering rules

CDT_Engineer should encode repeatable compliance logic as original deterministic rules/calculations where possible. Each derived rule records:

```text
rule_id/version
domain/skill
standard_record_id/version
clause/reference
interpretation/applicability notes
input definitions + units
formula/decision logic
tolerance/threshold provenance
positive/negative tests
required evidence
review authority
```

Do not copy restricted standards text unnecessarily. A rule summary must preserve enough provenance for an authorized reviewer to compare the implementation against the normative source.

Internal engineering heuristics are labeled `internal_policy` or `project_rule`; never relabel them as TCVN/QCVN/ISO/IEC/ASME requirements.

## 6. Selection and conflict resolution

1. Freeze project purpose, jurisdiction, lifecycle and deliverables in the Design Basis.
2. Resolve exact source and edition from authoritative material.
3. Evaluate applicability for the selected domain/skill/output.
4. Map only relevant requirements into versioned derived rules.
5. Resolve conflicts explicitly with responsible authority. Never average tolerances or silently prefer a standards family.
6. Pin the selection before compliance execution.
7. A later standards change invalidates only affected decisions/evidence and triggers targeted re-review.

## 7. Project/customer rules

Not all authoritative requirements are public standards. Manufacturer data, owner specifications, project technical specifications and approved design criteria may outrank generic defaults for a particular job. They use the same provenance/applicability discipline and are identified by source class.

The Design Basis records precedence and conflict decisions.

## 8. Legal/professional boundary

CDT_Engineer may calculate, map, verify and prepare a standards evidence package, but it does not self-declare legal authority or professional certification. Jurisdiction-specific responsibility, approval and signature remain explicit human/organizational actions.

The product target is evidence sufficient for accountable professional review.

## 9. Verification gate

Registry/derived-rule tests must cover at least:

- applicable source/edition;
- excluded/not-applicable source;
- conflicting requirements;
- superseded edition with historical replay;
- unavailable/protected source;
- unit conversion;
- missing clause mapping;
- changed standard invalidating affected evidence but not unrelated results.

A benchmark must be able to reproduce the exact historical standards basis even after the registry evolves.
