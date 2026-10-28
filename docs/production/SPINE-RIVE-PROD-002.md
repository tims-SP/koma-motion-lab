# SPINE-RIVE-PROD-002 — Reverse:1999 Spine → Rive production feasibility

Date: 2026-10-28

**Successful GitHub Actions run:** https://github.com/tims-SP/koma-motion-lab/actions/runs/40716505156

**Download two neutral diagnostic MP4s + reports:** https://github.com/tims-SP/koma-motion-lab/actions/runs/40716505156/artifacts/12827929701

Source is the publicly reachable (but not expressly licensed for redistribution) game asset repository `myssal/Reverse-1999-CN-Asset` at commit `45e75248ba3b25053fd32e63ab13c2f9f54dd9df`.

## Actual input

- Character: `300401_hongnujian` (红弩箭), `roles/300401_hongnujian/300401_hongnujian_room.skel`.
- Spine binary version: **4.2.36**.
- Converter: **BastienGimbert/SkelToJson** (MIT, 4.2/4.3), installed from its upstream GitHub repository; first attempted 3.8-only reader was incompatible and was replaced.
- Rive: official Linux CLI, generated RML and compiled/rendered headlessly in Actions.

## Source decoded successfully

| Field | Count |
| --- | ---: |
| Bones | 85 |
| Slots | 64 |
| Attachments | 112 |
| Mesh attachments | 101 |
| Potential weighted attachments | 49 |
| IK constraints | 2 |
| Transform constraints | 2 |
| Path constraints | 1 |
| Animations | 8 (`idle`, `walk`, `sleep`, `hit`, `click`, etc.) |

Potential weighted-attachment count is based on structural heuristics, not independent verification of each influence.

## Rive render A — real bone motion, source texture

1. Read real `idle_room` animation from converted JSON.
2. Select a source bone rotation track (`hnj_z_youbinjiao3`, 41 source keys, 102.7° source range).
3. Sample a 2-second window to 24 frames, animate a native Rive `RootBone > Bone`.
4. Attach one crop from the genuine Spine texture atlas in a new Rive `ImageAsset`.
5. Render 24 PNG frames using the official Rive CLI, encode local MP4 with FFmpeg.
6. Validate frames are not identical. This is a **single channel transfer**, not a source-rig import.

**Copyright protection:** The source-art-bearing MP4, PNG frames, converted JSON, original `.skel`, and original PNG are intentionally restricted to the ephemeral runner and **not** uploaded into the public test repository or its artifact downloads.

## Rive render B — 85-bone native structure + multiple source rotations

1. Convert all 85 source bones to named native Rive `RootBone`/`Bone` elements, retaining tree order.
2. Adapt Spine arbitrary child local translations using intermediate Rive offset bones, because Rive `Bone` cannot author `x/y` and must be a direct descendant of a Bone.
3. Sample **81 source bone rotation tracks** from `idle_room` over 2.4 seconds and apply them into RML for each output frame.
4. The diagnostic rig includes a visible source-driven reference bone to ensure output changes are measurable even if the converted skeleton's visual lines are off-canvas.
5. Verify, render 24 different PNG frames and FFmpeg MP4.

**Final Actions:** PASS. **24/24** frame hashes distinct. The neutral MP4 is downloadable; it contains no original artwork.

Caveat: **Full skeleton deformation fidelity is NOT verified.** Distinct frames can be driven by the visible reference bone; they do not prove the complete 85-bone rig visually matches the original.

## Verdict — production readiness

- **PASS:** Access to real assets, Spine 4.2.36 binary decoding, bone/mesh/animation data recovery, authored Rive bones, clip sampling, Rive headless video rendering.
- **PARTIAL:** Named bone hierarchy transferred, 81 rotation tracks sampled and written at frame times, limited original texture attachment.
- **NOT IMPLEMENTED:** Exact Spine mesh-to-Rive UV/triangles/weights transfer; draw-order/skin swaps; IK/transform/path constraint parity; bezier interpolation parity; complete authored Rive timeline instead of per-frame RML rebuild; character-quality motion parity.
- **NOT READY:** A full, production-quality faithful animated character migration. Existing stage is a technically working conversion-and-render vertical slice.

## Files

- [Spine binary parser + source audit](../../scripts/spine_binary_conversion.py)
- [Single source bone Rive adaptation and two videos](../../scripts/spine_rive_renderer.py)
- [Full native bone hierarchy prototype](../../scripts/spine_full_skeleton_rive.py)
- [Actions workflow](../../.github/workflows/spine-to-rive-video.yml)

Next engineering gate: map actual source mesh data (triangles, UVs, per-vertex weights, skins, slots) through Rive RML and compare selected animated frames against a compatible source Spine runtime. No need to re-prove Rive basic bones/CLI.
