# CORE-008 · Native Head Yaw Reference (Inox2D)

**Source:** genuine full Inochi2D example \`Aka.inx\`, © seagetch CC BY 4.0.
**Renderer:** real Inox2D pinned OpenGL example \`d4dd9dd7f16b775042cbda44370570abf9a8cf81\`, not our own texture crossfader.
**Source binary:** verified full Git LFS model SHA256 \`dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f\`; never stored in Git or Release.
**Original rig:** \`Head:: Yaw-Pitch\`, 9×3 sample grid, 114 actual parameter bindings.

## Already executed native video evidence

- First two Actions \`40976189269\`, \`40976302827\`: FAIL due to \`FBO incomplete: depth attachment incomplete\` and empty video despite MP4 encoding.
- Root cause in pinned upstream example: renderer starts with internal width/height=0 before an initial \`Resized\` event. It allocated 0×0 composite and depth-stencil textures in Mesa/Xvfb. Initial dimensions were patched to equal actual 720×880 window dimensions. This is a small example initialization fix; the native INX model mesh, textures, parameter system and backend rendering code were **not** replaced.
- Full dynamic native OpenGL video and validation: https://github.com/tims-SP/koma-motion-lab/actions/runs/40976547059 — SUCCESS.
- Independent actual finished MP4 decoding / full-head crop: https://github.com/tims-SP/koma-motion-lab/actions/runs/40977310203 — SUCCESS.
- Draft Release with original encoded 1024×900 video and native 640×640 head close-up and QA:
  https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-7fdc4103973991820fcf
- Full video: 6s/24fps, head video cut from real MP4, no AI-generated art. A successful video QA found 24 sampled frames at 4fps with minimum pixel contrast 64.46 and maximal adjacent changed fraction ~0.009.
- I independently viewed seven **decoded** frames from the actual close-up movie (0/4/8/12/16/20/23). Character is real Aka (orange hair, huge fox ears, burgundy leaf, magenta eyes); animation includes facial and hair motion; perceived turn is *limited* and does not establish target 45° profile.

## Why fixed-value test is mandatory

The dynamic loop in the demo uses time-based normalized \`Head:: Yaw-Pitch\` values. The screen grab starts after application startup; the frame index is NOT a reliable parameter timestamp. A moving-loop montage cannot establish what the largest available yaw view looks like.

The next experiment launches a FRESH original render process at exactly
\`[0,0.25,0.5,0.75,1.0]\`, all with pitch 0. The captures are independent native OpenGL screenshots, not invented angle artwork. \`HeadYaw=1.00\` is a normalized model parameter, **NOT 45° physical rotation**.

Planned direct-audit questions:
- Does changing HeadYaw change actual head silhouette and feature arrangement, beyond a pure screen-space horizontal squash?
- Is the far eye/cheek/hair occlusion credible at native maximum?
- Does native coverage stop before the needed 30°/45° novel-view design?
- Which real source PSD/INX components already have corresponding deformation, and which need generated new view skin?

## FIVE-POSE GRID — COMPLETED and visually inspected

- Workflow: https://github.com/tims-SP/koma-motion-lab/actions/runs/40979190580 — **SUCCESS**.
- Owner-only Draft Release with five real native screenshots, contact sheet, source and QA: https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-5232f5fcb469ede29155
- Independent FULL model process for each fixed normalized yaw (pitch=0), native screen contents captured after OpenGL initialization with no camera orbit, precomputed graphics, fake extra art or interpolation.
- Actual contact sheet was directly viewed by the agent from GitHub Actions logs.

| Genuine normalized HeadYaw | Subject-changed area vs 0 in source head crop | RGB mean absolute difference |
|---:|---:|---:|
| 0.00 | 0% | 0.00 |
| 0.25 | 10.43% | 7.29 |
| 0.50 | 13.96% | 10.95 |
| 0.75 | 16.28% | 13.89 |
| 1.00 | 18.15% | 16.34 |

Structural smoke tests PASS: all five PNGs are nonblank (minimum RGB standard deviation ~93.58), have distinct hashes, and changing the real parameter deforms rendered pixels.

**Direct visual assessment:** Head hair envelope, cheek outline, near/far eyes and fringe *do* move. However the far eye remains largely visible at maximum native parameter and the face remains close to frontal. The rig is good for limited Live2D-looking movement, not evidence of real 45° three-quarter-view anime artwork or full head spatial rotation. Eye, nose, face contour, exposed far hair and ear overlap likely need new view-conditioned art and part registration when the user requests stronger sideways shots. This is a visual observation, not a calibrated camera angle.

**Important negative findings:** no actual source native 3D depth or side painting; no physical degree mapping; no official D SDK exact reference parity. The original INX ArtMesh is still the best source for 0° and the limited angle it can reliably cover.

## Next explicit implementation phase

1. Use the **actual native 0.00/0.50/1.00 model screenshots** as existing same-character yaw references, not only a PSD 0° source.
2. Before sending any GPT edit, supply the real Aka original/source screenshot as a native editable image input (no prompt-only generation). Reject any output that changes Aka identity or layout.
3. Target one supplementary high-quality *single* ~45° three-quarter head image first; constrain to the original fox ears, orange hair, burgundy leaf, red-magenta eyes.
4. Split only missing semantic patches (far eye, nose/cheek, near/far side hair, ear roots), map them to original part IDs; preserve source UV on original 0° art.
5. Render actual encoded comparison video, inspect mid-angles and backside holes. A passed test must have convincing face rotation beyond native +1.00, not merely higher pixel delta.


## Rules for CORE-008 next stage

1. Native INX is an *existing 2D puppet rig*; preserve its exact deformers and image layers whenever possible.
2. Do not infer pixel-perfect parity with official D Inochi2D SDK from an Inox2D Rust port.
3. Do not assign physical 15/30/45° labels to normalized parameter values without independent camera/landmark calibration.
4. A previous GPT generation yielded an unrelated pink-haired fox girl and was REJECTED. No accepted side-view generated art exists; never add it to UV mapping.
5. Only if the native maximal credible view is visibly insufficient: supply **actual original Aka PNG as edit-reference input** for targeted missing side cheek, far eye and hair rather than guessing the entire design.
6. MP4 and frame binary products go to owner-only Draft Releases; Git contains code, provenance and report only. Never merge into \`tims-SP/koma-motion\` production until visual gates pass.
