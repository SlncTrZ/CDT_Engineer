"""Feature-level provenance receipts and release QA (ENG-R11).
Wing: code | Topic: provenance-release | Updated: 2026-10-06 16:10 (Asia/Ho_Chi_Minh)
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from execution.release_scope import RELEASE_CLASSES

_PROVENANCE_STATES = {
    "observed",
    "specified",
    "derived",
    "inferred",
    "approved_assumption",
    "unknown",
}

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


def build_chunk_receipt(
    chunk: Mapping[str, Any],
    *,
    engine_receipt_id: str,
    created_or_modified_ids: Sequence[str],
    transaction_mode: str,
    verification_status: str = "pass",
    artifact_revision: str | None = None,
) -> dict[str, Any]:
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
    if (
        isinstance(feature_ids, (str, bytes))
        or not isinstance(feature_ids, Sequence)
        or not feature_ids
        or any(not isinstance(f, str) or not f for f in feature_ids)
    ):
        raise ValueError(f"{chunk_id}: chunk.feature_ids must be a non-empty string sequence")
    if len(feature_ids) != len(set(feature_ids)):
        raise ValueError(f"{chunk_id}: duplicate feature IDs")
    provenance = chunk.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError(f"{chunk_id}: chunk.provenance must be a mapping")
    carried = {
        fid: _provenance_status(chunk_id, fid, provenance.get(fid, "unknown"))
        for fid in feature_ids
    }
    # IA-03 side observation: a failed/unverified execution must never mint a
    # "committed" receipt. Receipt status follows verification evidence.
    if transaction_mode not in _TRANSACTION_MODES:
        raise ValueError(f"{chunk_id}: invalid transaction_mode: {transaction_mode}")
    if verification_status not in {"pass", "fail", "unknown"}:
        raise ValueError(f"{chunk_id}: invalid verification_status: {verification_status}")
    receipt_status = {"pass": "committed", "fail": "verification_failed", "unknown": "unverified"}[
        verification_status
    ]
    if isinstance(created_or_modified_ids, (str, bytes)) or not isinstance(
        created_or_modified_ids, Sequence
    ):
        raise ValueError(f"{chunk_id}: created_or_modified_ids must be a sequence")
    if any(
        not isinstance(native_id, str) or not native_id for native_id in created_or_modified_ids
    ):
        raise ValueError(f"{chunk_id}: native IDs must be non-empty strings")
    if verification_status == "pass" and not created_or_modified_ids:
        raise ValueError(f"{chunk_id}: verified creation receipt requires native IDs")
    if not isinstance(engine_receipt_id, str) or not engine_receipt_id:
        raise ValueError(f"{chunk_id}: engine_receipt_id must be a non-empty string")
    source_bindings = {}
    for key in (
        "source_sha256",
        "source_inventory_sha256",
        "plan_sha256",
        "planning_policy_sha256",
        "chunk_sha256",
    ):
        if key in chunk:
            value = chunk[key]
            if (
                not isinstance(value, str)
                or len(value) != 64
                or set(value) - set("0123456789abcdef")
            ):
                raise ValueError(f"{chunk_id}: invalid {key}")
            source_bindings[key] = value
    if ("source_sha256" in source_bindings) != ("source_inventory_sha256" in source_bindings):
        raise ValueError(f"{chunk_id}: incomplete source inventory binding")
    return {
        **source_bindings,
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


def assess_provenance_release(
    receipts: Sequence[Mapping[str, Any]],
    release_target: str,
    *,
    plan_ledger: Mapping[str, Any] | None = None,
    expected_chunks: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
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
    if expected_chunks is not None:
        from execution.plan_revise import plan_fingerprint

        if isinstance(expected_chunks, (str, bytes)) or not isinstance(expected_chunks, Sequence):
            raise ValueError("expected_chunks must be a sequence")
        expected = {}
        for chunk in expected_chunks:
            if not isinstance(chunk, Mapping):
                raise ValueError("expected chunks must contain mappings")
            cid = chunk.get("chunk_id")
            if not isinstance(cid, str) or not cid or cid in expected:
                raise ValueError("expected chunks must have unique non-empty chunk IDs")
            material = {
                k: v for k, v in chunk.items() if k not in {"chunk_sha256", "payload_bytes"}
            }
            if chunk.get("chunk_sha256") != plan_fingerprint(material):
                blockers.append(f"compiled_chunk_fingerprint_invalid:{cid}")
            expected[cid] = chunk
        seen = set()
        committed = set()
        for receipt in receipts:
            if not isinstance(receipt, Mapping):
                raise ValueError("each receipt must be a mapping")
            cid = receipt.get("chunk_id")
            if cid in seen:
                blockers.append(f"duplicate_chunk_receipt:{cid}")
            seen.add(cid)
            chunk = expected.get(cid)
            if chunk is None:
                blockers.append(f"unexpected_chunk_receipt:{cid}")
                continue
            for key in ("plan_sha256", "planning_policy_sha256", "chunk_sha256", "feature_ids"):
                if receipt.get(key) != chunk.get(key) or key not in chunk:
                    blockers.append(f"chunk_binding_mismatch:{cid}:{key}")
            for dependency in chunk.get("depends_on", []):
                if dependency not in committed:
                    blockers.append(f"chunk_dependency_not_verified:{cid}:{dependency}")
            verification = receipt.get("verification")
            if (
                receipt.get("status") == "committed"
                and isinstance(verification, Mapping)
                and verification.get("status") == "pass"
            ):
                committed.add(cid)
        blockers.extend(f"chunk_receipt_missing:{cid}" for cid in expected if cid not in seen)

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
            blockers.append(
                f"receipt_verification_contradiction:{chunk_id}:"
                f"status_committed_vs_verification_{verification_status}"
            )
            continue
        feature_ids = receipt.get("feature_ids", [])
        mode = receipt.get("transaction_mode")
        if mode not in _TRANSACTION_MODES:
            blockers.append(f"receipt_transaction_mode_missing_or_invalid:{chunk_id}")
            continue
        if mode == "nonrecoverable" and requested_index > _release_index("concept"):
            blockers.append(f"nonrecoverable_mutation_blocks_release:{chunk_id}")
            continue
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
                    blockers.append(
                        f"provenance_ledger_contradiction:{chunk_id}:{fid}:"
                        f"receipt_{status}_vs_ledger_{ledger_status}"
                    )
                    continue
                if status == "approved_assumption" and not entry.get("assumption_id"):
                    blockers.append(f"assumption_link_missing:{chunk_id}:{fid}")
                    continue
            ceiling_index = _release_index(ceiling)
            if requested_index > ceiling_index:
                blockers.append(
                    f"provenance_blocks_release:{chunk_id}:{fid}:{status}:max_{ceiling}"
                )
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
