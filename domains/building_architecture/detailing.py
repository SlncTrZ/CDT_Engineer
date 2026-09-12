"""Building Architecture release-aware detail completeness policy.
Wing: code | Topic: architecture-detailing | Updated: 2026-09-12 20:11
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from execution.completeness_checker import assess_inventory
from execution.release_scope import RELEASE_CLASSES

_DESIGN_REVIEW_DETAILS={
    'opening': {'opening.head-jamb-sill-intent'},
    'door': {'door.threshold-intent'},
    'facade_system': {'facade.support-edge-intent'},
    'parapet': {'parapet.roof-junction-intent'},
    'railing': {'railing.support-intent'},
    'stair': {'stair.landing-handrail-intent'},
    'balcony': {'balcony.edge-support-intent'},
}

_CONSTRUCTION_DETAILS={
    'opening': {'opening.head-jamb-sill-detail'},
    'door': {'door.threshold-waterproofing-detail'},
    'facade_system': {'facade.anchor-subframe-detail'},
    'parapet': {'parapet.waterproofing-termination-detail'},
    'railing': {'railing.anchor-detail'},
    'stair': {'stair.landing-handrail-connection-detail'},
    'balcony': {'balcony.edge-waterproofing-detail'},
}


def _families(value: Sequence[str]) -> list[str]:
    if isinstance(value,(str,bytes)) or not isinstance(value,Sequence):
        raise ValueError('system_families must be a sequence')
    result=list(value)
    if any(not isinstance(x,str) or not x for x in result):
        raise ValueError('system_families must contain non-empty strings')
    if len(result)!=len(set(result)):
        raise ValueError('system_families must be unique')
    return result


def required_details_for_release(system_families: Sequence[str], *, release_target: str) -> list[str]:
    """Return release-documentation detail IDs; no regulatory dimensions are implied."""
    families=_families(system_families)
    if release_target not in RELEASE_CLASSES:
        raise ValueError('unsupported release target')
    rank=RELEASE_CLASSES.index(release_target)
    design_review_rank=RELEASE_CLASSES.index('design_review')
    construction_rank=RELEASE_CLASSES.index('fabrication_or_construction_candidate')
    required=set()
    if rank>=design_review_rank:
        for family in families:
            required.update(_DESIGN_REVIEW_DETAILS.get(family,set()))
    if rank>=construction_rank:
        for family in families:
            required.update(_CONSTRUCTION_DETAILS.get(family,set()))
    return sorted(required)


def evaluate_detail_inventory(system_families: Sequence[str], *, release_target: str, items: Sequence[Mapping]) -> dict:
    """Check that release-required system details exist and are independently verified."""
    required=set(required_details_for_release(system_families,release_target=release_target))
    if isinstance(items,(str,bytes)) or not isinstance(items,Sequence):
        raise ValueError('detail inventory must be a sequence')
    by_id={}
    for item in items:
        if not isinstance(item,Mapping):
            raise ValueError('detail inventory items must be mappings')
        item_id=item.get('item_id')
        if not isinstance(item_id,str) or not item_id:
            raise ValueError('detail item_id must be a non-empty string')
        if item_id in by_id:
            raise ValueError(f'duplicate detail item_id: {item_id}')
        by_id[item_id]=dict(item)
        if item.get('required') is True:
            required.add(item_id)

    normalized=[]
    for detail_id in sorted(required):
        source=by_id.get(detail_id,{})
        normalized.append({
            'item_id':detail_id,
            'required':True,
            'implementation_state':source.get('implementation_state','missing'),
            'verification_state':source.get('verification_state','unverified'),
        })
    for item_id,item in by_id.items():
        if item_id in required:
            continue
        normalized.append({
            'item_id':item_id,
            'required':False,
            'implementation_state':item.get('implementation_state','missing'),
            'verification_state':item.get('verification_state','unverified'),
        })

    base=assess_inventory(normalized)
    reasons=[]
    for reason in base['reason_codes']:
        if reason.startswith('required_item_missing:'):
            reasons.append('required_detail_missing:'+reason.split(':',1)[1])
        elif reason.startswith('required_item_unverified:'):
            reasons.append('required_detail_unverified:'+reason.split(':',1)[1])
        else:
            reasons.append(reason)
    return {
        **base,
        'result':'blocked' if reasons else 'pass',
        'reason_codes':reasons,
        'required_detail_ids':sorted(required),
        'release_target':release_target,
    }
