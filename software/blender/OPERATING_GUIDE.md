# Blender — Motion-Graphics Operating Guide

> Documentation class: PUBLIC_SOFTWARE_GUIDE
> Version: 0.1.0 · Target provider contract: `cdt-blender-contract-v10` · Measured Blender: 4.5.3 LTS / Windows 11.

## Step-0 and compatibility

Discover the target host, Blender executable/build, active Blender document and unsaved state, installed CDT-Blender provider contract and addon generation. Query `help`, `system_status`, `system_capabilities`, and current MCP tool names. Do not infer the seven new tools are installed just because they exist in the source repository. Missing versions/readiness cause typed `configuration_required`, `version_mismatch` or `capability_missing` outcomes.

Only Windows Blender 4.5.3 factory-startup headless has motion-graphics source/native acceptance so far. Interactive UI and Blender 5.x require separate native evidence; production video/audio and editable complex-script glyphs are not claimed.

Normative: [L2 motion-graphics contract](../../docs/BLENDER_MOTION_GRAPHICS_EXTENSION_CONTRACT.md). Semantic map: [engine-map.yaml](engine-map.yaml). This guide does not implement a Blender backend.

## Public semantic map

| Feature chunk | MCP tool | Verification |
| --- | --- | --- |
| Standalone bounded SVG | `import_svg_curves` | allow-root/whitelisted styles, count/names/bounds of imported curves |
| Draw line strokes / reveal | `create_grease_strokes` | GREASEPENCIL type, frame inventory and stroke geometry |
| Morph a closed filled polygon | `create_filled_grease_tween` | equal point topology, fill, first/mid/end drawings |
| Curated dots/particle paths | `create_particle_preset` | LINE/RING node group, instance counts and animation |
| Curated noise-wave grid | `create_animated_particle_grid` | grid node group, particle budget, distinct rendered frames |
| Latin/Vietnamese editable typography | `create_unicode_text` | NFC, glyph coverage/font, line layout and source text readback |
| Arabic/Indic/RTL titles | RAQM-shaped PNG, then `create_shaped_text_plane` | Arabic/Hindi shaping proof, PNG/plane identity and visual legibility; **raster, not editable glyphs** |

## Feature-based Chunk Streaming

`Step-0 → asset/font allow-roots and licensing check → empty sandbox/checkpoint → SVG → GP → GN → typography → read-after-write per chunk → sample render → native save/reopen → QA and SHA-256 handoff`.

Each bounded chunk retains a stable `op_id`; failed/uncertain mutations block dependent chunks pending `reconcile_operation` and object/readback verification. No whole-scene atomic rollback is claimed.

Example SVG tool arguments:

```json
{"filepath":"assets/arrow.svg","prefix":"SHOT_SVG","target_width":2.4,"location":[-2,0,0],"op_id":"shot01-svg"}
```

Example GP filled tween:

```json
{"name":"MORPH","start_strokes":[[[0,0],[1,0],[0.5,1]]],"end_strokes":[[[0,0],[1,0],[1,1]]],"steps":12,"start_frame":1,"end_frame":45,"op_id":"shot01-gp"}
```

Arabic/Indic: prepare a transparent glyph image using an independently qualified HarfBuzz/FriBidi/RAQM producer with explicit language, direction, legal local font and bounded output. Do not feed Arabic/Hindi directly into native TextCurve claiming it is shaped. `create_shaped_text_plane` accepts only a contained PNG; the image is packed into .blend. No font binaries are distributed.

## QA and blockers

A tool success is not a completed infographic. Verify first/mid/last frame differences and content, fill/cyclic strokes, current GN wave state, source typography and target language shape. Include the native Blender build, source revision, extension contract, exact scene/output hashes and screenshot/visual review. Old addon, unknown mode, escaped paths, unsupported SVG elements, mismatched GP point topology, GN over-budget, missing RAQM/font and unsupported Blender major releases must block stronger release claims.

Source-qualified headless tests are **not** current gateway-to-installed-addon E2E. Existing modeling/sculpt and CDT_Engineer professional interpretation retain their separate acceptance gates.
