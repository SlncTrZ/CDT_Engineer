"""Runtime configuration for the CDT_Engineer MCP provider.
Wing: code | Topic: mcp-provider | Updated: 2026-09-17
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Provider transport settings loaded from environment when not injected by tests."""

    auth_token: str
    allow_remote_http: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            auth_token=os.getenv("CDT_ENGINEER_AUTH_TOKEN", ""),
            allow_remote_http=_env_bool("CDT_ENGINEER_ALLOW_REMOTE_HTTP", False),
        )
