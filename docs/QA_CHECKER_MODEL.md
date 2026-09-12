# QA / Checker Model

Version: 0.1.0 · Updated: 2026-09-12 · Status: architecture baseline.

## Purpose

The Checker provides independent evidence that a deliverable satisfies the frozen Design Basis, applicable rules, domain requirements and delivery contract. The Checker is not a cosmetic review and does not treat successful tool execution as proof of engineering correctness.

## Independence principle

Production QA should separate producer and verifier as much as the environment permits. Early pilots may reuse one Agent in separate role contexts, but the run must preserve role separation and independent measurement. Higher release classes may require a distinct Agent, person, verification path or responsible professional according to the domain rubric.

The Checker must not simply restate mutation receipts, screenshots or the producing role's claims.

## Verification layers

A Checker evaluates, as applicable:

1. **Intent correctness** — deliverable matches the Design Basis and intended use.
2. **Source correctness** — source/dependency hashes, revisions and exclusions are correct.
3. **Engineering correctness** — calculations, dimensions, geometry, topology, interfaces and domain rules are independently checked.
4. **Standards applicability** — exact standard records/editions/applicability and unresolved compliance items are reviewed.
5. **Manufacturability/constructability** — when required, process/access/tolerance/detailing and execution constraints are checked.
6. **Drawing/document correctness** — views, sections, dimensions, notes, scale, legends, schedules/BOM, revisions and readability for the intended human consumer.
7. **Artifact integrity** — native/exchange artifacts reopen as required, hashes are sealed and stale evidence is detected.
8. **Handoff completeness** — unresolved findings, reproduction instructions and revision identity are explicit.

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
- unsupported public engine capability hidden by a bypass.

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
- source completeness and exclusions;
- hierarchy/tags/layers/components;
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

`BLOCKER` prevents the requested release class. `MAJOR` disposition is controlled by the domain rubric/project authority. Unknown critical evidence is not downgraded merely because no failure has yet been observed.

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

`execution.qa_checker` provides deterministic aggregation for hash-bound findings and emits `PASS_FOR_DECLARED_SCOPE`, `BLOCKED`, `FAIL` or `STALE_EVIDENCE`. `PASS_WITH_DOCUMENTED_LIMITATIONS` remains a policy vocabulary item only; the current executable baseline does not emit it. `execution.artifact_evidence` creates minimal hash/version manifests and detects changed artifact identity. These helpers do not perform native measurements or sealing; they only enforce verdict/evidence invariants once real evidence is supplied.
