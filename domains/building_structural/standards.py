"""Building Structural standards/applicability evidence guard.
Wing: code | Topic: building-structural | Updated: 2026-09-12 22:45

No standard is selected here. The caller supplies exact registry-like records;
this module only checks whether the evidence is strong enough for a compliance
basis. Domain-local placement is intentional until Rule-of-Two justifies a
shared standards runtime primitive.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from domains.guard_primitives import GuardInputError

_VERIFIED_SOURCE=frozenset({'source_verified','content_verified'})
_APPLICABILITY=frozenset({'applicable','not_applicable','unknown','conflict'})


def _text(value, name: str) -> str:
    if not isinstance(value,str) or not value.strip():
        raise GuardInputError(f'{name} must be a non-empty string')
    return value


def evaluate_standard_applicability(records: Sequence[Mapping], *, required_standard_ids: Sequence[str]) -> dict:
    """Fail closed on missing identity, edition, source verification or applicability."""
    if isinstance(records,(str,bytes)) or not isinstance(records,Sequence):
        raise GuardInputError('standards records must be a sequence')
    if isinstance(required_standard_ids,(str,bytes)) or not isinstance(required_standard_ids,Sequence):
        raise GuardInputError('required_standard_ids must be a sequence')
    required=list(required_standard_ids)
    if any(not isinstance(item,str) or not item.strip() for item in required):
        raise GuardInputError('required_standard_ids must contain non-empty strings')
    if len(required)!=len(set(required)):
        raise GuardInputError('required_standard_ids must be unique')

    by_id={}
    reasons=[]
    for index,raw in enumerate(records):
        if not isinstance(raw,Mapping):
            raise GuardInputError('each standard record must be a mapping')
        standard_id=_text(raw.get('standard_id'),f'standards[{index}].standard_id')
        if standard_id in by_id:
            raise GuardInputError(f'duplicate standard_id: {standard_id}')
        record={
            'standard_id':standard_id,
            'record_version':_text(raw.get('record_version'),f'{standard_id}.record_version'),
            'designation':_text(raw.get('designation'),f'{standard_id}.designation'),
            'issuer':_text(raw.get('issuer'),f'{standard_id}.issuer'),
            'edition':_text(raw.get('edition'),f'{standard_id}.edition'),
            'source':_text(raw.get('source'),f'{standard_id}.source'),
            'verification_status':_text(raw.get('verification_status'),f'{standard_id}.verification_status'),
            'applicability_state':_text(raw.get('applicability_state'),f'{standard_id}.applicability_state'),
            'reviewer':_text(raw.get('reviewer'),f'{standard_id}.reviewer'),
            'decision_reason':_text(raw.get('decision_reason'),f'{standard_id}.decision_reason'),
        }
        if record['applicability_state'] not in _APPLICABILITY:
            raise GuardInputError(f'{standard_id}: unsupported applicability_state')
        refs=raw.get('clause_refs')
        if isinstance(refs,(str,bytes)) or not isinstance(refs,Sequence):
            raise GuardInputError(f'{standard_id}.clause_refs must be a sequence')
        record['clause_refs']=list(refs)
        if any(not isinstance(ref,str) or not ref.strip() for ref in record['clause_refs']):
            raise GuardInputError(f'{standard_id}.clause_refs must contain non-empty strings')
        by_id[standard_id]=record

    applicable=[]
    for standard_id in required:
        record=by_id.get(standard_id)
        if record is None:
            reasons.append(f'required_standard_missing:{standard_id}')
            continue
        if record['edition'].strip().lower() in {'latest','current','unspecified','unknown'}:
            reasons.append(f'standard_edition_not_exact:{standard_id}')
        if record['verification_status'] not in _VERIFIED_SOURCE:
            reasons.append(f'standard_source_not_verified:{standard_id}')
        state=record['applicability_state']
        if state=='conflict':
            reasons.append(f'standard_applicability_conflict:{standard_id}')
        elif state=='unknown':
            reasons.append(f'standard_applicability_unknown:{standard_id}')
        elif state=='not_applicable':
            reasons.append(f'required_standard_marked_not_applicable:{standard_id}')
        if state=='applicable' and not record['clause_refs']:
            reasons.append(f'standard_clause_mapping_missing:{standard_id}')
        if state=='applicable' and standard_id not in applicable:
            applicable.append(standard_id)

    return {
        'result':'blocked' if reasons else 'pass',
        'reason_codes':reasons,
        'applicable_standard_ids':applicable if not reasons else [item for item in applicable if not any(code.endswith(f':{item}') for code in reasons)],
        'records':by_id,
    }
