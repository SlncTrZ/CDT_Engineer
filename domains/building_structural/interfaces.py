"""Building Structural Architecture↔Structural interface guards.
Wing: code | Topic: building-structural | Updated: 2026-09-19

This module intentionally implements only the cross-discipline pair consumed by
the current Building Architecture and Building Structural verticals. Additional
pairs require real consumers rather than an empty universal interface framework.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from domains.guard_primitives import GuardInputError

_PAIR = frozenset({"building-architecture", "building-structural"})
_ALLOWED_STATUS = frozenset({"open", "accepted", "rejected", "not_applicable"})
_ALLOWED_VERIFICATION = frozenset({"verified", "unverified", "stale"})
_ALLOWED_CONFLICT_STATE = frozenset({"none", "open", "resolved"})


def _text(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuardInputError(f"{name} must be a non-empty string")
    return value


def _refs(value, name: str) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise GuardInputError(f"{name} must be a sequence")
    refs = list(value)
    if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
        raise GuardInputError(f"{name} must contain non-empty strings")
    return refs


def _compile_current_revisions(current_revisions: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(current_revisions, Mapping):
        raise GuardInputError("current_revisions must be a mapping")
    compiled: dict[str, str] = {}
    for discipline, revision in current_revisions.items():
        if discipline not in _PAIR:
            raise GuardInputError(f"unsupported current revision discipline: {discipline}")
        compiled[discipline] = _text(revision, f"current_revisions.{discipline}")
    return compiled


def evaluate_architecture_structural_interfaces(
    records: Sequence[Mapping],
    *,
    current_revisions: Mapping[str, str],
    expected_unit_system: str,
    expected_coordinate_frame_id: str,
) -> dict:
    """Gate Architecture↔Structural handoffs on current revision and coordination evidence.

    The caller supplies independently discovered current discipline revisions plus
    the project unit/frame convention. A record that merely self-reports a verified
    state cannot survive an upstream revision mismatch.
    """
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise GuardInputError("interface records must be a sequence")

    current = _compile_current_revisions(current_revisions)
    expected_units = _text(expected_unit_system, "expected_unit_system")
    expected_frame = _text(expected_coordinate_frame_id, "expected_coordinate_frame_id")

    reasons: list[str] = []
    normalized: list[dict] = []
    seen: set[str] = set()

    for index, raw in enumerate(records):
        if not isinstance(raw, Mapping):
            raise GuardInputError("each interface record must be a mapping")

        interface_id = _text(raw.get("interface_id"), f"interfaces[{index}].interface_id")
        if interface_id in seen:
            raise GuardInputError(f"duplicate interface_id: {interface_id}")
        seen.add(interface_id)

        from_discipline = _text(raw.get("from_discipline"), f"{interface_id}.from_discipline")
        to_discipline = _text(raw.get("to_discipline"), f"{interface_id}.to_discipline")
        if frozenset({from_discipline, to_discipline}) != _PAIR or from_discipline == to_discipline:
            raise GuardInputError(
                f"{interface_id}: only Building Architecture↔Building Structural is supported in this lane"
            )

        owner = _text(raw.get("owner_discipline"), f"{interface_id}.owner_discipline")
        if owner not in {from_discipline, to_discipline}:
            raise GuardInputError(
                f"{interface_id}: owner_discipline must be one of the participating disciplines"
            )

        interface_type = _text(raw.get("interface_type"), f"{interface_id}.interface_type")
        source_revision = _text(raw.get("source_revision"), f"{interface_id}.source_revision")
        handoff_revision = _text(raw.get("handoff_revision"), f"{interface_id}.handoff_revision")
        unit_system = _text(raw.get("unit_system"), f"{interface_id}.unit_system")
        coordinate_frame_id = _text(
            raw.get("coordinate_frame_id"), f"{interface_id}.coordinate_frame_id"
        )

        required = raw.get("required")
        if not isinstance(required, bool):
            raise GuardInputError(f"{interface_id}.required must be bool")

        status = _text(raw.get("status"), f"{interface_id}.status")
        if status not in _ALLOWED_STATUS:
            raise GuardInputError(f"{interface_id}: unsupported interface status")

        verification = _text(raw.get("verification_state"), f"{interface_id}.verification_state")
        if verification not in _ALLOWED_VERIFICATION:
            raise GuardInputError(f"{interface_id}: unsupported verification state")

        conflict_state = _text(raw.get("conflict_state"), f"{interface_id}.conflict_state")
        if conflict_state not in _ALLOWED_CONFLICT_STATE:
            raise GuardInputError(f"{interface_id}: unsupported conflict state")

        evidence = _refs(raw.get("evidence_refs"), f"{interface_id}.evidence_refs")
        conflict_owner = raw.get("conflict_owner_discipline")
        conflict_evidence = _refs(
            raw.get("conflict_evidence_refs", []), f"{interface_id}.conflict_evidence_refs"
        )
        if conflict_owner is not None:
            conflict_owner = _text(conflict_owner, f"{interface_id}.conflict_owner_discipline")
            if conflict_owner not in {from_discipline, to_discipline}:
                raise GuardInputError(
                    f"{interface_id}: conflict_owner_discipline must be a participating discipline"
                )

        item_reasons: list[str] = []
        current_source_revision = current.get(from_discipline)
        if current_source_revision is None:
            item_reasons.append(f"current_source_revision_missing:{interface_id}")
        elif source_revision != current_source_revision:
            item_reasons.append(f"interface_source_revision_stale:{interface_id}")

        if unit_system != expected_units:
            item_reasons.append(f"interface_unit_system_mismatch:{interface_id}")
        if coordinate_frame_id != expected_frame:
            item_reasons.append(f"interface_coordinate_frame_mismatch:{interface_id}")

        if conflict_state == "open":
            item_reasons.append(f"interface_conflict_open:{interface_id}")
        elif conflict_state == "resolved":
            if conflict_owner is None:
                item_reasons.append(f"resolved_conflict_owner_missing:{interface_id}")
            if not conflict_evidence:
                item_reasons.append(f"resolved_conflict_evidence_missing:{interface_id}")

        if required and status not in {"accepted", "not_applicable"}:
            item_reasons.append(f"required_interface_unresolved:{interface_id}")
        if required and status == "not_applicable":
            if verification != "verified":
                item_reasons.append(f"not_applicable_interface_not_verified:{interface_id}")
            if not evidence:
                item_reasons.append(f"not_applicable_interface_without_evidence:{interface_id}")
        if status == "accepted" and verification != "verified":
            item_reasons.append(f"accepted_interface_not_verified:{interface_id}")
        if status == "accepted" and not evidence:
            item_reasons.append(f"accepted_interface_evidence_missing:{interface_id}")
        if verification == "stale":
            item_reasons.append(f"interface_evidence_stale:{interface_id}")

        reasons.extend(item_reasons)
        normalized.append(
            {
                "interface_id": interface_id,
                "from_discipline": from_discipline,
                "to_discipline": to_discipline,
                "interface_type": interface_type,
                "owner_discipline": owner,
                "required": required,
                "status": status,
                "verification_state": verification,
                "source_revision": source_revision,
                "current_source_revision": current_source_revision,
                "handoff_revision": handoff_revision,
                "unit_system": unit_system,
                "coordinate_frame_id": coordinate_frame_id,
                "conflict_state": conflict_state,
                "conflict_owner_discipline": conflict_owner,
                "conflict_evidence_refs": conflict_evidence,
                "evidence_refs": evidence,
                "reason_codes": item_reasons,
            }
        )

    return {
        "result": "blocked" if reasons else "pass",
        "reason_codes": reasons,
        "interfaces": normalized,
        "expected_unit_system": expected_units,
        "expected_coordinate_frame_id": expected_frame,
        "current_revisions": current,
    }
