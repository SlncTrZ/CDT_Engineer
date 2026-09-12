"""Building Architecture deterministic semantic and geometry guards.
Wing: code | Topic: building-architecture | Updated: 2026-09-12 19:49
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from domains.guard_primitives import GuardInputError, finite_number
from execution.release_scope import RELEASE_CLASSES

_EPS=1e-9


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
