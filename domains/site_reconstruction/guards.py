"""Site Reconstruction deterministic geometry and registration guards.

These functions implement only measurable domain invariants. They do not call
native CAD/DCC APIs and they do not invent project tolerances.
"""
from __future__ import annotations

import math
from typing import Iterable, Mapping, Sequence

from domains.guard_primitives import GuardInputError, finite_number, unit_ratio

_EPS=1e-12

def _matrix4(values: Sequence[float]) -> tuple[tuple[float,...],...]:
    if len(values)!=16:
        raise GuardInputError('transform must contain 16 finite numeric values')
    flat=[finite_number(x,f'transform[{i}]') for i,x in enumerate(values)]
    return tuple(tuple(flat[r*4+c] for c in range(4)) for r in range(4))

def _det3(m):
    return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
           -m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
           +m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))

def _column_norms(m):
    return tuple(math.sqrt(sum(m[r][c]**2 for r in range(3))) for c in range(3))

def inspect_affine(transform: Sequence[float], source_unit: str, target_unit: str, *, allow_reflection: bool=False, relative_scale_tolerance: float=1e-8) -> dict:
    """Validate row-major affine matrix, handedness, singularity and unit scale."""
    if not isinstance(allow_reflection,bool):
        raise GuardInputError('allow_reflection must be bool')
    relative_scale_tolerance=finite_number(relative_scale_tolerance,'relative_scale_tolerance')
    if relative_scale_tolerance<0:
        raise GuardInputError('relative_scale_tolerance must be nonnegative')
    m=_matrix4(transform)
    homogeneous_ok=all(abs(m[3][i])<=_EPS for i in range(3)) and abs(m[3][3]-1.0)<=_EPS
    det=_det3(m); singular=abs(det)<=_EPS; reflection=det < -_EPS
    scales=_column_norms(m)
    expected=unit_ratio(source_unit,target_unit)
    scale_ok=all(abs(s-expected)<=max(_EPS,abs(expected)*relative_scale_tolerance) for s in scales)
    reasons=[]
    if not homogeneous_ok: reasons.append('invalid_homogeneous_row')
    if singular: reasons.append('singular_transform')
    if reflection and not allow_reflection: reasons.append('unexplained_reflection')
    if not scale_ok: reasons.append('unit_scale_mismatch_or_duplicate_scaling')
    return {'result':'pass' if not reasons else 'fail','reason_codes':reasons,'determinant_3x3':det,'reflection':reflection,'singular':singular,'axis_scales':list(scales),'expected_unit_scale':expected,'unit_scale_consistent':scale_ok,'homogeneous_row_valid':homogeneous_ok}

def compose_affine(*transforms: Sequence[float]) -> list[float]:
    """Compose matrices in written order: compose(T,R,S) yields T*R*S."""
    out=_matrix4([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
    for values in transforms:
        b=_matrix4(values)
        out=tuple(tuple(sum(out[r][k]*b[k][c] for k in range(4)) for c in range(4)) for r in range(4))
    return [out[r][c] for r in range(4) for c in range(4)]

def apply_affine_point(transform: Sequence[float], point: Sequence[float]) -> list[float]:
    if len(point)!=3:
        raise GuardInputError('point must contain 3 finite numeric values')
    xyz=tuple(finite_number(x,f'point[{i}]') for i,x in enumerate(point))
    m=_matrix4(transform); v=(*xyz,1.0)
    out=[sum(m[r][c]*v[c] for c in range(4)) for r in range(4)]
    if abs(out[3])<=_EPS: raise GuardInputError('transform produced invalid homogeneous point')
    return [out[i]/out[3] for i in range(3)]

def _planar_noncollinear(points: Sequence[Mapping]) -> bool:
    if len(points)<3: return False
    xy=[p['source'][:2] for p in points]
    for i in range(len(xy)-2):
        for j in range(i+1,len(xy)-1):
            for k in range(j+1,len(xy)):
                area=(xy[j][0]-xy[i][0])*(xy[k][1]-xy[i][1])-(xy[j][1]-xy[i][1])*(xy[k][0]-xy[i][0])
                if abs(area)>_EPS: return True
    return False

def _residuals(transform, points):
    vals=[]
    for p in points:
        actual=apply_affine_point(transform,p['source']); target=p['target']
        if len(target)!=3: raise GuardInputError('target point must have 3 values')
        target_xyz=tuple(finite_number(x,f'target[{i}]') for i,x in enumerate(target))
        vals.append(math.sqrt(sum((actual[i]-target_xyz[i])**2 for i in range(3))))
    return vals

def evaluate_registration(transform: Sequence[float], controls: Sequence[Mapping], holdouts: Sequence[Mapping], tolerance: Mapping, target_unit: str) -> dict:
    """Evaluate SITE-03 without fitting or inventing an acceptance tolerance."""
    unit_ratio(target_unit,target_unit)
    if not controls or not holdouts: raise GuardInputError('controls and independent holdouts are required')
    control_res=_residuals(transform,controls); holdout_res=_residuals(transform,holdouts)
    max_control=max(control_res); max_holdout=max(holdout_res); reasons=[]
    if not _planar_noncollinear(controls): reasons.append('degenerate_controls')
    if reasons:
        result='fail'
    elif tolerance.get('status')!='approved':
        result='unknown'; reasons.append('approved_tolerance_unresolved')
    else:
        value=finite_number(tolerance.get('value'),'approved tolerance'); unit=tolerance.get('unit')
        if value<=0:
            raise GuardInputError('approved tolerance requires positive value and supported unit')
        limit=value*unit_ratio(unit,target_unit)
        if max_control>limit+_EPS: reasons.append('control_residual_exceeds_tolerance')
        if max_holdout>limit+_EPS: reasons.append('holdout_residual_exceeds_tolerance')
        result='fail' if reasons else 'pass'
    return {'result':result,'reason_codes':reasons,'control_residuals':control_res,'holdout_residuals':holdout_res,'max_control_residual':max_control,'max_holdout_residual':max_holdout,'target_unit':target_unit}

def validate_nested_graph(graph: Mapping[str, Sequence[str]], roots: Iterable[str], traversal_budget: int) -> dict:
    """Reject nested-block cycles and traversal truncation deterministically."""
    if isinstance(traversal_budget,bool) or not isinstance(traversal_budget,int) or traversal_budget<=0: raise GuardInputError('traversal_budget must be a positive integer')
    if not isinstance(graph,Mapping):
        raise GuardInputError('graph must be a mapping of node to child sequence')
    if isinstance(roots,(str,bytes)) or not isinstance(roots,Iterable):
        raise GuardInputError('roots must be an iterable of node ids')
    root_list=list(roots)
    if any(not isinstance(root,str) or not root for root in root_list):
        raise GuardInputError('roots must contain non-empty string node ids')
    for node,children in graph.items():
        if not isinstance(node,str) or not node:
            raise GuardInputError('graph node ids must be non-empty strings')
        if isinstance(children,(str,bytes)) or not isinstance(children,Sequence):
            raise GuardInputError('graph children must be a sequence of node ids')
        if any(not isinstance(child,str) or not child for child in children):
            raise GuardInputError('graph children must contain non-empty string node ids')
    visited=set(); active=set(); count=0; reasons=[]
    def walk(node):
        nonlocal count
        if reasons: return
        if node in active:
            reasons.append('cycle_detected'); return
        if node in visited: return
        if count>=traversal_budget:
            reasons.append('traversal_budget_exceeded'); return
        count+=1; active.add(node)
        for child in graph.get(node,[]): walk(child)
        active.remove(node); visited.add(node)
    for root in root_list:
        walk(root)
        if reasons: break
    return {'result':'pass' if not reasons else 'fail','reason_codes':reasons,'visited_count':count,'traversal_budget':traversal_budget}
