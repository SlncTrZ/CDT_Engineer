# Changelog — CDT_Engineer

## [0.2.0] — 2026-10-18

- Feat: Dual Technical & Visual Quality Gate Policy (`docs/DUAL_QUALITY_GATE_POLICY.md`) and deterministic evaluation helper (`execution/dual_quality_gate.py`). Both gates must independently pass on the identical final artifact SHA-256 before release.
- Feat: Observable Incremental Construction verification (`execution/incremental_construction.py`) to prevent one-shot generation and fake reveals in interactive CAD/DCC workflows.
- Integration: Integrated dual quality gate and incremental construction assessments into `execution/stage_runner.py` (via `run_profile`), `execution/release_bundle.py` (via `assess_release_bundle`), and `cdt_engineer/server.py` (via `profile_assess`).
- Refactor: Generic abstraction for artifact revisions (`native_artifact_sha256`) in incremental construction, preserving fallback compatibility for `native_skp_sha256`.
- Contract hygiene: Streamlined public software operating guide boundaries (`software/sketchup/OPERATING_GUIDE.md`) to keep demo/research script execution strictly separated from public MCP provider standards.

## [0.1.1] — 2026-10-10

- Documentation maintenance: current stable package 0.1.1 (tag `v.0.1.1`), user-facing installation/release guide and credential-safe rollback instructions.
- API contract remains `cdt-engineer-v1-alpha7`. No native feature or tool registration was changed by this release.
- Source release publication is separate from installed provider state and workstation-native verification.

## [0.1.0] — 2026-10-10

- Initial stable CDT product version under the `v.0.x.x` tag policy. Older benchmark, upstream and R&D evidence retains its original source identity.
