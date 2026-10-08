"""Snapshot freshness, native dependency and generation gates for Step-0 planning."""
from __future__ import annotations

import copy
import json

import pytest
from fastmcp import Client

from cdt_engineer.config import Settings
from cdt_engineer.server import create_mcp
from execution.environment_assessment import assess_execution_environment
from execution.stage_runner import run_profile


def assessment_input():
    observed = "2026-10-07T06:35:00Z"
    identity = {
        "runtime_generation": "generation-1", "session_id": "session-1",
        "application_instance_id": "process-123-created-1", "bridge_version": "bridge-1",
    }
    return {
        "inventory": {
            "schema_version": "0.1.0", "host_id": "workstation-1", "observed_at": observed,
            "os": {"family": "windows", "version": "11", "architecture": "x86_64"},
            "applications": [{
                "software_id": "autocad", "status": "installed",
                "install_path": "C:/Application", "executable_path": "C:/Application/app.exe",
                "version": "2027", "build": "build-1", "edition": "full",
                "discovery_method": "file-version", "observed_at": observed,
            }],
            "providers": [{
                "provider_id": "cdt-autocad", "software_id": "autocad", "status": "ready",
                "provider_version": "0.4.0rc3", "contract_version": "autocad-generic-v1-rc3",
                "discovered_capabilities": ["model.query"], "observed_at": observed,
            }],
        },
        "requirements": {
            "host_id": "workstation-1", "software_id": "autocad", "provider_id": "cdt-autocad",
            "application_version": "2027", "provider_version": "0.4.0rc3",
            "contract_version": "autocad-generic-v1-rc3",
            "required_capabilities": ["model.query"],
            "expected_runtime_identity": identity,
        },
        "runtime_observation": {
            "host_id": "workstation-1", "software_id": "autocad", "provider_id": "cdt-autocad",
            "application_version": "2027", "provider_version": "0.4.0rc3",
            "contract_version": "autocad-generic-v1-rc3", "observed_at": observed,
            "discovery_method": "public-provider-readback",
            "application_state": "running", "bridge_state": "ready",
            "runtime_identity": copy.deepcopy(identity), "observed_capabilities": ["model.query"],
        },
        "assessment_at": "2026-10-07T06:36:00Z", "max_age_seconds": 300,
    }


def test_valid_snapshot_assesses_planning_without_authorizing_execution():
    value = assessment_input()
    before = copy.deepcopy(value)
    result = assess_execution_environment(**value)
    assert result["result"] == "pass"
    assert result["compatibility"] == "compatible"
    assert result["verification_scope"] == "caller_supplied_observations"
    assert result["native_execution_authorized"] is False
    assert len(result["snapshot_sha256"]) == 64
    assert value == before
    reordered = json.loads(json.dumps(value, sort_keys=True))
    assert assess_execution_environment(**reordered)["snapshot_sha256"] == result["snapshot_sha256"]


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("bridge_state", "unavailable", "native_bridge_unavailable"),
        ("application_state", "stopped", "application_stopped"),
        ("host_id", "other-host", "runtime_identity_mismatch:host_id"),
        ("software_id", "other-software", "runtime_identity_mismatch:software_id"),
        ("provider_id", "other-provider", "runtime_identity_mismatch:provider_id"),
        ("application_version", "2026", "runtime_identity_mismatch:application_version"),
        ("contract_version", "different-contract", "runtime_identity_mismatch:contract_version"),
        ("provider_version", "different-version", "runtime_identity_mismatch:provider_version"),
        ("observed_capabilities", [], "runtime_capability_missing:model.query"),
    ],
)
def test_provider_ready_does_not_hide_native_blocker(field, value, reason):
    arguments = assessment_input()
    arguments["runtime_observation"][field] = value
    result = assess_execution_environment(**arguments)
    assert result["provider_state"] == "ready"
    assert result["result"] == "blocked"
    assert reason in result["reason_codes"]


@pytest.mark.parametrize("field", [
    "runtime_generation", "session_id", "application_instance_id", "bridge_version",
])
def test_changed_runtime_identity_blocks_even_with_unchanged_provider(field):
    arguments = assessment_input()
    arguments["runtime_observation"]["runtime_identity"][field] = "substituted"
    result = assess_execution_environment(**arguments)
    assert result["result"] == "blocked"
    assert "runtime_generation_identity_mismatch" in result["reason_codes"]


@pytest.mark.parametrize("target", ["inventory", "application", "provider", "runtime"])
def test_each_snapshot_must_be_fresh(target):
    arguments = assessment_input()
    obj = {
        "inventory": arguments["inventory"],
        "application": arguments["inventory"]["applications"][0],
        "provider": arguments["inventory"]["providers"][0],
        "runtime": arguments["runtime_observation"],
    }[target]
    obj["observed_at"] = "2026-10-07T06:00:00Z"
    result = assess_execution_environment(**arguments)
    assert result["result"] == "blocked"
    assert f"observation_stale:{target}" in result["reason_codes"]


def test_future_observation_is_unknown_not_a_fresh_pass():
    arguments = assessment_input()
    arguments["runtime_observation"]["observed_at"] = "2026-10-07T07:00:00Z"
    result = assess_execution_environment(**arguments)
    assert result["result"] == "unknown"
    assert "observation_in_future:runtime" in result["reason_codes"]


@pytest.mark.parametrize("target", ["snapshot", "expected_identity", "observed_identity", "bridge"])
def test_unknown_runtime_evidence_never_becomes_pass(target):
    arguments = assessment_input()
    if target == "snapshot":
        arguments["runtime_observation"] = None
    elif target == "expected_identity":
        arguments["requirements"]["expected_runtime_identity"] = None
    elif target == "observed_identity":
        arguments["runtime_observation"]["runtime_identity"] = None
    else:
        arguments["runtime_observation"]["bridge_state"] = "unknown"
    assert assess_execution_environment(**arguments)["result"] == "unknown"


@pytest.mark.parametrize("target", ["application", "provider"])
def test_absent_observation_is_unknown_and_not_asserted_absence(target):
    arguments = assessment_input()
    arguments["inventory"]["applications" if target == "application" else "providers"] = []
    result = assess_execution_environment(**arguments)
    assert result["result"] == "unknown"
    assert f"{target}_observation_missing" in result["reason_codes"]


def test_known_absent_software_and_provider_report_typed_blockers():
    arguments = assessment_input()
    app = arguments["inventory"]["applications"][0]
    app["status"] = "not_installed"
    for key in ["install_path", "executable_path", "version", "build", "edition"]:
        app[key] = None
    arguments["inventory"]["providers"][0]["status"] = "not_configured"
    result = assess_execution_environment(**arguments)
    assert result["result"] == "blocked"
    assert result["compatibility"] == "installation_required"
    assert {"software_not_installed", "provider_not_configured"} <= set(result["reason_codes"])


@pytest.mark.parametrize("target", ["applications", "providers"])
def test_duplicate_identity_cannot_select_a_convenient_ready_record(target):
    arguments = assessment_input()
    arguments["inventory"][target].append(copy.deepcopy(arguments["inventory"][target][0]))
    with pytest.raises(ValueError, match="duplicate_identity"):
        assess_execution_environment(**arguments)


@pytest.mark.parametrize("mutation", [
    "invalid_time", "naive_time", "bool_age", "excessive_age", "empty_caps",
    "unknown_requirement", "extra_runtime_field", "nonfinite", "oversized", "inventory_limit",
])
def test_malformed_or_unbounded_context_refuses(mutation):
    arguments = assessment_input()
    if mutation == "invalid_time":
        arguments["assessment_at"] = "not-a-date"
    elif mutation == "naive_time":
        arguments["assessment_at"] = "2026-10-07T06:36:00"
    elif mutation == "bool_age":
        arguments["max_age_seconds"] = True
    elif mutation == "excessive_age":
        arguments["max_age_seconds"] = 3601
    elif mutation == "empty_caps":
        arguments["requirements"]["required_capabilities"] = []
    elif mutation == "unknown_requirement":
        arguments["requirements"]["host_command"] = "must-not-execute"
    elif mutation == "extra_runtime_field":
        arguments["runtime_observation"]["host_command"] = "must-not-execute"
    elif mutation == "nonfinite":
        arguments["max_age_seconds"] = float("nan")
    elif mutation == "oversized":
        arguments["inventory"]["applications"][0]["discovery_method"] = "x" * 1_048_576
    else:
        row = arguments["inventory"]["applications"][0]
        arguments["inventory"]["applications"] = [
            {**row, "software_id": f"software-{i}"} for i in range(65)
        ]
    with pytest.raises(ValueError, match="invalid_execution_environment"):
        assess_execution_environment(**arguments)


@pytest.mark.parametrize("native_available", [True, False])
def test_assessment_feeds_existing_stage_runner_without_native_calls(native_available):
    arguments = assessment_input()
    if not native_available:
        arguments["runtime_observation"]["bridge_state"] = "unavailable"
    assessment = assess_execution_environment(**arguments)
    profile = {
        "profile_id": "environment-integration", "release_target": "technical_draft",
        "stages": [
            {"stage_id": "environment_preflight", "depends_on": [],
             "required_capabilities": ["execution_environment.compatible_or_typed_blocker"]},
            {"stage_id": "native_read", "depends_on": ["environment_preflight"],
             "software_candidates": ["autocad"], "required_capabilities": ["model.query"]},
        ],
    }
    result = run_profile(
        profile, capabilities=assessment["capabilities"],
        capabilities_by_software=assessment["capabilities_by_software"],
        stage_checks={name: {"result": "pass"} for name in ["environment_preflight", "native_read"]},
    )
    assert result["result"] == ("pass" if native_available else "blocked")
    assert result["stages"][1]["release_result"] == ("pass" if native_available else "blocked")


@pytest.mark.asyncio
async def test_mcp_assessment_never_invokes_environment_remediation(monkeypatch):
    import asyncio
    import subprocess

    def refused(*args, **kwargs):
        pytest.fail("snapshot assessment must not execute a process")

    monkeypatch.setattr(subprocess, "run", refused)
    monkeypatch.setattr(subprocess, "Popen", refused)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", refused)
    monkeypatch.setenv("CDT_ENGINEER_EXECUTION_CONTROLLER", "/must/not/be/used")
    async with Client(create_mcp(Settings(auth_token=""))) as client:
        result = await client.call_tool("execution_environment_assess", assessment_input())
    assert result.structured_content["result"] == "pass"


@pytest.mark.asyncio
async def test_mcp_validation_error_does_not_echo_malformed_input():
    arguments = assessment_input()
    arguments["runtime_observation"]["unexpected_input"] = "private-input-marker"
    async with Client(create_mcp(Settings(auth_token=""))) as client:
        result = await client.call_tool(
            "execution_environment_assess", arguments, raise_on_error=False
        )
    assert result.is_error
    assert result.structured_content["kind"] == "validation_error"
    assert "private-input-marker" not in str(result.structured_content)


@pytest.mark.asyncio
async def test_mcp_wrong_input_type_does_not_echo_framework_validation_value():
    arguments = assessment_input()
    arguments["runtime_observation"] = "private-input-marker"
    async with Client(create_mcp(Settings(auth_token=""))) as client:
        result = await client.call_tool(
            "execution_environment_assess", arguments, raise_on_error=False
        )
    assert result.is_error
    assert result.structured_content["kind"] == "validation_error"
    assert "private-input-marker" not in str(result)
