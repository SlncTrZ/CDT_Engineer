"""Integrated Architecture↔Structural handoff freshness acceptance.
Wing: code | Topic: cross-domain-handoff | Updated: 2026-09-19
"""
from domains.building_structural.interfaces import evaluate_architecture_structural_interfaces
from execution.impact_graph import assess_evidence_freshness, compute_impact


def _handoff(*, source_revision: str = "arch-r4", conflict_state: str = "resolved") -> dict:
    return {
        "interface_id": "stair-slab-01",
        "from_discipline": "building-architecture",
        "to_discipline": "building-structural",
        "interface_type": "stair_slab_opening",
        "owner_discipline": "building-structural",
        "required": True,
        "status": "accepted",
        "verification_state": "verified",
        "source_revision": source_revision,
        "handoff_revision": "coord-r7",
        "unit_system": "mm",
        "coordinate_frame_id": "project-grid-A",
        "conflict_state": conflict_state,
        "conflict_owner_discipline": "building-structural",
        "conflict_evidence_refs": ["decision:coord-44"],
        "evidence_refs": ["measurement:opening-01", "decision:struct-17"],
    }


def _nodes(architecture_revision: str) -> list[dict]:
    return [
        {"node_id": "architecture", "revision": architecture_revision, "depends_on": []},
        {"node_id": "handoff", "revision": "coord-r7", "depends_on": ["architecture"]},
        {"node_id": "structural-output", "revision": "struct-r2", "depends_on": ["handoff"]},
    ]


def _checker_evidence() -> list[dict]:
    return [
        {
            "evidence_id": "checker:struct-r2",
            "subject_id": "structural-output",
            "bound_revisions": {
                "architecture": "arch-r4",
                "handoff": "coord-r7",
                "structural-output": "struct-r2",
            },
        }
    ]


def test_current_handoff_and_transitive_checker_evidence_pass_together():
    interface = evaluate_architecture_structural_interfaces(
        [_handoff()],
        current_revisions={
            "building-architecture": "arch-r4",
            "building-structural": "struct-r2",
        },
        expected_unit_system="mm",
        expected_coordinate_frame_id="project-grid-A",
    )
    freshness = assess_evidence_freshness(_nodes("arch-r4"), _checker_evidence())

    assert interface["result"] == "pass"
    assert freshness["result"] == "current"
    assert freshness["current_evidence_ids"] == ["checker:struct-r2"]


def test_upstream_architecture_revision_invalidates_handoff_and_downstream_checker_evidence():
    interface = evaluate_architecture_structural_interfaces(
        [_handoff()],
        current_revisions={
            "building-architecture": "arch-r5",
            "building-structural": "struct-r2",
        },
        expected_unit_system="mm",
        expected_coordinate_frame_id="project-grid-A",
    )
    nodes = _nodes("arch-r5")
    impact = compute_impact(nodes, ["architecture"])
    freshness = assess_evidence_freshness(nodes, _checker_evidence())

    assert interface["result"] == "blocked"
    assert "interface_source_revision_stale:stair-slab-01" in interface["reason_codes"]
    assert impact["impacted_ids"] == ["architecture", "handoff", "structural-output"]
    assert freshness["result"] == "stale"
    assert freshness["stale_evidence_ids"] == ["checker:struct-r2"]
    assert freshness["reason_codes"]["checker:struct-r2"] == ["revision_mismatch:architecture"]


def test_open_coordination_conflict_blocks_even_with_current_revision_and_existing_evidence():
    interface = evaluate_architecture_structural_interfaces(
        [_handoff(conflict_state="open")],
        current_revisions={
            "building-architecture": "arch-r4",
            "building-structural": "struct-r2",
        },
        expected_unit_system="mm",
        expected_coordinate_frame_id="project-grid-A",
    )

    assert interface["result"] == "blocked"
    assert "interface_conflict_open:stair-slab-01" in interface["reason_codes"]
