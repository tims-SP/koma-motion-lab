# KOMA-25D-CORE-001 (experimental)

Status: **implementation submitted; quality NOT ACCEPTED until inspected**.

Goal: prove an original polygon/UV/weighted-skin 2D character can be loaded
without redrawing, given a lightweight depth field, and rendered in real
Three.js under a changing 3D camera.

## Real source

Godot's Skeleton2D GBot demo, by Andreas Esau (art) and RustyStriker (initial
rig/animation), MIT licensed:
https://github.com/godotengine/godot-demo-projects/tree/master/2d/skeleton

Source revision pinned: b761b4cd5718a7118f2c95eb55f181d0a5f004f1.
Source scene: 2d/skeleton/player/player.tscn
Texture: 2d/skeleton/player/gBot.png
Source files are downloaded at test runtime, never committed as binaries.

## What is implemented

- Parse Godot 4 Polygon2D vertices, local offsets, UVs, subpolygon indices,
  per-vertex bone weights, and Bone2D hierarchy.
- Ear-clip polygon regions, preserve original UV coordinates and source image.
- Add shallow depth over each source polygon (original projected X/Y preserved).
- Export a JSON intermediate; instantiate Three.js SkinnedMesh / Skeleton.
- Render 48 deterministic 0–90 degree camera-yaw frames using Chromium and ffmpeg.
- Structural QA rejects blank frames or a static render; outputs frame sheet and JSON.

## What is NOT implemented

- Godot animation timeline semantics, exact rest-pose/skinning parity,
  true depth for hidden regions, closed topologically correct surfaces,
  180+ degree back/side artwork, anime art acceptance, or complete production rig.
- Depth is a first-pass per-polygon field only; seams, surface overlaps,
  insufficient foreshortening, and edge visibility are expected defects.
- A passing structural QA result is NOT evidence of visual production quality.

## Reproduction

1. cd experiments/koma-25d-core
2. python3 tools/godot_to_koma.py --out viewer/public/asset --depth 0.16
3. cd viewer && npm install --no-audit --no-fund && npx playwright install chromium
4. npm run dev
5. In separate terminal run: node tools/capture.mjs && python3 tools/qa.py
6. Encode: ffmpeg -framerate 24 -i out/frames/%04d.png -c:v libx264 -pix_fmt yuv420p out/preview.mp4

All images, PNGs, JSON exports of third-party assets, and videos remain out of
Git. The CI job only publishes MIT-licensed sample previews to a DRAFT Release
after structural QA. Art acceptance remains a separate human/visual-model gate.

## Future quality gates

- CORE-001a: source projection parity under orthographic camera, verified
  against original Godot reference render with pixel-based metrics.
- CORE-001b: per-body-part curved + connected geometry with no holes.
- CORE-002: preserve source skinning/animations and original runtime parity.
- CORE-003: side/back art, view-dependent facial details, coherent shading.
- CORE-004: anime look and real-scene camera/character quality evaluation.
