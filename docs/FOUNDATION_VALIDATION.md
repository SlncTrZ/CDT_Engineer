# Foundation Validation

Version: 0.1.0 · Updated: 2026-09-12

`python3 scripts/validate_foundation.py` is the reproducible **offline foundation gate** for CDT_Engineer. It runs the full unit/acceptance suite, validates public JSON Schemas, checks relative Markdown links, runs `git diff --check`, and verifies that `_private/**` is not tracked.

A PASS from this command means the public/offline contracts, deterministic guards, Stage Runner including software-bound candidate isolation and anti-bypass regressions, software-guide baselines, sanitized regressions, QA aggregation and stale-evidence logic are internally coherent. The public test suite is self-contained and must not read customer/raw fixtures from `_private/`. It does **not** mean native AutoCAD/SketchUp/SolidWorks acceptance, engineering correctness of a customer artifact, manufacturing certification, or `ready_for_professional_review` has been achieved.

Runtime acceptance remains separate and must follow Step-0 discovery, actual public capability evidence, Feature-based Chunk execution, read-after-write checks, recovery/failure injection, final artifact identity/seal/reopen, and independent domain QA.
