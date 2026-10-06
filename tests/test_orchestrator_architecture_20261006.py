"""Architecture regressions; all executor observations here are offline doubles."""

import copy
import json

import pytest
from source_inventory_fixture import freeze_test_source
from test_plan_review_gates_20260917 import _valid_arch_spec

from execution.chunk_recovery import execute_chunk_with_recovery, fingerprint_state
from execution.plan_compiler import compile_plan_spec
from execution.plan_review import review_plan_spec
from execution.plan_revise import plan_fingerprint
from execution.provenance_release import assess_provenance_release, build_chunk_receipt


def _column_spec(center=(1450.0, 0.0), shape="rect", dimensions=(400.0, 400.0)):
    spec = _valid_arch_spec("column_opening")
    spec["payload"]["columns"] = [
        {"column_id": "c1", "shape": shape, "dimensions": list(dimensions), "center": list(center)}
    ]
    spec["provenance_ledger"]["c1"] = {"status": "specified", "source_id": "s1"}
    return freeze_test_source(spec)


def _spatial_result(spec):
    review = review_plan_spec(spec)
    return next(f for f in review.findings if f["gate"] == "spatial_clashes")


def test_column_door_clash_blocks_review_and_compilation():
    spec = _column_spec()
    assert not review_plan_spec(spec).approved
    assert "column_opening_clash:c1:door_d1" in _spatial_result(spec)["reason_codes"]
    compiled = compile_plan_spec(spec)
    assert not compiled.ok and compiled.chunks == []


def test_clear_column_preserves_approval():
    assert review_plan_spec(_column_spec(center=(3000.0, 0.0))).approved


def test_rotated_host_wall_clash_uses_wall_frame():
    spec = _column_spec(center=(0.0, 1450.0))
    spec["payload"]["walls"][0]["end"] = [0.0, 5000.0]
    spec["payload"]["walls"][1].update(start=[0.0, 5000.0], end=[4000.0, 5000.0])
    spec["payload"]["dimensions"][0]["witness_points"] = [[0.0, 0.0], [0.0, 5000.0]]
    freeze_test_source(spec)
    assert "column_opening_clash:c1:door_d1" in _spatial_result(spec)["reason_codes"]


def test_circle_corner_near_miss_is_not_a_bbox_false_positive():
    spec = _column_spec(center=(1950.0, 150.0), shape="circle", dimensions=(100.0,))
    assert _spatial_result(spec)["result"] == "pass"


def test_circular_columns_near_bbox_corners_do_not_falsely_clash():
    from execution.plan_review import _column_shapes_overlap

    a = {"shape": "circle", "center": [0.0, 0.0], "dimensions": [100.0]}
    b = {"shape": "circle", "center": [80.0, 80.0], "dimensions": [100.0]}
    assert not _column_shapes_overlap(a, b)
    b["center"] = [40.0, 40.0]
    assert _column_shapes_overlap(a, b)


def test_unresolved_finish_face_frame_blocks_cross_discipline_clash_claim():
    spec = _column_spec()
    spec["payload"]["walls"][0]["baseline"] = "finish_face_interior"
    freeze_test_source(spec)
    assert not review_plan_spec(spec).approved
    assert "opening_clash_frame_unresolved:door_d1" in _spatial_result(spec)["reason_codes"]


def _fixtures(position2=(2500.0, 2000.0), rotation=0.0):
    spec = _valid_arch_spec("fixture_overlap")
    spec["payload"]["fixtures"] = [
        {
            "fixture_id": fid,
            "fixture_type": "equipment",
            "position": list(position),
            "dimensions": [1000.0, 100.0],
            "rotation": rotation,
            "host_space_id": "space_living",
        }
        for fid, position in [("f1", (2500.0, 2000.0)), ("f2", position2)]
    ]
    for fid in ("f1", "f2"):
        spec["provenance_ledger"][fid] = {"status": "specified", "source_id": "s1"}
    return freeze_test_source(spec)


def test_fixture_overlap_blocks_even_with_valid_host_containment():
    spec = _fixtures()
    assert not review_plan_spec(spec).approved
    assert "fixture_overlap:f1:f2" in _spatial_result(spec)["reason_codes"]


def test_rotated_fixture_bbox_overlap_does_not_imply_footprint_overlap():
    assert _spatial_result(_fixtures((2400.0, 2100.0), rotation=45.0))["result"] == "pass"


def test_radian_rotation_is_handled_in_fixture_clashes():
    spec = _fixtures(rotation=0.5)
    spec["units"]["angle"] = "rad"
    freeze_test_source(spec)
    assert _spatial_result(spec)["result"] == "fail"


@pytest.mark.parametrize(
    "first_state,expected",
    [
        (None, "blocked"),
        ({"wrong": {}}, "blocked"),
        ({"a": {"x": 1}}, "committed"),
        ({}, "committed"),
    ],
)
def test_failed_receipt_observes_and_recovers_before_retry(first_state, expected):
    state, events = {}, []
    calls = 0
    chunk = {"chunk_id": "dirty_failure", "semantic_params": {"a": {"x": 1}, "b": {"x": 2}}}

    def execute(c, key):
        nonlocal calls, state
        calls += 1
        events.append("execute")
        if calls == 1:
            state = first_state
            return {"outcome": "failed"}
        state = copy.deepcopy(c["semantic_params"])
        return {"outcome": "committed"}

    def observe(cid):
        events.append("observe")
        return copy.deepcopy(state)

    def compensate(cid):
        nonlocal state
        events.append("compensate")
        state = {}

    record = execute_chunk_with_recovery(chunk, execute, observe, compensate)
    assert record.final == expected
    assert events[:2] == ["execute", "observe"]
    if first_state is None or "wrong" in first_state:
        assert calls == 1
    elif first_state:
        assert events[:5] == ["execute", "observe", "compensate", "observe", "execute"]


def test_failed_but_fully_observed_commit_is_adopted_without_replay():
    state = {"a": {"x": 1}}
    calls = []
    record = execute_chunk_with_recovery(
        {"chunk_id": "full", "semantic_params": state},
        lambda c, k: calls.append(k) or {"outcome": "failed"},
        lambda cid: state,
        lambda cid: pytest.fail("must not compensate a verified commit"),
    )
    assert record.final == "committed" and len(calls) == 1


def test_partial_failure_recovers_even_when_retry_budget_is_exhausted():
    state = {"a": {"x": 1}}
    calls = []
    record = execute_chunk_with_recovery(
        {"chunk_id": "last_attempt", "semantic_params": {"a": {"x": 1}, "b": {"x": 2}}},
        lambda c, k: calls.append("execute") or {"outcome": "failed"},
        lambda cid: dict(state),
        lambda cid: state.clear(),
        max_attempts=1,
    )
    assert record.final == "blocked" and calls == ["execute"] and state == {}


def test_malformed_receipt_preserves_uncertainty_and_never_blindly_retries():
    calls = []
    record = execute_chunk_with_recovery(
        {"chunk_id": "malformed", "semantic_params": {"a": {"x": 1}}},
        lambda c, k: calls.append("execute") or None,
        lambda cid: None,
        lambda cid: pytest.fail("unobserved state must block"),
    )
    assert record.final == "blocked" and len(calls) == 1


def test_changed_semantic_revision_uses_different_default_idempotency_key():
    keys = []
    for x in (1, 2):
        state = {"a": {"x": x}}
        execute_chunk_with_recovery(
            {"chunk_id": "same", "semantic_params": state},
            lambda c, k: keys.append(k) or {"outcome": "committed"},
            lambda cid, observed=state: observed,
            lambda cid: None,
        )
    assert keys[0] != keys[1]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), object()])
def test_recovery_fingerprint_rejects_noncanonical_properties(value):
    with pytest.raises((ValueError, TypeError)):
        fingerprint_state({"a": {"x": value}})


def test_chunks_bind_plan_revision_and_are_deeply_detached():
    spec = _valid_arch_spec("fingerprints")
    chunks = compile_plan_spec(spec).chunks
    assert chunks and all(c["plan_sha256"] == plan_fingerprint(spec) for c in chunks)
    changed = copy.deepcopy(spec)
    changed["payload"]["walls"][0]["height"] += 100.0
    second = compile_plan_spec(changed).chunks
    assert second[0]["plan_sha256"] != chunks[0]["plan_sha256"]
    chunks[0]["features"][0]["start"][0] = 99999
    assert spec["payload"]["axes"][0]["start"][0] == 0.0


def test_actual_utf8_payload_size_and_semantic_partition_coverage():
    spec = _valid_arch_spec("partition")
    result = compile_plan_spec(spec, {"spatial_cell_size": 1000.0, "max_features_per_chunk": 2})
    assert result.ok
    ids = [fid for c in result.chunks for fid in c["feature_ids"]]
    assert len(ids) == len(set(ids)) == result.feature_count
    predecessors = set()
    for c in result.chunks:
        assert set(c["depends_on"]) <= predecessors
        predecessors.add(c["chunk_id"])
        assert c["payload_bytes"] == len(
            json.dumps(
                c, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
            ).encode()
        )
        assert c["spatial_bounds"] is not None


def test_single_feature_over_payload_budget_is_refused_without_partial_chunks():
    spec = _valid_arch_spec("large")
    spec["payload"]["spaces"][0]["name"] = "大" * 10000
    result = compile_plan_spec(spec, {"max_chunk_payload_bytes": 4096})
    assert not result.ok and result.chunks == []
    assert any("feature_payload_exceeds_budget" in e for e in result.errors)


@pytest.mark.parametrize(
    "requirements",
    [
        {"max_features_per_chunk": True},
        {"max_chunk_payload_bytes": 100},
        {"spatial_cell_size": 10**400},
        {"spatial_cell_size": float("nan")},
        {"min_door_width": -1},
    ],
)
def test_unsafe_compilation_controls_are_typed_input_errors(requirements):
    with pytest.raises(ValueError):
        compile_plan_spec(_valid_arch_spec(), requirements)


def test_unrepresentable_spatial_partition_refuses_without_chunks():
    result = compile_plan_spec(_valid_arch_spec(), {"spatial_cell_size": 1e-320})
    assert not result.ok and not result.chunks


def test_rect_column_requires_two_dimensions_in_semantic_schema():
    spec = _column_spec(center=(3000.0, 0.0), dimensions=(200.0,))
    assert not compile_plan_spec(spec).ok


def test_stale_or_tampered_chunk_receipts_block_provenance_release():
    chunks = compile_plan_spec(_valid_arch_spec("bound_receipts")).chunks
    receipts = [
        build_chunk_receipt(
            c,
            engine_receipt_id="offline-double",
            created_or_modified_ids=c["feature_ids"],
            transaction_mode="checkpointed_atomic",
        )
        for c in chunks
    ]
    assert (
        assess_provenance_release(receipts, "design_review", expected_chunks=chunks)["result"]
        == "pass"
    )
    receipts[0]["plan_sha256"] = "0" * 64
    assert (
        assess_provenance_release(receipts, "design_review", expected_chunks=chunks)["result"]
        == "blocked"
    )


def test_missing_duplicate_and_out_of_order_receipts_do_not_release_dependents():
    chunks = compile_plan_spec(_valid_arch_spec("dag_receipts")).chunks
    receipts = [
        build_chunk_receipt(
            c,
            engine_receipt_id="offline-double",
            created_or_modified_ids=c["feature_ids"],
            transaction_mode="checkpointed_atomic",
        )
        for c in chunks
    ]
    for bad in (receipts[1:], receipts + [receipts[0]], list(reversed(receipts))):
        assert (
            assess_provenance_release(bad, "design_review", expected_chunks=chunks)["result"]
            == "blocked"
        )


@pytest.mark.parametrize("mode", [None, "invented_mode", "nonrecoverable"])
def test_invalid_or_nonrecoverable_mode_blocks_design_review(mode):
    chunks = compile_plan_spec(_valid_arch_spec("isolation_modes")).chunks
    receipts = [
        build_chunk_receipt(
            c,
            engine_receipt_id="offline-double",
            created_or_modified_ids=c["feature_ids"],
            transaction_mode="checkpointed_atomic",
        )
        for c in chunks
    ]
    receipts[0]["transaction_mode"] = mode
    assert (
        assess_provenance_release(receipts, "design_review", expected_chunks=chunks)["result"]
        == "blocked"
    )


def test_unknown_requirement_cannot_silently_disable_a_hard_gate():
    with pytest.raises(ValueError, match="unknown planning requirement"):
        compile_plan_spec(_valid_arch_spec(), {"min_doo_width": 900})


def test_transitive_dependency_barriers_do_not_repeat_all_predecessor_ids():
    result = compile_plan_spec(_valid_arch_spec(), {"max_features_per_chunk": 1})
    assert result.ok
    wall_chunks = [c for c in result.chunks if c["semantic_type"] == "wall_shell"]
    opening = next(c for c in result.chunks if c["semantic_type"] == "openings")
    assert opening["depends_on"] == [wall_chunks[-1]["chunk_id"]]
    assert all(len(c["depends_on"]) <= 1 for c in result.chunks)


def test_empty_optional_phase_preserves_upstream_dependency(monkeypatch):
    # An optional phase may emit no chunks; downstream work must still wait
    # for the complete upstream wall phase rather than losing its barrier.
    import execution.plan_compiler as compiler

    spec = _valid_arch_spec("optional_dependency")
    spec["payload"]["dimensions"] = []
    spec["provenance_ledger"].pop("dim_01", None)
    freeze_test_source(spec)
    groups = (
        compiler._ARCH_GROUPS[0],
        compiler._ARCH_GROUPS[1],
        (
            "optional_annotations",
            ("dimensions",),
            "dimension_id",
            ("wall_shell",),
            ("annotation.create",),
        ),
        ("openings", ("openings",), "opening_id", ("optional_annotations",), ("geometry.create",)),
        compiler._ARCH_GROUPS[3],
    )
    monkeypatch.setattr(compiler, "_ARCH_GROUPS", groups)
    compiled = compile_plan_spec(spec)
    assert compiled.ok, compiled.errors
    wall = [c for c in compiled.chunks if c["semantic_type"] == "wall_shell"][-1]
    opening = next(c for c in compiled.chunks if c["semantic_type"] == "openings")
    assert opening["depends_on"] == [wall["chunk_id"]]
