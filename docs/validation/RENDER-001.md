# RENDER-001 — Godot CPU software rendering without physical GPU/display

Date: 2026-10-29

## Accepted: real Godot rendering on GitHub Actions

- **PASS**: [workflow run #3](https://github.com/tims-SP/koma-motion-lab/actions/runs/40800202580) on Ubuntu 24.04.
- **Preview Release**: [godot-render-001-3](https://github.com/tims-SP/koma-motion-lab/releases/tag/godot-render-001-3). Synthetic original artwork only.
- Godot: `4.7.2.stable.official.ed1daf0bf`.
- Driver: Xvfb virtual X11 display and Mesa `llvmpipe` OpenGL 4.5 Compatibility renderer (no physical GPU required).
- Real output: 90 PNG frames, 960x540 at 30 FPS. Godot Movie Maker log reports 3s of video, rendered in about 2s in passing run.
- Encoded MP4: FFmpeg H.264.
- Independent Pillow + FFprobe validation: **PASS**, all 90 decoded video frames, dimensions 960x540, non-flat actual pixels, temporally different images, no reported errors.
- Original failed attempt [run #2](https://github.com/tims-SP/koma-motion-lab/actions/runs/40800081842) *did render and encode correctly*, but the Python verifier crashed with a local NameError. Corrected in [PR #2](https://github.com/tims-SP/koma-motion-lab/pull/2); do not classify that failed run as a quality pass.

## Local isolated-container corroboration (not the Godot binary)

- Xvfb starts a virtual display. Mesa `llvmpipe` (LLVM 19.1.7) provides OpenGL 4.5 Compatibility.
- Created a GLX context, drew real pixels, read them with `glReadPixels`: sample RGBA `(38,128,191,255)`, matching the test clear color.
- Separate local OpenGL-only animated drawing rendered 90 frames at 960x540, encoded H.264 MP4 via FFmpeg, and was checked with FFprobe: **PASS**.
- **NOT TESTED**: actually launching Godot locally. Godot binary absent from this container and outbound binary downloads blocked/unresolvable. This local run proves only the Xvfb/OpenGL/FFmpeg substrate, not independent Godot execution.
- The local output is a synthetic GLX regression artifact, **not** proof of Live2D/Spine fidelity.

## Scope and pending production gates

RENDER-001 demonstrates that Godot Movie Maker can produce and verify actual video on an Ubuntu runner with Xvfb and Mesa software OpenGL. It **does not** demonstrate compatibility or parity for GDCubism, Spine, VRM, alpha masks, weighted skinning, high-res effects or multi-minute anime rendering, and does not prove standard Godot `--headless` draws frames.

Next gates:
1. Render a genuine Live2D character and compare against reference frames with appropriate rights/access controls.
2. Render real Spine weighted meshes/animations and inspect masking, skinning and attachment order.
3. Test Vulkan lavapipe and GPU runner separately.
4. Record throughput and RAM use at 1080p and with multiple characters.
5. Repeat a **native Godot** run in the isolated container once the official executable can be staged there without bypassing network policy.

## Repository artifact policy

All source/test definitions and text reports are stored in Git. Synthetic binary previews are stored in a GitHub Release, not Git history. No third-party game artwork is redistributed by this experiment.
