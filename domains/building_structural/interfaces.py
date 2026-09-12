"""Building Structural Architecture↔Structural interface guards.
Wing: code | Topic: building-structural | Updated: 2026-09-12 22:44

This module intentionally implements only the cross-discipline pair consumed by
the current Building Architecture and Building Structural verticals. Additional
pairs require real consumers rather than an empty universal interface framework.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from domains.guard_primitives import GuardInputError

_PAIR=frozenset({'building-architecture','building-structural'})
_ALLOWED_STATUS=frozenset({'open','accepted','rejected','not_applicable'})
_ALLOWED_VERIFICATION=frozenset({'verified','unverified','stale'})


def _text(value, name: str) -> str:
    if not isinstance(value,str) or not value.strip():
        raise GuardInputError(f'{name} must be a non-empty string')
    return value


def evaluate_architecture_structural_interfaces(records: Sequence[Mapping]) -> dict:
    """Require typed ownership, source revision, disposition and independent evidence."""
    if isinstance(records,(str,bytes)) or not isinstance(records,Sequence):
        raise GuardInputError('interface records must be a sequence')
    reasons=[]
    normalized=[]
    seen=set()
    for index,raw in enumerate(records):
        if not isinstance(raw,Mapping):
            raise GuardInputError('each interface record must be a mapping')
        interface_id=_text(raw.get('interface_id'),f'interfaces[{index}].interface_id')
        if interface_id in seen:
            raise GuardInputError(f'duplicate interface_id: {interface_id}')
        seen.add(interface_id)
        from_discipline=_text(raw.get('from_discipline'),f'{interface_id}.from_discipline')
        to_discipline=_text(raw.get('to_discipline'),f'{interface_id}.to_discipline')
        if frozenset({from_discipline,to_discipline})!=_PAIR or from_discipline==to_discipline:
            raise GuardInputError(f'{interface_id}: only Building Architecture↔Building Structural is supported in this lane')
        owner=_text(raw.get('owner_discipline'),f'{interface_id}.owner_discipline')
        if owner not in {from_discipline,to_discipline}:
            raise GuardInputError(f'{interface_id}: owner_discipline must be one of the participating disciplines')
        interface_type=_text(raw.get('interface_type'),f'{interface_id}.interface_type')
        source_revision=_text(raw.get('source_revision'),f'{interface_id}.source_revision')
        required=raw.get('required')
        if not isinstance(required,bool):
            raise GuardInputError(f'{interface_id}.required must be bool')
        status=_text(raw.get('status'),f'{interface_id}.status')
        if status not in _ALLOWED_STATUS:
            raise GuardInputError(f'{interface_id}: unsupported interface status')
        verification=_text(raw.get('verification_state'),f'{interface_id}.verification_state')
        if verification not in _ALLOWED_VERIFICATION:
            raise GuardInputError(f'{interface_id}: unsupported verification state')
        evidence_refs=raw.get('evidence_refs')
        if isinstance(evidence_refs,(str,bytes)) or not isinstance(evidence_refs,Sequence):
            raise GuardInputError(f'{interface_id}.evidence_refs must be a sequence')
        evidence=list(evidence_refs)
        if any(not isinstance(ref,str) or not ref.strip() for ref in evidence):
            raise GuardInputError(f'{interface_id}.evidence_refs must contain non-empty strings')

        item_reasons=[]
        if required and status not in {'accepted','not_applicable'}:
            item_reasons.append(f'required_interface_unresolved:{interface_id}')
        if required and status=='not_applicable':
            if verification!='verified':
                item_reasons.append(f'not_applicable_interface_not_verified:{interface_id}')
            if not evidence:
                item_reasons.append(f'not_applicable_interface_without_evidence:{interface_id}')
        if status=='accepted' and verification!='verified':
            item_reasons.append(f'accepted_interface_not_verified:{interface_id}')
        if status=='accepted' and not evidence:
            item_reasons.append(f'accepted_interface_evidence_missing:{interface_id}')
        if verification=='stale':
            item_reasons.append(f'interface_evidence_stale:{interface_id}')
        reasons.extend(item_reasons)
        normalized.append({
            'interface_id':interface_id,
            'from_discipline':from_discipline,
            'to_discipline':to_discipline,
            'interface_type':interface_type,
            'owner_discipline':owner,
            'required':required,
            'status':status,
            'verification_state':verification,
            'source_revision':source_revision,
            'evidence_refs':evidence,
            'reason_codes':item_reasons,
        })
    return {'result':'blocked' if reasons else 'pass','reason_codes':reasons,'interfaces':normalized}
