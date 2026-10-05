"""Lifecycle authority, durable operation identity and fail-closed boundaries."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastmcp import Client

from cdt_engineer.config import Settings
from cdt_engineer.server import create_mcp


@pytest.mark.asyncio
async def test_unconfigured_controller_cannot_start_native_runtime():
    async with Client(create_mcp(Settings(auth_token=""))) as client:
        result = await client.call_tool("execution_ensure", {"engine": "autocad", "operation_id": "cold-1"})
    assert result.structured_content["code"] == "CONTROLLER_NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_arbitrary_host_and_operation_injection_are_refused():
    async with Client(create_mcp(Settings(auth_token=""))) as client:
        for arguments in [
            {"engine": "arbitrary-host", "operation_id": "op-1"},
            {"engine": "autocad", "operation_id": "op;launch"},
        ]:
            result = await client.call_tool("execution_ensure", arguments, raise_on_error=False)
            assert result.is_error
            assert result.structured_content["kind"] == "validation_error"


@pytest.mark.asyncio
async def test_lifecycle_side_effect_tools_are_not_advertised_read_only():
    async with Client(create_mcp(Settings(auth_token=""))) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
    assert tools["execution_ensure"].annotations.readOnlyHint is False
    assert tools["execution_stop"].annotations.readOnlyHint is False
    assert tools["execution_status"].annotations.readOnlyHint is True


def controller():
    path = Path(__file__).resolve().parents[1] / "scripts" / "execution_controller.py"
    spec = importlib.util.spec_from_file_location("controller_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_controller_accepts_no_arbitrary_shell_or_task(tmp_path):
    module = controller()
    cfg = {"state_dir": str(tmp_path)}
    assert module.handle(cfg, {"action": "ensure", "engine": "autocad", "operation_id": "safe", "command": "anything"})["code"] == "INVALID_REQUEST"
    assert module.handle(cfg, {"action": "ensure", "engine": "elsewhere", "operation_id": "safe"})["code"] == "ENGINE_NOT_CONFIGURED"


def test_operation_identity_survives_new_controller_instance_and_blocks_conflict(tmp_path, monkeypatch):
    module = controller()
    cfg = {"state_dir": str(tmp_path)}
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))
    request = {"action": "ensure", "engine": "autocad", "operation_id": "same-1"}
    first = module.handle(cfg, request)
    assert first["state"] == "QUEUED"
    restarted = controller()
    assert restarted.handle(cfg, request)["operation_id"] == first["operation_id"]
    conflicting = {"action": "stop", "engine": "autocad", "operation_id": "same-1", "scope": "both"}
    assert restarted.handle(cfg, conflicting)["code"] == "OPERATION_ID_CONFLICT"
    other = module.handle(cfg, {**request, "operation_id": "other-1"})
    assert other["code"] == "ENGINE_LIFECYCLE_BUSY"
    assert other["operation_id"] == "same-1"


def test_uncertified_stop_is_persisted_without_terminating_processes(tmp_path, monkeypatch):
    module = controller()
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: pytest.fail("stop must not launch or kill"))
    cfg = {"state_dir": str(tmp_path)}
    value = module.handle(cfg, {"action": "stop", "engine": "autocad", "operation_id": "stop-1", "scope": "both"})
    assert value["state"] == "BLOCKED"
    assert value["result"]["code"] == "NATIVE_STOP_NOT_CERTIFIED"
    assert value["result"]["no_process_terminated"] is True
