"""Installed-wheel smoke: build at HEAD, clean-target install, provider + PlanSpec proof.
Wing: code | Topic: wheel-smoke | Updated: 2026-09-18 03:00
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_SMOKE_CHILD = r"""
import asyncio, json
from fastmcp import Client
from cdt_engineer.server import create_mcp
from cdt_engineer.config import Settings
from execution.planspec import validate_plan_spec

async def main():
    app = create_mcp(Settings(auth_token="", allow_remote_http=False))
    async with Client(app) as client:
        tools = sorted(t.name for t in await client.list_tools())
    spec = {
        "schema_version": "0.1.0", "plan_id": "wheel_smoke",
        "domain_id": "building-architecture", "plan_type": "architectural_floor_plan",
        "units": {"length": "mm", "angle": "deg"},
        "coordinate_system": {"datum": "smoke", "origin": [0.0, 0.0],
                              "scale": {"horizontal": 1.0}},
        "provenance_ledger": {}, "assumptions": [], "payload": {},
    }
    result = validate_plan_spec(spec)
    print(json.dumps({"tools": tools, "tool_count": len(tools),
                      "planspec_valid": result.valid,
                      "planspec_verdict": result.verdict}))

asyncio.run(main())
"""


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, text=True, capture_output=True, **kwargs)
    if proc.returncode:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(f"command failed: {cmd}")
    return proc


def main() -> None:
    work = Path(tempfile.mkdtemp(prefix="cdt-wheel-smoke-"))
    dist = work / "dist"
    target = work / "target"
    dist.mkdir()
    target.mkdir()
    _run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps",
          "--no-build-isolation", "-w", str(dist)], cwd=str(ROOT))
    wheels = sorted(dist.glob("*.whl"))
    if not wheels:
        raise SystemExit("no wheel built")
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
    schema_entry = "cdt_engineer/data/schemas/plan-spec.schema.json"
    schema_packaged = schema_entry in names
    _run([sys.executable, "-m", "pip", "install", "--target", str(target),
          "--no-deps", str(wheel)])
    child = work / "smoke_child.py"
    child.write_text(_SMOKE_CHILD, encoding="utf-8")
    proc = _run([sys.executable, str(child)], cwd=str(work),
                env={"PATH": __import__("os").environ["PATH"],
                     "PYTHONPATH": str(target),
                     "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", ""),
                     "PYTHONDONTWRITEBYTECODE": "1"})
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    ok = schema_packaged and payload["tool_count"] == 14 and payload["planspec_valid"] is True
    print(json.dumps({
        "result": "PASS" if ok else "FAIL",
        "wheel": wheel.name,
        "schema_packaged": schema_packaged,
        "tools": payload["tools"],
        "tool_count": payload["tool_count"],
        "planspec_valid": payload["planspec_valid"],
        "planspec_verdict": payload["planspec_verdict"],
    }, indent=2))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
