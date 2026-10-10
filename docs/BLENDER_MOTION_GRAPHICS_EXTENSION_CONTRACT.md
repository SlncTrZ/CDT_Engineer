# Blender L2 Motion-Graphics Extension Contract

> Documentation class: PUBLIC_CONTRACT
> Version: 0.1.0 · Updated: 2026-10-10 · Status: source-qualified provider extension; deployed-runtime acceptance separate

## Authority and scope

This provider-specific **L2 contract** specializes the [common contract model](CONTRACTS.md) for bounded Blender 4.5.3 motion-infographic production. CDT_Engineer owns this semantic contract and software guidance; CDT-Blender owns every MCP tool schema, native Blender bridge/addon handler, format parser and lifecycle receipt. This contract does **not** authorize arbitrary Python, Geometry Node graph injection, font-file redistribution, user-scene overwrites or domain-specific engineering acceptance.

The measured native baseline is **Windows 11 + Blender 4.5.3 LTS**, in a separate factory-startup background process. A successful source-level fixture is **not proof that a user's currently installed provider/addon exposes these tools**. All executable workflows require fresh Step-0 installation/version/provider/addon generation and capability discovery before mutation. Other Blender versions/OS combinations are unverified.

Provider target: `blender`, additive contract `cdt-blender-contract-v10`. Earlier common CAD semantics remain unchanged.

## Public tool and semantic map

| Semantic capability | Public MCP tool | Bounded source-qualified behavior | Critical readback |
| --- | --- | --- | --- |
| `infographic.vector.svg_import` | `import_svg_curves` | offline SVG, ≤256 KiB, basic paths/rect/circle etc with whitelisted presentation style; up to 128 shapes, 12 levels, 256 elements; optional target width/placement | exact created CURVE names/count/bounds |
| `infographic.grease.stroke_reveal` | `create_grease_strokes` | GPv3 1–32 strokes, up to 4,096 points, held drawings across up to 30 frame steps | GREASEPENCIL object, strokes/drawings and frame numbers |
| `infographic.grease.filled_tween` | `create_filled_grease_tween` | GPv3 filled, closed, same-point-topology polygons, 2–32 steps, `LINEAR` or `SMOOTHSTEP` | filled material, identical topology, exact first/middle/last drawing |
| `infographic.gn.particle_motif` | `create_particle_preset` | curated LINE/RING instance graph, up to 256 instances | node group name, count, object/modifier readback, keyed rotation where applicable |
| `infographic.gn.animated_grid` | `create_animated_particle_grid` | curated Noise-driven animated instanced grid, up to 512 particles | node group/count + distinct frame render |
| `infographic.text.unicode_nfc` | `create_unicode_text` | native Blender TextCurve, NFC, Vietnamese/Latin multiline, bounded allowed-root TTF/OTF font | source text readback, font name/line count, visual proof |
| `infographic.text.complex_raster` | `create_shaped_text_plane` | RGBA PNG previously shaped by qualified RAQM/HarfBuzz/FriBidi asset producer, loaded from allow-root, packed into .blend | image-backed plane and PNG identity, no editable glyph claim |

All seven mutation tools require the ordinary bridge-generated **`op_id`** lifecycle, operation fingerprinting, bounded execution and uncertain-state reconciliation. A retry after timeout must **not** duplicate native objects; use `reconcile_operation` and independent readback first. Validation/refusal before mutation is the default. Real Blender mutation is **not an atomic transaction**; a native error after partial object creation requires verified compensation, checkpoint restore or explicit uncertainty, never fabricated rollback.

## Input boundaries and font path policy

- Source SVG is standalone and offline. Reject external references, XML entities/DOCTYPE, scripts, CSS stylesheets, unsupported filters, remote or embedded assets and over-budget shapes. Inline `style` supports only an explicit simple presentation whitelist; it is not a browser CSS interpreter.
- Every file-bearing tool resolves paths through **the workstation's configured allow-roots**; these roots are injected by the trusted bridge, never accepted as user-supplied authority. Re-check symlinks/junctions at the Blender addon boundary.
- Grease Pencil input arrays and Geometry Nodes count/amplitude/radius are finite and bounded. No arbitrary `bpy`, arbitrary node sockets, script expressions or unbounded generator access.
- Unicode Latin/Vietnamese stays native editable text only where font glyphs and layout are verified. RTL Arabic, Persian, Urdu and Indic (Hindi/Marathi/Nepali) require a **qualified external shaping engine**. Never reverse codepoints and pretend to shape them. The source-qualified path creates transparent PNGs with Pillow RAQM/HarfBuzz/FriBidi, local fonts and explicit language/direction; only the resulting PNG is imported into Blender. This is **raster text**. Glyph curves, live text editing, automatic font-fallback and mixed-direction complex layout are **not** claimed.
- Do not redistribute font binaries. The offline shaped image may be packed into the .blend, but its source font stays at the owner's licensed installation.

## Capability-state and execution gates

Semantic claims are graded independently:

1. `specified`: this contract and schema exist.
2. `native_source_qualified`: Blender 4.5.3 factory-startup fixture returned explicit structured receipt, native saved .blend and distinct frame renders; both positive and negative tests pass.
3. `provider_dispatch_qualified`: same-version addon command dispatcher handles all seven L2 tools with verified arguments, refusals and readback.
4. `deployed_runtime_ready`: fresh `help` / `system_status` / `system_capabilities`, actual installed matching provider and addon, authenticated gateway, and connected native E2E prove the target user scene.
5. `production_accepted`: render/artifact reopen and independent composition/typography QA satisfy declared release scope.

Do **not** infer a stronger state from a weaker state. A missing font/RAQM/image asset, wrong Blender version/context, non-contained path, unsupported SVG feature, mismatched GP topology, over-budget GN instance set, or missing deployed addon must return a non-success/refusal instead of an invented lower-fidelity fallback.

## Feature-chunk execution order

For a short motion infographic:

`preflight and checkpoint → protected vector import → GP feature/reveal → GN motif/wave → typography asset preparation and font-license check → Unicode/raster text placement → native readback and representative frames → checkpoint/save → full render → file-hash and visual QA`.

Create one bounded semantic chunk per feature/preset; a successful tool call alone is not a finished infographic acceptance. Old base tools remain backward compatible. The provider-specific source fixture and contract implementation are maintained in CDT-Blender, never imported into CDT_Engineer.

## Explicitly unclaimed

Blender 5.x/other OS compatibility; interactive UI context for all seven tools; arbitrary SVG gradients/filters/text; native GP stroke-morph with topology change; arbitrary Geometry Nodes authoring/physics; full UAX #29 segmentation/Unicode bidi text editing inside Blender; production GPU render/sound/VSE; professionally accepted 10-second/45-second promotional deliverables; automatically ready installed addon before user deployment.
