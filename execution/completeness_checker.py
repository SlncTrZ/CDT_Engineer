"""Completeness Checker — domain-neutral required-item coverage invariant.
Wing: code | Topic: completeness-qa | Updated: 2026-09-12 20:07
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

_IMPLEMENTATION_STATES=frozenset({'implemented','missing','not_applicable'})
_VERIFICATION_STATES=frozenset({'verified','unverified','not_applicable'})

# Shared layered-inventory vocabulary: every domain freezes layers (including
# background/occluded/off layers) before mutation so a layout/photo-to-3D job
# cannot silently drop what a foreground layer was covering.
LAYER_VISIBILITY=frozenset({'visible','occluded','off','absent'})
EVIDENCE_STATES=frozenset({'observed','specified','derived','inferred','unknown','approved_assumption'})


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


def assess_layer_ledger(frozen: Sequence[Mapping], final: Mapping) -> dict:
    """Block dropped or unresolved background/occluded layers across a handoff.

    The engineer's decomposition habit as executable invariant: before any
    layout/photo-to-3D mutation the Agent freezes every layer — including
    background layers a foreground layer covers. After mutation the final
    inventory is compared against that frozen ledger:

    - a required item absent from ``final`` is ``required_item_dropped``;
    - a required item unbuilt/unverified keeps the ``assess_inventory`` gates;
    - a required item that was ``occluded``/``off``/``absent`` at freeze time
      with ``unknown``/``inferred`` evidence stays
      ``required_item_occluded_unresolved`` until it is re-observed
      (``observed``/``specified``/``derived``) or explicitly approved
      (``approved_assumption``). Occlusion is never evidence of absence.

    Scope reduction stays explicit: mark the item ``required=False`` with a
    recorded exclusion instead of deleting it from the ledger.
    """
    if isinstance(frozen,(str,bytes)) or not isinstance(frozen,Sequence):
        raise ValueError('frozen ledger must be a sequence')
    if not isinstance(final,Mapping):
        raise ValueError('final inventory must be a mapping')
    seen=set(); reasons=[]; required_count=0; carried_required=0
    for i,item in enumerate(frozen):
        if not isinstance(item,Mapping):
            raise ValueError('frozen ledger items must be mappings')
        item_id=item.get('item_id')
        if not isinstance(item_id,str) or not item_id:
            raise ValueError(f'frozen[{i}].item_id must be a non-empty string')
        if item_id in seen:
            raise ValueError(f'duplicate frozen item_id: {item_id}')
        seen.add(item_id)
        layer_id=item.get('layer_id')
        if not isinstance(layer_id,str) or not layer_id:
            raise ValueError(f'{item_id}: layer_id must be a non-empty string')
        visibility=item.get('visibility')
        if visibility not in LAYER_VISIBILITY:
            raise ValueError(f'{item_id}: invalid visibility')
        evidence=item.get('evidence_state')
        if evidence not in EVIDENCE_STATES:
            raise ValueError(f'{item_id}: invalid evidence_state')
        required=item.get('required')
        if not isinstance(required,bool):
            raise ValueError(f'{item_id}: required must be bool')
        if not required:
            continue
        required_count+=1
        if visibility in ('occluded','off','absent') and evidence in ('unknown','inferred'):
            reasons.append(f'required_item_occluded_unresolved:{item_id}')
            continue
        state=final.get(item_id)
        if state is None:
            reasons.append(f'required_item_dropped:{item_id}')
            continue
        if not isinstance(state,Mapping):
            raise ValueError(f'final[{item_id}] must be a mapping')
        implementation=state.get('implementation_state')
        verification=state.get('verification_state')
        if implementation not in _IMPLEMENTATION_STATES:
            raise ValueError(f'final[{item_id}]: invalid implementation_state')
        if verification not in _VERIFICATION_STATES:
            raise ValueError(f'final[{item_id}]: invalid verification_state')
        item_ok=True
        if implementation=='missing' or implementation=='not_applicable':
            reasons.append(f'required_item_missing:{item_id}')
            item_ok=False
        if verification!='verified':
            reasons.append(f'required_item_unverified:{item_id}')
            item_ok=False
        if item_ok:
            carried_required+=1
    coverage=1.0 if required_count==0 else carried_required/required_count
    return {
        'result':'blocked' if reasons else 'pass',
        'reason_codes':reasons,
        'inventory_count':len(seen),
        'required_count':required_count,
        'verified_required_count':carried_required,
        'required_verification_coverage':coverage,
    }
