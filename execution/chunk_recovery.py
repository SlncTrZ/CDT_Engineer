"""Forced-uncertainty chunk recovery with fingerprint reconciliation (ENG-R05).
Wing: code | Topic: chunk-recovery | Updated: 2026-09-18 02:10
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

_DECISIONS = {"committed", "adopted", "retry", "verify_first", "compensate", "blocked"}


def chunk_to_recovery_params(chunk: Mapping[str, Any]) -> dict[str, Any]:
    """Adapt a compiler semantic chunk to recovery `semantic_params`.

    Public integration contract (IA-04): compiler chunks carry `features`
    (ordered semantic feature mappings) plus parallel `feature_ids`; the
    recovery driver needs `{feature_id: params}`. Zipped positionally so no
    identity is invented or dropped. Malformed chunks fail closed.
    """
    if not isinstance(chunk, Mapping):
        raise ValueError("chunk must be a mapping")
    chunk_id = chunk.get("chunk_id", "?")
    feature_ids = chunk.get("feature_ids")
    features = chunk.get("features")
    if isinstance(feature_ids, (str, bytes)) or not isinstance(feature_ids, Sequence) \
            or not feature_ids:
        raise ValueError(f"{chunk_id}: chunk.feature_ids must be a non-empty sequence")
    if isinstance(features, (str, bytes)) or not isinstance(features, Sequence):
        raise ValueError(f"{chunk_id}: chunk.features must be a sequence")
    if len(feature_ids) != len(features):
        raise ValueError(f"{chunk_id}: feature_ids/features length mismatch")
    params: dict[str, Any] = {}
    for fid, feat in zip(feature_ids, features):
        if not isinstance(fid, str) or not fid:
            raise ValueError(f"{chunk_id}: feature ids must be non-empty strings")
        if not isinstance(feat, Mapping):
            raise ValueError(f"{chunk_id}:{fid}: feature must be a mapping")
        # A dict keyed by id would silently collapse duplicates, shrinking
        # the reconciled identity set. Duplicates fail closed instead.
        if fid in params:
            raise ValueError(f"{chunk_id}: duplicate feature id: {fid}")
        params[fid] = dict(feat)
    return params


def fingerprint_state(state: Mapping[str, Any]) -> str:
    """Deterministic identity fingerprint over ids AND properties.

    Entity counts alone cannot distinguish a correct commit from an impostor
    with the same count, so reconciliation compares this fingerprint, never
    just lengths.
    """
    if not isinstance(state, Mapping):
        raise ValueError("state must be a mapping")
    canonical = json.dumps({fid: state[fid] for fid in sorted(state)},
                           sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _expected_fingerprint(chunk: Mapping[str, Any]) -> tuple[str, list[str]]:
    params = chunk.get("semantic_params")
    if not isinstance(params, Mapping):
        raise ValueError(f"{chunk.get('chunk_id', '?')}: chunk.semantic_params must be a mapping")
    ids = sorted(params)
    return fingerprint_state(dict(params)), ids


def reconcile(expected_fingerprint: str, expected_ids: Sequence[str],
              observed: Mapping[str, Any] | None, *, last_outcome: str,
              attempts_used: int, max_attempts: int) -> dict[str, Any]:
    """Pure reconcile decision: observation evidence first, never blind replay.

    Decisions: committed | adopted | retry | verify_first | compensate | blocked.
    """
    if last_outcome not in {"committed", "failed", "uncertain"}:
        raise ValueError(f"invalid last_outcome: {last_outcome}")
    if attempts_used < 1 or max_attempts < 1:
        raise ValueError("attempts_used and max_attempts must be positive")

    def _blocked(reasons: list[str]) -> dict[str, Any]:
        return {"decision": "blocked", "reasons": reasons}

    if last_outcome == "committed":
        if observed is None:
            return _blocked(["committed_receipt_without_observable_state"])
        if fingerprint_state(observed) != expected_fingerprint:
            return _blocked(["fingerprint_mismatch:receipt_claims_committed"])
        if sorted(observed) != sorted(expected_ids):
            return _blocked(["identity_set_mismatch:receipt_claims_committed"])
        return {"decision": "committed", "reasons": []}

    if last_outcome == "failed":
        if attempts_used >= max_attempts:
            return _blocked(["attempt_budget_exhausted"])
        return {"decision": "retry", "reasons": ["explicit_failure_with_budget_remaining"]}

    # last_outcome == "uncertain": transport lost the receipt; the mutation
    # may have committed. Observation decides; replay is never the default.
    if observed is None:
        return {"decision": "verify_first",
                "reasons": ["verify_first_no_observation"]}
    if fingerprint_state(observed) == expected_fingerprint \
            and sorted(observed) == sorted(expected_ids):
        return {"decision": "adopted", "reasons": ["adopted_without_replay"]}
    observed_ids = set(observed)
    if observed_ids and observed_ids < set(expected_ids):
        if attempts_used >= max_attempts:
            return _blocked(["partial_state_without_retry_budget"])
        return {"decision": "compensate",
                "reasons": ["partial_state_compensate_before_retry"]}
    return _blocked(["fingerprint_mismatch:uncertain_state_unreconcilable"])


@dataclass(frozen=True)
class ChunkExecutionRecord:
    chunk_id: str
    final: str  # committed | blocked
    attempts: int
    decisions: list[str] = field(default_factory=list)
    observed_fingerprint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"chunk_id": self.chunk_id, "final": self.final,
                "attempts": self.attempts, "decisions": list(self.decisions),
                "observed_fingerprint": self.observed_fingerprint}


class _UncertainTransport(Exception):
    """Marker base: executor doubles raise their own transport errors.

    The driver treats any exception that is not an explicit failure receipt
    as uncertainty. Doubles signal explicit failure by returning
    {"outcome": "failed"} instead of raising.
    """


def execute_chunk_with_recovery(chunk: Mapping[str, Any],
                                execute: Callable[..., Any],
                                observe: Callable[[str], Mapping[str, Any] | None],
                                compensate: Callable[[str], Any],
                                *, max_attempts: int = 3,
                                idempotency_key: str | None = None) -> ChunkExecutionRecord:
    """Execute one chunk with forced-uncertainty reconciliation.

    - `execute(chunk, idempotency_key)` returns {"outcome", "state"} or raises
      on transport uncertainty; {"outcome": "failed"} means explicit failure.
    - `observe(chunk_id)` reads executor state independently of receipts and
      MUST return the current state mapping, or an EMPTY mapping as positive
      proof the chunk is absent. None (or raising) means NO observation, never
      proof of absence: a blind observer must not launder a dirty state into a
      retry. A receipt's own "state" is a producer claim, never verification
      evidence: every committed claim is re-checked against `observe` (IA-01).
    - `compensate(chunk_id)` removes partial state before any retry; recovery
      is verified by post-compensation `observe` (empty/absent), never by the
      compensation return value (IA-02).
    Retries reuse one idempotency key; uncertain state is reconciled from
    observation (fingerprint/identity/properties), never blindly replayed.
    """
    if not isinstance(chunk, Mapping):
        raise ValueError("chunk must be a mapping")
    chunk_id = chunk.get("chunk_id")
    if not isinstance(chunk_id, str) or not chunk_id:
        raise ValueError("chunk.chunk_id must be a non-empty string")
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    expected_fp, expected_ids = _expected_fingerprint(chunk)
    key = idempotency_key or f"{chunk_id}:attempt-1"

    decisions: list[str] = []
    attempts = 0
    while True:
        attempts += 1
        try:
            receipt = execute(chunk, key)
        except Exception:
            outcome, observed = "uncertain", _safe_observe(observe, chunk_id)
            verdict = reconcile(expected_fp, expected_ids, observed,
                                last_outcome=outcome, attempts_used=attempts,
                                max_attempts=max_attempts)
            return _settle(chunk_id, attempts, decisions, verdict, observed,
                           compensate, observe, execute, chunk, key,
                           expected_fp, expected_ids, max_attempts)
        if not isinstance(receipt, Mapping) or receipt.get("outcome") not in \
                {"committed", "failed"}:
            raise ValueError(f"{chunk_id}: executor must return committed/failed outcome")
        if receipt["outcome"] == "failed":
            verdict = reconcile(expected_fp, expected_ids, None,
                                last_outcome="failed", attempts_used=attempts,
                                max_attempts=max_attempts)
            if verdict["decision"] == "retry":
                decisions.append(f"retry_after_explicit_failure:attempt_{attempts}")
                continue
            decisions.extend(verdict["reasons"])
            return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, None)
        # IA-01: the receipt state is a producer claim. Verification evidence
        # comes only from the independent observer; a blind observer blocks.
        observed = _safe_observe(observe, chunk_id)
        verdict = reconcile(expected_fp, expected_ids, observed,
                            last_outcome="committed", attempts_used=attempts,
                            max_attempts=max_attempts)
        if verdict["decision"] == "committed":
            decisions.append(f"committed_verified_by_observation:attempt_{attempts}")
            fp = fingerprint_state(observed) if observed is not None else None
            return ChunkExecutionRecord(chunk_id, "committed", attempts, decisions, fp)
        decisions.extend(f"{r}:attempt_{attempts}" for r in verdict["reasons"])
        fp = fingerprint_state(observed) if observed is not None else None
        return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, fp)


def _safe_observe(observe: Callable[[str], Any], chunk_id: str) -> Mapping[str, Any] | None:
    try:
        observed = observe(chunk_id)
    except Exception:
        return None
    return observed if observed is None or isinstance(observed, Mapping) else None


def _settle(chunk_id: str, attempts: int, decisions: list[str], verdict: dict[str, Any],
            observed: Mapping[str, Any] | None, compensate: Callable[[str], Any],
            observe: Callable[[str], Any], execute: Callable[..., Any],
            chunk: Mapping[str, Any], key: str,
            expected_fp: str, expected_ids: list[str], max_attempts: int) -> ChunkExecutionRecord:
    decision = verdict["decision"]
    if decision == "adopted":
        decisions.append("adopted_without_replay")
        fp = fingerprint_state(observed) if observed is not None else None
        return ChunkExecutionRecord(chunk_id, "committed", attempts, decisions, fp)
    if decision == "verify_first":
        decisions.append("verify_first_no_observation")
        return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, None)
    if decision == "compensate":
        # IA-02: recovery is proven by post-compensation observed state, never
        # by the compensation return value. A no-op/false return, an exception,
        # or remaining state all block before any further execute call.
        try:
            compensate(chunk_id)
        except Exception as exc:
            decisions.append(f"compensation_failed:{exc}")
            return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, None)
        try:
            recovered = observe(chunk_id)
        except Exception as exc:
            decisions.append(f"compensation_unverifiable:{exc}")
            return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, None)
        if recovered is None:
            # Absence of evidence is not evidence of recovery: a None read
            # cannot distinguish "compensated" from "observer went blind".
            decisions.append("compensation_unverified_absent_unconfirmed")
            return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, None)
        if not isinstance(recovered, Mapping):
            decisions.append("compensation_unverified_observation_type")
            return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, None)
        if recovered:
            decisions.append("compensation_unverified_state_remains")
            fp = fingerprint_state(recovered)
            return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, fp)
        decisions.append("compensated_partial_state")
        return _retry_after_compensation(chunk_id, attempts, decisions, execute, observe,
                                         compensate, chunk, key, expected_fp,
                                         expected_ids, max_attempts)
    decisions.extend(verdict["reasons"])
    fp = fingerprint_state(observed) if observed is not None else None
    return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, fp)


def _retry_after_compensation(chunk_id: str, attempts: int, decisions: list[str],
                              execute: Callable[..., Any], observe: Callable[[str], Any],
                              compensate: Callable[[str], Any], chunk: Mapping[str, Any],
                              key: str, expected_fp: str, expected_ids: list[str],
                              max_attempts: int) -> ChunkExecutionRecord:
    if attempts >= max_attempts:
        decisions.append("attempt_budget_exhausted")
        return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, None)
    attempts += 1
    try:
        receipt = execute(chunk, key)
    except Exception:
        observed = _safe_observe(observe, chunk_id)
        verdict = reconcile(expected_fp, expected_ids, observed,
                            last_outcome="uncertain", attempts_used=attempts,
                            max_attempts=max_attempts)
        if verdict["decision"] == "adopted":
            decisions.append("adopted_without_replay")
            fp = fingerprint_state(observed) if observed is not None else None
            return ChunkExecutionRecord(chunk_id, "committed", attempts, decisions, fp)
        decisions.extend(verdict["reasons"])
        fp = fingerprint_state(observed) if observed is not None else None
        return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, fp)
    if not isinstance(receipt, Mapping) or receipt.get("outcome") != "committed":
        decisions.append("retry_after_compensation_not_committed")
        return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, None)
    # IA-01 applies after compensation as well: verify via observer.
    observed = _safe_observe(observe, chunk_id)
    verdict = reconcile(expected_fp, expected_ids, observed,
                        last_outcome="committed", attempts_used=attempts,
                        max_attempts=max_attempts)
    if verdict["decision"] == "committed":
        decisions.append(f"committed_verified_by_observation:attempt_{attempts}")
        fp = fingerprint_state(observed) if observed is not None else None
        return ChunkExecutionRecord(chunk_id, "committed", attempts, decisions, fp)
    decisions.extend(f"{r}:attempt_{attempts}" for r in verdict["reasons"])
    fp = fingerprint_state(observed) if observed is not None else None
    return ChunkExecutionRecord(chunk_id, "blocked", attempts, decisions, fp)
