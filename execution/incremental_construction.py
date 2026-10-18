"""Strict evidence gate for visible feature-chunk streaming.

Checks one actual committed model revision per stage; no fake progressive reveals.
Native receipt authenticity and physical geometry must still be verified separately.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

_SHA = re.compile(r"[0-9a-f]{64}\Z")


def assess_incremental_receipts(
    expected_stages: Sequence[str],
    receipts: Sequence[Mapping[str, object]],
    *,
    min_required_stages: int = 2,
    visible_progress_required: bool = True,
) -> dict[str, object]:
    reasons: list[str] = []
    if not isinstance(expected_stages, (list, tuple)) or len(expected_stages) < min_required_stages:
        reasons.append("insufficient_frozen_feature_plan")
    if not isinstance(receipts, (list, tuple)):
        return {"result": "blocked", "reason_codes": ["missing_stage_receipts"], "verified_stages": 0}
    if len(receipts) != len(expected_stages):
        reasons.append("stage_count_mismatch")
    if len(set(expected_stages)) != len(expected_stages):
        reasons.append("duplicate_expected_stage")
    seen: set[str] = set()
    hashes: set[str] = set()
    for i, stage in enumerate(expected_stages):
        if i >= len(receipts):
            reasons.append("missing_stage:" + str(stage))
            continue
        receipt = receipts[i]
        if not isinstance(receipt, Mapping):
            reasons.append("invalid_receipt:" + str(stage))
            continue
        if receipt.get("stage_id") != stage:
            reasons.append("out_of_order_or_wrong_stage:" + str(stage))
        if receipt.get("stage_no") != i + 1 or receipt.get("root_cursor") != i + 1:
            reasons.append("stage_cursor_mismatch:" + str(stage))
        if receipt.get("status") != "verified_committed":
            reasons.append("stage_not_verified_committed:" + str(stage))
        added = receipt.get("entities_added")
        if isinstance(added, bool) or not isinstance(added, int) or added < 1:
            reasons.append("no_new_entities:" + str(stage))
        revision = receipt.get("native_artifact_sha256")
        if revision is None:
            revision = receipt.get("native_skp_sha256")
        if not isinstance(revision, str) or not _SHA.fullmatch(revision):
            reasons.append("missing_artifact_revision:" + str(stage))
        elif revision in hashes:
            reasons.append("unchanged_artifact_revision:" + str(stage))
        else:
            hashes.add(revision)
        if visible_progress_required and not (
            isinstance(receipt.get("proof_image"), str)
            and receipt["proof_image"].strip()
        ):
            reasons.append("missing_stage_visual_evidence:" + str(stage))
        if stage in seen:
            reasons.append("duplicate_committed_stage:" + str(stage))
        seen.add(stage)
    return {
        "result": "pass" if not reasons else "blocked",
        "verified_stages": len(receipts),
        "reason_codes": reasons,
    }
