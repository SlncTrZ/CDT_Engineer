"""Mechanical Reconstruction deterministic guards.

Implements measurable domain invariants only. No native CAD calls and no
fabricated tolerances or hidden geometry assumptions.
"""
from __future__ import annotations

import math
from typing import Mapping, Sequence

from domains.guard_primitives import GuardInputError, finite_number, unit_ratio

def evaluate_dimension(nominal: float, measured: float, tolerance: Mapping, unit: str) -> dict:
    """Evaluate one independent dimension without inventing tolerance."""
    unit_ratio(unit,unit)
    nominal=finite_number(nominal,'nominal'); measured=finite_number(measured,'measured')
    deviation=abs(measured-nominal); reasons=[]
    status=tolerance.get('status')
    if status not in {'specified','derived','approved'}:
        return {'result':'unknown','reason_codes':['critical_tolerance_unresolved'],'nominal':nominal,'measured':measured,'deviation':deviation,'unit':unit}
    value=finite_number(tolerance.get('value'),'resolved tolerance'); tol_unit=tolerance.get('unit')
    if value < 0:
        raise GuardInputError('resolved tolerance requires nonnegative value and supported unit')
    limit=value*unit_ratio(tol_unit,unit)
    if deviation>limit+1e-12: reasons.append('dimension_outside_tolerance')
    return {'result':'fail' if reasons else 'pass','reason_codes':reasons,'nominal':nominal,'measured':measured,'deviation':deviation,'tolerance':limit,'unit':unit}

def validate_feature_dag(features: Sequence[Mapping]) -> dict:
    """Validate feature identity/dependencies and return deterministic build order."""
    if isinstance(features,(str,bytes)) or not isinstance(features,Sequence):
        raise GuardInputError('features must be a sequence')
    ids=[]; reasons=[]; deps={}
    for f in features:
        if not isinstance(f,Mapping):
            raise GuardInputError('each feature must be a mapping')
        fid=f.get('id')
        if not isinstance(fid,str) or not fid: raise GuardInputError('feature id required')
        raw_deps=f.get('depends_on',[])
        if isinstance(raw_deps,(str,bytes)) or not isinstance(raw_deps,Sequence):
            raise GuardInputError(f'{fid}: depends_on must be a sequence of feature ids')
        ds=list(raw_deps)
        if any(not isinstance(d,str) or not d for d in ds):
            raise GuardInputError(f'{fid}: dependency ids must be non-empty strings')
        if len(ds)!=len(set(ds)):
            raise GuardInputError(f'{fid}: duplicate dependencies are not allowed')
        ids.append(fid); deps[fid]=ds
    if len(ids)!=len(set(ids)): reasons.append('duplicate_feature_id')
    idset=set(ids)
    for fid, ds in deps.items():
        if fid in ds: reasons.append('self_dependency')
        if any(d not in idset for d in ds): reasons.append('missing_dependency')
    if reasons:
        return {'result':'fail','reason_codes':sorted(set(reasons)),'build_order':[]}
    indeg={i:0 for i in ids}; children={i:[] for i in ids}
    for fid,ds in deps.items():
        indeg[fid]+=len(ds)
        for d in ds: children[d].append(fid)
    ready=[i for i in ids if indeg[i]==0]; order=[]
    while ready:
        node=ready.pop(0); order.append(node)
        for child in children[node]:
            indeg[child]-=1
            if indeg[child]==0: ready.append(child)
    if len(order)!=len(ids): return {'result':'fail','reason_codes':['cycle_detected'],'build_order':order}
    return {'result':'pass','reason_codes':[],'build_order':order}

def evaluate_exactness(*, required: str, representation: str, approved_max_deviation, measured_max_deviation) -> dict:
    """Enforce exact-vs-approximate representation semantics."""
    if required not in {'exact','approximation_allowed'}: raise GuardInputError('unsupported exactness requirement')
    if representation not in {'analytic','sampled'}: raise GuardInputError('unsupported representation')
    if required=='exact':
        if representation!='analytic': return {'result':'fail','reason_codes':['sampled_representation_not_exact']}
        return {'result':'pass','reason_codes':[]}
    if representation=='analytic': return {'result':'pass','reason_codes':[]}
    if approved_max_deviation is None: return {'result':'unknown','reason_codes':['approximation_tolerance_unresolved']}
    approved=finite_number(approved_max_deviation,'approved_max_deviation')
    if approved<0: raise GuardInputError('approved_max_deviation must be nonnegative')
    if measured_max_deviation is None: return {'result':'unknown','reason_codes':['approximation_deviation_unmeasured']}
    measured=finite_number(measured_max_deviation,'measured_max_deviation')
    if measured<0: raise GuardInputError('measured_max_deviation must be nonnegative')
    return {'result':'pass' if measured<=approved+1e-12 else 'fail','reason_codes':[] if measured<=approved+1e-12 else ['approximation_deviation_exceeds_approval'],'approved_max_deviation':approved,'measured_max_deviation':measured}

def evaluate_topology(*, expected_body_count: int, observed_body_count: int, all_bodies_valid: bool, unexpected_cavities: int, missing_required_treatments: Sequence[str]) -> dict:
    """Evaluate independent final topology evidence."""
    counts=(expected_body_count,observed_body_count,unexpected_cavities)
    if any(isinstance(x,bool) or not isinstance(x,int) or x<0 for x in counts):
        raise GuardInputError('counts must be nonnegative integers')
    if not isinstance(all_bodies_valid,bool):
        raise GuardInputError('all_bodies_valid must be bool')
    if isinstance(missing_required_treatments,(str,bytes)) or not isinstance(missing_required_treatments,Sequence):
        raise GuardInputError('missing_required_treatments must be a sequence of strings')
    if any(not isinstance(x,str) or not x for x in missing_required_treatments):
        raise GuardInputError('missing_required_treatments must contain non-empty strings')
    reasons=[]
    if observed_body_count!=expected_body_count: reasons.append('body_count_mismatch')
    if not all_bodies_valid: reasons.append('invalid_solid_topology')
    if unexpected_cavities: reasons.append('unexpected_cavity')
    if missing_required_treatments: reasons.append('missing_required_treatment')
    return {'result':'fail' if reasons else 'pass','reason_codes':reasons,'expected_body_count':expected_body_count,'observed_body_count':observed_body_count,'unexpected_cavities':unexpected_cavities,'missing_required_treatments':list(missing_required_treatments)}
