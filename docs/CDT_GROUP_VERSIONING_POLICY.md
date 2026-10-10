# CDT Group Release Version Policy

> Documentation class: PUBLIC_POLICY
> Policy version: 0.1.0 · Updated: 2026-10-10 · Lifecycle: stable-use-and-maintenance

## Release identity

All CDT product repositories publish **stable** release versions using exactly:

- **Package metadata:** `0.MINOR.PATCH` (three numeric fields; e.g. `0.2.0`).
- **Git/GitHub release tag:** `v.0.MINOR.PATCH` (e.g. `v.0.2.0`), including the literal dot after `v` as requested by the owner.
- **No version suffixes/prefixes:** no `rc`, `a`, `alpha`, `beta`, `dev`, `cdt`, `+local`, date, build-SHA or R&D marker attached to the package/release version. Git SHA and artifact hashes belong in **separate provenance fields**.
- Each repository advances **independently**; there is no forced shared numeric version or implied cross-product compatibility.
- Preserve historical upstream version, R&D/audit/freeze tags and prior package references for provenance, but never use those labels for a *new* product release.

The leading `0` is deliberate. These are owner-approved stable product releases, not prereleases. Do not infer prerelease status from the leading zero.

## Production lifecycle

CDT is in **use, maintenance, and targeted feature delivery**, not blanket R&D:

- `0.x.y → 0.x.(y+1)` for a compatible defect fix, maintenance update, documentation or release process repair.
- `0.x.y → 0.(x+1).0` when a new feature/capability is accepted or a compatibility-impacting change must be explicitly negotiated.
- A detected missing runtime capability or bug during normal usage should lead to targeted implementation/fix, focused+full tests, release gate acceptance and one new stable numeric version; Blender motion-graphics v10 is an example.
- Changing package version **never** automatically changes the independent MCP tool-contract ID, native application version or user-auth binding generation. Contract/schema changes require separately reviewed compatibility evidence.
- Do not rename upstream versions in attribution. For KiCAD, upstream `2.7.0` remains a historical third-party baseline while CDT packaging uses `0.x.x`.

## Release/promotion gates

1. Update version in **all declared package/runtime metadata** and lockfile roots. Enforce a repository regression test for version consistency.
2. Exact-source CI of the target `main` SHA must succeed before a release. Native host/OS-qualified scope is separate from offline CI.
3. Create an annotated tag **only** after exact-source CI PASS; workflow accepts `v.0.*.*` and independently rejects any tag not exactly equal to `v.` + the current package version. GitHub release must not be marked prerelease; release notes bind exact SHA, version, supported native build and evidence/limitations.
4. Artifact shipping differs by repository (wheel/addon, Node bundle, native binaries). No source release alone proves installation/deployment. Pin artifact SHA-256 or stronger and keep rollback receipts.
5. Deploy to immutable versioned locations; validate a canary before switching owner-managed Gateway registration. **Do not rotate credentials or rewrite credential stores** as part of a version bump. Compare OAuth/user auth, provider discovery, tool count and native app connectivity before and after promotion.
6. On a failed health/auth gate, recover using the previous pinned managed version. Never claim a production deploy completed just because GitHub release passed.

This policy does not grant deployment authority. Repository-specific owner approval and production UI/OAuth access requirements continue to apply.

## Historical transition

Existing `audit-*`, `freeze/*`, `v0.x.x`, and suffixed package tags remain immutable evidence. New canonical releases use **only** `v.0.x.x`. There is no force-moving/deleting old tags or pretending historical release notes were published under a new tag. If a published `0.x.y` package version has changed since that release, bump the patch rather than reuse an existing source version.
