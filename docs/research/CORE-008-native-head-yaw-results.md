# CORE-008 · Native Aka Head Yaw-Pitch video validation

**Date:** 2026-10-30
**Status:** native INX pose/renderer and real recorded MP4 **PASS**.
**Visual finding:** head/facial artwork remains recognizable under original rig's positive yaw but this is **2D native deform**, not a verified new 3D viewpoint or a 45° real rotation. AI-generated 30°/45° skin remains NOT ACCEPTED.
**No promotion to main.**

## Verified results

- Build + real Xvfb OpenGL capture (successful):
  https://github.com/tims-SP/koma-motion-lab/actions/runs/40976547059
- Closeup generated **from actual final native MP4**, not pre-encode frames:
  https://github.com/tims-SP/koma-motion-lab/actions/runs/40977310203
- Owner-only Draft Release with both MP4s, both contacts and QA:
  https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-7fdc4103973991820fcf
- Experiment PR: https://github.com/tims-SP/koma-motion-lab/pull/19

## Actual source & native parameter

- Full original Aka INX (17,731,911 B) SHA256
  \`dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f\`,
  pinned \`Inochi2D/example-models\` commit
  \`cd95dd00ddff63b1f7d2b84a19914c3c70d05945\`.
- Aka authored/rigged by seagetch; CC BY 4.0.
- 34 actual parameters; \`Head:: Yaw-Pitch\` has 114 bindings
  on 9×3 sample axes. The param uses normalized [-1,1], not physical degrees.
- Renderer: real \`Inochi2D/inox2d\` Rust/OpenGL implementation,
  pinned upstream \`d4dd9dd7f16b775042cbda44370570abf9a8cf81\`.
  The example sets \`Head:: Yaw-Pitch\` to a deterministic positive
  sweep \`0→0.85→0\`, pitch held at zero, camera fixed.
- The rest of the renderer, INX parsing, parameters, texture sampling,
  masks and draw calls are upstream Inox2D: the lab patches ONLY
  the example param waveform and initial display dimensions.
- Inox2D is an officially supported experimental Rust port and NOT
  the original D SDK; no byte-identical parity with the original D engine
  is claimed. Inox2D lists incomplete feature support (animations,
  certain mesh groups, z-sort).

## Real OpenGL issues diagnosed and corrected

First two Actions produced \`native_head_yaw.mp4\` but frames were
BLACK/BLANK. Native viewer logs proved:
\`FBO incomplete: depth attachment incomplete [-1]\` and
\`GL_INVALID_FRAMEBUFFER_OPERATION\`.
Root cause in this environment: upstream example initially assigns
\`width:0,height:0\` and invokes \`renderer.resize(0,0)\` before
an initial window resize; under Xvfb/Mesa this leaves depth/stencil
attachments incomplete. Fix was in the local test patch, **NOT**
a modification to upstream repo: initialize example framebuffer dimensions
to 720×880 matching the chosen window dimensions.

Video QA intentionally failed on the empty rendered output, rather than
publishing a useless black clip. After the fix the video records
original Aka art in the real OpenGL window.

## Final encoded-video audits

1. Original full-size X11 capture \`native_head_yaw.mp4\`:
   **1024×900, 24 fps, 6 seconds**, 24 independent decoded frame
   samples at 4 fps. Minimum screen contrast **64.47**; maximum
   adjacent decoded frame changed fraction **0.895%**.
   Structural QA \`ENCODED_NATIVE_VIDEO_DECODED_AND_NONBLANK\`.
2. Additional \`native_head_closeup.mp4\`: derived ONLY by cropping
   the existing encoded native recording to original screen
   \`x=205,y=18,w=285,h=285\`, resampling to 640×640.
   The crop includes both full fox ears and face; no new artwork
   is generated or substituted. 24 frame samples independently
   decoded and reviewed. Maximum changed fraction from first
   frame **18.74%** in the zoom crop.
3. I directly examined both 7-frame contact sheets.
   The character's true orange/golden hair, large orange fox ears,
   red-magenta eyes and burgundy leaf remain visible. There is a
   recognizable left/right head tilt/turn effect and consistent
   bangs/ear location. No whole-face obstruction by rear hair is
   visible, in contrast to previous hand-composited CORE-007 failure.
   However, angle progression is modest and the eyes/nose/chin stay
   fairly frontal: it is **not** a credible full side/profile pose,
   certainly not independently calibrated to 30°/45°.
4. No unapproved GPT character candidate, still or movie, is presented
   as original Aka.

## Comparison with planned 2.75D art scope

| Quality gate | Status |
|---|---|
| Native full INX model loads in software OpenGL | PASS |
| Real 2D original model HeadYaw binding animated | PASS |
| Render encoded MP4 independently decode/nonblank | PASS |
| Real face / ears / hair imagery directly inspected | PASS baseline review |
| Native D engine vs experimental Rust renderer pixel parity | NOT TESTED |
| Normalized INX x parameter ↔ physical head yaw degrees | NOT CALIBRATED |
| 30°/45° generated side paintings matching original Aka | MISSING |
| Novel-view 3D UV / curve / occlusion registration | NOT IMPLEMENTED |
| Production anime 45° head turn | NOT ACCEPTED |

## Next step

Use the actual native 2D head yaw as the first baseline. Native rig
may supply enough 0–small-yaw deform that GPT 15° generation is unnecessary.

For higher angles, generate ONE same-character 30° image with
**actual original Aka PNG attached as a native image-edit reference**,
validate against source identity, then attempt 45°. Without reliable
reference attachment, do not generate additional generic anime fox
characters. Original front UV/mesh remain immutable; supplemental view
skin gets separate per-part registration and texture coordinates.

Do not represent the normalized 0.85 head parameter as a physical
45° turn. Side art and 3D completion gates remain open.
