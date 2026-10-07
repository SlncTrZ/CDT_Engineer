"""Read-only Step-0 assessment of caller-collected execution observations.
Wing: code | Topic: execution-environment | Updated: 2026-10-07 13:45 (Asia/Ho_Chi_Minh)
"""
from __future__ import annotations

import json
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from execution.chunk_recovery import fingerprint_state

_MAX_BYTES = 1_048_576
_ENVIRONMENT_FACT = "execution_environment.compatible_or_typed_blocker"


def _schema(name: str) -> dict[str, Any]:
    source = Path(__file__).resolve().parents[1] / "docs" / "schemas" / name
    if source.is_file():
        return json.loads(source.read_text(encoding="utf-8"))
    return json.loads(
        resources.files("cdt_engineer").joinpath("data", "schemas", name).read_text(
            encoding="utf-8"
        )
    )


def _validate(schema: dict[str, Any], value: Any, label: str) -> None:
    # Do not echo malformed payload values (including accidental sensitive input).
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    if next(validator.iter_errors(value), None) is not None:
        raise ValueError(f"invalid_execution_environment:{label}")


def _time(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_execution_environment:timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("invalid_execution_environment:timestamp_timezone")
    return result


def assess_execution_environment(
    inventory: dict[str, Any],
    requirements: dict[str, Any],
    runtime_observation: dict[str, Any] | None,
    assessment_at: str,
    max_age_seconds: int = 300,
) -> dict[str, Any]:
    """Classify planning readiness; never discover, repair or execute a native host."""
    context = {
        "requirements": requirements,
        "runtime_observation": runtime_observation,
        "assessment_at": assessment_at,
        "max_age_seconds": max_age_seconds,
    }
    payload = {"inventory": inventory, **context}
    try:
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError("invalid_execution_environment:json") from exc
    if len(encoded) > _MAX_BYTES:
        raise ValueError("invalid_execution_environment:payload_limit")
    # Bound arrays before schema uniqueItems checks can do quadratic comparison work.
    if not isinstance(inventory, dict):
        raise ValueError("invalid_execution_environment:inventory")
    for field in ("applications", "providers"):
        rows = inventory.get(field)
        if isinstance(rows, list) and len(rows) > 64:
            raise ValueError("invalid_execution_environment:inventory_limit")
    providers = inventory.get("providers")
    if isinstance(providers, list):
        for row in providers:
            values = row.get("discovered_capabilities") if isinstance(row, dict) else None
            if isinstance(values, list) and len(values) > 256:
                raise ValueError("invalid_execution_environment:capability_limit")
    _validate(_schema("execution-environment.schema.json"), inventory, "inventory")
    _validate(_schema("execution-environment-assessment.schema.json"), context, "context")
    for field, key in (("applications", "software_id"), ("providers", "provider_id")):
        rows = inventory[field]
        if len({row[key] for row in rows}) != len(rows):
            raise ValueError("invalid_execution_environment:duplicate_identity")
    now = _time(assessment_at)
    blocked: list[str] = []
    unknown: list[str] = []
    ages: dict[str, float] = {}

    def fresh(label: str, observed_at: str) -> None:
        age = (now - _time(observed_at)).total_seconds()
        ages[label] = age
        if age < 0:
            unknown.append(f"observation_in_future:{label}")
        elif age > max_age_seconds:
            blocked.append(f"observation_stale:{label}")

    fresh("inventory", inventory["observed_at"])
    if inventory["host_id"] != requirements["host_id"]:
        blocked.append("host_identity_mismatch")
    application = next(
        (row for row in inventory["applications"]
         if row["software_id"] == requirements["software_id"]), None
    )
    provider = next(
        (row for row in inventory["providers"]
         if row["provider_id"] == requirements["provider_id"]), None
    )
    if application is None:
        unknown.append("application_observation_missing")
    else:
        fresh("application", application["observed_at"])
        if application["status"] == "not_installed":
            blocked.append("software_not_installed")
        elif application["status"] == "unknown":
            unknown.append("application_installation_unknown")
        elif application["version"] != requirements["application_version"]:
            blocked.append("application_version_mismatch")
    if provider is None:
        unknown.append("provider_observation_missing")
    else:
        fresh("provider", provider["observed_at"])
        if provider["software_id"] != requirements["software_id"]:
            blocked.append("provider_software_identity_mismatch")
        if provider["status"] in {"not_ready", "not_configured"}:
            blocked.append(f"provider_{provider['status']}")
        elif provider["status"] == "unknown":
            unknown.append("provider_state_unknown")
        if provider["status"] == "ready":
            for field in ("provider_version", "contract_version"):
                if provider[field] != requirements[field]:
                    blocked.append(f"{field}_mismatch")
            for capability in requirements["required_capabilities"]:
                if capability not in provider["discovered_capabilities"]:
                    blocked.append(f"provider_capability_missing:{capability}")

    if runtime_observation is None:
        unknown.append("runtime_observation_missing")
    else:
        fresh("runtime", runtime_observation["observed_at"])
        for field in (
            "host_id", "software_id", "provider_id", "application_version",
            "provider_version", "contract_version",
        ):
            observed = runtime_observation[field]
            if observed is None:
                unknown.append(f"runtime_identity_unknown:{field}")
            elif observed != requirements[field]:
                blocked.append(f"runtime_identity_mismatch:{field}")
        if runtime_observation["application_state"] == "stopped":
            blocked.append("application_stopped")
        elif runtime_observation["application_state"] == "unknown":
            unknown.append("application_running_unknown")
        if runtime_observation["bridge_state"] == "unavailable":
            blocked.append("native_bridge_unavailable")
        elif runtime_observation["bridge_state"] == "unknown":
            unknown.append("native_bridge_unknown")
        expected = requirements["expected_runtime_identity"]
        identity = runtime_observation["runtime_identity"]
        if identity is None or expected is None:
            unknown.append("runtime_generation_identity_required")
        elif identity != expected:
            blocked.append("runtime_generation_identity_mismatch")
        for capability in requirements["required_capabilities"]:
            if capability not in runtime_observation["observed_capabilities"]:
                blocked.append(f"runtime_capability_missing:{capability}")

    result = "blocked" if blocked else "unknown" if unknown else "pass"
    reasons = list(dict.fromkeys([*blocked, *unknown]))
    if result == "pass":
        compatibility = "compatible"
    elif any("mismatch" in reason and "version" in reason for reason in blocked):
        compatibility = "version_mismatch"
    elif "software_not_installed" in blocked:
        compatibility = "installation_required"
    elif "provider_not_configured" in blocked:
        compatibility = "configuration_required"
    elif application is not None and application["status"] == "installed" and blocked:
        compatibility = "guidance_only"
    else:
        compatibility = "unknown"
    fact = {"result": result, "reason_codes": reasons}
    return {
        "result": result,
        "compatibility": compatibility,
        "reason_codes": reasons,
        "verification_scope": "caller_supplied_observations",
        "provider_state": provider["status"] if provider else "unknown",
        "application_installation_state": application["status"] if application else "unknown",
        "native_state": {
            "application_state": (
                runtime_observation["application_state"] if runtime_observation else "unknown"
            ),
            "bridge_state": runtime_observation["bridge_state"] if runtime_observation else "unknown",
        },
        "runtime_identity": (
            dict(runtime_observation["runtime_identity"])
            if runtime_observation and runtime_observation["runtime_identity"] else None
        ),
        "snapshot_sha256": fingerprint_state(payload),
        "assessment_at": assessment_at,
        "observation_ages_seconds": ages,
        "capabilities": {_ENVIRONMENT_FACT: dict(fact)},
        "capabilities_by_software": {
            requirements["software_id"]: {
                capability: {"result": result, "reason_codes": list(reasons)}
                for capability in requirements["required_capabilities"]
            }
        },
        "native_execution_authorized": False,
        "remediation_owner": "client_agent",
    }
