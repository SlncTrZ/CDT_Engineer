# QA / Checker Model

> Documentation class: PUBLIC_POLICY

Version: 0.2.0 · Updated: 2026-09-12 · Status: public policy baseline.

## Purpose

The Checker provides independent evidence that a deliverable satisfies the frozen Design Basis, applicable rules, domain requirements and delivery contract. The Checker is not a cosmetic review and does not treat successful tool execution as proof of engineering correctness.

## Independence principle

Production QA should separate producer and verifier as much as the environment permits. Early pilots may reuse one Agent in separate role contexts, but the run must preserve role separation and independent measurement. Higher release classes may require a distinct Agent, person, verification path or responsible professional according to the domain rubric.

The Checker must not simply restate mutation receipts, screenshots or the producing role's claims.

## Verification layers

Checker evidence must preserve the difference between engine integrity and professional correctness. A native provider reporting a clean file/topology or successful save is not a domain PASS.

A Checker evaluates, as applicable:

1. **Intent correctness** — deliverable matches the Design Basis and intended use.
2. **Source correctness** — source/dependency hashes, revisions and exclusions are correct.
3. **Engine integrity** — native object/document state, generic topology/integrity, receipts, save/reopen and runtime contract behavior are valid.
4. **Domain engineering correctness** — semantic entities/systems, calculations, dimensions, domain relationships/topology and domain rules are independently checked.
5. **Completeness** — the frozen requirement/feature/detail inventory is compared with final implementation/verification state so omitted critical content is detected.
6. **Cross-discipline/interface correctness** — required discipline handoffs and relationships are independently checked rather than inferred from one model.
7. **Standards applicability** — exact standard records/editions/applicability and unresolved compliance items are reviewed.
8. **Manufacturability/constructability** — when required, process/access/tolerance/detailing and execution constraints are checked.
9. **Drawing/document correctness** — views, sections, dimensions, notes, scale, legends, schedules/BOM, revisions and readability for the intended human consumer.
10. **Artifact integrity** — native/exchange artifacts reopen as required, hashes are sealed and stale evidence is detected.
11. **Handoff completeness** — unresolved findings, dependency/scope limitations, reproduction instructions and revision identity are explicit.

## Hard gates vs scores

Review rubrics may use scores for quality prioritization, but a score cannot override a hard gate. Examples of hard gates include:

- unresolved critical source dependency;
- unapproved critical tolerance/load/material/process input;
- missing required standard applicability decision;
- invalid/singular coordinate transform;
- wrong scale/units;
- missing native/fabrication/construction deliverable;
- failed independent dimension/topology/level measurement;
- stale artifact hash;
- required drawing information missing;
- unsupported public engine capability hidden by a bypass;
- missing required semantic skill/catalog/library/cross-discipline dependency hidden by primitive/proxy substitution;
- required item omitted from the frozen feature/detail/requirement inventory;
- generic engine integrity PASS while a domain relationship/interface hard gate fails.
- an active human-deliverable family omitted, represented only by score/polish, or marked N/A without reviewed reason/evidence/revision identity;
- required human-deliverable evidence bound to the wrong reviewer role, non-independent review where independence is required, or stale source/artifact revision.

## Evidence requirements

A Checker finding records:

```text
finding_id
rule/requirement reference
expected value/state
measured value/state
unit/tolerance
measurement method
artifact hash/version
independent evidence reference
severity
result: pass | fail | unknown | not_applicable
reviewer/role
```

Screenshots are supplementary. Where a property can be measured deterministically, the evidence should include that measurement.

## Discipline-specific QA examples

### Architecture / site / landscape

- coordinates, levels, scale and registration;
- space/dimension/circulation requirements;
- source/feature/detail completeness and exclusions;
- semantic hierarchy, hosted openings, component/system resolution and repeated-instance identity;
- architecture/structural and other declared discipline interfaces;
- human-readable plans/sections/elevations where required;
- native model reopen and transfer fidelity.

### Mechanical / manufacturing

- critical dimensions, fits/tolerances and datums;
- feature/hole/thread/topology verification;
- material/process/manufacturability constraints;
- assembly interfaces/clearances where applicable;
- shop drawing views/sections/details/notes/BOM;
- native and required neutral/export artifacts.

### Civil / infrastructure

- alignments, coordinates, chainage/stations;
- existing/design levels, grades/cross-falls;
- drainage direction/capacity rules when implemented;
- plan/profile/cross-sections/details;
- interfaces, constructability and drawing readability.

### Electrical / electronics / embedded

Future verticals must define equivalent independent checks for ratings, connectivity, interfaces, calculation results, BOM/component constraints, firmware/hardware contracts and test evidence rather than inheriting CAD-centric QA.

## Finding severity

Recommended minimum levels:

```text
BLOCKER
MAJOR
MINOR
OBSERVATION
```

`BLOCKER` prevents the requested release class. `MAJOR` disposition is controlled by the domain rubric/project authority. The executable baseline has no waiver/disposition field, so an unresolved `MAJOR` finding returns `BLOCKED` until it is resolved, reclassified or dispositioned outside the checker and represented by a non-unknown finding. Unknown critical evidence is not downgraded merely because no failure has yet been observed.

## Release verdict

Suggested verdicts:

```text
PASS_FOR_DECLARED_SCOPE
PASS_WITH_DOCUMENTED_LIMITATIONS
BLOCKED
FAIL
STALE_EVIDENCE
```

The highest CDT_Engineer target is `ready_for_professional_review`. Legal/professional issue/signature remains an explicit external authority action.

## Seal and post-review mutation

The Checker binds its verdict to exact artifact hashes/versions. If a checked artifact changes, affected findings become stale and must not be reused as PASS. Reopen/measurement after final save/seal is required where the domain/output contract demands it.

## Executable baseline

`execution.qa_checker` provides deterministic aggregation for hash-bound findings and emits `PASS_FOR_DECLARED_SCOPE`, `BLOCKED`, `FAIL` or `STALE_EVIDENCE`. Finding IDs must be unique within one checker run; duplicate IDs are rejected because they make evidence/reason references ambiguous. Unknown `BLOCKER` and `MAJOR` findings block the baseline release; any explicit `fail` remains `FAIL`. `PASS_WITH_DOCUMENTED_LIMITATIONS` remains a policy vocabulary item only; the current executable baseline does not emit it. `execution.artifact_evidence` creates minimal hash/version manifests and detects changed artifact identity. These helpers do not perform native measurements or sealing; they only enforce verdict/evidence invariants once real evidence is supplied.

`professional_practice.human_deliverables` provides the release-aware communication baseline: active categories require explicit hard-gate accounting, reviewed N/A dispositions, evidence references, reviewer-role/independence evidence and matching source/artifact revisions. Its quality score is deliberately separate and cannot override hard blockers.
