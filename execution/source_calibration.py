"""Reference-source interpretation and calibration (ENG-R06).
Wing: code | Topic: source-calibration | Updated: 2026-09-18 01:00
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

_VERDICTS = {"CALIBRATED", "CONTRADICTORY", "NEEDS_ANCHOR", "INVALID_SOURCE"}
_FEATURE_KINDS = {"point", "polyline"}

_DEFAULT_MAX_SCALE_DISAGREEMENT_REL = 0.02


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite numeric")
    return float(value)


def _pixel(value: Any, name: str) -> list[float]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or len(value) != 2:
        raise ValueError(f"{name} must be an [x, y] pixel pair")
    return [_finite(value[0], f"{name}[0]"), _finite(value[1], f"{name}[1]")]


def _in_bounds(pt: Sequence[float], width: float, height: float) -> bool:
    return 0.0 - 1e-9 <= pt[0] <= width + 1e-9 and 0.0 - 1e-9 <= pt[1] <= height + 1e-9


@dataclass(frozen=True)
class CalibratedSource:
    verdict: str  # CALIBRATED | CONTRADICTORY | NEEDS_ANCHOR | INVALID_SOURCE
    frame: dict[str, Any] = field(default_factory=dict)
    features: list[dict[str, Any]] = field(default_factory=list)
    anchors: list[dict[str, Any]] = field(default_factory=list)
    scale_disagreement_rel: float = 0.0
    confidence: float = 0.0
    provenance_ledger: dict[str, dict[str, Any]] = field(default_factory=dict)
    assumptions: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "frame": dict(self.frame),
            "features": [dict(f) for f in self.features],
            "anchors": [dict(a) for a in self.anchors],
            "scale_disagreement_rel": self.scale_disagreement_rel,
            "confidence": self.confidence,
            "provenance_ledger": {k: dict(v) for k, v in self.provenance_ledger.items()},
            "assumptions": [dict(a) for a in self.assumptions],
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def calibrate_plan_source(*, source: Mapping[str, Any],
                          pixel_features: Sequence[Mapping[str, Any]] | None = None,
                          anchors: Sequence[Mapping[str, Any]] | None = None,
                          requirements: Mapping[str, Any] | None = None) -> CalibratedSource:
    """Calibrate a reference image into an engineering coordinate frame.

    Pixel readings are `observed`; dimensional anchors are owner-declared
    `approved_assumption` (never promoted to ground truth); calibrated
    coordinates are `derived`. Two or more anchors implying inconsistent
    scales fail closed as CONTRADICTORY instead of averaging silently.
    Image axes are assumed aligned with plan axes (uniform scale, y-flip
    to y-up engineering frame); rotation correction is out of scope.
    """
    errors: list[str] = []
    warnings: list[str] = []
    ledger: dict[str, dict[str, Any]] = {}
    assumptions: list[dict[str, Any]] = []

    if not isinstance(source, Mapping):
        raise ValueError("source must be a mapping")
    source_id = source.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        raise ValueError("source.source_id must be a non-empty string")
    try:
        width = _finite(source.get("pixel_width"), "source.pixel_width")
        height = _finite(source.get("pixel_height"), "source.pixel_height")
    except ValueError as exc:
        return CalibratedSource(verdict="INVALID_SOURCE", errors=[f"invalid_source_dimensions:{exc}"])
    if width <= 0 or height <= 0:
        return CalibratedSource(verdict="INVALID_SOURCE", errors=["invalid_source_dimensions:non_positive"])
    ledger[source_id] = {"status": "observed", "source_id": source_id,
                         "assumption_id": None, "confidence": 1.0}

    max_disagreement = _DEFAULT_MAX_SCALE_DISAGREEMENT_REL
    if requirements is not None:
        if not isinstance(requirements, Mapping):
            raise ValueError("requirements must be a mapping")
        if "max_scale_disagreement_rel" in requirements:
            max_disagreement = _finite(requirements["max_scale_disagreement_rel"],
                                       "requirements.max_scale_disagreement_rel")
            if max_disagreement < 0:
                raise ValueError("requirements.max_scale_disagreement_rel must be nonnegative")

    anchors = list(anchors or [])
    if not anchors:
        return CalibratedSource(verdict="NEEDS_ANCHOR", provenance_ledger=ledger,
                                errors=["no_dimensional_anchor:frame_unresolvable"])

    parsed_anchors: list[dict[str, Any]] = []
    units: set[str] = set()
    for idx, anchor in enumerate(anchors):
        tag = f"anchors[{idx}]"
        if not isinstance(anchor, Mapping):
            errors.append(f"anchor_malformed:{tag}")
            continue
        anchor_id = anchor.get("anchor_id")
        if not isinstance(anchor_id, str) or not anchor_id:
            errors.append(f"anchor_malformed:{tag}:missing_anchor_id")
            continue
        try:
            p0 = _pixel(anchor.get("pixel_from"), f"{tag}.pixel_from")
            p1 = _pixel(anchor.get("pixel_to"), f"{tag}.pixel_to")
            real_length = _finite(anchor.get("real_length"), f"{tag}.real_length")
            confidence = _finite(anchor.get("confidence", 1.0), f"{tag}.confidence")
        except ValueError as exc:
            errors.append(f"anchor_malformed:{anchor_id}:{exc}")
            continue
        if real_length <= 0:
            errors.append(f"anchor_non_positive_length:{anchor_id}")
            continue
        if not 0.0 <= confidence <= 1.0:
            errors.append(f"anchor_confidence_out_of_range:{anchor_id}")
            continue
        if not _in_bounds(p0, width, height) or not _in_bounds(p1, width, height):
            errors.append(f"anchor_out_of_bounds:{anchor_id}")
            continue
        pixel_span = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if pixel_span <= 1e-9:
            errors.append(f"anchor_zero_pixel_span:{anchor_id}")
            continue
        unit = anchor.get("unit", "mm")
        units.add(unit)
        parsed_anchors.append({
            "anchor_id": anchor_id,
            "statement": anchor.get("statement", ""),
            "pixel_from": p0,
            "pixel_to": p1,
            "pixel_span": pixel_span,
            "real_length": real_length,
            "unit": unit,
            "confidence": confidence,
            "computed_scale": real_length / pixel_span,
        })
    if errors:
        return CalibratedSource(verdict="INVALID_SOURCE", provenance_ledger=ledger, errors=errors)
    if len(units) > 1:
        return CalibratedSource(verdict="INVALID_SOURCE", provenance_ledger=ledger,
                                errors=[f"mixed_anchor_units:{sorted(units)}"])
    unit = next(iter(units))

    scales = [a["computed_scale"] for a in parsed_anchors]
    mean_scale = sum(scales) / len(scales)
    disagreement = (max(abs(s - mean_scale) for s in scales) / mean_scale) if mean_scale > 0 else 0.0
    for anchor in parsed_anchors:
        ledger[anchor["anchor_id"]] = {"status": "approved_assumption", "source_id": None,
                                       "assumption_id": anchor["anchor_id"],
                                       "confidence": anchor["confidence"]}
        assumptions.append({"id": anchor["anchor_id"], "statement": anchor["statement"],
                            "status": "approved_assumption"})
    confidence = min(a["confidence"] for a in parsed_anchors)

    if disagreement > max_disagreement + 1e-12:
        return CalibratedSource(
            verdict="CONTRADICTORY", anchors=parsed_anchors,
            scale_disagreement_rel=disagreement, confidence=confidence,
            provenance_ledger=ledger, assumptions=assumptions,
            errors=[f"anchor_scale_contradiction:disagreement_rel={disagreement:.6f}"
                    f">tolerance_rel={max_disagreement}"],
        )

    frame = {"unit": unit, "scale_unit_per_pixel": mean_scale,
             "origin_pixel": [0.0, 0.0], "y_direction": "up",
             "image_size": [width, height],
             "alignment_note": "image axes assumed aligned with plan axes; no rotation correction"}
    ledger["frame.scale"] = {"status": "derived", "source_id": source_id,
                             "assumption_id": None, "confidence": confidence}

    features: list[dict[str, Any]] = []
    for item in pixel_features or []:
        if not isinstance(item, Mapping):
            warnings.append("feature_malformed:missing_feature_id")
            continue
        fid = item.get("feature_id")
        if not isinstance(fid, str) or not fid:
            warnings.append("feature_malformed:missing_feature_id")
            continue
        kind = item.get("kind")
        raw_pixels = item.get("pixels")
        if kind not in _FEATURE_KINDS:
            ledger[fid] = {"status": "unknown", "source_id": source_id,
                           "assumption_id": None, "confidence": None}
            warnings.append(f"feature_unsupported_kind:{fid}")
            continue
        try:
            if kind == "point":
                pts = [_pixel(raw_pixels, f"features.{fid}.pixels")]
            else:
                if isinstance(raw_pixels, (str, bytes)) or not isinstance(raw_pixels, Sequence) \
                        or len(raw_pixels) < 2:
                    raise ValueError("polyline requires at least two pixel points")
                pts = [_pixel(p, f"features.{fid}.pixels[{i}]") for i, p in enumerate(raw_pixels)]
        except ValueError as exc:
            ledger[fid] = {"status": "unknown", "source_id": source_id,
                           "assumption_id": None, "confidence": None}
            warnings.append(f"feature_pixel_malformed:{fid}:{exc}")
            continue
        if not all(_in_bounds(p, width, height) for p in pts):
            ledger[fid] = {"status": "unknown", "source_id": source_id,
                           "assumption_id": None, "confidence": None}
            warnings.append(f"pixel_out_of_bounds:{fid}")
            continue
        ledger[f"{fid}.pixels"] = {"status": "observed", "source_id": source_id,
                                   "assumption_id": None, "confidence": 1.0}
        ledger[fid] = {"status": "derived", "source_id": source_id,
                       "assumption_id": None, "confidence": confidence}
        coords = [[p[0] * mean_scale, (height - p[1]) * mean_scale] for p in pts]
        features.append({"feature_id": fid, "kind": kind, "pixels": pts,
                         "coords_mm": coords[0] if kind == "point" else coords,
                         "provenance": "derived", "confidence": confidence})

    return CalibratedSource(verdict="CALIBRATED", frame=frame, features=features,
                            anchors=parsed_anchors, scale_disagreement_rel=disagreement,
                            confidence=confidence, provenance_ledger=ledger,
                            assumptions=assumptions, warnings=warnings)
