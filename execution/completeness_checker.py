"""Completeness Checker — domain-neutral required-item coverage invariant.
Wing: code | Topic: completeness-qa | Updated: 2026-09-12 20:07
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

_IMPLEMENTATION_STATES=frozenset({'implemented','missing','not_applicable'})
_VERIFICATION_STATES=frozenset({'verified','unverified','not_applicable'})


def assess_inventory(items: Sequence[Mapping]) -> dict:
    """Block required omissions/unverified items without interpreting domain semantics.

    Domains own what belongs in the inventory and what `implemented` means. This helper
    only enforces stable identity and required-item coverage, allowing Architecture,
    Structural and later disciplines to share one omission invariant without a Domain SDK.
    """
    if isinstance(items,(str,bytes)) or not isinstance(items,Sequence):
        raise ValueError('inventory must be a sequence')
    seen=set(); reasons=[]; required_count=0; verified_required=0
    for i,item in enumerate(items):
        if not isinstance(item,Mapping):
            raise ValueError('inventory items must be mappings')
        item_id=item.get('item_id')
        if not isinstance(item_id,str) or not item_id:
            raise ValueError(f'items[{i}].item_id must be a non-empty string')
        if item_id in seen:
            raise ValueError(f'duplicate inventory item_id: {item_id}')
        seen.add(item_id)
        required=item.get('required')
        if not isinstance(required,bool):
            raise ValueError(f'{item_id}: required must be bool')
        implementation=item.get('implementation_state')
        verification=item.get('verification_state')
        if implementation not in _IMPLEMENTATION_STATES:
            raise ValueError(f'{item_id}: invalid implementation_state')
        if verification not in _VERIFICATION_STATES:
            raise ValueError(f'{item_id}: invalid verification_state')
        if not required:
            continue
        required_count+=1
        if implementation=='missing' or implementation=='not_applicable':
            reasons.append(f'required_item_missing:{item_id}')
        if verification!='verified':
            reasons.append(f'required_item_unverified:{item_id}')
        if implementation=='implemented' and verification=='verified':
            verified_required+=1
    coverage=1.0 if required_count==0 else verified_required/required_count
    return {
        'result':'blocked' if reasons else 'pass',
        'reason_codes':reasons,
        'inventory_count':len(items),
        'required_count':required_count,
        'verified_required_count':verified_required,
        'required_verification_coverage':coverage,
    }
