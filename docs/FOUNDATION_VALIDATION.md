# Foundation Validation

> Documentation class: PUBLIC_CONTRIBUTOR

Version: 0.2.0 · Updated: 2026-09-12

`python3 scripts/validate_foundation.py` is the reproducible **offline foundation gate** for CDT_Engineer. It runs the full unit/acceptance suite, validates public JSON Schemas, validates every public Agent Profile and Engineering Asset Catalog instance, requires every public Markdown file to declare one `PUBLIC_*` documentation class, checks relative Markdown links across README/AGENTS/provider-standard/docs/domains/software/catalogs, rejects public Markdown dependencies that escape the repository or enter `_private/`, runs `git diff --check`, and verifies that `_private/**` is not tracked.

A PASS from this command means the public/offline Engineering OS foundation and currently declared packages are internally coherent: canonical architecture/documentation boundary, contracts, schemas/profiles/catalog metadata, deterministic guards, fail-closed release/dependency policy, Stage Runner software isolation/anti-bypass behavior, software-guide baselines, QA aggregation and stale-evidence logic. The public test suite is self-contained and must not read customer/raw fixtures from `_private/`. It does **not** mean native AutoCAD/SketchUp/SolidWorks acceptance has passed, a customer artifact is engineering-correct, or `ready_for_professional_review` has been achieved.

Runtime acceptance remains separate and must follow Step-0 discovery, actual public capability evidence, Feature-based Chunk execution, read-after-write checks, recovery/failure injection, final artifact identity/seal/reopen, and independent domain QA.
