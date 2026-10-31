# REVERSE1999-PROD-002 — Original Spine skeleton → Rive, real-texture video acceptance

Date: 2026-10-29 (JST). All tests run via GitHub Actions on `ubuntu-24.04`; no Rive Editor opened.

## Source and reproducibility

- Upstream: https://github.com/myssal/Reverse-1999-CN-Asset
- Pinned commit: `45e75248ba3b25053fd32e63ab13c2f9f54dd9df`
- Character: `300401_hongnujian` (红弩箭), `roles/300401_hongnujian/300401_hongnujian_room.skel`
- Source Spine version: `4.2.36`
- Parser: `BastienGimbert/SkelToJson` (MIT)
- Build/render: official Rive CLI `1.8.0` + FFmpeg
- Source files and game-derived video never committed or uploaded in this public repository.

## Actual runs

| Action | Result | Meaning |
|---|---|---|
| [PROD-002 #10](https://github.com/tims-SP/koma-motion-lab/actions/runs/40716505156) | PASS_PARTIAL | Source Spine binary decoded; an 85-bone Rive graph and original rotation tracks produce a *neutral-debug* 24-frame MP4 |
| [PROD-002 #14](https://github.com/tims-SP/koma-motion-lab/actions/runs/40743677348) | FAIL | 51 original Mesh/UV/Weight attachments serialize but Rive texture drawing is fully transparent |
| [PROD-002 #18](https://github.com/tims-SP/koma-motion-lab/actions/runs/40744629385) | FAIL | Original weighted image Mesh: 0 pixels; same Mesh with Skin and Weight removed: 61,975 visible pixels; direct atlas: 9,084 visible pixels |
| [PROD-002 #19](https://github.com/tims-SP/koma-motion-lab/actions/runs/40744980198) | FAIL | Rigid-bone attachment attempt also draws 0 pixels |
| [PROD-002 #22](https://github.com/tims-SP/koma-motion-lab/actions/runs/40745586311) | **PASS_TEXTURE_PREVIEW_ONLY** | Original mesh UV texture scene **without active skinning** renders 24 unique 640×360 frames, assembled to a 2-second, 12-fps MP4 with *additional camera-only motion*. Full source animation is **not** preserved |

## Data inventory and translation

| Feature | Source | Converted / used |
|---|---:|---:|
| Bones | 85 | 85 source-named native Rive bones |
| Slots | 64 | Slot mapping analyzed; not complete dynamic draw-order playback |
| Attachments | 112 | 51 original source Mesh attachments translated |
| Meshes | 101 | 51 selected/compatible setup attachments; not 101/101 |
| Weighted meshes | ≥49 candidates (converter heuristic) | 27 original weighted meshes translated into RML; **runtime skinning currently broken** |
| Vertex positions, UVs, triangles, weight records | Multiple source arrays | 843 vertices/weight records translated; only **unskinned UV/triangle rendering** passes |
| IK/transform/path constraints | 2/2/1 | Not translated faithfully |
| Animations | 8 | `idle_room` source keys read; 81 rotation bone tracks transferred to the Rive bone graph diagnostic |
| Full character parity | N/A | **NOT VALIDATED** |

## Textured acceptance video

[PROD-002 #22: run and sanitized evidence](https://github.com/tims-SP/koma-motion-lab/actions/runs/40745586311)

- File generated inside the ephemeral GitHub Actions runner: `real-spine-mesh-rive-acceptance.mp4`.
- Format: 640×360, 12 fps, 24 frames, 2 seconds, H.264 encoded with FFmpeg; private video size: **62,851 bytes**.
- Frame raster: **24 distinct frames**, 61,605–62,395 visible pixels.
- Actual imported textures: original Spine atlas with original Mesh topology and UVs; no stand-in art.
- Motion in this preview is an explicitly added *camera-level movement*. It is **not original Spine mesh deformation or character animation**.
- The actual game-art video lives in the temporary runner and is **not uploaded to public artifacts**, which deliberately preserve metadata, logs, and neutral bone-debug video only. Thus there is no user-accessible game-art MP4 from this public workflow after the runner is destroyed.

## Production decision

- **PASS**: source .skel → structural JSON; native Rive bones; original source texture + Mesh/UV render; headless Rive PNG → FFmpeg MP4. This establishes a technically valid ingestion/render path.
- **BLOCKED**: assigning source weights and skin binding transforms makes the same meshes fully transparent in the Rive runtime. The source .skel original constraints, mesh deformations and timeline interpolation are also not faithfully converted.
- **NOT READY**: full-character Rive production, character pose fidelity, automatic new actions from existing source rig.
- **DIAGNOSTIC NEXT ACTION**: construct a one-mesh, one-bone imported source fixture and numerically compare Spine setup world matrices versus Rive Skin/Tendon bind matrices; validate the first frame with and without Skin. Only widen to 85 bones after parity. Prioritize Rive CLI rigging schema, actual constraint transform conventions, and known-good 2-bone fixture.
- **FALLBACK**: retaining official Spine/Cubism runtime for original animation is currently more reliable than pretending the partial Rive conversion is complete.

## Usage and licensing

This upstream repository is a dump of copyrighted commercial game assets. No clear root `LICENSE` granting redistribution was identified. Personal/noncommercial use does not itself grant redistribution rights. GitHub Actions public artifacts contain only safe numeric reports and a neutral bone-debug video; game source files, cropped images, derived .riv and game-derived footage are not included.

## Maintained files

- [binary decoder](../../scripts/spine_binary_conversion.py)
- [partial source animation transfer](../../scripts/spine_rive_renderer.py)
- [85-bone Rive hierarchy](../../scripts/spine_full_skeleton_rive.py)
- [real texture Mesh + skin debug + video fallback](../../scripts/spine_textured_rive.py)
- [Rive workflow](../../.github/workflows/spine-to-rive-video.yml)
