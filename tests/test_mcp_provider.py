"""MCP provider contract for CDT_Engineer Engineering OS.
Wing: code | Topic: mcp-provider | Updated: 2026-09-17
"""
from __future__ import annotations

import pytest
from fastmcp import Client

from cdt_engineer.config import Settings
from cdt_engineer.contract_identity import CONTRACT_VERSION, PUBLIC_TOOL_COUNT
from cdt_engineer.server import _TOOL_DESCRIPTIONS, _validate_http_launch, create_mcp


EXPECTED_TOOLS = {
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
}


@pytest.mark.asyncio
async def test_provider_surface_is_bounded_and_semantic():
    app = create_mcp(Settings(auth_token="", allow_remote_http=False))
    async with Client(app) as client:
        tools = list(await client.list_tools())

    names = {tool.name for tool in tools}
    assert names == EXPECTED_TOOLS == set(_TOOL_DESCRIPTIONS)
    assert len(names) == PUBLIC_TOOL_COUNT == 14
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

    caps = caps_result.structured_content or {}
    assert caps["provider"] == "cdt-engineer"
    assert caps["capabilities"]["engineering.profile_assess"]["supported"] is True
    assert caps["capabilities"]["native.cad_mutation"]["supported"] is False


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
    assert engine_map["engine_map"]["source_snapshot"]["contract_version"] == "autocad-generic-v1-rc2"


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
