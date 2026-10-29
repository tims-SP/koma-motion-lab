# CORE-006 · Original 2D ArtMesh and Isolated Head/Elbow 3D Motion

**Executed:** 2026-10-30.  
**Verdict:** SOURCE PAYLOAD AND BONE MOTION SMOKE PASS; ANIME QUALITY **FAILED**.

## Evidence

- Final CI: https://github.com/tims-SP/koma-motion-lab/actions/runs/40943160359
- Draft Release, 3 MP4s and decoded-video montage:
  https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-6851ed7398e09d194364
- Draft PR: https://github.com/tims-SP/koma-motion-lab/pull/16

The source is a pinned MIT licensed Godot Skeleton2D GBot demo (7 actual 2D
Polygon2D meshes / 16 Bone2D joints / 8 source animation clips / 110 front
vertices). The original mesh UVs, triangles and per-vertex bone weight arrays
remain unchanged. Original front vertices are kept at Z=0. Four components
(head, chin, left arm and right arm) receive independent shallow side/rear
geometry; all other parts remain original front-only artwork.

**CRITICAL:** These side/back patches still use explicit synthetic diagnostic
canary art. This is a functional geometry/skinning experiment, NOT real
recovered side/back Japanese-animation painting.

## Actual video QA performed

Three fixed-format videos, 48 frames each, 960x540, 24fps:
`head_yaw.mp4`, `elbow_bend.mp4`, `camera_turn.mp4`.

- A separate `source_front.png` vs `part_front.png` test (same Three.js
  renderer, same source front mesh, shell disabled vs enabled) produced
  **0.00% pixel changes** at yaw=0. This is **NOT** source Godot-vs-Three.js
  fidelity parity.
- Camera fixed at yaw=0, independent 0->38->0 degree 3D head-axis rotation:
  **3.1468%** start-to-mid changed pixels excluding the HTML UI.
- Camera fixed at yaw=25, independent 0->64->0 degree out-of-plane
  forearm rotation: **0.6708%** start-to-mid changed pixels.
- Camera independent 0->55 degree turn: 5.1475% start-to-mid changed pixels.
- Every one of the 48 frames per clip was screened for adjacent-frame pixel
  jumps; maxima: head 0.922%, elbow 0.161%, camera 2.152%. The head/elbow
  sequences return to their initial rendered pose.
- Actual final **encoded MP4s were re-decoded**, and frame indices 0, 24 and
  47 from each were included in the video-derived review montage.
- I directly examined that montage (not only numerical checks).

## Actual image defects observed

- At 38 degree head yaw, the original front face becomes foreshortened but
  the actual character has no credible painted side/head/hair face.
  Diagnostic side geometry visibly appears near the head silhouette.
- The elbow does move independently of the camera, but the magnitude and
  deformation look simplistic; this is not a tested natural elbow,
  anatomical topology or valid hand/forearm collision solution.
- At 55 degree camera yaw the body remains substantially planar. Head/arm
  partial shells do not produce a coherent full-body 3D figure.
- While the source front mesh is preserved in the SAME Three.js rendering,
  it is still not proven pixel-identical to native Godot source output.

## What this round proves / does not prove

**Pass:** The real-world 2D ArtMesh payload can be preserved unmodified
while its skeleton drives 3D out-of-plane head/elbow motion; this can be
verified separately from camera movement, with encoded-video checks.

**Not accepted:** Anime-style multi-view painted skin, true 3D joint surface
continuity, native 2D runtime parity, face redraw, hair topology,
self-occlusion and large-angle character rotations.

## CORE-007 priority

Use a LICENSED anime-style character with actual layered 2D ArtMesh UV/rig
(e.g. an Inochi2D sample) and obtain matching front/profile painting,
preferably via existing licensed multi-view character data or an explicitly
validated authored/AI-generated supplementary view. Keep same character
throughout the test. Focus on head+hair under 0–45 degree yaw with explicit
contour/landmark registration and consistency checks, then a skinned elbow.

Do not publish unlicensed game sprite derivatives. No main-repo promotion.
