"""Release Scope Policy — fail-closed semantic dependency resolution.
Wing: code | Topic: release-scope | Updated: 2026-09-12 19:46
"""
from __future__ import annotations

from typing import Mapping, Sequence

RELEASE_CLASSES=(
    'concept',
    'technical_draft',
    'design_review',
    'fabrication_or_construction_candidate',
    'ready_for_professional_review',
)
DEPENDENCY_STATES=frozenset({
    'resolved',
    'custom_allowed',
    'proxy_allowed_for_scope',
    'reduced_scope',
    'blocked',
})


def _release_index(value: str) -> int:
    if value not in RELEASE_CLASSES:
        raise ValueError(f'invalid release class: {value}')
    return RELEASE_CLASSES.index(value)


def _reason_codes(value: Mapping) -> list[str]:
    reasons=value.get('reason_codes',[])
    if not isinstance(reasons,list) or any(not isinstance(x,str) or not x for x in reasons):
        raise ValueError('dependency reason_codes must be a list of non-empty strings')
    return list(reasons)


def _maximum_release(requirement: Mapping, fact: Mapping, state: str) -> str | None:
    if state=='proxy_allowed_for_scope':
        maximum=fact.get('maximum_release',requirement.get('proxy_allowed_through','concept'))
    elif state=='reduced_scope':
        maximum=fact.get('maximum_release')
        if maximum is None:
            raise ValueError('reduced_scope dependency requires maximum_release')
    else:
        return None
    _release_index(maximum)
    return maximum


def assess_dependencies(
    requested_release: str,
    requirements: Sequence[Mapping],
    states: Mapping[str,Mapping],
) -> dict:
    """Assess semantic/skill/catalog/evidence dependencies for one requested release.

    A stronger requested release is never silently downgraded to PASS. When an explicit
    proxy/reduced-scope path exists, the caller receives a recommended lower target and
    must re-run/re-plan that scope deliberately.
    """
    requested_index=_release_index(requested_release)
    if not isinstance(requirements,Sequence) or isinstance(requirements,(str,bytes)):
        raise ValueError('dependency requirements must be a sequence')
    if not isinstance(states,Mapping):
        raise ValueError('dependency states must be a mapping')

    seen=set()
    blockers=[]
    limitations=[]
    reduction_candidates=[]
    active_ids=[]

    for requirement in requirements:
        dependency_id=requirement.get('dependency_id')
        if not isinstance(dependency_id,str) or not dependency_id:
            raise ValueError('dependency_id must be a non-empty string')
        if dependency_id in seen:
            raise ValueError(f'duplicate dependency_id: {dependency_id}')
        seen.add(dependency_id)
        required_from=requirement.get('required_from_release','concept')
        if requested_index < _release_index(required_from):
            continue
        active_ids.append(dependency_id)

        raw=states.get(dependency_id)
        if raw is None:
            blockers.append(f'dependency_state_unknown:{dependency_id}')
            continue
        if not isinstance(raw,Mapping):
            raise ValueError(f'{dependency_id}: dependency state must be a mapping')
        state=raw.get('state')
        if state not in DEPENDENCY_STATES:
            raise ValueError(f'{dependency_id}: invalid dependency state: {state}')
        reasons=_reason_codes(raw)

        if state=='resolved':
            continue
        if state=='custom_allowed':
            limitations.append(f'custom_allowed:{dependency_id}')
            limitations.extend(reasons)
            continue
        if state=='blocked':
            blockers.append(f'dependency_blocked:{dependency_id}')
            blockers.extend(reasons)
            continue

        maximum=_maximum_release(requirement,raw,state)
        assert maximum is not None
        maximum_index=_release_index(maximum)
        marker='proxy' if state=='proxy_allowed_for_scope' else 'reduced_scope'
        if requested_index <= maximum_index:
            limitations.append(f'{marker}:{dependency_id}:{maximum}')
            limitations.extend(reasons)
            continue
        blockers.append(f'scope_reduction_required:{dependency_id}:{maximum}')
        blockers.extend(reasons)
        reduction_candidates.append(maximum)

    recommended=None
    if reduction_candidates:
        recommended=min(reduction_candidates,key=_release_index)
    result='blocked' if blockers else 'pass'
    return {
        'result':result,
        'requested_release_target':requested_release,
        'effective_release_target':requested_release if result=='pass' else None,
        'recommended_release_target':recommended,
        'active_dependencies':active_ids,
        'limitations':list(dict.fromkeys(limitations)),
        'reason_codes':list(dict.fromkeys(blockers)),
    }
