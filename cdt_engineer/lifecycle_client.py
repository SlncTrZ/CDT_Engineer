"""Bounded client for the separately authorized execution controller.
Wing: code | Topic: execution-lifecycle | Updated: 2026-10-05 17:58 (Asia/Ho_Chi_Minh)
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
_ACTIONS = {"list", "status", "ensure", "stop", "operation_status"}


async def request(controller: str, action: str, **arguments: Any) -> dict[str, Any]:
    if action not in _ACTIONS:
        raise ValueError("invalid_lifecycle_action")
    if arguments.get("engine", "autocad") != "autocad":
        raise ValueError("engine_not_configured")
    if "operation_id" in arguments and not _ID.fullmatch(arguments["operation_id"]):
        raise ValueError("invalid_operation_id")
    if not controller:
        return {"ok": False, "state": "BLOCKED", "code": "CONTROLLER_NOT_CONFIGURED"}
    path = Path(controller)
    if not path.is_absolute() or not path.is_file():
        return {"ok": False, "state": "BLOCKED", "code": "CONTROLLER_UNAVAILABLE"}
    process = await asyncio.create_subprocess_exec(
        str(path), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        stdout, _ = await asyncio.wait_for(
            process.communicate(json.dumps({"action": action, **arguments}).encode()), 50,
        )
    except TimeoutError:
        process.kill()
        await process.wait()
        return {"ok": False, "state": "UNKNOWN", "code": "CONTROLLER_TIMEOUT",
                "retryable": False, "reconcile_required": True}
    if process.returncode or len(stdout) > 65536:
        return {"ok": False, "state": "UNKNOWN", "code": "CONTROLLER_RESPONSE_INVALID",
                "retryable": False, "reconcile_required": True}
    try:
        result = json.loads(stdout)
    except (UnicodeError, json.JSONDecodeError):
        result = None
    if not isinstance(result, dict):
        return {"ok": False, "state": "UNKNOWN", "code": "CONTROLLER_RESPONSE_INVALID"}
    return result
