# GODOT-006 · Real MOC3 isolated-container acceptance

Date: 2026-10-29. GitHub Actions [run #99](https://github.com/tims-SP/koma-motion-lab/actions/runs/40851922127) succeeded. Local Godot version: `4.7.2.stable.official.ed1daf0bf`, Linux x86_64, Xvfb + Mesa llvmpipe.

Source: `myssal/Reverse-1999-CN-Asset/live2d/roles/301003_x`; compiled `gd_cubism` v0.9.1 / PurismCore v5 ABI supplied as a 2-day private workflow artifact `godot-006-private-real-moc3-project-99` (ID 12887810775). Six source hashes match `asset-integrity.json`. No original game artwork or binary committed to Git.

## Verified locally

- Archive SHA-256 verified; independent `--headless --editor --import` exited 0; real native GDExtension and MOC3 loaded.
- `nod` 1080p/30: **90/90 frames**, 3s, H.264 MP4.
- `idle` 1080p/30: **270/270 frames**, 9s; Godot's direct AVI/MJPEG write took ~13s, then H.264 encoding succeeded.
- `face_idle` 1080p/30: 90/90 frames, but its *visible motion is not validated*.
- `idle` 540p/30: 270/270 frames, 9s.
- 1080p idle PNG sequence stalled at 261/270 frames under the external execution timeout; this route is **not** counted as a pass. Use Godot direct AVI for long software-render sequences.
- Five matched sample frames for nod and idle compared to existing GODOT-004 Actions H.264 reference gave mean absolute RGB head ROI differences around **1.97–2.18 / 255** (compression included); this verifies cross-environment consistency **not** official Cubism parity.

## Blocker: mouth parameter update but misplaced visible deformation

Direct native `get_parameters()` trace for `face_idle`: `ParamMouthForm` ~-0.49 to -0.69, `ParamMouthOpenY` ~0.07 to 0.37. Those values vary as the 2.7-second source motion plays, but 1080p rendered head-ROI temporal differences are only ~0.03–0.05/255.

Independent, motion-disabled forced extreme-value probes at 2.75× face zoom, separately changing each parameter:

| Parameter | Confirmed forced values | Changed pixels (>10 RGB) | Change bounding box | Visible mouth ROI mean change |
| --- | --- | ---: | --- | ---: |
| `ParamMouthForm` | -1 → +1 | 58 | x947–975, y192–199 | 0 |
| `ParamMouthOpenY` | 0 → 1 | 326 | x944–975, y192–207 | 0 |

**Status: PRODUCTION BLOCKER.** The native parameter interface changes, but rendered pixel changes are concentrated near upper mask/hair instead of the visible mouth. This warrants differential tracing of the decoded MOC3 parameter-to-mesh binding, extension update order and draw/mesh indices against an independent reference. Do not assume this is solved by successful playback or native load; do not assert official Cubism parity. Source-model-specific mapping remains a possible cause.

## Next gate

1. Locate exactly which drawables/vertex buffers respond to the mouth parameters and whether that response matches the original source.
2. Compare official Live2D Cubism frame-aligned mouth and mask renders with Godot/Purism output.
3. Gate production on parameter-to-visible-mesh fidelity, not only frame counts or average movement.

This test branch and PR are for validation only; never publish the private model or motion files to a public Release.
