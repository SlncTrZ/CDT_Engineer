"""Feature-level provenance receipts and release QA (ENG-R11).
Wing: code | Topic: provenance-release | Updated: 2026-09-18 01:20
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from execution.release_scope import RELEASE_CLASSES

_PROVENANCE_STATES = {"observed", "specified", "derived", "inferred", "approved_assumption", "unknown"}

# Strongest release each evidence state can support. Mirrors the casework
# ceiling convention: inference caps at concept, unknown supports nothing.
PROVENANCE_MAX_RELEASE: dict[str, str | None] = {
    "observed": "design_review",
    "specified": "design_review",
    "derived": "design_review",
    "approved_assumption": "design_review",
    "inferred": "concept",
    "unknown": None,
}

_TRANSACTION_MODES = {"native_atomic", "checkpointed_atomic", "compensating", "nonrecoverable"}

# Passing states still worth flagging on the release record.
_TRACEABLE_LIMITATION_STATES = {"approved_assumption", "inferred"}


def _release_index(value: str) -> int:
    if value not in RELEASE_CLASSES:
        raise ValueError(f"invalid release class: {value}")
    return RELEASE_CLASSES.index(value)


def _provenance_status(chunk_id: str, fid: str, status: Any) -> str:
    if not isinstance(status, str) or status not in _PROVENANCE_STATES:
        raise ValueError(f"{chunk_id}:{fid}: invalid provenance status: {status!r}")
    return status


def build_chunk_receipt(chunk: Mapping[str, Any], *, engine_receipt_id: str,
                        created_or_modified_ids: Sequence[str],
                        transaction_mode: str,
                        verification_status: str = "pass",
                        artifact_revision: str | None = None) -> dict[str, Any]:
    """Build a traceable chunk receipt that preserves per-feature provenance.

    Provenance metadata flows compiler chunk -> receipt -> release QA without
    being reduced to entity counts. Malformed chunks fail closed.
    """
    if not isinstance(chunk, Mapping):
        raise ValueError("chunk must be a mapping")
    chunk_id = chunk.get("chunk_id")
    if not isinstance(chunk_id, str) or not chunk_id:
        raise ValueError("chunk.chunk_id must be a non-empty string")
    feature_ids = chunk.get("feature_ids")
    if isinstance(feature_ids, (str, bytes)) or not isinstance(feature_ids, Sequence) \
            or not feature_ids or any(not isinstance(f, str) or not f for f in feature_ids):
        raise ValueError(f"{chunk_id}: chunk.feature_ids must be a non-empty string sequence")
    provenance = chunk.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError(f"{chunk_id}: chunk.provenance must be a mapping")
    carried = {fid: _provenance_status(chunk_id, fid, provenance.get(fid, "unknown"))
               for fid in feature_ids}
    # IA-03 side observation: a failed/unverified execution must never mint a
    # "committed" receipt. Receipt status follows verification evidence.
    receipt_status = {"pass": "committed", "fail": "verification_failed",
                      "unknown": "unverified"}[verification_status]
    if transaction_mode not in _TRANSACTION_MODES:
        raise ValueError(f"{chunk_id}: invalid transaction_mode: {transaction_mode}")
    if verification_status not in {"pass", "fail", "unknown"}:
        raise ValueError(f"{chunk_id}: invalid verification_status: {verification_status}")
    if isinstance(created_or_modified_ids, (str, bytes)) or not isinstance(created_or_modified_ids, Sequence):
        raise ValueError(f"{chunk_id}: created_or_modified_ids must be a sequence")
    if not isinstance(engine_receipt_id, str) or not engine_receipt_id:
        raise ValueError(f"{chunk_id}: engine_receipt_id must be a non-empty string")
    return {
        "chunk_id": chunk_id,
        "batch_session_id": chunk.get("batch_session_id"),
        "semantic_type": chunk.get("semantic_type"),
        "feature_ids": list(feature_ids),
        "provenance": carried,
        "status": receipt_status,
        "transaction_mode": transaction_mode,
        "engine_receipt_id": engine_receipt_id,
        "created_or_modified_ids": list(created_or_modified_ids),
        "verification": {"status": verification_status},
        "artifact_revision": artifact_revision,
    }


def assess_provenance_release(receipts: Sequence[Mapping[str, Any]], release_target: str, *,
                             plan_ledger: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Gate a release target on per-feature provenance carried by chunk receipts.

    A stronger release is never silently granted: any feature whose evidence
    ceiling sits below the request blocks with an explicit reason and a
    recommended lower target. `unknown` blocks every release class.
    When `plan_ledger` is supplied, `approved_assumption` features must link
    to a ledger assumption id or they block as well.
    """
    requested_index = _release_index(release_target)
    if isinstance(receipts, (str, bytes)) or not isinstance(receipts, Sequence):
        raise ValueError("receipts must be a sequence")
    if plan_ledger is not None and not isinstance(plan_ledger, Mapping):
        raise ValueError("plan_ledger must be a mapping")

    blockers: list[str] = []
    limitations: list[str] = []
    reduction_candidates: list[str] = []
    feature_count = 0

    if not receipts:
        return {
            "result": "blocked",
            "requested_release_target": release_target,
            "effective_release_target": None,
            "recommended_release_target": None,
            "receipt_count": 0,
            "feature_count": 0,
            "limitations": [],
            "reason_codes": ["no_chunk_receipts"],
        }

    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            raise ValueError("each receipt must be a mapping")
        chunk_id = receipt.get("chunk_id", "?")
        # IA-03 + follow-up: only verified-committed execution evidence is
        # assessable. A missing status is never defaulted to committed, and a
        # "committed" top-level status contradicting its own verification
        # evidence blocks instead of passing.
        top_status = receipt.get("status")
        if top_status is None:
            blockers.append(f"receipt_status_missing:{chunk_id}")
            continue
        if top_status != "committed":
            blockers.append(f"receipt_not_committed:{chunk_id}:{top_status}")
            continue
        verification = receipt.get("verification")
        if not isinstance(verification, Mapping):
            blockers.append(f"receipt_verification_missing:{chunk_id}")
            continue
        verification_status = verification.get("status")
        if verification_status != "pass":
            blockers.append(f"receipt_verification_contradiction:{chunk_id}:"
                            f"status_committed_vs_verification_{verification_status}")
            continue
        feature_ids = receipt.get("feature_ids", [])
        if isinstance(feature_ids, (str, bytes)) or not isinstance(feature_ids, Sequence):
            raise ValueError(f"{chunk_id}: receipt.feature_ids must be a sequence")
        if not feature_ids:
            blockers.append(f"empty_receipt_feature_set:{chunk_id}")
            continue
        provenance = receipt.get("provenance")
        if not isinstance(provenance, Mapping):
            raise ValueError(f"{chunk_id}: receipt.provenance must be a mapping")
        # IA-03: every declared feature must carry a provenance entry; an
        # empty provenance mapping no longer yields a vacuous pass.
        for fid in feature_ids:
            if fid not in provenance:
                blockers.append(f"provenance_coverage_missing:{chunk_id}:{fid}")
        for fid, status in provenance.items():
            status = _provenance_status(chunk_id, fid, status)
            feature_count += 1
            ceiling = PROVENANCE_MAX_RELEASE[status]
            if ceiling is None:
                blockers.append(f"unknown_provenance_blocks_release:{chunk_id}:{fid}")
                continue
            if plan_ledger is not None:
                entry = plan_ledger.get(fid)
                if not isinstance(entry, Mapping):
                    blockers.append(f"provenance_ledger_missing:{chunk_id}:{fid}")
                    continue
                ledger_status = entry.get("status")
                if not isinstance(ledger_status, str) or ledger_status not in _PROVENANCE_STATES:
                    raise ValueError(f"{chunk_id}:{fid}: invalid ledger status: {ledger_status!r}")
                # IA-03: receipt evidence contradicting the plan ledger blocks;
                # execution must not upgrade what the plan recorded.
                if ledger_status != status:
                    blockers.append(f"provenance_ledger_contradiction:{chunk_id}:{fid}:"
                                    f"receipt_{status}_vs_ledger_{ledger_status}")
                    continue
                if status == "approved_assumption" and not entry.get("assumption_id"):
                    blockers.append(f"assumption_link_missing:{chunk_id}:{fid}")
                    continue
            ceiling_index = _release_index(ceiling)
            if requested_index > ceiling_index:
                blockers.append(f"provenance_blocks_release:{chunk_id}:{fid}:{status}:max_{ceiling}")
                reduction_candidates.append(ceiling)
            elif status in _TRACEABLE_LIMITATION_STATES:
                limitations.append(f"provenance:{chunk_id}:{fid}:{status}")

    recommended = None
    if reduction_candidates:
        recommended = min(reduction_candidates, key=_release_index)
    blocked = bool(blockers)
    return {
        "result": "blocked" if blocked else "pass",
        "requested_release_target": release_target,
        "effective_release_target": None if blocked else release_target,
        "recommended_release_target": recommended,
        "receipt_count": len(receipts),
        "feature_count": feature_count,
        "limitations": list(dict.fromkeys(limitations)),
        "reason_codes": list(dict.fromkeys(blockers)),
    }
