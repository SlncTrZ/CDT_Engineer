"""Final release-bundle machine gate for CDT_Engineer.
Wing: code | Topic: release-bundle | Updated: 2026-09-19
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_REQUIRED_VERSION_BINDINGS = (
    "domain",
    "workflow",
    "engineer_source_revision",
    "engineer_provider_version",
    "engineer_contract_version",
    "engineer_wheel_sha256",
)
_REQUIRED_RUNTIME_FIELDS = (
    "provider",
    "provider_version",
    "contract_version",
    "application_version",
)


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _sha(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be lowercase sha256")
    return value


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{name} must be a sequence")
    return value


def assess_release_bundle(
    bundle: Mapping[str, Any],
    *,
    current_source_hashes: Mapping[str, str],
    current_artifact_hashes: Mapping[str, str],
    current_runtime_identity: Mapping[str, str],
) -> dict[str, Any]:
    """Fail closed unless final release evidence is exact, current and independently verified.

    Runtime/artifact observations remain caller-supplied because CDT_Engineer does
    not own native executors. Reviewer and recovery claims must be represented by
    hash-bound evidence records rather than self-certifying booleans.
    """
    bundle = _mapping(bundle, "bundle")
    current_sources = _mapping(current_source_hashes, "current_source_hashes")
    current_artifacts = _mapping(current_artifact_hashes, "current_artifact_hashes")
    current_runtime = _mapping(current_runtime_identity, "current_runtime_identity")

    run_id = _text(bundle.get("run_id"), "run_id")
    design_basis_revision = _text(
        bundle.get("design_basis_revision"), "design_basis_revision"
    )
    reasons: list[str] = []

    sources = _sequence(bundle.get("source_hashes"), "source_hashes")
    if not sources:
        reasons.append("source_hashes_missing")
    source_ids: list[str] = []
    seen_sources: set[str] = set()
    for index, raw in enumerate(sources):
        source = _mapping(raw, f"source_hashes[{index}]")
        source_id = _text(source.get("source_id"), f"source_hashes[{index}].source_id")
        if source_id in seen_sources:
            raise ValueError(f"duplicate source_id: {source_id}")
        seen_sources.add(source_id)
        source_ids.append(source_id)
        recorded_hash = _sha(source.get("sha256"), f"{source_id}.sha256")
        current_hash = current_sources.get(source_id)
        if current_hash is None:
            reasons.append(f"current_source_hash_missing:{source_id}")
        else:
            current_hash = _sha(current_hash, f"current_source_hashes.{source_id}")
            if current_hash != recorded_hash:
                reasons.append(f"source_hash_mismatch:{source_id}")
        if source.get("verification_state") != "verified":
            reasons.append(f"source_not_verified:{source_id}")

    versions = _mapping(bundle.get("version_bindings"), "version_bindings")
    for key in _REQUIRED_VERSION_BINDINGS:
        value = versions.get(key)
        if not isinstance(value, str) or not value.strip():
            reasons.append(f"version_binding_missing:{key}")
    wheel_hash = versions.get("engineer_wheel_sha256")
    if isinstance(wheel_hash, str) and wheel_hash:
        _sha(wheel_hash, "version_bindings.engineer_wheel_sha256")

    recorded_runtime = _mapping(bundle.get("runtime_identity"), "runtime_identity")
    for key in _REQUIRED_RUNTIME_FIELDS:
        recorded = recorded_runtime.get(key)
        if not isinstance(recorded, str) or not recorded.strip():
            reasons.append(f"runtime_identity_recorded_missing:{key}")
            continue
        current = current_runtime.get(key)
        if not isinstance(current, str) or not current.strip():
            reasons.append(f"current_runtime_identity_missing:{key}")
        elif current != recorded:
            reasons.append(f"runtime_identity_mismatch:{key}")

    artifacts = _sequence(bundle.get("artifacts"), "artifacts")
    if not artifacts:
        reasons.append("artifacts_missing")
    artifact_ids: list[str] = []
    artifact_hashes: dict[str, str] = {}
    seen_artifacts: set[str] = set()
    for index, raw in enumerate(artifacts):
        artifact = _mapping(raw, f"artifacts[{index}]")
        artifact_id = _text(artifact.get("artifact_id"), f"artifacts[{index}].artifact_id")
        if artifact_id in seen_artifacts:
            raise ValueError(f"duplicate artifact_id: {artifact_id}")
        seen_artifacts.add(artifact_id)
        artifact_ids.append(artifact_id)

        recorded_hash = _sha(artifact.get("sha256"), f"{artifact_id}.sha256")
        artifact_hashes[artifact_id] = recorded_hash
        current_hash = current_artifacts.get(artifact_id)
        if current_hash is None:
            reasons.append(f"current_artifact_hash_missing:{artifact_id}")
        else:
            current_hash = _sha(current_hash, f"current_artifact_hashes.{artifact_id}")
            if current_hash != recorded_hash:
                reasons.append(f"artifact_hash_mismatch:{artifact_id}")

        reopened = artifact.get("reopened")
        if not isinstance(reopened, bool):
            raise ValueError(f"{artifact_id}.reopened must be bool")
        if not reopened:
            reasons.append(f"artifact_not_reopened:{artifact_id}")

        sealed = artifact.get("sealed")
        if not isinstance(sealed, bool):
            raise ValueError(f"{artifact_id}.sealed must be bool")
        if not sealed:
            reasons.append(f"artifact_not_sealed:{artifact_id}")

    checker = _mapping(bundle.get("checker_evidence"), "checker_evidence")
    if checker.get("verdict") != "PASS_FOR_DECLARED_SCOPE":
        reasons.append("checker_verdict_not_pass")
    _text(checker.get("reviewer_role"), "checker_evidence.reviewer_role")
    independent = checker.get("independent")
    if not isinstance(independent, bool):
        raise ValueError("checker_evidence.independent must be bool")
    if not independent:
        reasons.append("checker_not_independent")
    checker_evidence_sha256 = _sha(
        checker.get("evidence_sha256"), "checker_evidence.evidence_sha256"
    )
    checker_bindings = _mapping(
        checker.get("artifact_bindings"), "checker_evidence.artifact_bindings"
    )
    for artifact_id in artifact_ids:
        bound = checker_bindings.get(artifact_id)
        if bound is None:
            reasons.append(f"checker_artifact_binding_missing:{artifact_id}")
            continue
        bound_hash = _sha(bound, f"checker_evidence.artifact_bindings.{artifact_id}")
        if bound_hash != artifact_hashes[artifact_id]:
            reasons.append(f"checker_artifact_binding_mismatch:{artifact_id}")

    required_recovery = _sequence(
        bundle.get("required_recovery_classes"), "required_recovery_classes"
    )
    required_classes: list[str] = []
    for index, raw in enumerate(required_recovery):
        recovery_class = _text(raw, f"required_recovery_classes[{index}]")
        if recovery_class in required_classes:
            raise ValueError(f"duplicate required recovery class: {recovery_class}")
        required_classes.append(recovery_class)
    if not required_classes:
        reasons.append("required_recovery_classes_missing")

    recovery_evidence = _sequence(
        bundle.get("recovery_negative_evidence"), "recovery_negative_evidence"
    )
    seen_cases: set[str] = set()
    evidence_by_class: dict[str, list[Mapping[str, Any]]] = {}
    for index, raw in enumerate(recovery_evidence):
        evidence = _mapping(raw, f"recovery_negative_evidence[{index}]")
        case_id = _text(evidence.get("case_id"), f"recovery_negative_evidence[{index}].case_id")
        if case_id in seen_cases:
            raise ValueError(f"duplicate recovery case_id: {case_id}")
        seen_cases.add(case_id)
        recovery_class = _text(
            evidence.get("recovery_class"), f"{case_id}.recovery_class"
        )
        result = _text(evidence.get("result"), f"{case_id}.result")
        _sha(evidence.get("evidence_sha256"), f"{case_id}.evidence_sha256")
        evidence_by_class.setdefault(recovery_class, []).append(evidence)
        if recovery_class in required_classes and result != "pass":
            reasons.append(f"recovery_case_not_pass:{recovery_class}")

    for recovery_class in required_classes:
        candidates = evidence_by_class.get(recovery_class, [])
        if not candidates:
            reasons.append(f"recovery_evidence_missing:{recovery_class}")
        elif not any(row.get("result") == "pass" for row in candidates):
            reasons.append(f"recovery_evidence_no_pass:{recovery_class}")

    return {
        "result": "blocked" if reasons else "pass",
        "run_id": run_id,
        "design_basis_revision": design_basis_revision,
        "source_ids": source_ids,
        "artifact_ids": artifact_ids,
        "checker_evidence_sha256": checker_evidence_sha256,
        "recovery_classes": required_classes,
        "reason_codes": list(dict.fromkeys(reasons)),
    }
