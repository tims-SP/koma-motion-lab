# GODOT-002 — Real Live2D MOC3 on Godot (experimental)

## Goal
Prove, by real rendered frames, that a character from myssal/Reverse-1999-CN-Asset can be played in **unmodified Godot 4.7.2** under Xvfb/Mesa llvmpipe, preserving original MOC3, texture and motion resources instead of re-rigging.

## Asset and ownership constraints
- Source model: `live2d/roles/301003_x/301003_x.model3.json`, MOC3, two texture references, original `b_diantou` and `t_idle` motions.
- Download from the public upstream repository **only into the ephemeral Actions runner**. Check SHA-256 and MOC3 header; do not check binary assets into git.
- Derived footage must remain in a **draft Release only**, not in any publicly published Release or downloadable public artifact.
- This is a personal compatibility experiment; upstream source artwork licensing remains separate from the open-source renderer.

## Technical chain
1. PurismCore (MIT Core reimplementation) built with `PURISM_CORE_ABI=v5`.
2. GDCubism `v0.9.1` (Godot GDExtension) + CubismNativeFramework tag `5-r.1` (Live2D Open Software License).
3. Godot 4.7.2 on Ubuntu 24.04 with virtual X11 display and Mesa llvmpipe (OpenGL Compatibility).
4. Load real `.model3.json`, call `get_canvas_info`, then `start_motion("nod", 0, PRIORITY_FORCE)`.
5. Godot Movie Maker emits 90 frames at 30 FPS, FFmpeg encodes MP4; Pillow / FFprobe reject blank/static/missing frames.

## Run history — failures are not playback passes
- [Run 1](https://github.com/tims-SP/koma-motion-lab/actions/runs/40801481710): **FAIL** compilation — latest CubismNativeFramework changed constructor and render order API, incompatible with GDCubism v0.9.1.
- [Run 2](https://github.com/tims-SP/koma-motion-lab/actions/runs/40802604509): **FAIL** compilation — nested `stdint.h` in the legacy Cubism Core C++ namespace breaks glibc system types.
- [Run 3](https://github.com/tims-SP/koma-motion-lab/actions/runs/40802859043): **FAIL** compilation — Purism Core static library built as v5 but host-facing header defaulted to v6, so legacy `csmGetDrawableRenderOrders` declaration was absent.
- [Run 4](https://github.com/tims-SP/koma-motion-lab/actions/runs/40803372939): **FAIL at runtime**. v5 ABI GDCubism extension successfully compiled; Godot editor could not load `libgd_cubism.linux.debug.x86_64.so` because only the release variant was copied. It generated 90 *empty background frames* before a log assertion rejected the run; these are not valid character animation.
- [Run 6](https://github.com/tims-SP/koma-motion-lab/actions/runs/40806123334): **FAIL in native runtime**. GDCubism compiled and loaded from release library; Godot Movie Maker reached scene startup, but exited with `malloc(): corrupted top size` (SIGABRT, code 134). No valid character movie generated. This is likely memory/ABI interaction, not a simple render configuration problem.
- [Run 8](https://github.com/tims-SP/koma-motion-lab/actions/runs/40807160888): **FAIL build**: PurismCore's `moc3info` tool is v6-only and cannot compile with its v5 compatibility ABI. No native model playback was attempted.
- [Run 11](https://github.com/tims-SP/koma-motion-lab/actions/runs/40807318481): **PASS**: independent v6 MOC3 decode, v5 Core compiled, native extension built and cached. **FAIL**: real Godot scene crashed with heap corruption (`malloc(): corrupted top size`). GDB separately reproduced SIGSEGV in the GDCubism shared library. No valid Live2D frames.
- [Run 13](https://github.com/tims-SP/koma-motion-lab/actions/runs/40807997011): **PASS**: native `GDCubismUserModel.new()` and `add_child()`. **FAIL**: setting `character.assets` to the genuine model immediately corrupts native heap. This isolates the crash to model initialization, before playback.
- [Next validation](https://github.com/tims-SP/koma-motion-lab/pull/3): independent v5 Core MOC3 revival/update probe (`experiments/godot-002/purism_v5_probe.c`) added to distinguish v5 core decode/initialization from GDCubism's framework model loading; result pending CI execution.

Do not interpret the existence of a MOC3 file, its SHA, successful Purism build, successful GDExtension build, or a nonempty movie as visual parity with the official Cubism runtime. For parity, capture matched parameter/time/frame references and explicitly assess clipping masks, blend modes, part order, facial and garment deformation.

## Build provenance
The GDCubism assembly uses the user-provided upstream model and independent open-source Core implementation. No official proprietary Cubism Core binary is downloaded or committed. Any runtime output should be reviewed for correctness; interoperability is a **test hypothesis**, not assumed.

## Criteria for acceptance
- GDCubism library is built and loads into Godot without extension errors.
- Original model canvas and motion group are reported by the runtime.
- The actual character is visibly present at all sampled frames and moves through the nod motion.
- All 90 decoded MP4 frames are present at 960x540 and the sampled PNGs differ over time.
- Further comparison against the official Cubism reference is a **separate** fidelity gate.

This document describes experimental results and deliberately leaves the final gate open until the Action completes.

## 2026-10-29: narrowed native crash with independent ASan probes

- [Core ABI Action](https://github.com/tims-SP/koma-motion-lab/actions/runs/40809101502): **PASS** using the real `301003_x.moc3` in both baseline and AddressSanitizer builds. `csmReviveMocInPlace`, `csmInitializeModelInPlace`, `csmUpdateModel` completed with 137 parameters, 316 drawables and 825616-byte model buffer.
- [Framework API Action](https://github.com/tims-SP/koma-motion-lab/actions/runs/40809922256): **PASS** under ASan; `CubismFramework::Initialize` → `CubismMoc::Create` → `CreateModel` → `SaveParameters` → `Update` → cleanup. Same 137 parameters and 316 drawables.
- Both diagnostics use the same temporary upstream MOC3, with no proprietary Cubism Core binary. Passing these tests does **not** establish fidelity, runtime animation, or the absence of all possible defects.
- Primary runtime issue is now suspected in `GDCubismUserModel::load_model`, the Godot/GDExtension wrapper, the full `InternalCubismUserModel::model_load` path, or renderer/texture/JSON/motion initialization. It is **not** established that PurismCore has a fundamental inability to load this MOC3.
- [Native trace Action](https://github.com/tims-SP/koma-motion-lab/actions/runs/40810176001): builds a temporary instrumented GDCubism native extension and logs precise phase markers before/after JSON parsing, MOC loading, motions, texture resources and mesh creation. Outcome must be inspected independently.

**Acceptance remains open:** no full real-character Godot movie has passed visual validation.
