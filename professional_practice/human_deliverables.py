"""Human Deliverables — release-aware professional communication acceptance.
Wing: code | Topic: human-deliverables | Updated: 2026-09-12 22:39
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from execution.completeness_checker import assess_inventory
from execution.release_scope import RELEASE_CLASSES

DELIVERABLE_CATEGORIES=(
    'plans_views',
    'sections_details',
    'datums_references',
    'dimensions_tolerances',
    'notes_specifications_legends',
    'schedules_bom',
    'revision_issue_identity',
    'scale_readability',
    'downstream_usability',
)

CATEGORY_RELEASE_FLOORS={
    'plans_views':'technical_draft',
    'sections_details':'design_review',
    'datums_references':'technical_draft',
    'dimensions_tolerances':'design_review',
    'notes_specifications_legends':'design_review',
    'schedules_bom':'design_review',
    'revision_issue_identity':'technical_draft',
    'scale_readability':'technical_draft',
    'downstream_usability':'design_review',
}

_GATES=frozenset({'hard','score'})
_APPLICABILITY=frozenset({'applicable','not_applicable','unknown'})
_ACCEPTANCE=frozenset({'pass','fail','unknown','not_applicable'})
_IMPLEMENTATION=frozenset({'implemented','missing','not_applicable'})
_VERIFICATION=frozenset({'verified','unverified','not_applicable'})


def _release_index(value: str) -> int:
    if value not in RELEASE_CLASSES:
        raise ValueError(f'invalid release class: {value}')
    return RELEASE_CLASSES.index(value)


def _non_empty_string(value, field: str) -> str:
    if not isinstance(value,str) or not value.strip():
        raise ValueError(f'{field} must be a non-empty string')
    return value


def _evidence_refs(value, requirement_id: str) -> list[str]:
    refs=value.get('evidence_refs',[])
    if not isinstance(refs,list) or any(not isinstance(ref,str) or not ref for ref in refs):
        raise ValueError(f'{requirement_id}: evidence_refs must be a list of non-empty strings')
    return list(refs)


def _dedupe(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def assess_human_deliverables(
    requested_release: str,
    requirements: Sequence[Mapping],
    evidence: Mapping[str,Mapping],
    *,
    package_revision: str,
    source_revision: str,
) -> dict:
    """Assess a human-readable deliverable package without inferring discipline content.

    Domains/skills own what each concrete requirement means. This evaluator enforces
    release-aware category accounting, explicit N/A disposition, hard-gate evidence,
    independent review, revision freshness and score/hard-gate separation.
    """
    requested_index=_release_index(requested_release)
    _non_empty_string(package_revision,'package_revision')
    _non_empty_string(source_revision,'source_revision')
    if isinstance(requirements,(str,bytes)) or not isinstance(requirements,Sequence):
        raise ValueError('deliverable requirements must be a sequence')
    if not isinstance(evidence,Mapping):
        raise ValueError('deliverable evidence must be a mapping')

    required_categories=[
        category for category in DELIVERABLE_CATEGORIES
        if requested_index >= _release_index(CATEGORY_RELEASE_FLOORS[category])
    ]

    seen=set()
    active=[]
    accounted_categories=set()
    hard_accounted_categories=set()
    for requirement in requirements:
        if not isinstance(requirement,Mapping):
            raise ValueError('deliverable requirements must contain mappings')
        requirement_id=_non_empty_string(requirement.get('requirement_id'),'requirement_id')
        if requirement_id in seen:
            raise ValueError(f'duplicate deliverable requirement_id: {requirement_id}')
        seen.add(requirement_id)
        category=requirement.get('category')
        if category not in DELIVERABLE_CATEGORIES:
            raise ValueError(f'{requirement_id}: invalid deliverable category: {category}')
        floor=requirement.get('required_from_release',CATEGORY_RELEASE_FLOORS[category])
        floor_index=_release_index(floor)
        gate=requirement.get('gate','hard')
        if gate not in _GATES:
            raise ValueError(f'{requirement_id}: invalid gate: {gate}')
        _non_empty_string(requirement.get('reviewer_role'),f'{requirement_id}.reviewer_role')
        independent=requirement.get('requires_independent_review',True)
        if not isinstance(independent,bool):
            raise ValueError(f'{requirement_id}: requires_independent_review must be bool')
        if requested_index < floor_index:
            continue
        active.append(requirement)
        accounted_categories.add(category)
        if gate=='hard':
            hard_accounted_categories.add(category)

    blockers=[]
    quality_findings=[]
    for category in required_categories:
        if category not in accounted_categories:
            blockers.append(f'deliverable_category_unaccounted:{category}')
        elif category not in hard_accounted_categories:
            blockers.append(f'deliverable_category_hard_gate_missing:{category}')

    hard_inventory=[]
    score_total=0
    score_pass=0
    applicable_count=0
    not_applicable_count=0

    for requirement in active:
        requirement_id=requirement['requirement_id']
        gate=requirement.get('gate','hard')
        raw=evidence.get(requirement_id)
        if raw is None:
            marker=f'deliverable_evidence_missing:{requirement_id}'
            if gate=='hard':
                blockers.append(marker)
            else:
                quality_findings.append(marker)
                score_total+=1
            continue
        if not isinstance(raw,Mapping):
            raise ValueError(f'{requirement_id}: evidence must be a mapping')

        applicability=raw.get('applicability')
        if applicability not in _APPLICABILITY:
            raise ValueError(f'{requirement_id}: invalid applicability: {applicability}')
        implementation=raw.get('implementation_state')
        verification=raw.get('verification_state')
        acceptance=raw.get('acceptance_state')
        if implementation not in _IMPLEMENTATION:
            raise ValueError(f'{requirement_id}: invalid implementation_state')
        if verification not in _VERIFICATION:
            raise ValueError(f'{requirement_id}: invalid verification_state')
        if acceptance not in _ACCEPTANCE:
            raise ValueError(f'{requirement_id}: invalid acceptance_state')

        reviewer=raw.get('reviewer')
        if not isinstance(reviewer,str) or not reviewer.strip():
            blockers.append(f'deliverable_reviewer_missing:{requirement_id}')
        expected_reviewer_role=requirement['reviewer_role']
        if raw.get('reviewer_role') != expected_reviewer_role:
            blockers.append(f'deliverable_reviewer_role_mismatch:{requirement_id}')
        independent_required=requirement.get('requires_independent_review',True)
        independent=raw.get('independent')
        if not isinstance(independent,bool):
            raise ValueError(f'{requirement_id}: independent must be bool')
        if independent_required and not independent:
            blockers.append(f'deliverable_independent_review_missing:{requirement_id}')
        refs=_evidence_refs(raw,requirement_id)
        if not refs:
            marker=f'deliverable_evidence_reference_missing:{requirement_id}'
            if gate=='hard': blockers.append(marker)
            else: quality_findings.append(marker)

        artifact_revision=raw.get('artifact_revision')
        observed_source_revision=raw.get('source_revision')
        if artifact_revision != package_revision:
            blockers.append(f'deliverable_artifact_revision_stale:{requirement_id}')
        if observed_source_revision != source_revision:
            blockers.append(f'deliverable_source_revision_stale:{requirement_id}')

        if applicability=='unknown':
            blockers.append(f'deliverable_applicability_unknown:{requirement_id}')
            continue

        if applicability=='not_applicable':
            not_applicable_count+=1
            if implementation!='not_applicable' or verification!='not_applicable' or acceptance!='not_applicable':
                blockers.append(f'deliverable_na_state_inconsistent:{requirement_id}')
            reason=raw.get('na_reason')
            approved_by=raw.get('na_approved_by')
            if not isinstance(reason,str) or not reason.strip():
                blockers.append(f'deliverable_na_reason_missing:{requirement_id}')
            if not isinstance(approved_by,str) or not approved_by.strip():
                blockers.append(f'deliverable_na_unapproved:{requirement_id}')
            continue

        applicable_count+=1
        if implementation=='not_applicable' or verification=='not_applicable' or acceptance=='not_applicable':
            blockers.append(f'deliverable_applicable_state_inconsistent:{requirement_id}')

        if gate=='hard':
            hard_inventory.append({
                'item_id':requirement_id,
                'required':True,
                'implementation_state':implementation,
                'verification_state':verification,
            })
            if acceptance=='fail':
                blockers.append(f'deliverable_hard_gate_fail:{requirement_id}')
            elif acceptance=='unknown':
                blockers.append(f'deliverable_hard_gate_unknown:{requirement_id}')
            elif acceptance!='pass':
                blockers.append(f'deliverable_hard_gate_invalid:{requirement_id}')
        else:
            score_total+=1
            if acceptance=='pass' and implementation=='implemented' and verification=='verified':
                score_pass+=1
            else:
                quality_findings.append(f'deliverable_quality_fail:{requirement_id}')

    completeness=assess_inventory(hard_inventory)
    blockers.extend(completeness['reason_codes'])
    blockers=_dedupe(blockers)
    quality_findings=_dedupe(quality_findings)
    quality_score=1.0 if score_total==0 else score_pass/score_total

    return {
        'result':'blocked' if blockers else 'pass',
        'requested_release_target':requested_release,
        'package_revision':package_revision,
        'source_revision':source_revision,
        'required_categories':required_categories,
        'active_requirement_ids':[r['requirement_id'] for r in active],
        'applicable_requirement_count':applicable_count,
        'not_applicable_requirement_count':not_applicable_count,
        'hard_gate_required_count':completeness['required_count'],
        'hard_gate_verified_count':completeness['verified_required_count'],
        'hard_gate_verification_coverage':completeness['required_verification_coverage'],
        'quality_score':quality_score,
        'quality_findings':quality_findings,
        'reason_codes':blockers,
    }
