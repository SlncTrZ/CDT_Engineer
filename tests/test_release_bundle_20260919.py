"""Machine release-bundle hard gate acceptance.
Wing: code | Topic: release-bundle | Updated: 2026-10-06 16:03 (Asia/Ho_Chi_Minh)
"""

import pytest
from release_evidence_fixture import bind_test_evidence

from execution.release_bundle import assess_release_bundle


def _recovery_evidence() -> list[dict]:
    return [
        {
            "case_id": f"recovery-{kind}",
            "recovery_class": kind,
            "result": "pass",
            "evidence_sha256": ("e", "f", "1", "2")[index] * 64,
        }
        for index, kind in enumerate(("early", "middle", "late", "uncertain"))
    ]


def _bundle() -> dict:
    return {
        "run_id": "run-42",
        "design_basis_revision": "DB-7",
        "source_hashes": [
            {"source_id": "brief", "sha256": "a" * 64, "verification_state": "verified"},
            {"source_id": "survey", "sha256": "b" * 64, "verification_state": "verified"},
        ],
        "version_bindings": {
            "domain": "building-architecture@0.2.2",
            "workflow": "design-review@0.2.0",
            "engineer_source_revision": "abc1234",
            "engineer_provider_version": "0.1.0a4",
            "engineer_contract_version": "cdt-engineer-v1-alpha4",
            "engineer_wheel_sha256": "c" * 64,
        },
        "runtime_identity": {
            "provider": "autocad",
            "provider_version": "0.4.0rc3",
            "contract_version": "autocad-generic-v1-rc3",
            "application_version": "AutoCAD 2027",
        },
        "artifacts": [
            {
                "artifact_id": "drawing",
                "sha256": "d" * 64,
                "reopened": True,
                "sealed": True,
            }
        ],
        "checker_evidence": {
            "verdict": "PASS_FOR_DECLARED_SCOPE",
            "reviewer_role": "Checker / QA Engineer",
            "independent": True,
            "evidence_sha256": "9" * 64,
            "artifact_bindings": {"drawing": "d" * 64},
        },
        "required_recovery_classes": ["early", "middle", "late", "uncertain"],
        "recovery_negative_evidence": _recovery_evidence(),
    }


def _runtime() -> dict:
    return {
        "provider": "autocad",
        "provider_version": "0.4.0rc3",
        "contract_version": "autocad-generic-v1-rc3",
        "application_version": "AutoCAD 2027",
    }


def _sources() -> dict[str, str]:
    return {"brief": "a" * 64, "survey": "b" * 64}


def _assess(bundle: dict, *, artifacts=None, runtime=None, sources=None):
    records = bind_test_evidence(bundle)
    return assess_release_bundle(
        bundle,
        current_source_hashes=_sources() if sources is None else sources,
        current_artifact_hashes={"drawing": "d" * 64} if artifacts is None else artifacts,
        current_runtime_identity=_runtime() if runtime is None else runtime,
        evidence_records=records,
        current_engineer_identity=bundle["version_bindings"],
        current_design_basis_revision=bundle["design_basis_revision"],
    )


def test_complete_current_release_bundle_passes_machine_gate():
    result = _assess(_bundle())

    assert result["result"] == "pass"
    assert result["reason_codes"] == []
    assert result["source_ids"] == ["brief", "survey"]
    assert result["artifact_ids"] == ["drawing"]
    assert result["recovery_classes"] == ["early", "middle", "late", "uncertain"]


def test_source_hash_drift_invalidates_final_release():
    result = _assess(
        _bundle(),
        sources={"brief": "8" * 64, "survey": "b" * 64},
    )

    assert result["result"] == "blocked"
    assert "source_hash_mismatch:brief" in result["reason_codes"]


def test_hash_drift_runtime_drift_and_missing_seal_block_release():
    bundle = _bundle()
    bundle["artifacts"][0]["sealed"] = False
    current_runtime = _runtime()
    current_runtime["provider_version"] = "0.4.0rc4"

    result = _assess(
        bundle,
        artifacts={"drawing": "e" * 64},
        runtime=current_runtime,
    )

    assert result["result"] == "blocked"
    assert "artifact_hash_mismatch:drawing" in result["reason_codes"]
    assert "artifact_not_sealed:drawing" in result["reason_codes"]
    assert "runtime_identity_mismatch:provider_version" in result["reason_codes"]


def test_release_requires_hash_bound_independent_checker_evidence():
    bundle = _bundle()
    bundle["checker_evidence"]["independent"] = False
    bundle["checker_evidence"]["artifact_bindings"]["drawing"] = "8" * 64

    result = _assess(bundle)

    assert result["result"] == "blocked"
    assert "checker_not_independent" in result["reason_codes"]
    assert "checker_artifact_binding_mismatch:drawing" in result["reason_codes"]


def test_release_requires_each_declared_recovery_class_with_hash_bound_pass_evidence():
    bundle = _bundle()
    bundle["recovery_negative_evidence"] = [
        row for row in bundle["recovery_negative_evidence"] if row["recovery_class"] != "uncertain"
    ]
    bundle["recovery_negative_evidence"][0]["result"] = "blocked"

    result = _assess(bundle)

    assert result["result"] == "blocked"
    assert "recovery_evidence_missing:uncertain" in result["reason_codes"]
    assert "recovery_case_not_pass:early" in result["reason_codes"]


def test_unverified_source_and_nonpassing_checker_block_release():
    bundle = _bundle()
    bundle["source_hashes"][0]["verification_state"] = "metadata_only"
    bundle["checker_evidence"]["verdict"] = "BLOCKED"
    result = _assess(bundle)

    assert "source_not_verified:brief" in result["reason_codes"]
    assert "checker_verdict_not_pass" in result["reason_codes"]


def test_missing_current_source_runtime_or_artifact_observation_fails_closed():
    result = _assess(_bundle(), sources={}, artifacts={}, runtime={})

    assert "current_source_hash_missing:brief" in result["reason_codes"]
    assert "current_artifact_hash_missing:drawing" in result["reason_codes"]
    assert "current_runtime_identity_missing:provider" in result["reason_codes"]


def test_duplicate_source_artifact_or_recovery_case_ids_are_invalid_input():
    bundle = _bundle()
    bundle["source_hashes"].append(dict(bundle["source_hashes"][0]))
    with pytest.raises(ValueError, match="duplicate source_id"):
        _assess(bundle)

    bundle = _bundle()
    bundle["artifacts"].append(dict(bundle["artifacts"][0]))
    with pytest.raises(ValueError, match="duplicate artifact_id"):
        _assess(bundle)

    bundle = _bundle()
    bundle["recovery_negative_evidence"].append(dict(bundle["recovery_negative_evidence"][0]))
    with pytest.raises(ValueError, match="duplicate recovery case_id"):
        _assess(bundle)


def test_reopen_or_seal_evidence_bound_to_different_artifact_blocks_release():
    bundle = _bundle()
    bundle["artifacts"].append(
        {
            "artifact_id": "model",
            "sha256": "f" * 64,
            "reopened": True,
            "sealed": True,
        }
    )
    bundle["checker_evidence"]["artifact_bindings"]["model"] = "f" * 64
    artifacts = {"drawing": "d" * 64, "model": "f" * 64}

    records = bind_test_evidence(bundle)
    # B reuses A's reopen evidence
    bundle["artifacts"][1]["reopen_evidence_sha256"] = bundle["artifacts"][0][
        "reopen_evidence_sha256"
    ]

    result = assess_release_bundle(
        bundle,
        current_source_hashes=_sources(),
        current_artifact_hashes=artifacts,
        current_runtime_identity=_runtime(),
        evidence_records=records,
        current_engineer_identity=bundle["version_bindings"],
        current_design_basis_revision=bundle["design_basis_revision"],
    )

    assert result["result"] == "blocked"
    assert "evidence_record_binding_mismatch:reopen:artifact_id" in result["reason_codes"]

