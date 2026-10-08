"""Content-bound offline test records; never native acceptance evidence."""

from execution.plan_revise import plan_fingerprint


def bind_test_evidence(bundle):
    bundle["verification_scope"] = "offline_contract_test"
    bundle["producer_id"] = "offline-producer"
    records = {}
    bindings = {a["artifact_id"]: a["sha256"] for a in bundle["artifacts"]}

    def record(kind, **extra):
        value = {
            "kind": kind,
            "run_id": bundle["run_id"],
            "verification_scope": "offline_contract_test",
            "result": "pass",
            "design_basis_revision": bundle["design_basis_revision"],
            "version_bindings": dict(bundle["version_bindings"]),
            "source_hashes": {s["source_id"]: s["sha256"] for s in bundle["source_hashes"]},
            "runtime_identity": dict(bundle["runtime_identity"]),
            "artifact_bindings": dict(bindings),
            "method": "offline deterministic fixture",
            "measurements": {"fixture_assertions": True},
            **extra,
        }
        digest = plan_fingerprint(value)
        records[digest] = value
        return digest

    for artifact in bundle["artifacts"]:
        artifact["reopen_evidence_sha256"] = record("reopen", artifact_id=artifact["artifact_id"])
        artifact["seal_evidence_sha256"] = record("seal", artifact_id=artifact["artifact_id"])
    checker = bundle["checker_evidence"]
    checker["evidence_sha256"] = record(
        "checker", reviewer_id="offline-checker", reviewer_role=checker["reviewer_role"]
    )
    for recovery in bundle["recovery_negative_evidence"]:
        recovery["evidence_sha256"] = record(
            "recovery", case_id=recovery["case_id"], recovery_class=recovery["recovery_class"]
        )
    return records
