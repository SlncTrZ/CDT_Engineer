"""FastMCP entrypoint for the CDT_Engineer Engineering OS provider.
Wing: code | Topic: mcp-provider | Updated: 2026-09-17
"""
from __future__ import annotations

import argparse
import json
from importlib import resources
from pathlib import Path
from typing import Any

import yaml
from fastmcp import FastMCP
from fastmcp.server.auth import StaticTokenVerifier
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult

from execution.artifact_evidence import artifact_manifest as build_artifact_manifest
from execution.artifact_evidence import evidence_is_stale
from execution.catalog_resolver import resolve_catalog_assets
from execution.completeness_checker import assess_inventory, assess_layer_ledger
from execution.qa_checker import checker_verdict
from execution.release_scope import assess_dependencies
from execution.stage_runner import run_profile
from professional_practice.human_deliverables import assess_human_deliverables

from . import __version__
from .config import Settings
from .contract_identity import (
    CONTRACT_VERSION,
    EXECUTION_MODEL,
    PROTOCOL_VERSION,
    PUBLIC_TOOL_COUNT,
    UPDATED_AT,
    contract_hash,
    contract_material,
)

_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_HTTP_TRANSPORTS = {"http", "sse", "streamable-http"}

_PROFILE_FILES = {
    "building-architecture": "domains/building-architecture/agent-profile.json",
    "building-structural": "domains/building-structural/agent-profile.json",
    "laser-2d3d-assembly": "domains/laser-2d3d-assembly/agent-profile.json",
    "mechanical-reconstruction": "domains/mechanical-reconstruction/agent-profile.json",
    "site-reconstruction": "domains/site-reconstruction/agent-profile.json",
}
_ENGINE_MAP_FILES = {
    "autocad": "software/autocad/engine-map.yaml",
    "sketchup": "software/sketchup/engine-map.yaml",
    "solidworks": "software/solidworks/engine-map.yaml",
}

_TOOL_DESCRIPTIONS = {
    "help": (
        "Return the current CDT_Engineer provider contract, operating boundary, tool guidance, and "
        "capability summary without mutating engineering or CAD state."
    ),
    "system_status": (
        "Report the Engineering OS provider runtime identity and source-package availability; this "
        "does not claim that any external CAD executor is installed or ready."
    ),
    "system_capabilities": (
        "Return the deterministic engineering assessment capabilities exposed by this provider and "
        "explicitly declare native CAD mutation as outside the provider boundary."
    ),
    "profile_get": (
        "Read one version-controlled public Agent Profile by domain identifier so a model can plan "
        "against canonical stages without inventing a private workflow."
    ),
    "engine_map_get": (
        "Read one public software engine map by software identifier; source expectations remain "
        "non-runtime evidence and current executor capabilities must still be discovered separately."
    ),
    "profile_assess": (
        "Evaluate one Agent Profile using caller-supplied runtime capability facts, stage checks, "
        "dependency states, and deliverable evidence without invoking any native CAD engine."
    ),
    "dependency_assess": (
        "Apply the release-scope dependency policy to explicit semantic dependency states and return "
        "typed blockers or a recommended lower release target without silently downgrading."
    ),
    "catalog_resolve": (
        "Resolve required semantic engineering assets against an explicit native mapping, current "
        "registry evidence, and released runtime capability without selecting proxy substitutions."
    ),
    "completeness_check": (
        "Check required-item implementation and verification coverage using the domain-neutral "
        "completeness invariant; omitted or unverified required content blocks release."
    ),
    "layer_ledger_check": (
        "Compare a frozen layered source ledger with final implementation evidence so occluded, off, "
        "or background requirements cannot disappear silently during reconstruction."
    ),
    "human_deliverable_check": (
        "Assess release-aware human-readable deliverable requirements, reviewer independence, "
        "revision freshness, hard gates, and quality findings without inferring discipline content."
    ),
    "qa_check": (
        "Aggregate independent checker findings against the current artifact hash and return a "
        "release-oriented verdict while rejecting stale evidence and unresolved major findings."
    ),
    "artifact_manifest": (
        "Build a deterministic engineering artifact evidence manifest from caller-supplied SHA-256 "
        "identity, source hashes, version bindings, and reopen status; no file is modified."
    ),
    "evidence_stale_check": (
        "Compare recorded artifact evidence with the current artifact SHA-256 and report whether the "
        "evidence is stale after a later mutation or artifact replacement."
    ),
}


def _runtime_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_runtime_text(relative: str) -> str:
    source = _runtime_root() / relative
    if source.is_file():
        return source.read_text(encoding="utf-8")
    parts = Path(relative).parts
    if parts and parts[0] == "domains":
        packaged = resources.files("domains")
        parts = parts[1:]
    else:
        packaged = resources.files("cdt_engineer").joinpath("data")
    for part in parts:
        packaged = packaged.joinpath(part)
    return packaged.read_text(encoding="utf-8")


def _load_profile(domain_id: str) -> dict[str, Any]:
    relative = _PROFILE_FILES.get(domain_id)
    if relative is None:
        raise ValueError(f"unknown domain_id: {domain_id}")
    payload = json.loads(_read_runtime_text(relative))
    if not isinstance(payload, dict):
        raise ValueError(f"profile must be a JSON object: {domain_id}")
    return payload


def _load_engine_map(software_id: str) -> dict[str, Any]:
    relative = _ENGINE_MAP_FILES.get(software_id)
    if relative is None:
        raise ValueError(f"unknown software_id: {software_id}")
    payload = yaml.safe_load(_read_runtime_text(relative))
    if not isinstance(payload, dict):
        raise ValueError(f"engine map must be a mapping: {software_id}")
    return payload


def _capabilities() -> dict[str, dict[str, Any]]:
    supported = {
        "engineering.profile_source": "Version-controlled Agent Profile discovery.",
        "engineering.engine_map_source": "Version-controlled software capability-map discovery.",
        "engineering.profile_assess": "Deterministic workflow-stage and release assessment.",
        "engineering.dependency_assess": "Fail-closed semantic dependency and release-scope assessment.",
        "engineering.catalog_resolve": "Semantic asset to verified native-registry binding assessment.",
        "engineering.completeness_check": "Required-item and layered-ledger completeness checks.",
        "engineering.human_deliverable_check": "Release-aware human deliverable acceptance checks.",
        "engineering.qa_check": "Independent finding aggregation with stale-evidence enforcement.",
        "engineering.artifact_evidence": "Hash-bound artifact manifest and staleness checks.",
    }
    result = {
        key: {"supported": True, "mode": "deterministic", "reason": description}
        for key, description in supported.items()
    }
    result["native.cad_mutation"] = {
        "supported": False,
        "mode": "external_executor_only",
        "reason": "Native CAD execution belongs to CDT-* Generic CAD executor providers.",
    }
    return result


def _help_payload() -> dict[str, Any]:
    content, digest = contract_material()
    return {
        "provider_name": "cdt-engineer",
        "provider_version": __version__,
        "protocol_version": PROTOCOL_VERSION,
        "contract_version": CONTRACT_VERSION,
        "contract_hash": digest,
        "public_tool_count": PUBLIC_TOOL_COUNT,
        "execution_model": EXECUTION_MODEL,
        "updated_at": UPDATED_AT,
        "authentication": "Bearer token required for HTTP transport; credentials are never returned",
        "capabilities": _capabilities(),
        "content": content,
    }


def _error_chain(exc: Exception) -> list[BaseException]:
    chain: list[BaseException] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(current)
        current = current.__cause__ or current.__context__
    return chain


def _classify_error(exc: Exception) -> tuple[str, dict[str, Any], str] | None:
    chain = _error_chain(exc)
    for item in chain:
        if isinstance(item, FileNotFoundError | KeyError):
            return "not_found", {"retryable": False}, str(item).strip("'")
    for item in chain:
        if isinstance(item, ValueError | TypeError | json.JSONDecodeError | yaml.YAMLError):
            return "validation_error", {"retryable": False}, str(item)
    for item in chain:
        if isinstance(item, RuntimeError):
            return "provider_unavailable", {"retryable": False}, str(item)
    return None


class ProviderErrorMiddleware(Middleware):
    """Convert expected engineering/provider failures into stable MCP errors."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        try:
            return await call_next(context)
        except Exception as exc:
            classified = _classify_error(exc)
            if classified is None:
                raise
            kind, extra, message = classified
            return ToolResult(
                content=message,
                structured_content={
                    "ok": False,
                    "kind": kind,
                    "error": message,
                    "tool": context.message.name,
                    **extra,
                },
                is_error=True,
            )


def create_mcp(settings: Settings | None = None) -> FastMCP:
    settings = settings or Settings.from_env()
    auth = None
    if settings.auth_token:
        auth = StaticTokenVerifier(
            tokens={
                settings.auth_token: {
                    "client_id": "cdt-engineer-client",
                    "scopes": ["mcp:read", "mcp:write"],
                }
            }
        )

    app = FastMCP(
        name="CDT Engineer",
        auth=auth,
        instructions=(
            "CDT_Engineer is the Engineering OS / thinking layer. It owns Design Basis semantics, "
            "workflow/release assessment, deterministic professional checks, QA and handoff evidence. "
            "It does not execute CAD. Discover and call CDT-* Generic CAD executor providers separately, "
            "then feed measured execution evidence back into CDT_Engineer checks."
        ),
    )
    app.add_middleware(ProviderErrorMiddleware())

    def provider_tool(*, tags: set[str]):
        def decorate(fn):
            name = fn.__name__
            description = _TOOL_DESCRIPTIONS.get(name)
            if description is None:
                raise RuntimeError(f"Missing public tool description: {name}")
            read_only = "write" not in tags
            return app.tool(
                tags=tags,
                description=description,
                annotations={"readOnlyHint": read_only},
            )(fn)

        return decorate

    @provider_tool(tags={"identity", "read"})
    async def help() -> dict[str, Any]:
        return _help_payload()

    @provider_tool(tags={"identity", "read"})
    async def system_status() -> dict[str, Any]:
        return {
            "provider": "cdt-engineer",
            "provider_version": __version__,
            "protocol_version": PROTOCOL_VERSION,
            "contract_version": CONTRACT_VERSION,
            "contract_hash": contract_hash(),
            "public_tool_count": PUBLIC_TOOL_COUNT,
            "execution_model": EXECUTION_MODEL,
            "runtime": {"ready": True, "state": "alpha_provider_slice"},
            "execution_boundary": {
                "engineering_os": True,
                "native_cad_execution": False,
                "orchestration_owner": "client_agent",
                "gateway_owner": "SlncTrZ-MCP",
            },
            "source_packages": {
                "profiles": sorted(_PROFILE_FILES),
                "engine_maps": sorted(_ENGINE_MAP_FILES),
            },
        }

    @provider_tool(tags={"identity", "read"})
    async def system_capabilities() -> dict[str, Any]:
        return {
            "provider": "cdt-engineer",
            "contract_version": CONTRACT_VERSION,
            "public_tool_count": PUBLIC_TOOL_COUNT,
            "execution_model": EXECUTION_MODEL,
            "capabilities": _capabilities(),
        }

    @provider_tool(tags={"source", "read"})
    async def profile_get(domain_id: str) -> dict[str, Any]:
        return {"domain_id": domain_id, "profile": _load_profile(domain_id)}

    @provider_tool(tags={"source", "read"})
    async def engine_map_get(software_id: str) -> dict[str, Any]:
        return {"software_id": software_id, "engine_map": _load_engine_map(software_id)}

    @provider_tool(tags={"workflow", "read"})
    async def profile_assess(
        profile: dict[str, Any],
        stage_checks: dict[str, Any],
        capabilities: dict[str, Any] | None = None,
        capabilities_by_software: dict[str, Any] | None = None,
        dependency_states: dict[str, Any] | None = None,
        stage_applicability: dict[str, Any] | None = None,
        human_deliverable_evidence: dict[str, Any] | None = None,
        package_revision: str | None = None,
        source_revision: str | None = None,
    ) -> dict[str, Any]:
        return run_profile(
            profile,
            capabilities=capabilities,
            stage_checks=stage_checks,
            capabilities_by_software=capabilities_by_software,
            dependency_states=dependency_states,
            stage_applicability=stage_applicability,
            human_deliverable_evidence=human_deliverable_evidence,
            package_revision=package_revision,
            source_revision=source_revision,
        )

    @provider_tool(tags={"release", "read"})
    async def dependency_assess(
        requested_release: str,
        requirements: list[dict[str, Any]],
        states: dict[str, Any],
    ) -> dict[str, Any]:
        return assess_dependencies(requested_release, requirements, states)

    @provider_tool(tags={"catalog", "read"})
    async def catalog_resolve(
        catalog: dict[str, Any],
        software_id: str,
        required_asset_ids: list[str],
        registry_evidence: dict[str, Any],
        runtime_capability: dict[str, Any],
    ) -> dict[str, Any]:
        return resolve_catalog_assets(
            catalog,
            software_id=software_id,
            required_asset_ids=required_asset_ids,
            registry_evidence=registry_evidence,
            runtime_capability=runtime_capability,
        )

    @provider_tool(tags={"qa", "read"})
    async def completeness_check(items: list[dict[str, Any]]) -> dict[str, Any]:
        return assess_inventory(items)

    @provider_tool(tags={"qa", "read"})
    async def layer_ledger_check(
        frozen: list[dict[str, Any]],
        final: dict[str, Any],
    ) -> dict[str, Any]:
        return assess_layer_ledger(frozen, final)

    @provider_tool(tags={"qa", "release", "read"})
    async def human_deliverable_check(
        requested_release: str,
        requirements: list[dict[str, Any]],
        evidence: dict[str, Any],
        package_revision: str,
        source_revision: str,
    ) -> dict[str, Any]:
        return assess_human_deliverables(
            requested_release,
            requirements,
            evidence,
            package_revision=package_revision,
            source_revision=source_revision,
        )

    @provider_tool(tags={"qa", "release", "read"})
    async def qa_check(
        findings: list[dict[str, Any]],
        current_artifact_sha256: str,
    ) -> dict[str, Any]:
        return checker_verdict(findings, current_artifact_sha256=current_artifact_sha256)

    @provider_tool(tags={"evidence", "read"})
    async def artifact_manifest(
        run_id: str,
        artifact_id: str,
        sha256: str,
        source_hashes: list[str],
        versions: dict[str, str],
        reopened: bool,
    ) -> dict[str, Any]:
        return build_artifact_manifest(
            run_id=run_id,
            artifact_id=artifact_id,
            sha256=sha256,
            source_hashes=source_hashes,
            versions=versions,
            reopened=reopened,
        )

    @provider_tool(tags={"evidence", "read"})
    async def evidence_stale_check(
        evidence: dict[str, Any],
        current_artifact_sha256: str,
    ) -> dict[str, Any]:
        stale = evidence_is_stale(evidence, current_artifact_sha256=current_artifact_sha256)
        return {
            "stale": stale,
            "result": "stale" if stale else "current",
            "current_artifact_sha256": current_artifact_sha256,
        }

    app._cdt_settings = settings  # type: ignore[attr-defined]
    return app


def _validate_http_launch(settings: Settings, host: str) -> None:
    if not settings.auth_token:
        raise SystemExit(
            "Refusing HTTP transport without CDT_ENGINEER_AUTH_TOKEN; use stdio or configure auth"
        )
    if host not in _LOOPBACK_HOSTS and not settings.allow_remote_http:
        raise SystemExit(
            "Refusing non-loopback HTTP bind; set CDT_ENGINEER_ALLOW_REMOTE_HTTP=true explicitly"
        )


mcp = create_mcp()
_original_run_async = mcp.run_async


async def _guarded_run_async(transport=None, *args, **kwargs):
    selected = transport or kwargs.get("transport")
    if selected in _HTTP_TRANSPORTS:
        host = str(kwargs.get("host") or "127.0.0.1")
        _validate_http_launch(mcp._cdt_settings, host)  # type: ignore[attr-defined]
    return await _original_run_async(transport, *args, **kwargs)


mcp.run_async = _guarded_run_async


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CDT_Engineer MCP provider")
    parser.add_argument("--transport", default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8010)
    args = parser.parse_args()

    if args.transport in _HTTP_TRANSPORTS:
        _validate_http_launch(mcp._cdt_settings, args.host)  # type: ignore[attr-defined]
        mcp.run(transport=args.transport, host=args.host, port=args.port)
    else:
        mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
