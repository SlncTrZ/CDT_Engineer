"""QA Checker — deterministic finding aggregation and release verdict.
Wing: code | Topic: qa-checker | Updated: 2026-09-12 14:47
"""
from __future__ import annotations

from typing import Mapping, Sequence
from execution.artifact_evidence import evidence_is_stale

_RESULTS={'pass','fail','unknown','not_applicable'}
_SEVERITIES={'BLOCKER','MAJOR','MINOR','OBSERVATION'}

def checker_verdict(findings: Sequence[Mapping], *, current_artifact_sha256: str) -> dict:
    if not findings:
        return {'verdict':'BLOCKED','reason_codes':['no_checker_findings']}
    stale=[]; blockers=[]; failures=[]; unresolved_majors=[]; seen_ids=set()
    for finding in findings:
        fid=finding.get('finding_id')
        if not isinstance(fid,str) or not fid:
            raise ValueError('finding_id required')
        if fid in seen_ids:
            raise ValueError(f'duplicate finding_id: {fid}')
        seen_ids.add(fid)
        severity=finding.get('severity'); result=finding.get('result')
        if severity not in _SEVERITIES: raise ValueError(f'{fid}: invalid severity')
        if result not in _RESULTS: raise ValueError(f'{fid}: invalid result')
        if evidence_is_stale(finding,current_artifact_sha256=current_artifact_sha256): stale.append(fid)
        if result=='fail': failures.append(fid)
        if severity=='BLOCKER' and result in {'unknown','fail'}: blockers.append(fid)
        if severity=='MAJOR' and result=='unknown': unresolved_majors.append(fid)
    if stale: return {'verdict':'STALE_EVIDENCE','reason_codes':[f'stale:{x}' for x in stale]}
    if failures: return {'verdict':'FAIL','reason_codes':[f'fail:{x}' for x in failures]}
    if blockers or unresolved_majors:
        return {'verdict':'BLOCKED','reason_codes':[*[f'blocker:{x}' for x in blockers],*[f'major_unresolved:{x}' for x in unresolved_majors]]}
    return {'verdict':'PASS_FOR_DECLARED_SCOPE','reason_codes':[]}
