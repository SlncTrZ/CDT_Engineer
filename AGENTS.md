# AGENTS.md — CDT_Engineer Control Plane

## Role

`CDT_Engineer` is the architecture/specification/control repository for the CDT provider family. It does not own provider runtime business logic.

## Owned scope

Allowed here:

- `MCP_PROVIDER_STANDARD.md`;
- architecture/common-contract specifications;
- ADRs, master/sub-plans, repository maps and conformance definitions;
- cross-provider capability semantics and versioned spec baselines;
- coordination documents for provider agents.

Provider runtime repositories:

- `SlncTrZ/CDT-AutoCAD`
- `SlncTrZ/CDT-SketchUp`
- `SlncTrZ/CDT-Blender`
- `SlncTrZ/CDT-SolidWorks`

## Forbidden in this repo

- AutoCAD/SketchUp/Blender/SolidWorks runtime source or provider-specific backend business logic;
- runtime imports from provider repositories;
- provider-specific dependency environments;
- creating `CDT-Provider-Kit` before Rule-of-Two evidence;
- changing a provider repo while acting as a normal control-plane agent unless the task explicitly assigns that repo.

## Contract change protocol

1. Identify whether the change is provider extension or genuinely common semantics.
2. Common promotion requires stable semantics plus at least two-provider evidence unless foundational.
3. Update source-of-truth specs/ADRs here first.
4. Version breaking semantic changes explicitly; prefer additive evolution.
5. Provider repos sync an explicit pinned CDT_Engineer commit and run conformance review; they never silently track hub `main`.

## Parallel-agent ownership

- Agent A: `CDT-AutoCAD/**`
- Agent S: `CDT-SketchUp/**`
- Agent B: `CDT-Blender/**`
- Agent W: `CDT-SolidWorks/**`
- Architect/Core: `CDT_Engineer/**`

Provider agents treat this repo as read-only unless the Architect explicitly assigns a contract/spec change.

## Required workflow

1. Follow the global SlncTrZ Agent Harness returned by `context.bootstrap`.
2. Read ground truth before edits; preserve architecture invariants.
3. Do not turn provider-specific concepts into a lowest-common-denominator API.
4. Validate spec consistency and `git diff --check` before commit.
5. Every code/deploy change must be logged through CyberBrain `kb.knowledge_store`.
6. End each work session with episodic save (`memory_store`/`conversation_save`) followed by `dream_enqueue`.
7. Default branch is `main`; no secrets or runtime credentials in source.

## Repository map

Canonical operational map: `docs/PROVIDER_REPO_MAP.md`.
