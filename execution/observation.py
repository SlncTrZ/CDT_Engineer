"""Independent observation contract for execution read-back evidence.
Wing: code | Topic: observation-contract | Updated: 2026-09-19
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from execution.chunk_recovery import fingerprint_state

_STATUSES = {"observed", "absent", "unavailable", "unsupported"}


def _nonempty_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def assess_observation(
    observation: Mapping[str, Any],
    *,
    expected_semantic_id: str,
    expected_revision: str,
    expected_native_id: str | None = None,
    expected_state: Mapping[str, Any] | None = None,
    expect_absent: bool = False,
) -> dict[str, Any]:
    """Assess one independent read-back receipt against caller-planned identity/state."""
    if not isinstance(observation, Mapping):
        raise ValueError("observation must be a mapping")
    _nonempty_text(expected_semantic_id, "expected_semantic_id")
    _nonempty_text(expected_revision, "expected_revision")
    if expected_native_id is not None:
        _nonempty_text(expected_native_id, "expected_native_id")
    if not isinstance(expect_absent, bool):
        raise ValueError("expect_absent must be bool")

    observation_id = _nonempty_text(observation.get("observation_id"), "observation_id")
    _nonempty_text(observation.get("observer_id"), "observer_id")
    _nonempty_text(observation.get("method"), "method")
    semantic_id = _nonempty_text(observation.get("semantic_id"), "semantic_id")
    observed_revision = _nonempty_text(observation.get("observed_revision"), "observed_revision")
    status = observation.get("status")
    if status not in _STATUSES:
        raise ValueError(f"{observation_id}: invalid observation status: {status!r}")

    native_id = observation.get("native_id")
    if native_id is not None:
        _nonempty_text(native_id, "native_id")

    precision = observation.get("precision")
    if precision is not None:
        if isinstance(precision, bool) or not isinstance(precision, (int, float)) \
                or not math.isfinite(precision) or precision < 0:
            raise ValueError("precision must be finite nonnegative numeric")

    confidence = observation.get("confidence")
    if confidence is not None:
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) \
                or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("confidence must be within [0, 1]")

    if status in {"unavailable", "unsupported"}:
        return {
            "result": "unknown",
            "verified": False,
            "observation_id": observation_id,
            "reason_codes": [f"observation_{status}"],
        }

    reasons: list[str] = []
    if semantic_id != expected_semantic_id:
        reasons.append("semantic_identity_mismatch")
    if observed_revision != expected_revision:
        reasons.append("observation_revision_stale")
    if expected_native_id is not None and native_id != expected_native_id:
        reasons.append("native_identity_mismatch")

    state = observation.get("state")
    if status == "absent":
        if state not in ({}, None):
            reasons.append("absence_state_contradiction")
        if not expect_absent:
            reasons.append("unexpected_absence")
    else:
        if expect_absent:
            reasons.append("unexpected_presence")
        if not isinstance(state, Mapping):
            reasons.append("observed_state_missing")
        elif expected_state is not None:
            if not isinstance(expected_state, Mapping):
                raise ValueError("expected_state must be a mapping")
            if fingerprint_state(state) != fingerprint_state(expected_state):
                reasons.append("state_fingerprint_mismatch")

    return {
        "result": "blocked" if reasons else "pass",
        "verified": not reasons,
        "observation_id": observation_id,
        "reason_codes": reasons,
        "observed_state_fingerprint": (
            fingerprint_state(state) if isinstance(state, Mapping) and status == "observed" else None
        ),
    }
