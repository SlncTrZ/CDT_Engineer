# Foundation Validation

> Documentation class: PUBLIC_CONTRIBUTOR

Version: 0.3.0 · Updated: 2026-10-06 16:03 (Asia/Ho_Chi_Minh)

Install the offline validation dependencies in a clean Python environment with `python3 -m pip install -r requirements.txt -c requirements.constraints.txt`, then run `python3 scripts/validate_foundation.py`. The gate runs the full unit/acceptance suite, validates public JSON Schemas, validates every public Agent Profile and Engineering Asset Catalog instance, requires every public Markdown file to declare one `PUBLIC_*` documentation class, checks relative Markdown links across README/AGENTS/provider-standard/docs/domains/software/catalogs, rejects public Markdown dependencies that escape the repository or enter `_private/`, runs `git diff --check`, and verifies that `_private/**` is not tracked.

A PASS means the currently declared public/offline packages satisfy the invariants exercised by the present schemas, contracts and automated tests. It is **not an exhaustive correctness proof**. Newly discovered counterexamples must become regression tests and can invalidate an earlier broad interpretation of PASS without making the historical run dishonest. The public test suite is self-contained and must not read customer/raw fixtures from `_private/`. A PASS does **not** mean native AutoCAD/SketchUp/SolidWorks acceptance has passed, a customer artifact is engineering-correct, or `ready_for_professional_review` has been achieved.

Runtime acceptance remains separate and must follow Step-0 discovery, actual public capability evidence, Feature-based Chunk execution, read-after-write checks, recovery/failure injection, final artifact identity/seal/reopen, and independent domain QA.

## Clean deployment and assessment boundaries

The version constraints snapshot records the dependencies verified on Linux Python
3.12. It is not a hash-locked multi-platform certificate; platform-only dependencies
may resolve separately. The offline CI matrix covers Python 3.11/3.12 on Linux and
Windows when run. A workflow file alone is not evidence of a successful remote run.

`scripts/smoke_installed_wheel.py` rebuilds the working tree, installs the wheel in
a fresh virtual environment outside the source tree, verifies all advertised tools
and packaged schema/guide resources, then reruns foundation validation. It uses
the constraints and canonical public tool count rather than a historical constant.

Repository architecture, implemented capability, packaging and offline validation
are assessed separately from integrated application acceptance. Missing native CAD
runs cannot reduce repository quality or block its quality target. Conversely, an
offline test, packaged provider or repository score cannot imply native acceptance.
Native verification has its own 0–100 assessment with exact engine/application/run
identities; an unperformed run is unscored, not zero.
