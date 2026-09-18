"""Deterministic PlanSpec revise loop: auto-fix, proposals, bounded re-validation.
Wing: code | Topic: plan-revise-loop | Updated: 2026-09-18 03:40
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Mapping

from execution.plan_review import review_plan_spec
from execution.planspec import validate_plan_spec

# Reason prefixes the loop may repair by deterministic recomputation from
# geometry. Everything else needs a manual design decision and becomes a
# proposal. The allowlist is deliberately narrow: recompute, never invent.
_AUTO_FIXABLE_PREFIXES = ("dimension_witness_mismatch:", "pavement_order_not_sequential:")

_SUGGESTIONS = (
    ("orphan_wall:", "reconnect both wall endpoints to the wall network or remove the isolated wall"),
    ("unjoined_tee:", "extend or trim the branch endpoint to a clean join on the host wall"),
    ("wall_overlap:", "merge or trim the overlapping colinear walls into one run"),
    ("opening_overlap:", "shift opening offsets along the host wall so spans no longer overlap"),
    ("opening_too_close_to_wall_end:", "move the opening inward or shorten the host wall opening band"),
    ("opening_exceeds_host_wall", "shorten the opening or lengthen the host wall"),
    ("column_off_grid:", "move the column center onto the declared grid axis"),
    ("column_off_intersection:", "move the column center onto the nearest grid intersection"),
    ("column_overlap:", "separate the overlapping column footprints"),
    ("fixture_outside_host_space:", "move the fixture inside its host space or reassign the host"),
    ("missing_layer:", "assign the lane layer name to the feature"),
    ("split_layer:", "unify the lane layer per feature kind"),
    ("missing_axes_grid", "declare the grid axes the walls and spaces are dimensioned from"),
    ("self_intersecting_boundary:", "reorder the space boundary polygon into a simple ring"),
    ("grade_declaration_mismatch", "reconcile the declared grade with the PVI geometry"),
    ("low_provenance_blocks_release:", "strengthen the feature evidence or lower the release target"),
)


def _suggestion_for(reason: str) -> str:
    for prefix, text in _SUGGESTIONS:
        if reason.startswith(prefix):
            return text
    return "manual design decision required"


def _witness_span(dimension: Mapping[str, Any]) -> float | None:
    points = dimension.get("witness_points", [])
    if len(points) != 2:
        return None
    try:
        return math.hypot(float(points[1][0]) - float(points[0][0]),
                          float(points[1][1]) - float(points[0][1]))
    except (TypeError, ValueError, IndexError):
        return None


def _fix_dimension(spec: Mapping[str, Any], feature_id: str) -> dict[str, Any] | None:
    for dimension in (spec.get("payload", {}).get("dimensions", []) or []):
        if isinstance(dimension, Mapping) and dimension.get("dimension_id") == feature_id:
            span = _witness_span(dimension)
            if span is None:
                return None
            old = dimension.get("measured_value")
            dimension["measured_value"] = span
            return {"reason": f"dimension_witness_mismatch:{feature_id}",
                    "feature_id": feature_id, "action": "recomputed_measured_from_witness_span",
                    "old_value": old, "new_value": span}
    return None


def _fix_pavement_order(spec: Mapping[str, Any]) -> dict[str, Any] | None:
    layers = (spec.get("payload", {}).get("pavement_structure", []) or [])
    if not layers or not all(isinstance(ly, Mapping) for ly in layers):
        return None
    old_orders = [ly.get("order") for ly in layers]
    for idx, layer in enumerate(sorted(layers, key=lambda ly: (ly.get("order") is None,
                                                               ly.get("order") or 0)), start=1):
        layer["order"] = idx
    return {"reason": "pavement_order_not_sequential",
            "feature_id": ",".join(str(ly.get("layer_id", "?")) for ly in layers),
            "action": "renumbered_pavement_orders_1_to_n preserving relative order",
            "old_value": old_orders,
            "new_value": [ly.get("order") for ly in layers]}


def _reason_feature_id(reason: str) -> str:
    head, _, _tail = reason.partition("(")
    core = head
    if ":" in core:
        core = core.split(":", 1)[1]
    return core.split(":")[0]


@dataclass(frozen=True)
class PlanReviseResult:
    approved: bool
    verdict: str  # "REVISED_APPROVED" | "NEEDS_MANUAL_DECISION"
    rounds: int
    applied_repairs: list[dict[str, Any]] = field(default_factory=list)
    proposals: list[dict[str, Any]] = field(default_factory=list)
    spec: dict[str, Any] = field(default_factory=dict)
    blocked_gates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "verdict": self.verdict,
            "rounds": self.rounds,
            "applied_repairs": [dict(r) for r in self.applied_repairs],
            "proposals": [dict(p) for p in self.proposals],
            "spec": copy.deepcopy(self.spec),
            "blocked_gates": list(self.blocked_gates),
        }


def revise_plan_spec(spec: Mapping[str, Any], requirements: Mapping[str, Any] | None = None, *,
                     max_rounds: int = 3,
                     repair_authorizations: Mapping[str, Any] | None = None) -> PlanReviseResult:
    """Revise a PlanSpec against review findings with a bounded auto-fix loop.

    Each round runs schema validation then the professional review. Reasons on
    the allowlist require explicit repair_authorizations keyed by dimension ID
    (action: recompute_dimension_from_witness) or pavement_structure (action:
    renumber_pavement_order), each with a nonempty evidence_ref. Dimensions must
    also have derived provenance; specified dimensions are never overwritten.
    The caller must validate authority and bind evidence to the current plan;
    this local function does not authenticate approval evidence. Other BLOCKER /
    MAJOR failures become structured proposals for a manual design decision.
    The input mapping is never mutated. Rounds are bounded by max_rounds.
    """
    if not isinstance(spec, Mapping):
        raise ValueError("spec must be a mapping")
    if isinstance(max_rounds, bool) or not isinstance(max_rounds, int) or max_rounds < 1:
        raise ValueError("max_rounds must be a positive integer")
    if repair_authorizations is not None and not isinstance(repair_authorizations, Mapping):
        raise ValueError("repair_authorizations must be a mapping")
    authorizations = copy.deepcopy(dict(repair_authorizations or {}))
    working: dict[str, Any] = copy.deepcopy(dict(spec))
    applied: list[dict[str, Any]] = []
    attempted: set[str] = set()
    rounds = 0

    while True:
        validity = validate_plan_spec(working)
        if not validity.valid:
            proposals = [{"finding_id": "R08-G0-planspec_valid", "gate": "planspec_valid",
                          "reason": error, "feature_refs": [],
                          "suggestion": "fix the schema violation manually; structure is not auto-repaired",
                          "auto_fixable": False} for error in validity.errors[:8]]
            return PlanReviseResult(approved=False, verdict="NEEDS_MANUAL_DECISION",
                                    rounds=rounds, applied_repairs=applied,
                                    proposals=proposals, spec=working,
                                    blocked_gates=["planspec_valid"])
        review = review_plan_spec(working, requirements)
        if review.approved:
            return PlanReviseResult(approved=True, verdict="REVISED_APPROVED",
                                    rounds=rounds, applied_repairs=applied,
                                    proposals=[], spec=working, blocked_gates=[])
        if rounds >= max_rounds:
            return PlanReviseResult(approved=False, verdict="NEEDS_MANUAL_DECISION",
                                    rounds=rounds, applied_repairs=applied,
                                    proposals=_proposals(review, attempted, working, authorizations),
                                    spec=working, blocked_gates=list(review.blocked_gates))
        fixed_this_round = _apply_allowlisted_fixes(working, review, attempted, applied, authorizations)
        if not fixed_this_round:
            return PlanReviseResult(approved=False, verdict="NEEDS_MANUAL_DECISION",
                                    rounds=rounds, applied_repairs=applied,
                                    proposals=_proposals(review, attempted, working, authorizations),
                                    spec=working, blocked_gates=list(review.blocked_gates))
        rounds += 1


def _blocking_reasons(review) -> list[tuple[str, str, str, list[str]]]:
    out: list[tuple[str, str, str, list[str]]] = []
    for finding in review.findings:
        if finding["severity"] in ("BLOCKER", "MAJOR") and finding["result"] in ("fail", "unknown"):
            for reason in finding["reason_codes"]:
                out.append((finding["finding_id"], finding["gate"], reason, list(finding["feature_refs"])))
    return out


def _repair_authorization(spec, reason: str, authorizations) -> Mapping[str, Any] | None:
    if reason.startswith("dimension_witness_mismatch:"):
        target = _reason_feature_id(reason)
        provenance = spec.get("provenance_ledger", {}).get(target, {})
        if provenance.get("status") != "derived":
            return None
        action = "recompute_dimension_from_witness"
    elif reason.startswith("pavement_order_not_sequential:"):
        target = "pavement_structure"
        action = "renumber_pavement_order"
    else:
        return None
    authorization = authorizations.get(target)
    if not isinstance(authorization, Mapping) or authorization.get("action") != action:
        return None
    evidence = authorization.get("evidence_ref")
    if not isinstance(evidence, str) or not evidence.strip():
        return None
    return authorization


def _proposals(review, attempted: set[str], working, authorizations) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    seen: set[str] = set()
    for finding_id, gate, reason, refs in _blocking_reasons(review):
        key = f"{finding_id}:{reason}"
        if key in seen:
            continue
        seen.add(key)
        proposals.append({
            "finding_id": finding_id,
            "gate": gate,
            "reason": reason,
            "feature_refs": refs,
            "suggestion": _suggestion_for(reason),
            "auto_fixable": _repair_authorization(working, reason, authorizations) is not None
                             and key not in attempted,
        })
    return proposals


def _apply_allowlisted_fixes(working: dict[str, Any], review, attempted: set[str],
                             applied: list[dict[str, Any]], authorizations) -> bool:
    fixed = False
    for finding_id, _gate, reason, _refs in _blocking_reasons(review):
        key = f"{finding_id}:{reason}"
        if key in attempted:
            continue
        if not any(reason.startswith(p) for p in _AUTO_FIXABLE_PREFIXES):
            continue
        authorization = _repair_authorization(working, reason, authorizations)
        if authorization is None:
            continue
        attempted.add(key)
        repair = None
        if reason.startswith("dimension_witness_mismatch:"):
            repair = _fix_dimension(working, _reason_feature_id(reason))
        elif reason.startswith("pavement_order_not_sequential:"):
            repair = _fix_pavement_order(working)
        if repair is not None:
            repair["authorization_evidence_ref"] = authorization["evidence_ref"]
            applied.append(repair)
            fixed = True
    return fixed
