"""Agent Profile Stage Runner — deterministic acceptance orchestration.
Wing: code | Topic: stage-runner | Updated: 2026-09-12 16:10
"""
from __future__ import annotations

from typing import Mapping

_VALID={'pass','fail','unknown','blocked','not_applicable'}
_PRECEDENCE={'blocked':4,'fail':3,'unknown':2,'pass':1,'not_applicable':0}

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
    """Project one software's source map into fail-closed capability facts.

    Cross-software flattening is rejected because equal semantic names do not
    share one runtime truth value. Use ``capability_facts_by_software`` instead.
    """
    software_ids={m.get('software_id','unknown') for m in engine_maps}
    if len(software_ids)>1:
        raise ValueError('cross-software capability flattening is not allowed')
    facts={}
    for engine_map in engine_maps:
        software_id=engine_map.get('software_id','unknown')
        runtime_proof=bool(engine_map.get('source_snapshot',{}).get('runtime_proof',False))
        for mapping in engine_map.get('capability_mappings',[]):
            semantic=mapping.get('semantic')
            support=mapping.get('support')
            if not semantic:
                continue
            if support=='blocked':
                fact={'result':'blocked','reason_codes':[f'source_map_blocked:{software_id}:{semantic}']}
            elif support=='unproven':
                fact={'result':'blocked','reason_codes':[f'source_map_unproven:{software_id}:{semantic}']}
            elif runtime_proof and support=='expected':
                fact={'result':'pass','reason_codes':[]}
            else:
                fact={'result':'unknown','reason_codes':[f'runtime_proof_missing:{software_id}:{semantic}']}
            previous=facts.get(semantic)
            if previous is None or _PRECEDENCE[fact['result']]>_PRECEDENCE[previous['result']]:
                facts[semantic]=fact
    return facts


def capability_facts_by_software(engine_maps: list[Mapping]) -> dict[str, dict]:
    """Return fail-closed source facts keyed by software, never merged across engines."""
    result={}
    for engine_map in engine_maps:
        software_id=engine_map.get('software_id','unknown')
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

def run_profile(profile: Mapping, *, capabilities: Mapping[str,Mapping] | None = None, stage_checks: Mapping[str,Mapping], capabilities_by_software: Mapping[str,Mapping] | None = None) -> dict:
    """Assess stages and release dependencies without invoking native engines."""
    capabilities=capabilities or {}
    capabilities_by_software=capabilities_by_software or {}
    stages=profile.get('stages',[])
    if not isinstance(stages,list) or not stages:
        raise ValueError('profile requires stages')
    seen=set(); releases={}; output=[]
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
        software_bound={
            semantic
            for software in software_candidates
            for semantic in capabilities_by_software.get(software,{})
        }
        local_semantics=[semantic for semantic in required_capabilities if semantic not in software_bound and semantic in capabilities]
        software_semantics=[semantic for semantic in required_capabilities if semantic not in local_semantics]
        for semantic in local_semantics:
            cap_facts.append(_fact(capabilities.get(semantic),default_unknown_reason=f'capability_unknown:{semantic}'))
        if software_semantics and software_candidates and capabilities_by_software:
            cap_facts.extend(_candidate_stage_capability_facts(software_semantics,software_candidates,capabilities_by_software))
        else:
            for semantic in software_semantics:
                cap_facts.append(_fact(None,default_unknown_reason=f'capability_unknown:{semantic}'))
        check_fact=_fact(stage_checks.get(sid),default_unknown_reason='stage_check_unknown')
        assessment_result,assessment_reasons=_combine([*cap_facts,check_fact])
        blocked_deps=[dep for dep in deps if releases.get(dep)!='pass']
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
        })
        releases[sid]=release_result
        seen.add(sid)
    release_results=[s['release_result'] for s in output if s['release_result']!='not_applicable']
    if not release_results or all(r=='pass' for r in release_results):
        overall='pass'
    elif 'blocked' in release_results:
        overall='blocked'
    elif 'fail' in release_results:
        overall='fail'
    else:
        overall='unknown'
    return {'profile_id':profile.get('profile_id'),'release_target':profile.get('release_target'),'result':overall,'stages':output}
