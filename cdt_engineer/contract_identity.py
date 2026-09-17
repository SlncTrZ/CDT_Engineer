"""Public contract identity for the CDT_Engineer MCP provider.
Wing: code | Topic: mcp-provider | Updated: 2026-09-17
"""
from __future__ import annotations

import hashlib
from importlib import resources
from pathlib import Path

PROTOCOL_VERSION = "MCP"
CONTRACT_VERSION = "cdt-engineer-v1-alpha1"
UPDATED_AT = "2026-09-17"
PUBLIC_TOOL_COUNT = 14
EXECUTION_MODEL = "agent-orchestrated-engineering-os-v1"


def guide_content() -> str:
    """Load the canonical public provider guide from source or packaged data."""
    source_path = Path(__file__).resolve().parents[1] / "docs" / "TOOL_GUIDE.md"
    if source_path.is_file():
        return source_path.read_text(encoding="utf-8")
    packaged = resources.files("cdt_engineer").joinpath("docs").joinpath("TOOL_GUIDE.md")
    return packaged.read_text(encoding="utf-8")


def contract_material() -> tuple[str, str]:
    content = guide_content()
    return content, hashlib.sha256(content.encode("utf-8")).hexdigest()


def contract_hash() -> str:
    return contract_material()[1]
