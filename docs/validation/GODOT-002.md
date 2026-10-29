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

## 2026-10-29: genuine motion3 meta overflow fixed; movie now renders

- [GDCubism native trace, run 36](https://github.com/tims-SP/koma-motion-lab/actions/runs/40810176001) proved that original `LoadModel` returns and the original crash happens at `motion_load`, before any character video.
- [No-motion model, run 41](https://github.com/tims-SP/koma-motion-lab/actions/runs/40813189646) proved original texture loading, rendering object and mesh construction, with a real 15-frame static sequence. Visual check found only 0.64% foreground; no quality pass.
- [Raw motion ASan, run 19](https://github.com/tims-SP/koma-motion-lab/actions/runs/40813817328) reproduced **heap-buffer-overflow** at CubismNativeFramework 5-r.1 `src/Motion/CubismMotion.cpp:633`, from `Points.UpdateSize(json->GetMotionTotalPointCount())` at line 568. This was triggered by mismatched upstream `motion3.json` Meta counters; do not attribute it solely to Godot or OpenGL.
- Counts recomputed from actual segment arrays:
  - `b_diantou.motion3.json`: declared 126 curves, 305 segments, 337 points. Verified **126 curves, 304 segments, 462 points**.
  - `t_idle.motion3.json`: declared 6 curves, 20 segments, 24 points. Verified **6 curves, 19 segments, 29 points**.
- Created `scripts/godot_002_normalize_motion.py`; applies count correction **only to transient CI copies**, preserving original curves, interpolation, parameter IDs, time values, textures and MOC3. This change is transparent and reproducible.
- [ASan normalized motion, run 24](https://github.com/tims-SP/koma-motion-lab/actions/runs/40814230230): **PASS**, both original motions parsed and applied through 90 numerical frames each. A required UserData event callback was registered in the independent test harness.
- [Godot motion render, run 54](https://github.com/tims-SP/koma-motion-lab/actions/runs/40814383002): **PASS runtime** (GDCubism motion loading, scene init, `GODOT002_REAL_MOTION_STARTED`, 90 PNG and MP4 frames at 960x540). **FAIL visual QA**: small foreground (around 0.64%); whole-frame motion differences under initial fixed threshold.
- [Auto-frame, run 62](https://github.com/tims-SP/koma-motion-lab/actions/runs/40814958058): **PASS foreground visibility threshold**: character-focused diagnostic framing applied zoom 1.9583x with original MOC and curves unchanged; foreground 2.62–2.66%. Still **FAIL motion QA** due an absolute whole-frame threshold that undercounts localized nod movement.
- [Independent motion-vs-static validator, run 66](https://github.com/tims-SP/koma-motion-lab/actions/runs/40815188894): **PASS_PLAYBACK_NOT_PARITY**; full GitHub job completed/success. Real GDCubism loaded, authentic nod motion started, 90 PNG and 90 decoded MP4 frames at 960x540, foreground 2.62–2.66%, normalized motion signal 21.13, static-control frame difference 0.0, no verifier errors. The run published a **draft-only** visual inspection release; no official Cubism frame parity is asserted.

**Strict interpretation:** Godot + Xvfb + Mesa has now rendered an original MOC3 and authentic (count-normalized) motion into a full MP4, but this is **not** proof of official Cubism visual parity, complete body appearance, masking correctness, or production-grade anime quality. Owner-only draft Releases preserve diagnostic footage for inspection; no third-party game art is committed to git or publicly released.

### Final playback gate and remaining quality gate

- **PASSED**: Godot 4.7.2 under Xvfb + Mesa llvmpipe successfully plays original `301003_x.moc3` plus original point/segment-keyframe curves after metadata count repair. It can generate deterministic frames and MP4 on CPU-only GitHub Actions.
- **NOT PASSED / NOT TESTED**: direct pixel parity against official Cubism Runtime, clothing/face/blend/mask fidelity, character completeness, and production anime quality. `GDCubism` model textures and meshes were loaded, but numerical frame checks alone cannot certify the artwork.
- **Owner review draft**: [Run 66 draft visual QA](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-dbb0948d84a7851240cb) contains one static original frame, the motion preview, a contact sheet and per-run JSON checks. Draft is intentionally not published because it contains third-party game-derived artwork. If the owner cannot see the draft with the linked account, open the repository's Releases -> Drafts.
- **Branch isolation**: these experiments remain in `validation/godot-002-live2d` until the visual fidelity gate is independently reviewed. No third-party MOC3, PNGs or videos in Git history.
