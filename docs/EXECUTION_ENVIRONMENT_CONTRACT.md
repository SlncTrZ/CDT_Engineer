# Execution Environment Contract

Version: 0.1.0 · Updated: 2026-09-12 · Status: Engineering OS Step-0 baseline.

## Purpose

Before CDT_Engineer selects an engineering application, gives version-specific operating guidance, or performs native execution, the Agent must discover the actual execution environment. Installed software, application version/path, and provider readiness are observed facts, not assumptions.

This is **Step 0**. It precedes Design Basis execution planning and software capability mapping; it does not replace engineering intent or Design Basis.

Machine-readable inventory instances conform to [`schemas/execution-environment.schema.json`](schemas/execution-environment.schema.json).

## Two independent inventories

The Agent keeps these facts separate:

1. **Installed Software Inventory** — whether the application exists on the target host, its executable/install path, version/build/edition, OS context and observation method/time.
2. **Execution Capability Inventory** — whether the corresponding public MCP/provider is configured and ready, its provider/contract version, and the capabilities discovered from the current runtime.

`software installed` does not imply `Agent can execute it`. Provider readiness does not prove a compatible application/version exists.

## Mandatory Step-0 flow

```text
identify target host
→ observe OS/architecture
→ discover required application
→ resolve executable/install path + version/build/edition
→ discover provider/runtime contract + capabilities
→ compare with Software Operating Guide support range
→ classify compatibility
→ continue, guide-only, request installation/configuration, or BLOCK
```

Do not infer installation from a remembered path, infer version from a folder name alone when a stronger source exists, or reuse stale runtime capabilities as current proof.

## Required application states

- `installed`: executable/install path and application version are observed.
- `not_installed`: discovery was performed and the application was not found; version/path fields remain null.
- `unknown`: discovery could not establish the state; never silently treat it as installed or absent.

For native execution, `unknown` is fail-closed.

## Provider states

- `ready`: runtime provider version, contract version and at least one discovered capability are observed.
- `not_ready`: provider exists but cannot currently execute its declared role.
- `not_configured`: no usable provider configuration exists for the target software.
- `unknown`: provider state could not be established.

A machine may therefore validly report `solidworks installed` + `cdt-solidworks not_ready`. In that state the Agent may give appropriately versioned human guidance, but it must not claim native automation readiness.

## Version compatibility

Every Software Operating Guide declares its supported application/version range and pinned provider contract. Step 0 compares observed environment facts against that guide before execution.

Compatibility result is one of:

- `compatible` — observed application/provider versions are within the guide's proven range and required runtime capabilities are present;
- `guidance_only` — the application is known well enough for human operating guidance, but native provider execution is unavailable or unproven;
- `installation_required` — required software is explicitly not installed;
- `configuration_required` — software exists but provider/plugin/runtime configuration is missing;
- `version_mismatch` — installed version is outside the guide's proven range or provider contract is incompatible;
- `unknown` — evidence is insufficient; native execution blocks.

Do not silently downgrade a version mismatch into `compatible`.

## Freshness and cache policy

Inventory may be cached to avoid rescanning the host for every prompt. Each observation carries `observed_at` and `discovery_method`.

Before mutation-heavy/native work, revalidate drift-prone facts at minimum:

- target application version/running attachment where relevant;
- provider version and contract version;
- runtime capability surface;
- required plugin/add-in readiness where the Software Operating Guide declares one;
- required writable workspace/output path when execution depends on it.

A cached inventory is context, not runtime proof.

## Safety and user interaction

If required software is not installed, the Agent reports the typed blocker and asks the user to install/authorize installation rather than pretending execution is possible. CDT_Engineer must not self-install licensed engineering software unless a separately authorized installation workflow exists.

If software is installed but execution integration is unavailable, distinguish human guidance from native automation. If version or environment is unknown, ask for or perform permitted discovery instead of guessing.

## Relationship to software guides and workflows

Software Operating Guides consume Step-0 inventory and define application-specific discovery methods, supported versions, required plugins/providers, capability expectations and compatibility rules. Workflows consume the resulting compatibility classification before capability preflight and Feature-based Chunk planning.

Historical runs pin the inventory observation used for execution so later QA can distinguish environment drift from engineering logic changes.
