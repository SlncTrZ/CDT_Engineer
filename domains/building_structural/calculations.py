"""Building Structural bounded deterministic calculation evidence.
Wing: code | Topic: building-structural | Updated: 2026-09-12 22:43

These helpers only evaluate explicitly supplied engineering inputs. They do not
select load factors, derive member resistance, infer material/section data, or
claim whole-structure adequacy.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from domains.guard_primitives import GuardInputError, finite_number

_RESOLVED_EVIDENCE=frozenset({'observed','specified','derived','approved_assumption'})
_ASSUMPTION_STATE='approved_assumption'
_BASIS_SOURCE_CLASSES=frozenset({'standard_derived','project_rule','manufacturer','calculation_method','test_evidence'})
_BASIS_VERIFICATION=frozenset({'verified','metadata_only','unverified'})


def _nonempty_string(value, name: str) -> str:
    if not isinstance(value,str) or not value.strip():
        raise GuardInputError(f'{name} must be a non-empty string')
    return value


def _basis(value, name: str) -> tuple[dict,list[str]]:
    if not isinstance(value,Mapping):
        raise GuardInputError(f'{name} must be a mapping')
    required=('source_class','record_id','record_version','clause_or_rule_ref','verification_state')
    normalized={key:_nonempty_string(value.get(key),f'{name}.{key}') for key in required}
    if normalized['source_class'] not in _BASIS_SOURCE_CLASSES:
        raise GuardInputError(f'{name}.source_class: unsupported source class')
    if normalized['verification_state'] not in _BASIS_VERIFICATION:
        raise GuardInputError(f'{name}.verification_state: unsupported verification state')
    reasons=[]
    if normalized['verification_state']!='verified':
        reasons.append('combination_basis_unverified' if name=='basis' else 'check_basis_unverified')
    return normalized,reasons


def _evidence_state(value, name: str) -> str:
    value=_nonempty_string(value,name)
    if value not in _RESOLVED_EVIDENCE | {'inferred','unknown'}:
        raise GuardInputError(f'{name}: invalid evidence status')
    return value


def evaluate_load_combination(load_cases: Mapping, combination: Mapping) -> dict:
    """Linearly combine supplied action effects using explicit, source-bound factors.

    The function never chooses factors or combinations. A non-verified basis or
    unresolved case evidence blocks the calculation result rather than emitting
    apparently authoritative combined effects.
    """
    if not isinstance(load_cases,Mapping) or not load_cases:
        raise GuardInputError('load_cases must be a non-empty mapping')
    if not isinstance(combination,Mapping):
        raise GuardInputError('combination must be a mapping')
    combination_id=_nonempty_string(combination.get('combination_id'),'combination.combination_id')
    factors=combination.get('factors')
    if not isinstance(factors,Mapping) or not factors:
        raise GuardInputError('combination.factors must be a non-empty mapping')
    basis,basis_reasons=_basis(combination.get('basis'),'basis')

    normalized_cases={}
    for case_id,raw_case in load_cases.items():
        case_id=_nonempty_string(case_id,'load case id')
        if not isinstance(raw_case,Mapping):
            raise GuardInputError(f'load_cases[{case_id}] must be a mapping')
        state=_evidence_state(raw_case.get('evidence_status'),f'load_cases[{case_id}].evidence_status')
        effects=raw_case.get('effects')
        if not isinstance(effects,Mapping) or not effects:
            raise GuardInputError(f'load_cases[{case_id}].effects must be a non-empty mapping')
        normalized_effects={}
        for component,value in effects.items():
            component=_nonempty_string(component,f'load_cases[{case_id}] effect component')
            normalized_effects[component]=finite_number(value,f'load_cases[{case_id}].effects[{component}]')
        normalized_cases[case_id]={'evidence_status':state,'effects':normalized_effects}

    factor_values={}
    for case_id,value in factors.items():
        case_id=_nonempty_string(case_id,'combination factor case id')
        if case_id not in normalized_cases:
            raise GuardInputError(f'combination references missing load case: {case_id}')
        factor_values[case_id]=finite_number(value,f'combination.factors[{case_id}]')

    component_set=None
    for case_id in factor_values:
        components=set(normalized_cases[case_id]['effects'])
        if component_set is None:
            component_set=components
        elif components!=component_set:
            raise GuardInputError('all combined load cases must provide the same effect components')

    reasons=list(basis_reasons)
    limitations=[]
    for case_id in factor_values:
        state=normalized_cases[case_id]['evidence_status']
        if state not in _RESOLVED_EVIDENCE:
            reasons.append(f'load_case_evidence_unresolved:{case_id}')
        elif state==_ASSUMPTION_STATE:
            limitations.append(f'assumption_dependent_load_case:{case_id}')
    if reasons:
        return {
            'result':'blocked',
            'reason_codes':reasons,
            'limitations':limitations,
            'combination_id':combination_id,
        }

    combined={component:0.0 for component in sorted(component_set or set())}
    for case_id,factor in factor_values.items():
        for component,value in normalized_cases[case_id]['effects'].items():
            product=finite_number(factor*value,f'combined_effects[{component}] product:{case_id}')
            combined[component]=finite_number(combined[component]+product,f'combined_effects[{component}] accumulation')
    return {
        'result':'pass',
        'reason_codes':[],
        'limitations':limitations,
        'combination_id':combination_id,
        'combined_effects':combined,
        'calculation_evidence':{
            'case_ids':list(factor_values),
            'factors':factor_values,
            'components':sorted(combined),
            'basis':basis,
        },
    }


def evaluate_demand_capacity_checks(checks: Sequence[Mapping]) -> dict:
    """Compare supplied demand with supplied capacity without deriving resistance.

    `capacity` must already come from an explicit calculation/test/source route.
    This helper only performs a unit-consistent ratio check against an explicit
    caller-supplied limit and therefore cannot establish global structural
    adequacy by itself.
    """
    if isinstance(checks,(str,bytes)) or not isinstance(checks,Sequence) or not checks:
        raise GuardInputError('checks must be a non-empty sequence')
    results=[]
    reasons=[]
    limitations=[]
    seen=set()
    any_fail=False
    any_block=False
    for index,raw in enumerate(checks):
        if not isinstance(raw,Mapping):
            raise GuardInputError('each demand/capacity check must be a mapping')
        check_id=_nonempty_string(raw.get('check_id'),f'checks[{index}].check_id')
        if check_id in seen:
            raise GuardInputError(f'duplicate check_id: {check_id}')
        seen.add(check_id)
        member_id=_nonempty_string(raw.get('member_id'),f'checks[{index}].member_id')
        section_ref=_nonempty_string(raw.get('section_ref'),f'checks[{index}].section_ref')
        material_ref=_nonempty_string(raw.get('material_ref'),f'checks[{index}].material_ref')
        unit=_nonempty_string(raw.get('unit'),f'checks[{index}].unit')
        demand=finite_number(raw.get('demand'),f'checks[{index}].demand')
        capacity=finite_number(raw.get('capacity'),f'checks[{index}].capacity')
        limit=finite_number(raw.get('limit'),f'checks[{index}].limit')
        if capacity<=0:
            raise GuardInputError(f'{check_id}: capacity must be positive')
        if limit<=0:
            raise GuardInputError(f'{check_id}: limit must be positive')
        demand_state=_evidence_state(raw.get('demand_evidence_status'),f'{check_id}.demand_evidence_status')
        capacity_state=_evidence_state(raw.get('capacity_evidence_status'),f'{check_id}.capacity_evidence_status')
        basis,basis_reasons=_basis(raw.get('basis'),'check_basis')
        check_reasons=list(basis_reasons)
        if demand_state not in _RESOLVED_EVIDENCE:
            check_reasons.append(f'demand_evidence_unresolved:{check_id}')
        if capacity_state not in _RESOLVED_EVIDENCE:
            check_reasons.append(f'capacity_evidence_unresolved:{check_id}')
        if demand_state==_ASSUMPTION_STATE or capacity_state==_ASSUMPTION_STATE:
            limitations.append(f'assumption_dependent_check:{check_id}')
        utilization=None if check_reasons else abs(demand)/capacity
        if check_reasons:
            any_block=True
            reasons.extend(check_reasons)
            result='blocked'
        elif utilization>limit+1e-12:
            any_fail=True
            code=f'demand_exceeds_capacity:{check_id}'
            reasons.append(code)
            check_reasons.append(code)
            result='fail'
        else:
            result='pass'
        results.append({
            'check_id':check_id,
            'member_id':member_id,
            'section_ref':section_ref,
            'material_ref':material_ref,
            'unit':unit,
            'demand':demand,
            'capacity':capacity,
            'limit':limit,
            'utilization':utilization,
            'result':result,
            'reason_codes':check_reasons,
            'basis':basis,
        })
    overall='blocked' if any_block else ('fail' if any_fail else 'pass')
    return {'result':overall,'reason_codes':reasons,'limitations':limitations,'checks':results}
