"""Agent Profile Stage Runner — deterministic acceptance orchestration.
Wing: code | Topic: stage-runner | Updated: 2026-09-12 16:10
"""
from __future__ import annotations

from typing import Mapping

from execution.release_scope import RELEASE_CLASSES, assess_dependencies

_VALID={'pass','fail','unknown','blocked','not_applicable'}
_PRECEDENCE={'blocked':4,'fail':3,'unknown':2,'pass':1,'not_applicable':0}

# Engineering-OS/domain-local semantics are explicit so a same-named global
# fact cannot accidentally bypass a software-bound requirement.
LOCAL_CAPABILITIES=frozenset({
    'execution_environment.compatible_or_typed_blocker',
    'feature.plan',
    'dependency.validate',
    'qa.independent_measure',
    'evidence.source_hashes_verified',
    'evidence.artifact_hash_bound',
    'evidence.sketchup_hash_current',
    'evidence.sketchup_reopen_verified',
    'evidence.round_trip_verified',
})

def _fact(value, *, default_unknown_reason: str) -> dict:
    if value is None:
        return {'result':'unknown','reason_codes':[default_unknown_reason]}
    result=value.get('result','unknown')
    if result not in _VALID:
        raise ValueError(f'invalid result: {result}')
    reasons=value.get('reason_codes',[])
    if not isinstance(reasons,list):
        raise ValueError('reason_codes must be a list')
    return {'result':result,'reason_codes':list(reasons)}

def _combine(facts: list[dict]) -> tuple[str,list[str]]:
    active=[f for f in facts if f['result']!='not_applicable']
    if not active:
        return 'not_applicable',[]
    winner=max(active,key=lambda f:_PRECEDENCE[f['result']])['result']
    reasons=[]
    for f in active:
        if f['result']==winner:
            reasons.extend(f['reason_codes'])
    return winner,list(dict.fromkeys(reasons))


def capability_facts_from_engine_maps(engine_maps: list[Mapping]) -> dict:
    """Project one software's source map into fail-closed source facts.

    Engine maps are source-derived expectations, never runtime PASS evidence.
    Current runtime observations must be supplied separately to ``run_profile``.
    """
    software_ids={m.get('software_id') for m in engine_maps}
    if any(not isinstance(x,str) or not x for x in software_ids):
        raise ValueError('engine map software_id must be a non-empty string')
    if len(software_ids)>1:
        raise ValueError('cross-software capability flattening is not allowed')
    facts={}
    for engine_map in engine_maps:
        software_id=engine_map['software_id']
        for mapping in engine_map.get('capability_mappings',[]):
            semantic=mapping.get('semantic')
            support=mapping.get('support')
            if not semantic:
                continue
            if support=='blocked':
                fact={'result':'blocked','reason_codes':[f'source_map_blocked:{software_id}:{semantic}']}
            elif support=='unproven':
                fact={'result':'blocked','reason_codes':[f'source_map_unproven:{software_id}:{semantic}']}
            elif support=='expected':
                fact={'result':'unknown','reason_codes':[f'runtime_fact_required:{software_id}:{semantic}']}
            else:
                raise ValueError(f'invalid source-map support state: {support}')
            previous=facts.get(semantic)
            if previous is None or _PRECEDENCE[fact['result']]>_PRECEDENCE[previous['result']]:
                facts[semantic]=fact
    return facts


def capability_facts_by_software(engine_maps: list[Mapping]) -> dict[str, dict]:
    """Return fail-closed source facts keyed by software, never merged across engines."""
    result={}
    for engine_map in engine_maps:
        software_id=engine_map.get('software_id')
        if not isinstance(software_id,str) or not software_id:
            raise ValueError('engine map software_id must be a non-empty string')
        if software_id in result:
            raise ValueError(f'duplicate software_id: {software_id}')
        result[software_id]=capability_facts_from_engine_maps([engine_map])
    return result

def _candidate_stage_capability_facts(
    semantics: list[str],
    software_candidates: list[str],
    capabilities_by_software: Mapping[str, Mapping],
) -> list[dict]:
    """Resolve software-bound semantics through one candidate engine for the whole stage.

    A stage may choose one software candidate, but it may not assemble a synthetic
    PASS by taking different required semantics from different engines.
    """
    candidate_assessments=[]
    for software in software_candidates:
        facts=[]
        for semantic in semantics:
            value=capabilities_by_software.get(software,{}).get(semantic)
            facts.append(_fact(value,default_unknown_reason=f'capability_unknown:{software}:{semantic}'))
        result,reasons=_combine(facts)
        candidate_assessments.append({'software':software,'result':result,'reason_codes':reasons})
    if not candidate_assessments:
        return [_fact(None,default_unknown_reason=f'capability_unknown:{semantic}') for semantic in semantics]
    rank={'pass':4,'not_applicable':3,'unknown':2,'blocked':1,'fail':0}
    best=max(candidate_assessments,key=lambda item:rank[item['result']])
    reasons=list(best['reason_codes'])
    if best['result']!='pass':
        reasons.insert(0,f'software_candidate_not_released:{best["software"]}')
    return [{'result':best['result'],'reason_codes':list(dict.fromkeys(reasons))}]

def run_profile(profile: Mapping, *, capabilities: Mapping[str,Mapping] | None = None, stage_checks: Mapping[str,Mapping], capabilities_by_software: Mapping[str,Mapping] | None = None, dependency_states: Mapping[str,Mapping] | None = None) -> dict:
    """Assess stages and release dependencies without invoking native engines."""
    capabilities=capabilities or {}
    capabilities_by_software=capabilities_by_software or {}
    dependency_states=dependency_states or {}
    stages=profile.get('stages',[])
    if not isinstance(stages,list) or not stages:
        raise ValueError('profile requires stages')
    release_target=profile.get('release_target')
    seen=set(); releases={}; output=[]; recommended_targets=[]
    for stage in stages:
        sid=stage.get('stage_id')
        if not isinstance(sid,str) or not sid or sid in seen:
            raise ValueError('stage_id must be unique non-empty string')
        deps=stage.get('depends_on',[])
        if any(dep not in seen for dep in deps):
            raise ValueError(f'{sid}: dependency must reference prior stage')
        cap_facts=[]
        software_candidates=list(stage.get('software_candidates',[]))
        required_capabilities=list(stage.get('required_capabilities',[]))
        local_semantics=[
            semantic for semantic in required_capabilities
            if not software_candidates or semantic in LOCAL_CAPABILITIES
        ]
        software_semantics=[semantic for semantic in required_capabilities if semantic not in local_semantics]
        for semantic in local_semantics:
            cap_facts.append(_fact(capabilities.get(semantic),default_unknown_reason=f'capability_unknown:{semantic}'))
        if software_semantics and software_candidates:
            cap_facts.extend(_candidate_stage_capability_facts(software_semantics,software_candidates,capabilities_by_software))
        else:
            for semantic in software_semantics:
                cap_facts.append(_fact(None,default_unknown_reason=f'capability_unknown:{semantic}'))
        dependency_requirements=stage.get('dependency_requirements',[])
        dependency_assessment=None
        dependency_fact=None
        if dependency_requirements:
            dependency_assessment=assess_dependencies(
                release_target,
                dependency_requirements,
                dependency_states.get(sid,{}),
            )
            dependency_fact={
                'result':dependency_assessment['result'],
                'reason_codes':dependency_assessment['reason_codes'],
            }
            if dependency_assessment['recommended_release_target']:
                recommended_targets.append(dependency_assessment['recommended_release_target'])
        check_fact=_fact(stage_checks.get(sid),default_unknown_reason='stage_check_unknown')
        assessment_inputs=[*cap_facts,check_fact]
        if dependency_fact is not None:
            assessment_inputs.append(dependency_fact)
        assessment_result,assessment_reasons=_combine(assessment_inputs)
        blocked_deps=[dep for dep in deps if releases.get(dep) not in {'pass','not_applicable'}]
        release_reasons=[]
        if blocked_deps:
            release_result='blocked'
            release_reasons=['dependency_not_released',*[f'dependency:{d}:{releases[d]}' for d in blocked_deps]]
        else:
            release_result=assessment_result
            release_reasons=list(assessment_reasons)
        output.append({
            'stage_id':sid,
            'checkpoint':stage.get('checkpoint'),
            'assessment_result':assessment_result,
            'assessment_reason_codes':assessment_reasons,
            'release_result':release_result,
            'release_reason_codes':release_reasons,
            'depends_on':list(deps),
            'dependency_limitations':dependency_assessment['limitations'] if dependency_assessment else [],
            'recommended_release_target':dependency_assessment['recommended_release_target'] if dependency_assessment else None,
        })
        releases[sid]=release_result
        seen.add(sid)
    release_results=[s['release_result'] for s in output if s['release_result']!='not_applicable']
    if not release_results or all(r=='pass' for r in release_results):
        overall='pass'
    elif 'fail' in release_results:
        overall='fail'
    elif 'blocked' in release_results:
        overall='blocked'
    else:
        overall='unknown'
    recommended=None
    if recommended_targets:
        recommended=min(recommended_targets,key=RELEASE_CLASSES.index)
    return {
        'profile_id':profile.get('profile_id'),
        'release_target':release_target,
        'result':overall,
        'recommended_release_target':recommended,
        'stages':output,
    }
