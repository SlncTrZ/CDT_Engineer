#!/usr/bin/env python3
"""Live planner -> SketchUp -> oracle end-to-end runner (ENG-R03).

Wing: code | Topic: live-e2e | Updated: 2026-09-17

Drives the CDT-SketchUp loopback bridge (127.0.0.1:9876) with real
``e2e-fixtures/*.json`` recipes: ``execute_geometry/create_mesh`` then
``get_entity_state`` read-back, verified by
:mod:`domains.building_architecture.plan_oracle`.

Dependency hygiene: this script uses only the Python standard library and
speaks the newline-delimited JSON bridge protocol directly. It deliberately
does NOT import engine runtime source; the bridge wire format is the pinned
public contract surface. Run only against a disposable test model:

    $env:PYTHONPATH="."; python scripts/live_run_e2e.py [--case ID] [--unit mm]

Evidence JSON is written under ignored ``_test_workspace/`` (never committed);
the human-readable verdict summary goes to stdout for the SOT/KB record.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FIXTURE_DIR = ROOT / "domains" / "building-architecture" / "e2e-fixtures"
EVIDENCE_DIR = ROOT / "_test_workspace"

from domains.building_architecture.plan_oracle import (  # noqa: E402
    assess_plan_execution,
)

BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 9876
MAX_FRAME = 256 * 1024


def _token_path() -> Path:
    configured = os.environ.get("CDT_SKETCHUP_BRIDGE_TOKEN_FILE", "")
    if configured:
        return Path(configured).expanduser()
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        return Path(local) / "CDT-SketchUp" / "bridge.token"
    return Path.home() / ".cdt-sketchup" / "bridge.token"


async def _bridge_call(command: str, params: dict, timeout: float = 30.0) -> object:
    token = _token_path().read_text(encoding="utf-8").strip()
    request = {
        "protocol": 1,
        "request_id": secrets.token_hex(16),
        "command": command,
        "params": params,
        "token": token,
    }
    frame = (json.dumps(request) + "\n").encode("utf-8")
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(BRIDGE_HOST, BRIDGE_PORT, limit=MAX_FRAME + 1),
        timeout=timeout,
    )
    try:
        writer.write(frame)
        await asyncio.wait_for(writer.drain(), timeout=timeout)
        raw = await asyncio.wait_for(reader.readuntil(b"\n"), timeout=timeout)
        payload = json.loads(raw.decode("utf-8"))
    finally:
        writer.close()
    if payload.get("ok") is not True:
        raise RuntimeError(f"bridge rejected {command}: {payload.get('error')}")
    if payload.get("request_id") != request["request_id"]:
        raise RuntimeError("bridge request_id mismatch")
    return payload.get("result")


def _unwrap(result: object) -> dict:
    """Unwrap one bridge result layer (server envelopes vary); fail loudly."""
    if isinstance(result, dict) and isinstance(result.get("result"), dict):
        return result["result"]
    if isinstance(result, dict):
        return result
    raise RuntimeError(f"unexpected bridge result shape: {type(result)}")


async def _run_case(case_id: str, unit: str, tolerance_mm: float, dump_raw: bool) -> dict:
    fixture = json.loads((FIXTURE_DIR / f"{case_id}.json").read_text(encoding="utf-8"))
    payload = fixture["create_mesh"]
    create_result = await _bridge_call(
        "execute_geometry",
        {
            "action": "create_mesh",
            "params": {
                "name": f"eng_r03_{case_id}",
                "points": payload["points"],
                "faces": payload["faces"],
            },
            "expect": payload["expect"],
            "unit": unit,
            "coordinate_space": "active_context",
        },
    )
    if dump_raw:
        print(json.dumps({"create_mesh_raw": create_result}, indent=2)[:4000])
    created = _unwrap(create_result)
    pid = created.get("created_pid", created.get("persistent_id"))
    if pid is None:
        # Fall back to whatever PID-like field the receipt carries.
        for key in ("group_pid", "entity_pid", "pid", "id"):
            if created.get(key) is not None:
                pid = created[key]
                break
    if pid is None:
        raise RuntimeError(f"no PID in create_mesh receipt keys: {sorted(created)}")
    state_result = await _bridge_call(
        "get_entity_state",
        {"persistent_id": pid, "unit": unit, "coordinate_space": "active_context"},
    )
    if dump_raw:
        print(json.dumps({"state_raw": state_result}, indent=2)[:4000])
    state = _unwrap(state_result)
    native_receipt = {
        "bbox": state.get("bounds") or {},
        "vertex_count": state.get("vertex_count"),
        "face_count": state.get("face_count"),
        "manifold": state.get("manifold"),
        "volume": state.get("volume"),
        "unit": unit,
        "persistent_id": state.get("persistent_id", pid),
    }
    verdict = assess_plan_execution(
        fixture["recipe"], fixture["expected"], native_receipt,
        tolerance_mm=tolerance_mm,
    )
    return {
        "case_id": case_id,
        "unit": unit,
        "tolerance_mm": tolerance_mm,
        "persistent_id": pid,
        "native_receipt": native_receipt,
        "oracle": verdict,
    }


async def main_async(args) -> int:
    cases = [args.case] if args.case else sorted(
        path.stem for path in FIXTURE_DIR.glob("*.json")
    )
    results = []
    for case_id in cases:
        try:
            results.append(await _run_case(case_id, args.unit, args.tolerance_mm, args.dump_raw))
        except Exception as exc:  # noqa: BLE001 - evidence must record failures
            results.append({"case_id": case_id, "error": f"{type(exc).__name__}: {exc}"})
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    evidence_path = EVIDENCE_DIR / f"live_e2e_evidence_{stamp}.json"
    evidence_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    for entry in results:
        if "error" in entry:
            print(f"{entry['case_id']}: ERROR {entry['error']}")
        else:
            checks = {
                name: check["result"]
                for name, check in entry["oracle"]["checks"].items()
            }
            print(f"{entry['case_id']}: verdict={entry['oracle']['verdict']} "
                  f"pid={entry['persistent_id']} checks={json.dumps(checks)}")
    print(f"evidence: {evidence_path.relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Live ENG-R03 end-to-end runner")
    parser.add_argument("--case", default=None, help="single fixture case_id")
    parser.add_argument("--unit", default="mm", help="native length unit")
    # 1 micron default: covers measured native float roundtrip (~3.2e-6 mm on
    # SketchUp 2024 mm->in->mm) while staying far below any engineering
    # tolerance. The oracle default stays strict at 1e-6 mm.
    parser.add_argument("--tolerance-mm", type=float, default=1e-3)
    parser.add_argument("--dump-raw", action="store_true",
                        help="print raw bridge receipts (debug)")
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
