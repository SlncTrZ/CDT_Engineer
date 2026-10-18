# Software Operating Guide Contract

> Documentation class: PUBLIC_CONTRACT

Version: 1.0.0 · Updated: 2026-10-17 · Status: dual-quality contract integration (local source).

## Purpose

Every engineering application used through CDT_Engineer must have a software-specific operating guide. The guide teaches an Agent how a competent engineer should use that application's public MCP capabilities for professional work without moving native backend code into CDT_Engineer.

The guide specializes generic Engineering OS rules — Step-0 Execution Environment Discovery, Design Basis, Engineering Skills, Feature-based Chunk Streaming, QA and recovery — into application-specific execution behavior.

## Required guide contents

Each software guide defines:

- software identity and supported application/version range;
- Step-0 discovery methods for installation/executable path, version/build/edition and required plugin/add-in state;
- compatibility rules mapping observed environment state to `compatible`, `guidance_only`, `installation_required`, `configuration_required`, `version_mismatch` or `unknown`;
- pinned public MCP/provider contract and runtime capability-discovery method;
- professional modeling/drafting conventions for that application;
- semantic capability map from CDT_Engineer requirements to public tools;
- preferred feature-chunk types and dependency patterns;
- concrete chunk payload examples for the public MCP surface;
- truthful transaction mode: `native_atomic`, `checkpointed_atomic`, `compensating` or `nonrecoverable`;
- begin/execute/query/commit/rollback or equivalent lifecycle when supported;
- safe chunk budgets: entity/operation/payload/time/complexity bounds;
- read-after-write verification methods;
- timeout/uncertain-state reconciliation and duplicate-mutation prevention;
- UI redraw/yield/cursor/viewport behavior for interactive presentation;
- native save/open/export/reopen/seal requirements;
- known limitations and typed blockers;
- positive/negative benchmark cases.

## Target repository shape

```text
software/
  autocad/
    OPERATING_GUIDE.md
    engine-map.yaml
    examples/
  sketchup/
    OPERATING_GUIDE.md
    engine-map.yaml
    examples/
  blender/
    OPERATING_GUIDE.md
    engine-map.yaml
    examples/
  solidworks/
    OPERATING_GUIDE.md
    engine-map.yaml
    examples/
```

Create these directories only when actual guide/map content is implemented.

## Separation of responsibility

CDT_Engineer owns **why and how the Agent should work professionally**. The engine repository owns **how the native application actually executes a tool**.

The software guide may name and demonstrate public MCP tools, but it must not embed:

- AutoCAD COM implementation;
- SketchUp Ruby bridge implementation;
- Blender `bpy` server/backend implementation;
- SolidWorks COM/.NET backend implementation;
- hidden/private script bypasses.

If a required capability does not exist publicly, the guide records a blocker/backlog instead of documenting an unsupported bypass as production procedure.

## Feature-based Chunk Streaming specialization

Each software guide answers five questions for every mutation-heavy workflow:

1. **What is a good semantic chunk in this application?**
2. **How is the chunk represented in the public MCP payload?**
3. **How is pre-chunk state protected and failure recovered?**
4. **How is the committed result queried/measured?**
5. **How can the application visibly yield/redraw after commit without changing engineering semantics?**

The guide must explicitly reject both monolithic whole-project mutation and primitive-per-Agent-turn streaming except where a primitive is itself the correct semantic feature.

## Example execution envelope

The Engineering OS may plan conceptually:

```json
{
  "batch_session_id": "house_01",
  "chunk_id": "chunk_ground_floor_walls",
  "semantic_type": "wall_system",
  "scope": "ground_floor",
  "depends_on": ["chunk_ground_floor_grid"],
  "ui_yield": true
}
```

The AutoCAD, SketchUp, Blender or SolidWorks guide then maps that envelope to the specific public tool sequence and payload supported by that engine. The semantic `chunk_id` and evidence chain must survive the mapping even if native tool names differ.

## Visual interaction policy

Interactive guides should prefer visible application progress at safe commit boundaries when the application/provider supports it. Desired effects may include viewport redraw, object appearance, feature-tree growth or cursor/selection feedback.

The guide must distinguish presentation capability from correctness capability:

- redraw success is not transaction success;
- cursor motion is not engineering evidence;
- UI pacing must not extend a transaction unnecessarily;
- headless mode may omit visual effects while producing the same committed engineering state.

## Guide acceptance

A software operating guide consumes the [Execution Environment Contract](EXECUTION_ENVIRONMENT_CONTRACT.md) and is not production-qualified until benchmark evidence demonstrates:

- advertised public tools match actual runtime discovery;
- declared transaction/recovery mode is truthful;
- chunk budget limits are measured or conservatively bounded;
- forced partial/failure/timeout cases reconcile without duplicate/corrupt mutation;
- read-after-write verification catches incorrect state;
- presentation mode and headless/non-presentation mode produce equivalent engineering outputs for the benchmark;
- required native artifact lifecycle/reopen behavior is proven where claimed.

## Mandatory software-specific dual quality workflow

Each Operating Guide MUST describe a workflow-specific `technical_gate` and `visual_gate` for graphical deliverables under the [Dual Technical & Visual Quality Gate Policy](DUAL_QUALITY_GATE_POLICY.md). The technical gate includes application-native units/topology/editability/feature identity/save-reopen plus discipline-specific accuracy. The visual gate covers native application screenshots or equivalent render at useful overall and detail scales, intended proportions, clear drafting, material and finish quality, and readable presentation. Guides must say explicitly when a category is not relevant (e.g. illumination for an electrical schematic), rather than blindly impose architecture rendering standards.

The Agent performs `base geometry → purposeful detailing → native multi-view inspection → technical measurement → independent visual review → rework → saved/reopened QA`. Do not set a fixed number of line segments/features as a proxy for detailed professional work. Do not treat headless smoke, syntax-only validation, a pretty preview or a provider's tool PASS as either complete gate. If a required native view/quality path is unsupported, state the limitation and block the stronger claim or request documented scope reduction. Engine public contracts, safe chunk recovery and explicit provenance remain authoritative.
