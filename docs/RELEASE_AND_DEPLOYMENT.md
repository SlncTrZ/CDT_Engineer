# CDT_Engineer — Release and deployment

> Documentation class: PUBLIC_SOFTWARE_GUIDE

**Engineering OS provider package:** `0.1.1` · tag `v.0.1.1` · **independent** contract `cdt-engineer-v1-alpha7`. The `alpha7` component is the **contract identifier**, not a package release suffix; do not rename a wire contract without a compatibility review.

GitHub [source releases](https://github.com/SlncTrZ/CDT_Engineer/releases) are not proof of a running managed Gateway deployment, a native CAD/DCC installation, or professional engineering approval.

## Install and connect

1. Install from the selected versioned checkout into a fresh environment: `python -m pip install .`; run `cdt-engineer` with the supported authentication/transport configuration in the [Provider Standard](../MCP_PROVIDER_STANDARD.md).
2. Call `help`, `system_status`, `system_capabilities`, verify provider and contract identity and decide which executor is actually available. CDT_Engineer does not launch or remotely control CAD/DCC applications on its own.
3. Follow Design Basis → discipline role/skill → source evidence → runtime executor capability → independent checker before professional handoff. Missing native/standards dependencies must BLOCK or explicitly reduce scope.

## Upgrade and rollback

Keep immutable package/release provenance and pin the execution provider contracts separately. Preserve existing credential stores and Owner Console registration on a source-only release. For a managed Gateway activation, compare auth, 19-tool catalogue, workflow/skill discovery and runtime status against the prior release; roll back the owner-managed provider entry if any gate fails. Never silently rewrite `engine-map.yaml` historical `source_snapshot` records to assert a newer native certification.

[Group stable version policy](CDT_GROUP_VERSIONING_POLICY.md) · [Software guides](README.md) · [Lifecycle contract](EXECUTION_LIFECYCLE_CONTRACT.md) · [Release-scope policy](RELEASE_SCOPE_POLICY.md).
