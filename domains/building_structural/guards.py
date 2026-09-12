"""Building Structural deterministic intent and coordination guards.
Wing: code | Topic: building-structural | Updated: 2026-09-12 19:54
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from domains.guard_primitives import GuardInputError, finite_number
from execution.completeness_checker import assess_inventory
from execution.release_scope import RELEASE_CLASSES

_EPS=1e-9
_RESOLVED_EVIDENCE=frozenset({'observed','specified','derived','approved_assumption'})
_ALLOWED_EVIDENCE=_RESOLVED_EVIDENCE | {'inferred','unknown'}


def _id(value, name: str) -> str:
    if not isinstance(value,str) or not value:
        raise GuardInputError(f'{name} must be a non-empty string')
    return value


def _sequence_of_ids(value, name: str) -> list[str]:
    if isinstance(value,(str,bytes)) or not isinstance(value,Sequence):
        raise GuardInputError(f'{name} must be a sequence of node ids')
    result=list(value)
    if any(not isinstance(x,str) or not x for x in result):
        raise GuardInputError(f'{name} must contain non-empty string node ids')
    if len(result)!=len(set(result)):
        raise GuardInputError(f'{name} must not contain duplicate node ids')
    return result


def validate_grid(grid: Mapping) -> dict:
    """Validate finite ordered orthogonal reference-axis coordinates."""
    if not isinstance(grid,Mapping):
        raise GuardInputError('grid must be a mapping')
    axes={}
    reasons=[]
    for key in ('x','y'):
        raw=grid.get(key)
        if isinstance(raw,(str,bytes)) or not isinstance(raw,Sequence) or not raw:
            raise GuardInputError(f'grid.{key} must be a non-empty coordinate sequence')
        values=[finite_number(v,f'grid.{key}[{i}]') for i,v in enumerate(raw)]
        axes[key]=values
        if len(values)!=len(set(values)):
            reasons.append(f'duplicate_{key}_axis_position')
        if any(b<=a for a,b in zip(values,values[1:])):
            reasons.append(f'{key}_axes_not_strictly_ascending')
    return {
        'result':'fail' if reasons else 'pass',
        'reason_codes':reasons,
        'x_count':len(axes['x']),
        'y_count':len(axes['y']),
        'intersection_count':len(axes['x'])*len(axes['y']),
    }


def validate_load_path(graph: Mapping[str,Sequence[str]], *, loaded_nodes: Sequence[str], terminal_nodes: Sequence[str]) -> dict:
    """Require every declared loaded node to have an acyclic path to a declared terminal."""
    if not isinstance(graph,Mapping):
        raise GuardInputError('load_path graph must be a mapping')
    loaded=_sequence_of_ids(loaded_nodes,'loaded_nodes')
    terminals=set(_sequence_of_ids(terminal_nodes,'terminal_nodes'))
    normalized={}
    for node,children in graph.items():
        node_id=_id(node,'load_path node')
        normalized[node_id]=_sequence_of_ids(children,f'load_path[{node_id}]')
    referenced={child for children in normalized.values() for child in children}
    missing=sorted(referenced-set(normalized))
    if missing:
        raise GuardInputError(f'load_path references missing nodes: {missing}')
    if any(node not in normalized for node in loaded):
        raise GuardInputError('loaded_nodes must exist in graph')
    cycle=False
    visited=set(); active=set()
    def detect(node: str):
        nonlocal cycle
        if cycle or node in visited:
            return
        if node in active:
            cycle=True
            return
        active.add(node)
        for child in normalized[node]:
            detect(child)
        active.remove(node); visited.add(node)
    for node in normalized:
        detect(node)
        if cycle:
            break

    reasons=[]
    if cycle:
        reasons.append('load_path_cycle')

    def reaches_terminal(start: str) -> bool:
        stack=[start]; seen=set()
        while stack:
            node=stack.pop()
            if node in terminals:
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(normalized[node])
        return False

    for node in loaded:
        if not reaches_terminal(node):
            reasons.append(f'load_path_does_not_reach_terminal:{node}')
    return {
        'result':'fail' if reasons else 'pass',
        'reason_codes':reasons,
        'loaded_nodes':loaded,
        'terminal_nodes':sorted(terminals),
    }


def _bounds(value, name: str) -> tuple[float,float,float,float]:
    if isinstance(value,(str,bytes)) or not isinstance(value,Sequence) or len(value)!=4:
        raise GuardInputError(f'{name} must be [xmin,ymin,xmax,ymax]')
    xmin,ymin,xmax,ymax=(finite_number(v,f'{name}[{i}]') for i,v in enumerate(value))
    if xmax<=xmin or ymax<=ymin:
        raise GuardInputError(f'{name} must have positive extents')
    return xmin,ymin,xmax,ymax


def _overlap(a,b,clearance: float) -> bool:
    ax0,ay0,ax1,ay1=a; bx0,by0,bx1,by1=b
    return not (
        ax1+clearance < bx0-_EPS
        or bx1+clearance < ax0-_EPS
        or ay1+clearance < by0-_EPS
        or by1+clearance < ay0-_EPS
    )


def evaluate_architecture_clashes(*, columns: Sequence[Mapping], openings: Sequence[Mapping], clearance: float=0.0) -> dict:
    """Detect simplified plan-view column/opening clashes for coordination evidence."""
    clearance=finite_number(clearance,'clearance')
    if clearance<0:
        raise GuardInputError('clearance must be nonnegative')
    if isinstance(columns,(str,bytes)) or not isinstance(columns,Sequence):
        raise GuardInputError('columns must be a sequence')
    if isinstance(openings,(str,bytes)) or not isinstance(openings,Sequence):
        raise GuardInputError('openings must be a sequence')
    parsed_columns=[]; parsed_openings=[]
    for i,item in enumerate(columns):
        if not isinstance(item,Mapping): raise GuardInputError('columns must contain mappings')
        parsed_columns.append((_id(item.get('id'),f'columns[{i}].id'),_bounds(item.get('bounds'),f'columns[{i}].bounds')))
    for i,item in enumerate(openings):
        if not isinstance(item,Mapping): raise GuardInputError('openings must contain mappings')
        parsed_openings.append((_id(item.get('id'),f'openings[{i}].id'),_bounds(item.get('bounds'),f'openings[{i}].bounds')))
    reasons=[]
    for column_id,column_bounds in parsed_columns:
        for opening_id,opening_bounds in parsed_openings:
            if _overlap(column_bounds,opening_bounds,clearance):
                reasons.append(f'column_opening_clash:{column_id}:{opening_id}')
    return {'result':'fail' if reasons else 'pass','reason_codes':reasons,'clearance':clearance}


def evaluate_interface_inventory(items: Sequence[Mapping]) -> dict:
    """Apply the shared required-item completeness invariant to discipline interfaces."""
    try:
        return assess_inventory(items)
    except ValueError as exc:
        raise GuardInputError(str(exc)) from exc


def evaluate_release_evidence(evidence: Mapping, *, release_target: str) -> dict:
    """Preserve unknown structural design inputs and block adequacy claims at stronger releases."""
    if not isinstance(evidence,Mapping):
        raise GuardInputError('structural evidence must be a mapping')
    if release_target not in RELEASE_CLASSES:
        raise GuardInputError('unsupported release target')
    required_keys=('structural_system','materials','loads','standards')
    states={}
    for key in required_keys:
        state=evidence.get(key,'unknown')
        if state not in _ALLOWED_EVIDENCE:
            raise GuardInputError(f'{key}: invalid evidence state')
        states[key]=state
    reasons=[]; limitations=[]
    release_index=RELEASE_CLASSES.index(release_target)
    design_review_index=RELEASE_CLASSES.index('design_review')
    fabrication_index=RELEASE_CLASSES.index('fabrication_or_construction_candidate')
    if release_index>=design_review_index and states['structural_system'] not in _RESOLVED_EVIDENCE:
        reasons.append('structural_system_unresolved')
    unresolved_adequacy=[key for key in ('materials','loads','standards') if states[key] not in _RESOLVED_EVIDENCE]
    if release_index>=fabrication_index:
        reasons.extend(f'{key}_unresolved' for key in unresolved_adequacy)
    elif unresolved_adequacy:
        limitations.append('structural_adequacy_unclaimed')
    return {
        'result':'blocked' if reasons else 'pass',
        'reason_codes':reasons,
        'limitations':limitations,
        'release_target':release_target,
    }
