"""Build the current working tree and verify its wheel in an isolated venv.
Wing: code | Topic: wheel-smoke | Updated: 2026-10-01
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import venv
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_SMOKE_CHILD = r'''
import asyncio, copy, importlib.metadata, json, math, pathlib, sys
from fastmcp import Client
from cdt_engineer.server import create_mcp
from cdt_engineer.config import Settings
from execution.planspec import validate_plan_spec
from execution.plan_review import review_plan_spec
from execution.plan_compiler import compile_plan_spec
from execution.source_calibration import calibrate_plan_source

def fixture():
    # A specified synthetic source, independently enumerated below. No image
    # interpretation or native execution is claimed by this packaging fixture.
    walls = [
        {"wall_id": "w1", "wall_type": "bearing", "start": [0, 0], "end": [5000, 0]},
        {"wall_id": "w2", "wall_type": "exterior", "start": [5000, 0], "end": [5000, 4000]},
        {"wall_id": "w3", "wall_type": "exterior", "start": [5000, 4000], "end": [0, 4000]},
        {"wall_id": "w4", "wall_type": "exterior", "start": [0, 4000], "end": [0, 0]},
    ]
    for wall in walls:
        wall.update(thickness=220, height=3300, baseline="center")
    requirements = {
        "axes": ["a", "b"], "walls": ["w1", "w2", "w3", "w4"],
        "bearing_walls": ["w1"], "partition_walls": [], "columns": ["c"],
        "doors": ["d"], "windows": ["window"], "spaces": ["room"],
        "fixtures": ["sofa"], "dimensions": ["dim"],
    }
    items = []
    for family, refs in requirements.items():
        item = {"item_id": family, "semantic_family": family, "required": bool(refs),
                "feature_refs": refs, "evidence_state": "specified",
                "source_evidence": ["Synthetic packaging fixture specification v1"]}
        if not refs:
            item.update(exclusion_reason="No internal partition in this one-room fixture",
                        reviewed_by="packaging-fixture-definition")
        items.append(item)
    ids = ["a", "b", "w1", "w2", "w3", "w4", "c", "d", "window", "room", "sofa", "dim"]
    return {
        "schema_version": "0.1.0", "plan_id": "wheel_smoke",
        "domain_id": "building-architecture", "plan_type": "architectural_floor_plan",
        "units": {"length": "mm", "angle": "deg"},
        "coordinate_system": {"datum": "synthetic", "origin": [0, 0],
                              "scale": {"horizontal": 1}},
        "provenance_ledger": {i: {"status": "specified", "source_id": "synthetic"} for i in ids},
        "assumptions": [],
        "source_inventory": {
            "source_id": "synthetic", "source_sha256": "1" * 64,
            "source_type": "specified", "review_passes": [], "items": items},
        "payload": {
            "axes": [{"axis_id": "a", "label": "A", "start": [0, 0], "end": [5000, 0]},
                     {"axis_id": "b", "label": "B", "start": [0, 0], "end": [0, 4000]}],
            "walls": walls,
            "columns": [{"column_id": "c", "shape": "rect", "dimensions": [220, 220],
                         "center": [0, 0]}],
            "openings": [
                {"opening_id": "d", "host_wall_id": "w1", "opening_type": "door",
                 "offset_along_wall": 1000, "width": 900, "height": 2200,
                 "sill_height": 0, "head_height": 2200},
                {"opening_id": "window", "host_wall_id": "w2", "opening_type": "window",
                 "offset_along_wall": 1000, "width": 1200, "height": 1200,
                 "sill_height": 900, "head_height": 2100}],
            "spaces": [{"space_id": "room", "name": "Room",
                        "boundary_polygon": [[0, 0], [5000, 0], [5000, 4000], [0, 4000]],
                        "net_area": 20}],
            "fixtures": [{"fixture_id": "sofa", "fixture_type": "sofa",
                          "host_space_id": "room", "position": [2500, 2000],
                          "dimensions": [1000, 600], "rotation": 0}],
            "dimensions": [{"dimension_id": "dim", "dimension_type": "linear",
                            "measured_value": 5000, "witness_points": [[0, 0], [5000, 0]],
                            "feature_refs": ["w1"]}],
        },
    }

async def main():
    app = create_mcp(Settings(auth_token="", allow_remote_http=False))
    async with Client(app) as client:
        tools = sorted(t.name for t in await client.list_tools())
    spec = fixture()
    compiled = compile_plan_spec(spec)
    checks = {
        "valid_spec": validate_plan_spec(spec).valid,
        "review_approved": review_plan_spec(spec).approved,
        "compiled": compiled.ok and bool(compiled.chunks),
        "chunk_source_binding": all(c.get("source_sha256") == "1" * 64 and
                                   len(c.get("source_inventory_sha256", "")) == 64
                                   for c in compiled.chunks),
    }
    empty = copy.deepcopy(spec)
    empty["payload"] = {}
    checks["empty_floor_plan_refused"] = not compile_plan_spec(empty).ok
    missing = copy.deepcopy(spec)
    missing["payload"]["openings"] = []
    checks["required_openings_refused"] = not compile_plan_spec(missing).ok
    for label, value in (("nan", float("nan")), ("infinity", float("inf"))):
        unsafe = copy.deepcopy(spec)
        unsafe["payload"]["spaces"][0]["boundary_polygon"][2][0] = value
        checks[label + "_refused"] = not compile_plan_spec(unsafe).ok
    overflow = calibrate_plan_source(
        source={"source_id": "s", "pixel_width": 100, "pixel_height": 100},
        anchors=[{"anchor_id": "a", "pixel_from": [0, 0], "pixel_to": [1, 0],
                  "real_length": 1e307, "unit": "mm"}],
        pixel_features=[{"feature_id": "p", "kind": "point", "pixels": [100, 0]}])
    checks["calibration_overflow_refused"] = overflow.verdict == "INVALID_SOURCE"
    import cdt_engineer, execution.planspec, fastmcp
    origins = {m.__name__: str(pathlib.Path(m.__file__).resolve())
               for m in (cdt_engineer, execution.planspec, fastmcp)}
    prefix = pathlib.Path(sys.prefix).resolve()
    checks["venv_isolated"] = sys.prefix != sys.base_prefix
    checks["imports_from_venv"] = all(pathlib.Path(p).is_relative_to(prefix)
                                     for p in origins.values())
    print(json.dumps({"tools": tools, "tool_count": len(tools), "checks": checks,
                      "origins": origins, "python": sys.version.split()[0],
                      "fastmcp_version": importlib.metadata.version("fastmcp")},
                     allow_nan=False))
    if not all(checks.values()):
        raise SystemExit(1)

asyncio.run(main())
'''


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
        env.pop(name, None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _run(cmd: list[str], *, cwd: Path, timeout: int = 180) -> str:
    proc = subprocess.run(cmd, cwd=cwd, env=_environment(), text=True,
                          capture_output=True, timeout=timeout)
    if proc.returncode:
        # Preserve generic stage failure without leaking index URLs/credentials.
        raise RuntimeError(f"verification command failed (exit {proc.returncode})")
    return proc.stdout


def _source_fingerprint() -> str:
    proc = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                          cwd=ROOT, capture_output=True, check=True)
    digest = hashlib.sha256()
    for name in sorted(set(proc.stdout.split(b"\0")) - {b""}):
        path = ROOT / os.fsdecode(name)
        if not path.is_file():
            continue
        digest.update(name + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=ROOT / "_private" / "wheel-verification")
    args = parser.parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="candidate-", dir=args.work_dir.resolve()))
    # Source/evidence may be on a Windows-backed share that cannot create
    # Unix symlinks. Virtual environments belong on the host's temp filesystem;
    # the durable wheel/report remain in the requested evidence directory.
    runtime_work = Path(tempfile.mkdtemp(prefix="cdt-wheel-runtime-"))
    fingerprint = _source_fingerprint()
    report = {"result": "FAIL", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "source_fingerprint_sha256": fingerprint, "work_directory": str(work),
              "runtime_work_directory": str(runtime_work),
              "native_acceptance": "NOT_RUN"}
    stage = "create_build_environment"
    try:
        builder = runtime_work / "builder"
        installed = runtime_work / "installed"
        venv.EnvBuilder(with_pip=True).create(builder)
        build_python = builder / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        stage = "install_build_dependency"
        _run([str(build_python), "-m", "pip", "install", "--disable-pip-version-check",
              "--retries", "1", "--timeout", "15", "hatchling"], cwd=work)
        dist = work / "dist"
        dist.mkdir()
        stage = "build_wheel"
        _run([str(build_python), "-m", "pip", "wheel", str(ROOT), "--no-deps",
              "--no-build-isolation", "-w", str(dist)], cwd=work)
        wheel, = dist.glob("*.whl")
        report["wheel"] = str(wheel)
        report["wheel_sha256"] = hashlib.sha256(wheel.read_bytes()).hexdigest()
        with zipfile.ZipFile(wheel) as zf:
            report["schema_packaged"] = "cdt_engineer/data/schemas/plan-spec.schema.json" in zf.namelist()
        stage = "create_installed_environment"
        venv.EnvBuilder(with_pip=True).create(installed)
        installed_python = installed / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        stage = "install_wheel_and_declared_dependencies"
        _run([str(installed_python), "-m", "pip", "install", "--disable-pip-version-check",
              "--retries", "1", "--timeout", "15", str(wheel) + "[dev]"], cwd=work)
        stage = "pip_check"
        _run([str(installed_python), "-m", "pip", "check"], cwd=work)
        report["pip_check"] = "PASS"
        report["dependencies"] = json.loads(_run(
            [str(installed_python), "-m", "pip", "list", "--format=json"], cwd=work))
        stage = "installed_wheel_behavior"
        child = runtime_work / "smoke_child.py"
        child.write_text(_SMOKE_CHILD, encoding="utf-8")
        payload = json.loads(_run([str(installed_python), "-I", str(child)], cwd=work).strip().splitlines()[-1])
        report["installed_wheel"] = payload
        required = {"observation_assess", "impact_assess",
                    "architecture_structural_interface_assess", "release_bundle_check"}
        if not (report["schema_packaged"] and payload["tool_count"] == 18 and
                required.issubset(payload["tools"]) and all(payload["checks"].values())):
            raise RuntimeError("installed wheel acceptance failed")
        stage = "source_foundation_in_clean_dependency_environment"
        # This is source-suite validation using newly resolved dependencies,
        # separately from the isolated installed-wheel behavior above.
        foundation = json.loads(_run(
            [str(installed_python), "-B", str(ROOT / "scripts" / "validate_foundation.py")],
            cwd=ROOT))
        report["source_foundation_clean_env"] = foundation
        report["source_fingerprint_unchanged"] = fingerprint == _source_fingerprint()
        if not report["source_fingerprint_unchanged"]:
            raise RuntimeError("source changed during verification")
        report["result"] = "PASS"
    except Exception as exc:
        report["failed_stage"] = stage
        report["error_type"] = type(exc).__name__
    evidence = work / "verification.json"
    evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                        encoding="utf-8")
    print(json.dumps({"result": report["result"], "report": str(evidence),
                      "wheel_sha256": report.get("wheel_sha256"),
                      "failed_stage": report.get("failed_stage"),
                      "foundation": report.get("source_foundation_clean_env"),
                      "installed_checks": report.get("installed_wheel", {}).get("checks")},
                     ensure_ascii=False, indent=2))
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
