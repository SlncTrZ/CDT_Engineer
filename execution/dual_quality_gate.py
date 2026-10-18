"""Deterministic, revision-bound aggregation of independent technical and visual gates.

This helper checks evidence completeness/identity, not native measurements or subjective
aesthetic correctness. A human/independent Checker supplies the factual gate results.
"""
from __future__ import annotations

import re
from collections.abc import Mapping

_SHA256 = re.compile(r"[a-f0-9]{64}\Z")


def assess_dual_quality_gate(
    *,
    artifact_sha256: str,
    technical_gate: Mapping[str, object] | None,
    visual_gate: Mapping[str, object] | None,
    visual_artifact: bool = True,
    required_visual_views: tuple[str, ...] = ("overall", "detail"),
) -> dict[str, object]:
    """Fail closed unless both independently evidenced gates pass for identical bytes.

    Gate input: status, artifact_sha256, evidence_refs, reviewer, reviewer_role,
    independent (boolean). A visual gate may be not_applicable only for genuinely
    nonvisual deliverables and with na_reason, na_approved_by and evidence.
    """
    reasons: list[str] = []
    if not isinstance(artifact_sha256, str) or not _SHA256.fullmatch(artifact_sha256):
        reasons.append("artifact_identity_missing_or_invalid")
    gate_statuses: dict[str, str] = {}
    for label, data in (("technical_gate", technical_gate), ("visual_gate", visual_gate)):
        if not isinstance(data, Mapping):
            gate_statuses[label] = "unknown"
            reasons.append(label + ":missing")
            continue
        status = data.get("status")
        gate_statuses[label] = status if isinstance(status, str) else "unknown"
        if status not in ("pass", "fail", "unknown", "not_applicable"):
            reasons.append(label + ":invalid_status")
        elif status in ("fail", "unknown"):
            reasons.append(label + ":" + status)
        elif status == "not_applicable":
            if label == "technical_gate" or visual_artifact:
                reasons.append(label + ":not_applicable_for_visual_artifact")
            elif not (
                isinstance(data.get("na_reason"), str) and data["na_reason"].strip()
                and isinstance(data.get("na_approved_by"), str)
                and data["na_approved_by"].strip()
            ):
                reasons.append(label + ":unapproved_not_applicable")
        if label == "visual_gate" and visual_artifact and status == "pass":
            views = data.get("view_types")
            if not isinstance(views, (list, tuple)) or any(
                view not in views for view in required_visual_views
            ):
                reasons.append("visual_gate:required_views_missing")
        if data.get("artifact_sha256") != artifact_sha256:
            reasons.append(label + ":artifact_revision_mismatch")
        refs = data.get("evidence_refs")
        if not isinstance(refs, (list, tuple)) or not refs or any(
            not isinstance(x, str) or not x.strip() for x in refs
        ):
            reasons.append(label + ":evidence_missing")
        for field in ("reviewer", "reviewer_role"):
            if not isinstance(data.get(field), str) or not data[field].strip():
                reasons.append(label + ":" + field + "_missing")
        if data.get("independent") is not True:
            reasons.append(label + ":independent_review_missing")
    return {
        "result": "pass" if not reasons else "blocked",
        "technical_gate": gate_statuses.get("technical_gate", "unknown"),
        "visual_gate": gate_statuses.get("visual_gate", "unknown"),
        "artifact_sha256": artifact_sha256,
        "reason_codes": reasons,
    }
