"""Engineering assessments must not retain infrastructure lifecycle ownership."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client

from cdt_engineer.config import Settings
from cdt_engineer.server import create_mcp

RETIRED = {
    "execution_list", "execution_status", "execution_ensure",
    "execution_stop", "execution_operation_status",
}


@pytest.mark.asyncio
async def test_catalog_excludes_infrastructure_lifecycle():
    async with Client(create_mcp(Settings(auth_token=""))) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
    assert RETIRED.isdisjoint(tools)
    assert tools["execution_environment_assess"].annotations.readOnlyHint is True
    assert len(tools) == 19


def test_product_has_no_controller_executable_or_client():
    root = Path(__file__).resolve().parents[1]
    assert not (root / "scripts" / "execution_controller.py").exists()
    assert not (root / "cdt_engineer" / "lifecycle_client.py").exists()
    assert not hasattr(Settings(auth_token=""), "execution_controller")
