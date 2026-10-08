"""Offline evidence-gate architecture, separate from native application scoring."""

import copy

import pytest
from release_evidence_fixture import bind_test_evidence
from test_release_bundle_20260919 import _bundle, _runtime, _sources

from execution.plan_revise import plan_fingerprint
from execution.release_bundle import assess_release_bundle


def _assess(bundle, records=None):
    return assess_release_bundle(
        bundle,
        current_source_hashes=_sources(),
        current_artifact_hashes={"drawing": "d" * 64},
        current_runtime_identity=_runtime(),
        evidence_records=records,
        current_engineer_identity=bundle["version_bindings"],
        current_design_basis_revision=bundle["design_basis_revision"],
    )


def test_booleans_and_unresolved_hashes_alone_cannot_grant_release():
    result = _assess(_bundle())
    assert result["result"] == "blocked"
    assert any("evidence_record_missing:checker" in r for r in result["reason_codes"])


def test_content_bound_offline_scope_is_explicit_and_never_native_acceptance():
    bundle = _bundle()
    records = bind_test_evidence(bundle)
    result = _assess(bundle, records)
    assert result["result"] == "pass"
    assert result["verification_scope"] == "offline_contract_test"
    bundle["verification_scope"] = "native_application"
    assert _assess(bundle, records)["result"] == "blocked"


@pytest.mark.parametrize(
    "field,value",
    [
        ("run_id", "another-run"),
        ("kind", "producer"),
        ("result", "unknown"),
        ("method", ""),
        ("measurements", {}),
        ("artifact_bindings", {}),
        ("reviewer_id", "offline-producer"),
        ("source_hashes", {}),
        ("runtime_identity", {}),
        ("design_basis_revision", "stale"),
        ("version_bindings", {}),
    ],
)
def test_wrong_record_bindings_block_even_with_recomputed_valid_hash(field, value):
    bundle = _bundle()
    records = bind_test_evidence(bundle)
    old = bundle["checker_evidence"]["evidence_sha256"]
    record = copy.deepcopy(records.pop(old))
    record[field] = value
    digest = plan_fingerprint(record)
    records[digest] = record
    bundle["checker_evidence"]["evidence_sha256"] = digest
    assert _assess(bundle, records)["result"] == "blocked"


def test_record_content_tampering_is_detected_before_release():
    bundle = _bundle()
    records = bind_test_evidence(bundle)
    records[bundle["checker_evidence"]["evidence_sha256"]]["measurements"] = {"forged": True}
    result = _assess(bundle, records)
    assert result["result"] == "blocked"
    assert any("evidence_record_hash_mismatch" in r for r in result["reason_codes"])


@pytest.mark.parametrize(
    "field",
    [
        "domain",
        "workflow",
        "engineer_source_revision",
        "engineer_provider_version",
        "engineer_contract_version",
        "engineer_wheel_sha256",
    ],
)
def test_current_engineer_identity_drift_blocks_complete_record_set(field):
    bundle = _bundle()
    records = bind_test_evidence(bundle)
    current = dict(bundle["version_bindings"])
    current[field] = "f" * 64 if field.endswith("sha256") else "changed"
    result = assess_release_bundle(
        bundle,
        current_source_hashes=_sources(),
        current_artifact_hashes={"drawing": "d" * 64},
        current_runtime_identity=_runtime(),
        evidence_records=records,
        current_engineer_identity=current,
        current_design_basis_revision=bundle["design_basis_revision"],
    )
    assert result["result"] == "blocked"
    assert f"engineer_binding_mismatch:{field}" in result["reason_codes"]


def test_current_design_basis_drift_blocks_complete_record_set():
    bundle = _bundle()
    records = bind_test_evidence(bundle)
    result = assess_release_bundle(
        bundle,
        current_source_hashes=_sources(),
        current_artifact_hashes={"drawing": "d" * 64},
        current_runtime_identity=_runtime(),
        evidence_records=records,
        current_engineer_identity=bundle["version_bindings"],
        current_design_basis_revision="changed-basis",
    )
    assert result["result"] == "blocked"


@pytest.mark.parametrize("kind", ["reopen", "seal", "checker", "recovery"])
def test_missing_any_required_record_type_blocks(kind):
    bundle = _bundle()
    records = bind_test_evidence(bundle)
    records = {k: v for k, v in records.items() if v["kind"] != kind}
    assert _assess(bundle, records)["result"] == "blocked"


def test_c02_producer_smoke_never_self_certifies_native_release():
    from scripts.live_run_autocad_c02 import unverified_native_report

    result = unverified_native_report(
        run_id="offline-check-of-runner",
        artifact_sha256="d" * 64,
        created_entities_count=34,
        source_sha256="a" * 64,
        observations={"entity_count": 34},
    )
    assert result["verdict"] == "blocked"
    assert "independent_checker_missing" in result["reason_codes"]


@pytest.mark.asyncio
async def test_mcp_release_gate_exposes_and_enforces_record_context():
    from fastmcp import Client

    from cdt_engineer.config import Settings
    from cdt_engineer.server import create_mcp

    bundle = _bundle()
    records = bind_test_evidence(bundle)
    args = {
        "bundle": bundle,
        "current_source_hashes": _sources(),
        "current_artifact_hashes": {"drawing": "d" * 64},
        "current_runtime_identity": _runtime(),
        "current_engineer_identity": bundle["version_bindings"],
        "current_design_basis_revision": bundle["design_basis_revision"],
    }
    async with Client(create_mcp(Settings(auth_token="", allow_remote_http=False))) as client:
        missing = await client.call_tool("release_bundle_check", args)
        assert missing.data["result"] == "blocked"
        result = await client.call_tool(
            "release_bundle_check", {**args, "evidence_records": records}
        )
        assert result.data["result"] == "pass"
        assert result.data["verification_scope"] == "offline_contract_test"
