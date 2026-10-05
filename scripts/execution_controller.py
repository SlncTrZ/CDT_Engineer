#!/usr/bin/python3
"""Owner-authorized AutoCAD lifecycle controller; no native CAD backend.
Wing: code | Topic: execution-lifecycle | Updated: 2026-10-05 17:58 (Asia/Ho_Chi_Minh)
"""
from __future__ import annotations

import base64
import hashlib
import http.client
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "controller-config.json"
MAX_BYTES = 65536
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
TOOLS = ["help", "system_status", "system_capabilities", "native_integrity_status", "document_info"]


def user_manager_env():
    uid = getattr(os, "getuid", lambda: 1000)()
    return {**os.environ, "XDG_RUNTIME_DIR": f"/run/user/{uid}",
            "DBUS_SESSION_BUS_ADDRESS": f"unix:path=/run/user/{uid}/bus"}


def blocked(code, **extra):
    return {"ok": False, "state": "BLOCKED", "code": code, **extra}


def windows(config, action):
    if action not in {"start", "status", "stop"}:
        raise ValueError("invalid_windows_action")
    # Only trusted deployment paths enter this PowerShell command.
    script = "$ErrorActionPreference='Stop';& '" + config["windows_python"].replace("'", "''") + "' '" + config["windows_worker"].replace("'", "''") + "' '" + action + "';exit $LASTEXITCODE"
    command = ["/usr/bin/ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=5", "-o", "ServerAliveInterval=10",
               "-o", "ServerAliveCountMax=2", "truon@192.168.1.171",
               "powershell.exe -NoProfile -NonInteractive -EncodedCommand " +
               base64.b64encode(script.encode("utf-16-le")).decode()]
    try:
        r = subprocess.run(command, capture_output=True, timeout=40)
        if r.returncode or len(r.stdout) > MAX_BYTES:
            return blocked("WINDOWS_CONTROL_UNAVAILABLE")
        result = json.loads(r.stdout.decode("utf-8-sig"))
        return result if isinstance(result, dict) else blocked("WINDOWS_RESPONSE_INVALID")
    except (OSError, subprocess.TimeoutExpired, UnicodeError, json.JSONDecodeError):
        return blocked("WINDOWS_CONTROL_UNAVAILABLE")


class Owner:
    """Existing gateway owner authentication, confined to the AutoCAD route."""
    def __init__(self):
        secret = Path("/var/lib/slnctrz-mcp/secrets/owner-passphrase").read_text().rstrip("\r\n")
        self.cookie = ""
        self.csrf = ""
        self.call("POST", "/owner/api/login", {"secret": secret}, login=True)

    def call(self, method, path, body=None, login=False):
        permitted = {"/owner/api/login", "/owner/api/logout", "/owner/api/mcp",
                     "/owner/api/mcp/cdt-autocad", "/owner/api/mcp/cdt-autocad/sync"}
        if path not in permitted:
            raise RuntimeError("owner_route_not_allowed")
        connection = http.client.HTTPConnection("127.0.0.1", 3100, timeout=90)
        headers = {"Host": "mcp.truongcongdinh.org", "Origin": "https://mcp.truongcongdinh.org",
                   "Content-Type": "application/json"}
        if self.cookie:
            headers.update({"Cookie": self.cookie, "X-SlncTrZ-CSRF": self.csrf})
        try:
            connection.request(method, path, json.dumps(body or {}).encode(), headers)
            response = connection.getresponse()
            data = response.read(MAX_BYTES + 1)
            if response.status not in {200, 201} or len(data) > MAX_BYTES:
                raise RuntimeError("gateway_control_rejected")
            value = json.loads(data)
            if login:
                self.cookie = response.getheader("Set-Cookie", "").split(";", 1)[0]
                self.csrf = value.get("csrf", "")
                if not self.cookie or not self.csrf:
                    raise RuntimeError("gateway_control_unavailable")
            return value
        finally:
            connection.close()

    def close(self):
        try:
            self.call("POST", "/owner/api/logout")
        except Exception:
            pass
        self.cookie = self.csrf = ""


def manifest(config):
    return {"id": "cdt-autocad", "version": "0.4.0rc3", "transport": "stdio",
        "command": "/usr/bin/ssh", "args": [
            "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=5",
            "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3",
            "truon@192.168.1.171", config["relay_command"]],
        "maxQueue": 4, "requestTimeoutMs": 30000, "startupTimeoutMs": 30000,
        "maxRestarts": 3,
        "tools": [{"canonicalId": "cdt-autocad." + name, "riskClass": "read"} for name in TOOLS]}


def activate(config):
    record = next((p for p in json.loads(Path("/var/lib/slnctrz-mcp/mcp/providers.json").read_text())["providers"]
                   if p["manifest"]["id"] == "cdt-autocad"), None)
    owner = Owner()
    try:
        if record is None:
            value = owner.call("POST", "/owner/api/mcp", {"name": "AutoCAD", "manifest": manifest(config)})
            if value.get("status") != "committed":
                raise RuntimeError("gateway_registration_failed")
        else:
            actual = record["manifest"]
            desired = manifest(config)
            if actual["transport"] != desired["transport"] or {t["canonicalId"] for t in actual["tools"]} != {t["canonicalId"] for t in desired["tools"]}:
                raise RuntimeError("gateway_manifest_drift")
            if not record["enabled"]:
                value = owner.call("PATCH", "/owner/api/mcp/cdt-autocad", {"enabled": True})
                if not value.get("reload", {}).get("activated"):
                    raise RuntimeError("gateway_enable_failed")
        value = owner.call("POST", "/owner/api/mcp/cdt-autocad/sync")
        if not value.get("reload", {}).get("activated"):
            raise RuntimeError("gateway_sync_failed")
        return {"activated": True, "accepted_tools": len(TOOLS), "client_refresh_required": True}
    finally:
        owner.close()


def ready(value):
    native = value.get("native", {})
    return (value.get("interactive_session") is True and value.get("mcp_discoverable") is True
            and bool(value.get("application")) and native.get("backend") == "com"
            and native.get("runtime", {}).get("ready") is True)


def db(config):
    path = Path(config["state_dir"])
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    connection = sqlite3.connect(path / "operations.sqlite3", timeout=5)
    connection.execute("CREATE TABLE IF NOT EXISTS operations (id TEXT PRIMARY KEY, request TEXT NOT NULL, state TEXT NOT NULL, result TEXT, created REAL NOT NULL, updated REAL NOT NULL)")
    os.chmod(path / "operations.sqlite3", 0o600)
    return connection


def fetch(connection, ident):
    row = connection.execute("SELECT id,state,result,created,updated FROM operations WHERE id=?", (ident,)).fetchone()
    if row is None:
        return blocked("OPERATION_NOT_FOUND")
    return {"ok": row[1] == "READY", "operation_id": row[0], "state": row[1],
            "result": json.loads(row[2]) if row[2] else None,
            "created_at": row[3], "updated_at": row[4]}


def work(config, ident):
    connection = db(config)
    with connection:
        changed = connection.execute("UPDATE operations SET state='RUNNING',updated=? WHERE id=? AND state='QUEUED'", (time.time(), ident)).rowcount
    if not changed:
        return
    started = time.monotonic()
    result = blocked("CONTROLLER_FAILURE")
    try:
        value = windows(config, "start")
        if value.get("ok") is not True:
            result = value
        else:
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                value = windows(config, "status")
                if ready(value):
                    if value.get("contract_version") != "autocad-generic-v1-rc3" or value.get("contract_hash") != value.get("expected_contract_hash"):
                        result = blocked("PROVIDER_CONTRACT_MISMATCH")
                        break
                    gateway = activate(config)
                    observed = windows(config, "status")
                    if not ready(observed):
                        result = blocked("POST_ACTIVATION_READINESS_FAILED", gateway=gateway)
                        break
                    result = {"ok": True, "state": "READY", "scope": "application_read_only",
                              "native_bridge_ready": observed.get("native", {}).get("bridge", {}).get("ready"),
                              "gateway": gateway, "observed": observed}
                    break
                if value.get("task_state") in {"Ready", "Disabled"} and not value.get("provider_running"):
                    result = blocked("INTERACTIVE_LAUNCH_FAILED", observed=value)
                    break
                time.sleep(2)
            else:
                result = blocked("STARTUP_DEADLINE", observed=value)
    except Exception:
        # Never persist exception text, HTTP responses, auth material or command output.
        result = blocked("GATEWAY_OR_CONTROLLER_UNAVAILABLE", partial_runtime_may_be_running=True)
    result["total_latency_ms"] = round((time.monotonic() - started) * 1000)
    with connection:
        connection.execute("UPDATE operations SET state=?,result=?,updated=? WHERE id=?",
                           ("READY" if result.get("ok") else "BLOCKED", json.dumps(result), time.time(), ident))


def handle(config, request):
    action = request.get("action")
    allowed = {"list": {"action"}, "status": {"action", "engine"},
               "ensure": {"action", "engine", "operation_id"},
               "stop": {"action", "engine", "operation_id", "scope"},
               "operation_status": {"action", "operation_id"}}
    if action not in allowed or set(request) - allowed[action]:
        return blocked("INVALID_REQUEST")
    if request.get("engine", "autocad") != "autocad":
        return blocked("ENGINE_NOT_CONFIGURED")
    if action == "list":
        return {"ok": True, "engines": [{"engine": "autocad", "display_name": "AutoCAD",
                 "host": ".171", "ensure_scope": "application_read_only",
                 "native_mutations_enabled": False, "stop_certified": False}]}
    if action == "status":
        return windows(config, "status")
    ident = request.get("operation_id", "")
    if not isinstance(ident, str) or not ID.fullmatch(ident):
        return blocked("INVALID_OPERATION_ID")
    connection = db(config)
    if action == "operation_status":
        value = fetch(connection, ident)
        # A transient systemd worker is checked after restart; never replay automatically.
        if value.get("state") == "RUNNING":
            unit = "slnctrz-exec-" + hashlib.sha256(ident.encode()).hexdigest()[:20] + ".service"
            check = subprocess.run(["systemctl", "--user", "is-active", unit], capture_output=True, timeout=5, env=user_manager_env())
            if check.returncode:
                return {**value, "state": "UNKNOWN", "code": "RECONCILIATION_REQUIRED", "retryable": False}
        return value
    encoded = json.dumps(request, sort_keys=True)
    connection.execute("BEGIN IMMEDIATE")
    row = connection.execute("SELECT request FROM operations WHERE id=?", (ident,)).fetchone()
    if row:
        connection.rollback()
        return fetch(connection, ident) if row[0] == encoded else blocked("OPERATION_ID_CONFLICT")
    active = connection.execute("SELECT id FROM operations WHERE state IN ('QUEUED','RUNNING') LIMIT 1").fetchone()
    if active:
        connection.rollback()
        return {"ok": False, "state": "BUSY", "operation_id": active[0], "code": "ENGINE_LIFECYCLE_BUSY"}
    if action == "stop":
        if request.get("scope", "provider") not in {"provider", "application", "both"}:
            connection.rollback()
            return blocked("INVALID_STOP_SCOPE")
        value = blocked("NATIVE_STOP_NOT_CERTIFIED", no_process_terminated=True,
                        reason="The existing launcher has no ownership-safe remote drain/shutdown contract.")
        connection.execute("INSERT INTO operations VALUES (?,?,?,?,?,?)", (ident, encoded, "BLOCKED", json.dumps(value), time.time(), time.time()))
        connection.commit()
        return fetch(connection, ident)
    connection.execute("INSERT INTO operations VALUES (?,?,?,?,?,?)", (ident, encoded, "QUEUED", None, time.time(), time.time()))
    connection.commit()
    unit = "slnctrz-exec-" + hashlib.sha256(ident.encode()).hexdigest()[:20]
    run = subprocess.run(["systemd-run", "--user", "--quiet", "--collect", "--unit=" + unit,
                          "/usr/bin/python3", str(Path(__file__).resolve()), "--work", ident],
                         capture_output=True, timeout=10, env=user_manager_env())
    if run.returncode:
        with connection:
            connection.execute("UPDATE operations SET state='BLOCKED',result=? WHERE id=?",
                               (json.dumps(blocked("WORKER_START_FAILED")), ident))
    return fetch(connection, ident)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        config = json.loads(CONFIG.read_text())
        if len(sys.argv) == 3 and sys.argv[1] == "--work" and ID.fullmatch(sys.argv[2]):
            work(config, sys.argv[2])
        elif len(sys.argv) == 1:
            raw = sys.stdin.buffer.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("request_too_large")
            print(json.dumps(handle(config, json.loads(raw))))
        else:
            raise ValueError("invalid_controller_arguments")
    except Exception:
        print(json.dumps(blocked("CONTROLLER_UNAVAILABLE")))
        sys.exit(1)
