"""Shared deterministic guard primitives proven by Site + Mechanical Rule-of-Two."""
from __future__ import annotations

import math

_UNIT_TO_M={'mm':0.001,'cm':0.01,'m':1.0,'in':0.0254,'ft':0.3048}

class GuardInputError(ValueError):
    """Raised when deterministic guard input is malformed."""

def finite_number(value, name: str) -> float:
    """Return one finite numeric value as float or fail closed."""
    if not isinstance(value,(int,float)) or not math.isfinite(value):
        raise GuardInputError(f'{name} must be finite numeric')
    return float(value)

def unit_ratio(source_unit: str, target_unit: str) -> float:
    """Return multiplicative ratio converting source-unit values into target units."""
    if source_unit not in _UNIT_TO_M or target_unit not in _UNIT_TO_M:
        raise GuardInputError('unsupported unit')
    return _UNIT_TO_M[source_unit]/_UNIT_TO_M[target_unit]

def convert_value(value, source_unit: str, target_unit: str) -> float:
    """Convert a finite numeric value between supported engineering length units."""
    return finite_number(value,'value')*unit_ratio(source_unit,target_unit)
