# MVP-002 · CORE-FIRST 2.75D — superseding V2 process

Date: 2026-10-31. **Authoritative next-priority plan** for \`koma-motion-lab\`. The previous MVP-001 V2 T00–T11 and K0/K1/K2 reference experiments are **CANCELLED AS PREREQUISITES**, not deleted or considered successful.

## Correct dependency logic

1. Build **one unified TypeScript runtime**, immediately. Do not do official Spine runtime playback demos, Cubism samples or paper math reimplementations as separate gates. They are established references.
2. Use an intentionally small **original 4-keyview vector character**, with stable separately drawn parts and a handful of manually corresponding vertices. No complex commercial assets, no AI view-generation requirements, no PSD importer first.
3. Demonstrate on that one character: yaw 360 / interpolation and VDD, depth and part visibility; articulated whole-body action with two-link IK; eye/mouth, art shadow and particles. **One deterministic evaluator, three shots.**
4. Produce real browser-captured video in a single CI run with debug metadata. Assess whether the *whole architectural pipeline* works without opaque component swaps, duplicated eyes, broken limbs or missing frames. Avoid redundant isolated subsystem tests.
5. Only **after** an integrated preview passes, upgrade the representation from simple vector meshes to high-fidelity textured ArtMesh, real per-vertex RGBA/UV correspondence, stronger occlusion/depth, local skeletal camera direction, dynamic shading and advanced corrections. Then use complex existing assets **as reference or optional inputs**, not as a blocker to progress.
6. End-state still requires high-quality Japanese-anime visual scenes with a full-body 360 shot, full-body acting and character FX; this small-art MVP demonstrates only the technical arrangement, **not commercial-grade visual quality**.

## Real implemented experiment (MVP-002)

Source: [experiments/mvp002](../../experiments/mvp002/)
- \`src/main.ts\`: four cardinal key contours for face, fringe and skirt with per-vertex interpolation; anchor 3D projection and keyed VDD offsets for component positioning; per-part show/hide and depth; limb parts, two-bone planar IK, facial features, art-directed shadow and particles.
- \`src/controls.ts\`: browser scene selection and scrub.
- \`scripts/render.ts\`: deterministic Playwright capture, FFmpeg encoded 3 clips, contact sheets, frame metadata and checks.
- \`.github/workflows/mvp002-integrated.yml\`: compile + ONE 3-scene run, redundant concurrent CI auto-cancelled.
- 3 clips, each 72 frames at 24fps, 960×540: \`turn\` (full body yaw 0–360), \`action\` (step, body direction, hand reaching), \`fx\` (close-up eye/face/shadow/particles).

**Limits**:
- Vector authored proxy art, not original high-fidelity anime illustrations.
- Part contour mesh correspondence exists for 3 key parts, but no actual RGBA texture/UV multi-image interpolation yet.
- Two-link IK is currently 2D projected-image-space analytic, not a production full-body 3D solver. Legs are hierarchical-looking geometric parts and step animation, not ground-constrained full IK.
- Shape meshes are layered colors, no per-pixel normal maps nor large geometry reconstruct.
- This is *technical minimum of the integrated pipeline*, not proof that arbitrary 3D motion or high-quality 360 anime is solved.

## Single acceptance gate

Review the full **actual 3 output videos** and key frames. Record and fix:
- 360: stable identity/occlusion/shape around complete yaw loop (all angles including side/back), 0/360 seam.
- Action: visible independently moving limbs, actual IK endpoint reaches the onscreen target, no broken joints.
- FX: real face-part changes, shadow mask changes, particles visibly in front/behind; face remains recognizable.
- Consistent character asset across all 3 outputs; no third-party assets.

On PASS_ENGINEERING_ONLY, next engineering work is **higher-fidelity per-vertex textured art** and view correspondence, not reverse engineering game data. On FAIL, fix the same integrated demo and rerender; do not branch into a new technology study.

## Status

- Previous M0 renderer infrastructure: PASS_INFRA_ONLY (historic, separate).
- MVP-002 TS core: **PASS_ENGINEERING_RENDER_ONLY**, [GitHub Actions #41191491411](https://github.com/tims-SP/koma-motion-lab/actions/runs/41191491411) (successful). Actual H.264 clips each contain 72 frames at 960x540: turn.mp4 (133,721 B), action.mp4 (136,192 B), fx.mp4 (266,101 B). Three contact PNGs and quality report created; assets verified in [Draft Release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-cbdcb29f362bf38e3849) (owner access). **Visual/manual acceptance NOT DONE**, and **Japanese-anime quality NOT CLAIMED**. Earlier Actions failed on CSS screenshot dimensions/encoder; fixed. First successful preview available after code fixes. 2D planar IK, primitive vector art and incomplete per-vertex RGBA/UV mapping remain limitations.
- Resource reference: [Reverse-1999 CN Asset](https://github.com/myssal/Reverse-1999-CN-Asset), [2.5D Cartoon Models](https://alecrivers.com/2.5dcartoonmodels/), [VDD](https://arxiv.org/abs/2103.15472), [Puppeteering 2.5D](https://www.brunodorta.com.br/publication/puppeteering-cartoon/), [Anime2.5DRig](https://github.com/852wa/Anime2.5DRig). They are references **only** for this MVP.

## Implementation result and immediate correction

- [360 turn MP4](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-cbdcb29f362bf38e3849/turn.mp4)
- [full-body action MP4](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-cbdcb29f362bf38e3849/action.mp4)
- [face FX MP4](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-cbdcb29f362bf38e3849/fx.mp4)
- [contact sheets](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-cbdcb29f362bf38e3849)

**The next implementation step is not a new K0/K1/K2 investigation. It is a DIRECT ART REPLACEMENT in this same runtime**, moving from vector test parts to RGBA-mesh/UV-keyed art for front/right/back/left. Only after genuine art displays correctly do we strengthen local 3D pose/occlusion/shading for high quality. Existing Reverse1999 assets are not needed to do this first replacement.

## Next tasks after actual integrated preview

A. Replace three vector proxy meshes with authored **RGBA art mesh** having compatible per-vertex UV/correspondence across front/right/back/left keyviews; keep rest of app unchanged. This is the **first image-quality task**.
B. Replace image-space IK with real bone-local 3D transforms and evaluate per-part view from bone-to-camera.
C. Refine occlusion, art-directed normals/SDF, compositing, and shot corrections using only the needed extra art.
D. Final original or permissioned high-fidelity anime asset and 1080p three-shot acceptance.
