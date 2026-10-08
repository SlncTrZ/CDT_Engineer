"""Dependency impact and revision-bound evidence freshness for Engineering OS.
Wing: code | Topic: dependency-impact | Updated: 2026-09-19
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _compile_nodes(nodes: Sequence[Mapping[str, Any]]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    if isinstance(nodes, (str, bytes)) or not isinstance(nodes, Sequence):
        raise ValueError("nodes must be a sequence")
    order: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    for raw in nodes:
        if not isinstance(raw, Mapping):
            raise ValueError("each node must be a mapping")
        node_id = raw.get("node_id")
        revision = raw.get("revision")
        depends_on = raw.get("depends_on", [])
        if not isinstance(node_id, str) or not node_id:
            raise ValueError("node_id must be a non-empty string")
        if node_id in by_id:
            raise ValueError(f"duplicate node_id: {node_id}")
        if not isinstance(revision, str) or not revision:
            raise ValueError(f"{node_id}: revision must be a non-empty string")
        if isinstance(depends_on, (str, bytes)) or not isinstance(depends_on, Sequence):
            raise ValueError(f"{node_id}: depends_on must be a sequence")
        deps: list[str] = []
        for dep in depends_on:
            if not isinstance(dep, str) or not dep:
                raise ValueError(f"{node_id}: dependency ids must be non-empty strings")
            if dep in deps:
                raise ValueError(f"{node_id}: duplicate dependency: {dep}")
            deps.append(dep)
        order.append(node_id)
        by_id[node_id] = {"node_id": node_id, "revision": revision, "depends_on": deps}

    for node_id in order:
        for dep in by_id[node_id]["depends_on"]:
            if dep not in by_id:
                raise ValueError(f"{node_id}: dangling dependency: {dep}")
            if dep == node_id:
                raise ValueError(f"{node_id}: self dependency")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            raise ValueError(f"dependency cycle detected at: {node_id}")
        if node_id in visited:
            return
        visiting.add(node_id)
        for dep in by_id[node_id]["depends_on"]:
            visit(dep)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in order:
        visit(node_id)
    return order, by_id


def _dependency_closure(subject_id: str, by_id: Mapping[str, Mapping[str, Any]]) -> set[str]:
    required: set[str] = set()

    def collect(node_id: str) -> None:
        if node_id in required:
            return
        required.add(node_id)
        for dep in by_id[node_id]["depends_on"]:
            collect(dep)

    collect(subject_id)
    return required


def compute_impact(
    nodes: Sequence[Mapping[str, Any]],
    changed_ids: Sequence[str],
) -> dict[str, list[str]]:
    """Return exact transitive impact from one or more changed dependency nodes."""
    order, by_id = _compile_nodes(nodes)
    if isinstance(changed_ids, (str, bytes)) or not isinstance(changed_ids, Sequence):
        raise ValueError("changed_ids must be a sequence")
    changed: list[str] = []
    for node_id in changed_ids:
        if not isinstance(node_id, str) or not node_id:
            raise ValueError("changed_ids must contain non-empty strings")
        if node_id not in by_id:
            raise ValueError(f"unknown changed node: {node_id}")
        if node_id not in changed:
            changed.append(node_id)

    impacted = set(changed)
    progressed = True
    while progressed:
        progressed = False
        for node_id in order:
            if node_id in impacted:
                continue
            if any(dep in impacted for dep in by_id[node_id]["depends_on"]):
                impacted.add(node_id)
                progressed = True

    return {
        "changed_ids": [node_id for node_id in order if node_id in set(changed)],
        "impacted_ids": [node_id for node_id in order if node_id in impacted],
        "unaffected_ids": [node_id for node_id in order if node_id not in impacted],
    }


def assess_evidence_freshness(
    nodes: Sequence[Mapping[str, Any]],
    evidence: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Verify evidence binds the subject and every transitive dependency revision."""
    order, by_id = _compile_nodes(nodes)
    order_index = {node_id: index for index, node_id in enumerate(order)}
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise ValueError("evidence must be a sequence")

    stale: list[str] = []
    current: list[str] = []
    reasons_by_evidence: dict[str, list[str]] = {}
    seen: set[str] = set()

    for record in evidence:
        if not isinstance(record, Mapping):
            raise ValueError("each evidence record must be a mapping")
        evidence_id = record.get("evidence_id")
        subject_id = record.get("subject_id")
        bindings = record.get("bound_revisions")
        if not isinstance(evidence_id, str) or not evidence_id:
            raise ValueError("evidence_id must be a non-empty string")
        if evidence_id in seen:
            raise ValueError(f"duplicate evidence_id: {evidence_id}")
        seen.add(evidence_id)
        if not isinstance(subject_id, str) or subject_id not in by_id:
            raise ValueError(f"{evidence_id}: unknown subject_id")
        if not isinstance(bindings, Mapping):
            raise ValueError(f"{evidence_id}: bound_revisions must be a mapping")

        unknown_bindings = sorted(set(bindings) - set(by_id))
        if unknown_bindings:
            raise ValueError(
                f"{evidence_id}: unknown bound revision nodes: {','.join(unknown_bindings)}"
            )

        required = _dependency_closure(subject_id, by_id)
        required_order = sorted(required, key=order_index.__getitem__)
        reasons: list[str] = []
        for node_id in required_order:
            bound = bindings.get(node_id)
            if bound is None:
                reasons.append(f"binding_missing:{node_id}")
                continue
            if not isinstance(bound, str) or not bound:
                reasons.append(f"binding_invalid:{node_id}")
                continue
            if bound != by_id[node_id]["revision"]:
                reasons.append(f"revision_mismatch:{node_id}")
        reasons_by_evidence[evidence_id] = reasons
        if reasons:
            stale.append(evidence_id)
        else:
            current.append(evidence_id)

    return {
        "result": "stale" if stale else "current",
        "stale_evidence_ids": stale,
        "current_evidence_ids": current,
        "reason_codes": reasons_by_evidence,
    }
