"""MCP provider contract for CDT_Engineer Engineering OS.
Wing: code | Topic: mcp-provider | Updated: 2026-10-07 13:45 (Asia/Ho_Chi_Minh)
"""
from __future__ import annotations

import pytest
from fastmcp import Client

from cdt_engineer.config import Settings
from cdt_engineer.contract_identity import CONTRACT_VERSION, PUBLIC_TOOL_COUNT
from cdt_engineer.server import _TOOL_DESCRIPTIONS, _validate_http_launch, create_mcp


EXPECTED_TOOLS = {
    "execution_environment_assess",

    "help",
    "system_status",
    "system_capabilities",
    "profile_get",
    "engine_map_get",
    "profile_assess",
    "dependency_assess",
    "catalog_resolve",
    "completeness_check",
    "layer_ledger_check",
    "human_deliverable_check",
    "qa_check",
    "artifact_manifest",
    "evidence_stale_check",
    "observation_assess",
    "impact_assess",
    "architecture_structural_interface_assess",
    "release_bundle_check",
}


@pytest.mark.asyncio
async def test_provider_surface_is_bounded_and_semantic():
    app = create_mcp(Settings(auth_token="", allow_remote_http=False))
    async with Client(app) as client:
        tools = list(await client.list_tools())

    names = {tool.name for tool in tools}
    assert names == EXPECTED_TOOLS == set(_TOOL_DESCRIPTIONS)
    assert len(names) == PUBLIC_TOOL_COUNT == 19
    assert not any(
        token in name
        for name in names
        for token in ("draw_line", "create_circle", "extrude", "autocad_save")
    )


@pytest.mark.asyncio
async def test_help_status_and_capabilities_describe_engineering_os_boundary():
    app = create_mcp(Settings(auth_token="", allow_remote_http=False))
    async with Client(app) as client:
        help_result = await client.call_tool("help", {})
        status_result = await client.call_tool("system_status", {})
        caps_result = await client.call_tool("system_capabilities", {})

    help_payload = help_result.structured_content or {}
    assert help_payload["provider_name"] == "cdt-engineer"
    assert help_payload["contract_version"] == CONTRACT_VERSION
    assert help_payload["public_tool_count"] == PUBLIC_TOOL_COUNT
    assert len(help_payload["contract_hash"]) == 64
    assert "Generic CAD executor" in help_payload["content"]

    status = status_result.structured_content or {}
    assert status["provider"] == "cdt-engineer"
    assert status["runtime"]["ready"] is True
    assert status["execution_boundary"]["native_cad_execution"] is False
    assert status["execution_environment"]["external_native_readiness"] == "not_observed"

    caps = caps_result.structured_content or {}
    assert caps["provider"] == "cdt-engineer"
    assert caps["capabilities"]["engineering.profile_assess"]["supported"] is True
    assert caps["capabilities"]["engineering.observation_assess"]["supported"] is True
    assert caps["capabilities"]["engineering.impact_assess"]["supported"] is True
    assert caps["capabilities"]["engineering.architecture_structural_interface_assess"]["supported"] is True
    assert caps["capabilities"]["engineering.release_bundle_check"]["supported"] is True
    assert caps["capabilities"]["native.cad_mutation"]["supported"] is False
    assert caps["capabilities"]["engineering.execution_lifecycle"]["supported"] is False
    assert caps["capabilities"]["engineering.execution_environment_assess"]["supported"] is True


@pytest.mark.asyncio
async def test_profile_and_engine_map_are_read_only_contract_sources():
    app = create_mcp(Settings(auth_token="", allow_remote_http=False))
    async with Client(app) as client:
        profile_result = await client.call_tool("profile_get", {"domain_id": "building-architecture"})
        map_result = await client.call_tool("engine_map_get", {"software_id": "autocad"})

    profile = profile_result.structured_content or {}
    assert profile["domain_id"] == "building-architecture"
    assert profile["profile"]["profile_id"]

    engine_map = map_result.structured_content or {}
    assert engine_map["software_id"] == "autocad"
    assert engine_map["engine_map"]["source_snapshot"]["contract_version"] == "autocad-generic-v1-rc3"


@pytest.mark.asyncio
async def test_profile_assess_wraps_existing_stage_runner_without_native_execution():
    app = create_mcp(Settings(auth_token="", allow_remote_http=False))
    profile = {
        "profile_id": "provider-smoke",
        "release_target": "technical_draft",
        "stages": [
            {
                "stage_id": "draft",
                "depends_on": [],
                "checkpoint": "draft-reviewed",
                "required_capabilities": ["feature.plan"],
            }
        ],
    }
    async with Client(app) as client:
        result = await client.call_tool(
            "profile_assess",
            {
                "profile": profile,
                "capabilities": {"feature.plan": {"result": "pass", "reason_codes": []}},
                "stage_checks": {"draft": {"result": "pass", "reason_codes": []}},
            },
        )

    payload = result.structured_content or {}
    assert payload["result"] == "pass"
    assert payload["stages"][0]["release_result"] == "pass"


@pytest.mark.asyncio
async def test_observation_and_impact_tools_expose_e3_invariants():
    app = create_mcp(Settings(auth_token="", allow_remote_http=False))
    async with Client(app) as client:
        observation_result = await client.call_tool(
            "observation_assess",
            {
                "observation": {
                    "observation_id": "obs-1",
                    "observer_id": "checker-1",
                    "method": "native_query",
                    "semantic_id": "wall-1",
                    "native_id": "pid:wall-1",
                    "observed_revision": "D2",
                    "status": "observed",
                    "state": {"wall-1": {"length": 5000.0}},
                },
                "expected_semantic_id": "wall-1",
                "expected_native_id": "pid:wall-1",
                "expected_revision": "D2",
                "expected_state": {"wall-1": {"length": 5000.0}},
            },
        )
        impact_result = await client.call_tool(
            "impact_assess",
            {
                "nodes": [
                    {"node_id": "source", "revision": "S2", "depends_on": []},
                    {"node_id": "model", "revision": "M2", "depends_on": ["source"]},
                ],
                "changed_ids": ["source"],
                "evidence": [{
                    "evidence_id": "ev-model",
                    "subject_id": "model",
                    "bound_revisions": {"source": "S1", "model": "M2"},
                }],
            },
        )

    observation = observation_result.structured_content or {}
    assert observation["result"] == "pass"
    impact = impact_result.structured_content or {}
    assert impact["impact"]["impacted_ids"] == ["source", "model"]
    assert impact["evidence"]["stale_evidence_ids"] == ["ev-model"]


@pytest.mark.asyncio
async def test_architecture_structural_interface_tool_invalidates_stale_handoff():
    app = create_mcp(Settings(auth_token="", allow_remote_http=False))
    record = {
        "interface_id": "stair-slab-01",
        "from_discipline": "building-architecture",
        "to_discipline": "building-structural",
        "interface_type": "stair_slab_opening",
        "owner_discipline": "building-structural",
        "required": True,
        "status": "accepted",
        "verification_state": "verified",
        "source_revision": "arch-r3",
        "handoff_revision": "coord-r7",
        "unit_system": "mm",
        "coordinate_frame_id": "project-grid-A",
        "conflict_state": "none",
        "evidence_refs": ["measurement:opening-01"],
    }
    async with Client(app) as client:
        result = await client.call_tool(
            "architecture_structural_interface_assess",
            {
                "records": [record],
                "current_revisions": {
                    "building-architecture": "arch-r4",
                    "building-structural": "struct-r2",
                },
                "expected_unit_system": "mm",
                "expected_coordinate_frame_id": "project-grid-A",
            },
        )

    payload = result.structured_content or {}
    assert payload["result"] == "blocked"
    assert "interface_source_revision_stale:stair-slab-01" in payload["reason_codes"]


@pytest.mark.asyncio
async def test_release_bundle_tool_is_a_fail_closed_machine_gate():
    app = create_mcp(Settings(auth_token="", allow_remote_http=False))
    bundle = {
        "run_id": "run-1",
        "design_basis_revision": "DB-1",
        "source_hashes": [
            {"source_id": "brief", "sha256": "a" * 64, "verification_state": "verified"}
        ],
        "version_bindings": {
            "domain": "building-architecture@0.2.2",
            "workflow": "design-review@0.2.0",
            "engineer_source_revision": "abc1234",
            "engineer_provider_version": "0.1.0a4",
            "engineer_contract_version": "cdt-engineer-v1-alpha4",
            "engineer_wheel_sha256": "b" * 64,
        },
        "runtime_identity": {
            "provider": "autocad",
            "provider_version": "0.4.0rc3",
            "contract_version": "autocad-generic-v1-rc3",
            "application_version": "AutoCAD 2027",
        },
        "artifacts": [
            {"artifact_id": "drawing", "sha256": "c" * 64, "reopened": True, "sealed": False}
        ],
        "checker_evidence": {
            "verdict": "PASS_FOR_DECLARED_SCOPE",
            "reviewer_role": "Checker / QA Engineer",
            "independent": True,
            "evidence_sha256": "d" * 64,
            "artifact_bindings": {"drawing": "c" * 64},
        },
        "required_recovery_classes": ["uncertain"],
        "recovery_negative_evidence": [
            {
                "case_id": "recovery-uncertain",
                "recovery_class": "uncertain",
                "result": "pass",
                "evidence_sha256": "e" * 64,
            }
        ],
    }
    async with Client(app) as client:
        result = await client.call_tool(
            "release_bundle_check",
            {
                "bundle": bundle,
                "current_source_hashes": {"brief": "a" * 64},
                "current_artifact_hashes": {"drawing": "c" * 64},
                "current_runtime_identity": bundle["runtime_identity"],
            },
        )

    payload = result.structured_content or {}
    assert payload["result"] == "blocked"
    assert "artifact_not_sealed:drawing" in payload["reason_codes"]


@pytest.mark.asyncio
async def test_validation_error_is_structured_at_mcp_boundary():
    app = create_mcp(Settings(auth_token="", allow_remote_http=False))
    async with Client(app) as client:
        result = await client.call_tool(
            "dependency_assess",
            {"requested_release": "not-a-release", "requirements": [], "states": {}},
            raise_on_error=False,
        )

    assert result.is_error is True
    payload = result.structured_content or {}
    assert payload["kind"] == "validation_error"
    assert payload["retryable"] is False
    assert payload["tool"] == "dependency_assess"


def test_http_transport_fails_closed_without_token():
    settings = Settings(auth_token="", allow_remote_http=False)
    with pytest.raises(SystemExit, match="CDT_ENGINEER_AUTH_TOKEN"):
        _validate_http_launch(settings, "127.0.0.1")


def test_remote_http_requires_explicit_opt_in():
    settings = Settings(auth_token="configured-at-runtime", allow_remote_http=False)
    with pytest.raises(SystemExit, match="non-loopback"):
        _validate_http_launch(settings, "0.0.0.0")


def test_remote_http_allowed_when_both_controls_are_present():
    settings = Settings(auth_token="configured-at-runtime", allow_remote_http=True)
    _validate_http_launch(settings, "0.0.0.0")
