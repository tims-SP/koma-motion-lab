# MVP-002 · Small Core Feasibility, not Another Asset-Import Project

This **replaces V2 T00–T11/K0–K2 as the next priority**. Previous docs and code are retained as historical evidence, not required gates.

Goal: first make the **entire chosen architecture run end-to-end**, with deliberately minimal **original, authored, 4-keyview vector parts**. Reverse1999, Cubism, Spine and academic SVGs are **references only**. Do not download or convert game art in MVP-002.

Implemented (engineering code present, not yet independently verified):
- Browser in strict TypeScript, Three.js/WebGL2.
- 4 key view forms per component at yaw 0/90/180/270; interpolation around 0/360.
- 3D anchor projection and per-part VDD artist offset.
- Independent meshes/layers, facial/eyelid animation, front/back visibility.
- Joint-based 2-link analytic IK reach + stepping legs + local animation.
- Art-directed light-mask shape, simple particle effects and close-up camera.
- One deterministic timeline evaluator and 3 shots; render tool encodes video with ffmpeg.

This is an **original stylized colored vector test character**, not high-quality anime art, NOT a complete Live2D or Spine runtime, and not a generally correct artist mesh/UV importer. The purpose is to find out if all subsystem interfaces can run on ONE model **before** pursuing difficult asset work. Its face/shape construction uses procedural ellipses and manually authored form factors. Full-fledged per-vertex artmesh correspondence, rich textures, and art quality remain follow-up engineering work, not a proven success.

## Usage

\`\`\`bash
npm install
npm run typecheck
npm run dev
# browser http://127.0.0.1:5174
# with chromium + xvfb + ffmpeg:
xvfb-run -a npm run render
\`\`\`

Expected three clips: \`turn.mp4\`, \`action.mp4\`, \`fx.mp4\`. 72 frames / 24 FPS each at 960x540; 3 seconds per scene. This is the minimum core-loop, not the 1080p/final 18-second production acceptance bar. Original visuals may be freely included in GitHub Draft Release, no third-party game textures.

## Single decision gate

Review actual three clips, especially facing 45/135/225/315 and the arm reach. If this cannot show an understandable 360 rotating character, connected full-body motion, and one functioning face/FX on the same asset, **fix the code now**. Only after that expand the art representation: triangular RGBA mesh, per-vertex correspondences, real face/cloth keyviews, occlusion corrections and assets. Avoid repeated tutorial reproductions of already working Spine/Live2D runtimes.
