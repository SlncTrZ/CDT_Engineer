"""Building Architecture deterministic semantic and geometry guards.
Wing: code | Topic: building-architecture | Updated: 2026-09-17
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from domains.guard_primitives import GuardInputError, finite_number
from execution.release_scope import RELEASE_CLASSES

_EPS=1e-9
_CASEWORK_EVIDENCE_MAX_RELEASE={
    'observed':'design_review',
    'specified':'design_review',
    'derived':'design_review',
    'approved_assumption':'design_review',
    'inferred':'concept',
    'unknown':None,
}


def _string_id(value, name: str) -> str:
    if not isinstance(value,str) or not value:
        raise GuardInputError(f'{name} must be a non-empty string')
    return value


def _point2(value, name: str) -> tuple[float,float]:
    if isinstance(value,(str,bytes)) or not isinstance(value,Sequence) or len(value)!=2:
        raise GuardInputError(f'{name} must contain two finite numeric values')
    return finite_number(value[0],f'{name}[0]'),finite_number(value[1],f'{name}[1]')


def validate_levels(levels: Sequence[Mapping]) -> dict:
    """Validate level identity/elevation ordering without inventing storey heights."""
    if isinstance(levels,(str,bytes)) or not isinstance(levels,Sequence) or not levels:
        raise GuardInputError('levels must be a non-empty sequence')
    ids=[]; elevations=[]
    for i,level in enumerate(levels):
        if not isinstance(level,Mapping):
            raise GuardInputError('each level must be a mapping')
        ids.append(_string_id(level.get('id'),f'levels[{i}].id'))
        elevations.append(finite_number(level.get('elevation'),f'levels[{i}].elevation'))
    reasons=[]
    if len(ids)!=len(set(ids)):
        reasons.append('duplicate_level_id')
    if len(elevations)!=len(set(elevations)):
        reasons.append('duplicate_level_elevation')
    if any(b<=a for a,b in zip(elevations,elevations[1:])):
        reasons.append('levels_not_strictly_ascending')
    return {
        'result':'fail' if reasons else 'pass',
        'reason_codes':reasons,
        'level_count':len(levels),
        'vertical_span':elevations[-1]-elevations[0],
    }


def _orientation(a,b,c) -> float:
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def _on_segment(a,b,p) -> bool:
    return (
        min(a[0],b[0])-_EPS<=p[0]<=max(a[0],b[0])+_EPS
        and min(a[1],b[1])-_EPS<=p[1]<=max(a[1],b[1])+_EPS
        and abs(_orientation(a,b,p))<=_EPS
    )


def _segments_intersect(a,b,c,d) -> bool:
    o1=_orientation(a,b,c); o2=_orientation(a,b,d); o3=_orientation(c,d,a); o4=_orientation(c,d,b)
    if ((o1>_EPS and o2<-_EPS) or (o1<-_EPS and o2>_EPS)) and ((o3>_EPS and o4<-_EPS) or (o3<-_EPS and o4>_EPS)):
        return True
    return any((
        abs(o1)<=_EPS and _on_segment(a,b,c),
        abs(o2)<=_EPS and _on_segment(a,b,d),
        abs(o3)<=_EPS and _on_segment(c,d,a),
        abs(o4)<=_EPS and _on_segment(c,d,b),
    ))


def _normalize_polygon(boundary: Sequence[Sequence[float]]) -> list[tuple[float,float]]:
    if isinstance(boundary,(str,bytes)) or not isinstance(boundary,Sequence):
        raise GuardInputError('space boundary must be a sequence of points')
    pts=[_point2(p,f'boundary[{i}]') for i,p in enumerate(boundary)]
    if len(pts)>=2 and pts[0]==pts[-1]:
        pts=pts[:-1]
    if len(pts)<3 or len(set(pts))<3:
        raise GuardInputError('space boundary requires at least three unique points')
    return pts


def _self_intersects(pts: Sequence[tuple[float,float]]) -> bool:
    n=len(pts)
    for i in range(n):
        a,b=pts[i],pts[(i+1)%n]
        for j in range(i+1,n):
            if j in {i,(i+1)%n} or i==(j+1)%n:
                continue
            c,d=pts[j],pts[(j+1)%n]
            if _segments_intersect(a,b,c,d):
                return True
    return False


def _area(pts: Sequence[tuple[float,float]]) -> float:
    return abs(sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts))))/2.0


def _axis_aligned_rectangle_clear_dimension(pts: Sequence[tuple[float,float]]) -> float | None:
    if len(pts)!=4:
        return None
    xs=sorted({p[0] for p in pts}); ys=sorted({p[1] for p in pts})
    if len(xs)!=2 or len(ys)!=2:
        return None
    expected={(xs[0],ys[0]),(xs[0],ys[1]),(xs[1],ys[0]),(xs[1],ys[1])}
    if set(pts)!=expected:
        return None
    return min(xs[1]-xs[0],ys[1]-ys[0])


def evaluate_space(boundary: Sequence[Sequence[float]], requirements: Mapping) -> dict:
    """Evaluate measurable space geometry using only explicit project/standard requirements."""
    if not isinstance(requirements,Mapping):
        raise GuardInputError('space requirements must be a mapping')
    pts=_normalize_polygon(boundary)
    reasons=[]
    self_intersection=_self_intersects(pts)
    area=_area(pts)
    if self_intersection:
        reasons.append('self_intersecting_boundary')
    if area<=_EPS:
        reasons.append('degenerate_space_area')

    minimum_area=requirements.get('minimum_area')
    if minimum_area is not None:
        minimum_area=finite_number(minimum_area,'minimum_area')
        if minimum_area<0:
            raise GuardInputError('minimum_area must be nonnegative')
        if area+_EPS<minimum_area:
            reasons.append('area_below_requirement')

    clear_dimension=_axis_aligned_rectangle_clear_dimension(pts)
    minimum_clear=requirements.get('minimum_clear_dimension')
    if minimum_clear is not None:
        minimum_clear=finite_number(minimum_clear,'minimum_clear_dimension')
        if minimum_clear<0:
            raise GuardInputError('minimum_clear_dimension must be nonnegative')
        if clear_dimension is None:
            return {
                'result':'unknown' if not reasons else 'fail',
                'reason_codes':[*reasons,'clear_dimension_method_unresolved'],
                'area':area,
                'clear_dimension':None,
            }
        if clear_dimension+_EPS<minimum_clear:
            reasons.append('clear_dimension_below_requirement')
    return {'result':'fail' if reasons else 'pass','reason_codes':reasons,'area':area,'clear_dimension':clear_dimension}


def evaluate_opening_host(wall: Mapping, opening: Mapping) -> dict:
    """Check simplified opening-to-wall hosting bounds for Building Architecture v1."""
    if not isinstance(wall,Mapping) or not isinstance(opening,Mapping):
        raise GuardInputError('wall and opening must be mappings')
    wall_id=_string_id(wall.get('id'),'wall.id')
    host_id=_string_id(opening.get('host_wall_id'),'opening.host_wall_id')
    wall_length=finite_number(wall.get('length'),'wall.length')
    wall_height=finite_number(wall.get('height'),'wall.height')
    offset=finite_number(opening.get('offset'),'opening.offset')
    width=finite_number(opening.get('width'),'opening.width')
    height=finite_number(opening.get('height'),'opening.height')
    sill=finite_number(opening.get('sill_height',0.0),'opening.sill_height')
    if wall_length<=0 or wall_height<=0 or width<=0 or height<=0 or offset<0 or sill<0:
        raise GuardInputError('wall/opening dimensions must be physically positive and offsets nonnegative')
    reasons=[]
    if host_id!=wall_id:
        reasons.append('opening_host_id_mismatch')
    if offset+width>wall_length+_EPS:
        reasons.append('opening_exceeds_wall_length')
    if sill+height>wall_height+_EPS:
        reasons.append('opening_exceeds_wall_height')
    return {
        'result':'fail' if reasons else 'pass',
        'reason_codes':reasons,
        'host_wall_id':wall_id,
        'opening_id':opening.get('id'),
    }


def resolve_opening_elevation(levels: Sequence[Mapping], wall: Mapping, opening: Mapping) -> dict:
    """Bind opening sill/head to absolute elevation via the host wall's level.

    sill_height is relative to the wall base (its level elevation); native
    placement must use sill_elevation/head_elevation, never the raw sill.
    Returns 'unknown' when the wall level cannot be resolved and 'fail' when
    the absolute opening exceeds the wall (e.g. a window head eating the
    ceiling). Relative-only checks cannot catch these; this binding can.
    """
    if isinstance(levels,(str,bytes)) or not isinstance(levels,Sequence):
        raise GuardInputError('levels must be a sequence')
    if not isinstance(wall,Mapping) or not isinstance(opening,Mapping):
        raise GuardInputError('wall and opening must be mappings')
    wall_id=_string_id(wall.get('id'),'wall.id')
    host_id=_string_id(opening.get('host_wall_id'),'opening.host_wall_id')
    level_id=_string_id(wall.get('level_id'),'wall.level_id')
    wall_height=finite_number(wall.get('height'),'wall.height')
    sill=finite_number(opening.get('sill_height',0.0),'opening.sill_height')
    height=finite_number(opening.get('height'),'opening.height')
    if wall_height<=0 or height<=0 or sill<0:
        raise GuardInputError('wall/opening vertical dimensions must be physically positive and sill nonnegative')
    elevations={}
    for i,level in enumerate(levels):
        if not isinstance(level,Mapping):
            raise GuardInputError('each level must be a mapping')
        elevations[_string_id(level.get('id'),f'levels[{i}].id')]=finite_number(level.get('elevation'),f'levels[{i}].elevation')
    reasons=[]
    if host_id!=wall_id:
        reasons.append('opening_host_id_mismatch')
    if level_id not in elevations:
        return {
            'result':'unknown' if not reasons else 'fail',
            'reason_codes':[*reasons,'level_unresolved'],
            'host_wall_id':wall_id,
            'opening_id':opening.get('id'),
            'sill_elevation':None,
            'head_elevation':None,
            'wall_base_elevation':None,
            'wall_top_elevation':None,
        }
    base=elevations[level_id]
    top=base+wall_height
    sill_abs=base+sill
    head_abs=sill_abs+height
    if head_abs>top+_EPS:
        reasons.append('head_above_wall_top')
    return {
        'result':'fail' if reasons else 'pass',
        'reason_codes':reasons,
        'host_wall_id':wall_id,
        'opening_id':opening.get('id'),
        'sill_elevation':sill_abs,
        'head_elevation':head_abs,
        'wall_base_elevation':base,
        'wall_top_elevation':top,
    }


def verify_opening_placement(resolved: Mapping, measured_sill_elevation, measured_head_elevation, tolerance) -> dict:
    """Verify natively measured opening elevations against a resolved reference.

    The caller declares the project tolerance (same units as the elevations);
    the oracle never invents one. An unresolved reference yields 'unknown',
    never a silent pass.
    """
    if not isinstance(resolved,Mapping):
        raise GuardInputError('resolved must be a mapping')
    tolerance=finite_number(tolerance,'tolerance')
    if tolerance<0:
        raise GuardInputError('tolerance must be nonnegative')
    if resolved.get('result')!='pass':
        return {'result':'unknown','reason_codes':['unresolved_reference']}
    sill_ref=finite_number(resolved.get('sill_elevation'),'resolved.sill_elevation')
    head_ref=finite_number(resolved.get('head_elevation'),'resolved.head_elevation')
    sill_meas=finite_number(measured_sill_elevation,'measured_sill_elevation')
    head_meas=finite_number(measured_head_elevation,'measured_head_elevation')
    reasons=[]
    if abs(sill_meas-sill_ref)>tolerance+_EPS:
        reasons.append('sill_elevation_mismatch')
    if abs(head_meas-head_ref)>tolerance+_EPS:
        reasons.append('head_elevation_mismatch')
    return {'result':'fail' if reasons else 'pass','reason_codes':reasons}


def evaluate_stair(stair: Mapping, requirements: Mapping) -> dict:
    """Check stair dimensional consistency; regulatory thresholds must be supplied explicitly."""
    if not isinstance(stair,Mapping) or not isinstance(requirements,Mapping):
        raise GuardInputError('stair and requirements must be mappings')
    from_elevation=finite_number(stair.get('from_elevation'),'from_elevation')
    to_elevation=finite_number(stair.get('to_elevation'),'to_elevation')
    riser_count=stair.get('riser_count')
    if isinstance(riser_count,bool) or not isinstance(riser_count,int) or riser_count<=0:
        raise GuardInputError('riser_count must be a positive integer')
    riser=finite_number(stair.get('riser_height'),'riser_height')
    going=finite_number(stair.get('going'),'going')
    width=finite_number(stair.get('width'),'width')
    if to_elevation<=from_elevation or riser<=0 or going<=0 or width<=0:
        raise GuardInputError('stair dimensions/elevations must be physically positive')
    reasons=[]
    level_rise=to_elevation-from_elevation
    model_rise=riser_count*riser
    if abs(model_rise-level_rise)>max(_EPS,abs(level_rise)*1e-8):
        reasons.append('stair_total_rise_mismatch')
    checks=(
        ('maximum_riser_height',lambda value: riser>value+_EPS,'riser_height_above_requirement'),
        ('minimum_going',lambda value: going+_EPS<value,'going_below_requirement'),
        ('minimum_width',lambda value: width+_EPS<value,'width_below_requirement'),
    )
    for key,predicate,reason in checks:
        if key not in requirements:
            continue
        value=finite_number(requirements[key],key)
        if value<0:
            raise GuardInputError(f'{key} must be nonnegative')
        if predicate(value):
            reasons.append(reason)
    return {
        'result':'fail' if reasons else 'pass',
        'reason_codes':reasons,
        'level_rise':level_rise,
        'modeled_rise':model_rise,
        'riser_count':riser_count,
    }


def evaluate_feature_inventory(items: Sequence[Mapping], *, release_target: str) -> dict:
    """Block required omissions and proxies that exceed their explicitly allowed release."""
    if release_target not in RELEASE_CLASSES:
        raise GuardInputError('unsupported release target')
    if isinstance(items,(str,bytes)) or not isinstance(items,Sequence):
        raise GuardInputError('feature inventory must be a sequence')
    reasons=[]; seen=set(); limitations=[]
    requested_index=RELEASE_CLASSES.index(release_target)
    for i,item in enumerate(items):
        if not isinstance(item,Mapping):
            raise GuardInputError('feature inventory items must be mappings')
        item_id=_string_id(item.get('item_id'),f'items[{i}].item_id')
        if item_id in seen:
            raise GuardInputError(f'duplicate feature inventory item: {item_id}')
        seen.add(item_id)
        required=item.get('required')
        if not isinstance(required,bool):
            raise GuardInputError(f'{item_id}: required must be bool')
        resolution=item.get('resolution_state')
        implementation=item.get('implementation_state')
        verification=item.get('verification_state')
        if resolution not in {'resolved','custom_allowed','proxy_allowed_for_scope','reduced_scope','blocked'}:
            raise GuardInputError(f'{item_id}: invalid resolution_state')
        if implementation not in {'implemented','proxy','missing','not_applicable'}:
            raise GuardInputError(f'{item_id}: invalid implementation_state')
        if verification not in {'verified','unverified','not_applicable'}:
            raise GuardInputError(f'{item_id}: invalid verification_state')
        if not required:
            continue
        if resolution=='blocked':
            reasons.append(f'resolution_blocked:{item_id}')
        if implementation in {'missing','not_applicable'}:
            reasons.append(f'required_feature_missing:{item_id}')
        if verification!='verified':
            reasons.append(f'required_feature_unverified:{item_id}')
        if resolution=='proxy_allowed_for_scope' or implementation=='proxy':
            maximum=item.get('proxy_allowed_through','concept')
            if maximum not in RELEASE_CLASSES:
                raise GuardInputError(f'{item_id}: invalid proxy_allowed_through')
            if requested_index>RELEASE_CLASSES.index(maximum):
                reasons.append(f'proxy_not_valid_for_release:{item_id}')
            else:
                limitations.append(f'proxy:{item_id}:{maximum}')
        if resolution=='reduced_scope':
            maximum=item.get('maximum_release')
            if maximum not in RELEASE_CLASSES:
                raise GuardInputError(f'{item_id}: reduced_scope requires maximum_release')
            if requested_index>RELEASE_CLASSES.index(maximum):
                reasons.append(f'reduced_scope_exceeded:{item_id}')
            else:
                limitations.append(f'reduced_scope:{item_id}:{maximum}')
    return {
        'result':'blocked' if reasons else 'pass',
        'reason_codes':reasons,
        'limitations':limitations,
        'inventory_count':len(items),
    }


def evaluate_casework_box(module: Mapping, requirements: Mapping) -> dict:
    """Derive a rectangular casework clear envelope from explicit dimensions/panels."""
    if not isinstance(module,Mapping) or not isinstance(requirements,Mapping):
        raise GuardInputError('casework module and requirements must be mappings')
    module_id=_string_id(module.get('id'),'module.id')
    width=finite_number(module.get('width'),'module.width')
    height=finite_number(module.get('height'),'module.height')
    depth=finite_number(module.get('depth'),'module.depth')
    if min(width,height,depth)<=0:
        raise GuardInputError('casework outer dimensions must be positive')
    panels=module.get('panels')
    if not isinstance(panels,Mapping):
        raise GuardInputError('module.panels must be a mapping')
    panel_values={}
    for key in ('left','right','top','bottom','back'):
        if key not in panels:
            raise GuardInputError(f'module.panels.{key} is required')
        value=finite_number(panels[key],f'module.panels.{key}')
        if value<0:
            raise GuardInputError('panel thicknesses must be nonnegative')
        panel_values[key]=value
    clear_width=width-panel_values['left']-panel_values['right']
    clear_height=height-panel_values['top']-panel_values['bottom']
    clear_depth=depth-panel_values['back']
    reasons=[]
    if clear_width<=_EPS:
        reasons.append('nonpositive_clear_width')
    if clear_height<=_EPS:
        reasons.append('nonpositive_clear_height')
    if clear_depth<=_EPS:
        reasons.append('nonpositive_clear_depth')
    checks=(
        ('minimum_clear_width',clear_width,'clear_width_below_requirement'),
        ('minimum_clear_height',clear_height,'clear_height_below_requirement'),
        ('minimum_clear_depth',clear_depth,'clear_depth_below_requirement'),
    )
    for key,actual,reason in checks:
        if key not in requirements:
            continue
        required=finite_number(requirements[key],key)
        if required<0:
            raise GuardInputError(f'{key} must be nonnegative')
        if actual+_EPS<required:
            reasons.append(reason)
    return {
        'result':'fail' if reasons else 'pass',
        'reason_codes':reasons,
        'module_id':module_id,
        'clear_width':clear_width,
        'clear_height':clear_height,
        'clear_depth':clear_depth,
    }


def evaluate_casework_compartments(*, clear_span, compartment_widths: Sequence, partition_thickness) -> dict:
    """Reconcile explicit compartment widths and intervening partitions to one clear span."""
    span=finite_number(clear_span,'clear_span')
    partition=finite_number(partition_thickness,'partition_thickness')
    if span<=0 or partition<0:
        raise GuardInputError('clear_span must be positive and partition_thickness nonnegative')
    if isinstance(compartment_widths,(str,bytes)) or not isinstance(compartment_widths,Sequence) or not compartment_widths:
        raise GuardInputError('compartment_widths must be a non-empty sequence')
    widths=[]
    for i,value in enumerate(compartment_widths):
        width=finite_number(value,f'compartment_widths[{i}]')
        if width<=0:
            raise GuardInputError('compartment widths must be positive')
        widths.append(width)
    modeled=sum(widths)+partition*(len(widths)-1)
    tolerance=max(_EPS,abs(span)*1e-9)
    reasons=[] if abs(modeled-span)<=tolerance else ['compartment_span_mismatch']
    return {
        'result':'fail' if reasons else 'pass',
        'reason_codes':reasons,
        'clear_span':span,
        'modeled_span':modeled,
        'compartment_count':len(widths),
        'partition_count':max(0,len(widths)-1),
    }


def evaluate_corner_casework(module: Mapping, requirements: Mapping | None = None) -> dict:
    """Validate a simple orthogonal L-casework footprint without inventing design clearances."""
    if not isinstance(module,Mapping):
        raise GuardInputError('corner casework module must be a mapping')
    if requirements is None:
        requirements={}
    if not isinstance(requirements,Mapping):
        raise GuardInputError('corner casework requirements must be a mapping')
    module_id=_string_id(module.get('id'),'module.id')
    values={}
    for key in ('leg_a','leg_b','depth_a','depth_b','height'):
        value=finite_number(module.get(key),f'module.{key}')
        if value<=0:
            raise GuardInputError('corner casework dimensions must be positive')
        values[key]=value
    reasons=[]
    if values['leg_a']<=values['depth_b']+_EPS:
        reasons.append('corner_leg_a_not_beyond_return_depth')
    if values['leg_b']<=values['depth_a']+_EPS:
        reasons.append('corner_leg_b_not_beyond_return_depth')
    for key in ('minimum_leg_a','minimum_leg_b','minimum_height'):
        if key not in requirements:
            continue
        required=finite_number(requirements[key],key)
        if required<0:
            raise GuardInputError(f'{key} must be nonnegative')
        actual=values[{'minimum_leg_a':'leg_a','minimum_leg_b':'leg_b','minimum_height':'height'}[key]]
        if actual+_EPS<required:
            reasons.append(f'{key}_not_met')
    footprint=values['leg_a']*values['depth_a']+values['leg_b']*values['depth_b']-values['depth_a']*values['depth_b']
    if footprint<=_EPS:
        reasons.append('nonpositive_corner_footprint')
    return {
        'result':'fail' if reasons else 'pass',
        'reason_codes':reasons,
        'module_id':module_id,
        'footprint_area':footprint,
    }


def evaluate_rectangular_fit(opening: Mapping, item: Mapping, clearances: Mapping) -> dict:
    """Check a drawer/appliance envelope against an opening using only supplied clearances."""
    if not isinstance(opening,Mapping) or not isinstance(item,Mapping) or not isinstance(clearances,Mapping):
        raise GuardInputError('opening, item and clearances must be mappings')
    opening_dims={}
    item_dims={}
    for key in ('width','height','depth'):
        opening_value=finite_number(opening.get(key),f'opening.{key}')
        item_value=finite_number(item.get(key),f'item.{key}')
        if opening_value<=0 or item_value<=0:
            raise GuardInputError('opening and item dimensions must be positive')
        opening_dims[key]=opening_value
        item_dims[key]=item_value
    clearance_values={}
    for key in ('left','right','top','bottom','front','back'):
        if key not in clearances:
            raise GuardInputError(f'clearances.{key} is required')
        value=finite_number(clearances[key],f'clearances.{key}')
        if value<0:
            raise GuardInputError('clearances must be nonnegative')
        clearance_values[key]=value
    available={
        'width':opening_dims['width']-clearance_values['left']-clearance_values['right'],
        'height':opening_dims['height']-clearance_values['top']-clearance_values['bottom'],
        'depth':opening_dims['depth']-clearance_values['front']-clearance_values['back'],
    }
    reasons=[]
    for axis in ('width','height','depth'):
        if available[axis]<=_EPS:
            reasons.append(f'nonpositive_clear_{axis}')
        elif item_dims[axis]>available[axis]+_EPS:
            reasons.append(f'item_exceeds_clear_{axis}')
    return {
        'result':'fail' if reasons else 'pass',
        'reason_codes':reasons,
        'available_width':available['width'],
        'available_height':available['height'],
        'available_depth':available['depth'],
        'margin_width':available['width']-item_dims['width'],
        'margin_height':available['height']-item_dims['height'],
        'margin_depth':available['depth']-item_dims['depth'],
    }


def _iter_casework_evidence(item: Mapping, item_id: str):
    geometry=item.get('geometry',{})
    if isinstance(geometry,Mapping):
        for key,value in geometry.items():
            if key!='type':
                yield f'{item_id}.geometry.{key}',value
    panels=item.get('panels',{})
    if isinstance(panels,Mapping):
        for key,value in panels.items():
            yield f'{item_id}.panels.{key}',value
    requirements=item.get('requirements',{})
    if isinstance(requirements,Mapping):
        for key,value in requirements.items():
            yield f'{item_id}.requirements.{key}',value
    compartments=item.get('compartments')
    if isinstance(compartments,Mapping):
        widths=compartments.get('widths',[])
        if isinstance(widths,Sequence) and not isinstance(widths,(str,bytes)):
            for index,value in enumerate(widths):
                yield f'{item_id}.compartments.widths[{index}]',value
        if 'partition_thickness' in compartments:
            yield f'{item_id}.compartments.partition_thickness',compartments['partition_thickness']
    envelope=item.get('envelope',{})
    if isinstance(envelope,Mapping):
        for key,value in envelope.items():
            yield f'{item_id}.envelope.{key}',value
    clearances=item.get('clearances',{})
    if isinstance(clearances,Mapping):
        for key,value in clearances.items():
            yield f'{item_id}.clearances.{key}',value


def validate_casework_input_package(payload: Mapping) -> dict:
    """Fail closed on provenance and semantic-resolution invariants for casework skill v0.2.

    JSON Schema validates structural shape. This validator covers cross-record rules that
    JSON Schema cannot express cleanly: unique semantic IDs, package source membership,
    provenance release ceilings and proxy/reduced-scope ceilings.
    """
    if not isinstance(payload,Mapping):
        raise GuardInputError('casework input package must be a mapping')
    release_target=payload.get('release_target')
    if release_target not in {'concept','technical_draft','design_review'}:
        raise GuardInputError('interior-casework-layout supports concept through design_review')
    source_refs=payload.get('source_refs')
    if isinstance(source_refs,(str,bytes)) or not isinstance(source_refs,Sequence) or not source_refs:
        raise GuardInputError('source_refs must be a non-empty sequence')
    if any(not isinstance(ref,str) or not ref for ref in source_refs):
        raise GuardInputError('source_refs must contain non-empty strings')
    declared_sources=set(source_refs)
    requested_index=RELEASE_CLASSES.index(release_target)
    reasons=[]; limitations=[]; seen=set(); evidence_count=0

    groups=[]
    for group_name in ('modules','equipment'):
        raw=payload.get(group_name,[])
        if isinstance(raw,(str,bytes)) or not isinstance(raw,Sequence):
            raise GuardInputError(f'{group_name} must be a sequence')
        groups.extend(raw)

    for index,item in enumerate(groups):
        if not isinstance(item,Mapping):
            raise GuardInputError('casework modules/equipment must be mappings')
        item_id=_string_id(item.get('id'),f'items[{index}].id')
        if item_id in seen:
            reasons.append(f'duplicate_semantic_id:{item_id}')
        seen.add(item_id)

        for field_path,evidence in _iter_casework_evidence(item,item_id):
            evidence_count+=1
            if not isinstance(evidence,Mapping):
                raise GuardInputError(f'{field_path} must be a typed evidence number')
            status=evidence.get('status')
            if status not in _CASEWORK_EVIDENCE_MAX_RELEASE:
                raise GuardInputError(f'{field_path}: unsupported evidence status')
            source_ref=evidence.get('source_ref')
            maximum=_CASEWORK_EVIDENCE_MAX_RELEASE[status]
            if status=='unknown':
                reasons.append(f'critical_evidence_unknown:{field_path}')
                continue
            if not isinstance(source_ref,str) or not source_ref:
                reasons.append(f'evidence_source_missing:{field_path}')
            elif source_ref not in declared_sources:
                reasons.append(f'evidence_source_not_declared:{field_path}:{source_ref}')
            if maximum is not None and requested_index>RELEASE_CLASSES.index(maximum):
                reasons.append(f'evidence_state_exceeds_release:{field_path}:{status}:{maximum}')
            if status=='approved_assumption':
                approved_by=evidence.get('approved_by')
                if not isinstance(approved_by,str) or not approved_by:
                    reasons.append(f'approved_assumption_missing_approval:{field_path}')

        resolution=item.get('component_resolution')
        if resolution=='resolved':
            component_id=item.get('component_id')
            if not isinstance(component_id,str) or not component_id:
                reasons.append(f'resolved_component_identity_missing:{item_id}')
        elif resolution=='proxy_allowed_for_scope':
            proxy=item.get('proxy')
            if not isinstance(proxy,Mapping):
                reasons.append(f'proxy_metadata_missing:{item_id}')
            else:
                maximum=proxy.get('maximum_release')
                if maximum not in RELEASE_CLASSES:
                    raise GuardInputError(f'{item_id}: invalid proxy maximum_release')
                if requested_index>RELEASE_CLASSES.index(maximum):
                    reasons.append(f'proxy_not_valid_for_release:{item_id}:{maximum}')
                else:
                    limitations.append(f'proxy:{item_id}:{maximum}')
        elif resolution=='reduced_scope':
            reduced=item.get('reduced_scope')
            if not isinstance(reduced,Mapping):
                reasons.append(f'reduced_scope_metadata_missing:{item_id}')
            else:
                maximum=reduced.get('maximum_release')
                if maximum not in RELEASE_CLASSES:
                    raise GuardInputError(f'{item_id}: invalid reduced-scope maximum_release')
                if requested_index>RELEASE_CLASSES.index(maximum):
                    reasons.append(f'reduced_scope_exceeded:{item_id}:{maximum}')
                else:
                    limitations.append(f'reduced_scope:{item_id}:{maximum}')
        elif resolution=='blocked':
            reasons.append(f'component_resolution_blocked:{item_id}')
        elif resolution!='custom_allowed':
            raise GuardInputError(f'{item_id}: invalid component_resolution')

    reasons=list(dict.fromkeys(reasons))
    return {
        'result':'blocked' if reasons else 'pass',
        'reason_codes':reasons,
        'limitations':list(dict.fromkeys(limitations)),
        'semantic_item_count':len(groups),
        'evidence_field_count':evidence_count,
        'release_target':release_target,
    }
