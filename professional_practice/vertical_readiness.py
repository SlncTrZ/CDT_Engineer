"""Vertical Readiness — evidence-gated expansion preparation without production claims.
Wing: code | Topic: vertical-readiness | Updated: 2026-09-12 22:39
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

_REQUIRED_EVIDENCE=(
    'source_evidence',
    'skill_evidence',
    'rule_evidence',
    'benchmark_evidence',
    'reviewer_evidence',
)
_EVIDENCE_STATES=frozenset({'verified','missing','unknown','blocked'})
_FOUNDATION_STATES=frozenset({'resolved','blocked','unknown'})


def _dedupe(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _refs(record: Mapping, evidence_id: str) -> list[str]:
    refs=record.get('evidence_refs',[])
    if not isinstance(refs,list) or any(not isinstance(ref,str) or not ref for ref in refs):
        raise ValueError(f'{evidence_id}: evidence_refs must be a list of non-empty strings')
    return list(refs)


def assess_vertical_readiness(
    vertical_id: str,
    evidence: Mapping[str,Mapping],
    *,
    foundation_dependencies: Sequence[Mapping],
    requested_state: str='pilot_definition',
) -> dict:
    """Assess whether a future vertical has enough evidence to define a real pilot.

    This helper deliberately does not assess provider/core/catalog applicability and never
    emits a production-ready verdict. Agent 4 and later domain/runtime acceptance own any
    stronger claim.
    """
    if not isinstance(vertical_id,str) or not vertical_id.strip():
        raise ValueError('vertical_id must be a non-empty string')
    if not isinstance(evidence,Mapping):
        raise ValueError('vertical evidence must be a mapping')
    if isinstance(foundation_dependencies,(str,bytes)) or not isinstance(foundation_dependencies,Sequence):
        raise ValueError('foundation_dependencies must be a sequence')
    if not isinstance(requested_state,str) or not requested_state:
        raise ValueError('requested_state must be a non-empty string')

    reasons=[]
    verified=[]

    if requested_state!='pilot_definition':
        if requested_state=='production_ready':
            reasons.append('vertical_production_readiness_not_authorized')
        else:
            reasons.append(f'vertical_requested_state_unsupported:{requested_state}')

    for evidence_id in _REQUIRED_EVIDENCE:
        record=evidence.get(evidence_id)
        if record is None:
            reasons.append(f'vertical_evidence_missing:{evidence_id}')
            continue
        if not isinstance(record,Mapping):
            raise ValueError(f'{evidence_id}: evidence must be a mapping')
        state=record.get('state')
        if state not in _EVIDENCE_STATES:
            raise ValueError(f'{evidence_id}: invalid state: {state}')
        refs=_refs(record,evidence_id)
        if state!='verified':
            reasons.append(f'vertical_evidence_{state}:{evidence_id}')
            continue
        if not refs:
            reasons.append(f'vertical_evidence_reference_missing:{evidence_id}')
            continue
        verified.append(evidence_id)

    benchmark=evidence.get('benchmark_evidence')
    if isinstance(benchmark,Mapping) and benchmark.get('state')=='verified':
        positives=benchmark.get('positive_cases')
        negatives=benchmark.get('negative_cases')
        measurable=benchmark.get('measurable_acceptance')
        if not isinstance(positives,int) or isinstance(positives,bool) or positives < 1:
            reasons.append('vertical_benchmark_positive_cases_missing')
        if not isinstance(negatives,int) or isinstance(negatives,bool) or negatives < 1:
            reasons.append('vertical_benchmark_negative_cases_missing')
        if measurable is not True:
            reasons.append('vertical_benchmark_not_measurable')

    reviewer=evidence.get('reviewer_evidence')
    if isinstance(reviewer,Mapping) and reviewer.get('state')=='verified':
        independent=reviewer.get('independent')
        if independent is not True:
            reasons.append('vertical_independent_reviewer_missing')

    seen_dependencies=set()
    resolved_dependencies=[]
    for dependency in foundation_dependencies:
        if not isinstance(dependency,Mapping):
            raise ValueError('foundation_dependencies must contain mappings')
        dependency_id=dependency.get('dependency_id')
        if not isinstance(dependency_id,str) or not dependency_id:
            raise ValueError('foundation dependency_id must be a non-empty string')
        if dependency_id in seen_dependencies:
            raise ValueError(f'duplicate foundation dependency_id: {dependency_id}')
        seen_dependencies.add(dependency_id)
        state=dependency.get('state')
        if state not in _FOUNDATION_STATES:
            raise ValueError(f'{dependency_id}: invalid foundation state: {state}')
        if state=='resolved':
            resolved_dependencies.append(dependency_id)
        else:
            reasons.append(f'vertical_foundation_{state}:{dependency_id}')

    reasons=_dedupe(reasons)
    return {
        'vertical_id':vertical_id,
        'readiness_state':'blocked' if reasons else 'ready_for_pilot_definition',
        'requested_state':requested_state,
        'verified_evidence':verified,
        'resolved_foundation_dependencies':resolved_dependencies,
        'reason_codes':reasons,
        'scope_limitations':[
            'no_provider_runtime_applicability_decision',
            'no_asset_catalog_applicability_decision',
            'no_production_release_claim',
        ],
    }
