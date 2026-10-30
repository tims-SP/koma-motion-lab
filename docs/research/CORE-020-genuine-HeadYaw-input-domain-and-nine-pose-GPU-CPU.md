# CORE-020 · Genuine Aka ear GPU/CPU pixel-parity curve, authoritative parameter-domain correction

**Execution date 2026-10-30.** Real upstream Inox2D OpenGL GPU footage, independent source ear CPU renders and ACTUAL encoded/decoded MP4 have been performed, inspected and reproducibly packaged. **True 0° source pixel parity NOT PASSED. 360° character skin NOT ACHIEVED.**

## 1. Most important discovery: erroneous external-vs-normalized HeadYaw mapping in CORE-017/018/019

The pinned authentic full Aka.inx by seagetch (CC BY 4.0) SHA256 `dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f` defines the following **authoring input** for parameter `Head:: Yaw-Pitch`:

- `min = [-1,-1]`, `max = [1,1]`, `defaults = [0,0]`.
- Internal normalized interpolation `axis_points.x = [0,.125,.25,.375,.5,.625,.75,.875,1]`, `axis_points.y = [0,.5,1]`.
- 114 HeadYaw bindings; across original ear ancestry, 12 are relevant including 4 directly on the ear ArtMeshes.
- The native Rust `Param::apply` internally **normalizes** input `(raw-min)/(max-min)`. It thus maps native API input yaw `0.50`, pitch `0.50` to grid `(0.75,0.75)`, NOT grid `(0.50,0.50)`. Input `(0,0)` is the true parameter default/center (with upstream zero-parameter bypass behavior).
- The CORE-017–019 independent CPU ear renderer had incorrectly treated native raw input `x=.5` as internal grid `x=.5`, and pitch input `.5` as grid `.5`. **All previous reported GPU/CPU IoU under that mismatched input are real measured numbers, but invalid for same-pose parity claims.** They must not be used as current performance measures.

Actual source verification: [Actions #41016292154](https://github.com/tims-SP/koma-motion-lab/actions/runs/41016292154) **SUCCESS** via `.github/workflows/koma-25d-param-domain-020.yml` and corrected sampler tests in `experiments/koma-25d-core/tools/headyaw_domain20.py`.

## 2. Original source channels and non-interference

Also read **all 8** original model parameters affecting ear ancestors / ear meshes: `Head:: Yaw-Pitch` (12 relevant ancestry bindings), `Head:: Roll` (7), `Body:: Yaw-Pitch` (11), `Body:: Roll` (2), `Body:: X:: Move` (1), `Breath` (1), and each ear Physics (1+1). The other channels' original defaults are `[0,0]`; this audit does NOT yet definitively attribute residual GPU/CPU differences to parameter interactions, texture blend or native vertex transforms.

## 3. ACTUAL native GL curve and real encoded movie

[GitHub Actions #41014990222](https://github.com/tims-SP/koma-motion-lab/actions/runs/41014990222) **SUCCESS**. Inox2D Rust original source commit `d4dd9dd7f16b775042cbda44370570abf9a8cf81`, genuine original Aka INX full hierarchy/params. The debug filter ONLY suppresses draws of non-ear meshes; source ArtMesh 57/59 native vertices, 89/93 triangles, original TGA textures and original UV remain unmodified.

- 17 independently actually GPU-rendered OpenGL ear-only 720×880 PNGs: nine going from raw yaw .5 to 1.0 in increments .0625, then eight returning to .5, with external pitch .5 held fixed.
- H264 final file `actual_native_ear_17pose_hold24.mp4`: **102 H264 frames, 24fps**, exactly **17 original GPU source captures**, repeated frame holds at source 4fps; **no novel GPU poses synthesized** and no optical flow. SHA256 `482385b26c73624d8e52dc24885669dd3f872e8ce52894a881eca24d635b052f`.
- FFmpeg final MP4 re-decoded at frames `0,12,24,36,48,60,72,96`, all actually visually inspected. Source first/last PNG byte identity validated; nine ascending source poses truly distinct. Exact GitHub Actions artifact `CORE020-17-native-Inox-GL-ear-poses-and-H264` available (no draft release hiding).
- Critically, these native raw yaw .5–1 poses are **NOT original neutral**; they sample internal yaw .75–1.0 at internal pitch .75. They are NOT physical 45°–90° rotations.

## 4. Corrected independent original INX ear CPU rendering and numerical QA

Loaded the genuine original ear vertices/UV/indices + TGA and full ancestor transforms from CORE-016/017, then re-evaluated each binding by **bilinear interpolation over the correct 2D normalized axis** (raw yaw .5→1 mapped to normalized .75→1; raw pitch .5 mapped to .75). Rendered NINE actual separate CPU source-ear images, each 720×880 with alpha. Fitted exactly ONE screen XY translation to the first GPU frame (-1,0) px and applied it UNCHANGED to all other poses and both ears.

| Actual native external yaw input | Original INX grid X | GPU/CPU ear silhouette IoU | RGB overlap MAE (0–255) |
|---:|---:|---:|---:|
| .5000 | .7500 | **.9403** | **8.40** |
| .5625 | .7813 | .9300 | 8.35 |
| .6250 | .8125 | .9166 | 8.83 |
| .6875 | .8438 | .9047 | 9.48 |
| .7500 | .8750 | .8933 | 10.61 |
| .8125 | .9063 | .8804 | 11.38 |
| .8750 | .9375 | .8715 | 11.60 |
| .9375 | .9688 | .8566 | 11.69 |
| 1.0000 | 1.0000 | **.8452** | **12.59** |

Previously incorrectly compared endpoints were .8934/.8059 with fixed neutral fit (-9,+2). Correct source mapping increases measured same-pose IoU and reduces fitted screen offset to (-1,0), **but still FAILS exact pixel parity, and error grows toward max raw yaw input.** Direct visual inspection of 9-pose color/source/difference strips confirms residual boundary mismatch.

The correct mapping is the central achievement; claiming 94% from a truly neutral pose would also be wrong: it is **raw yaw=.5, pitch=.5** (normalized internal [.75,.75]).

### Small additional source sampling test

Pinned upstream native `inox2d-opengl/src/texture.rs` uses **GL_LINEAR** sampling and **GL_CLAMP_TO_BORDER** transparent outside UV. We independently compared old CPU sampling `u*(width-1)` vs OpenGL pixel-center mapping `u*width-.5`. Under corrected input-domain evaluation with same (-1,0) offset, neutral source RGB MAE **8.396→8.085** (tiny improvement), max **12.592→12.605** (slight regression). GPU/source shape error does not vanish with UV sampling change. A naive V-axis flip produces gross failure (MAE ≳35), rejected. No claim that shader texture sampling is already pixel-perfect.

## 5. ACTUAL encoded GPU-vs-corrected-CPU video

Local `CORE020_native_GPU_vs_corrected_INX_CPU_Diagnostic.mp4`: **102 H264 frames, 24fps, 1500×520**, SHA256 `397a29fa6234728ce5d34c56e351e9287ca1605cf0a3de648f9de5132587d164`.
- Each of 17 original GPU source frames is compared with the actual independently rendered source-Inochi CPU mesh view under **corrected parameter domain**, with return-path CPU views reused from nine.
- Left: actual native Inox2D GPU from GitHub. Center: original 57/59 vertex ear CPU mesh UV and real TGA. Right: overlap green/GPU-only red/CPU-only cyan.
- Encoded frames `0/12/24/36/48/60/72/96` were decoded from final MP4 and opened for visual review, not just PNG source checks.
- Source 17 frames at 4fps held to 24fps, **not a continuous high-frequency native parameter stream**, not a 3D turn and not 360° character video.

## 6. Reproducibility, artifact policy, final gate

Complete local conversation ZIP `CORE020_Aka_corrected_param_native_GPU_CPU_QA.zip`, SHA256 `c7fc6c10f2590ceb4963ddf21d58b5e23f00cbb594bddb99ac33126ac42f2bba` (1.36MB, 73 entries) contains real GPU source frame PNGs and native H264, original ear source RGBA textures, original native ArtMesh UV/triangle arrays and all source binding records, independent CPU 9 pose PNGs, replay Python source, post-decode diagnostic movie, contact sheets, actual per-pose numerical JSON and exact recreation README. The reproduction was actually rerun, yielding identical original INX CPU neutral image bytes. **No binary committed as Git blobs.**

GitHub text-only changes:
- `.github/workflows/koma-25d-core-020.yml`: 17 real native GPU poses and final encoded H264 source verification.
- `.github/workflows/koma-25d-param-domain-020.yml`: direct original INX authoring range, other param defaults and explicit regression test.
- `experiments/koma-25d-core/tools/qa_native_pose20.py`: source frame/encoded source video QA.
- `experiments/koma-25d-core/tools/headyaw_domain20.py`: correct original parameter domain normalization and bilinear axis sampling.

**Core-020 Verdict: real native GPU curve PASS; original parameter domain bug repaired; same-component silhouette QA still FAIL for pixel-perfect parity; 0° truly default [0,0] native-vs-CPU capture NOT yet made; real side/rear painted skin, per-part 3D UV and high-quality 0–360° Aka rotation NOT IMPLEMENTED.** This round contributes to original UV/rig correctness, not completion of missing 360° view illustrations. Next CORE-021 should explicitly capture raw (yaw,pitch)=(0,0) and maximum yaw raw (1,0) with native INX original pose; use the source domain-correct CPU and GL sampler for identical camera/texture comparisons, then separately resume actual side/rear painterly assets and curve skin. Avoid further re-labeling native normalized parameters as degrees or neutral when not.

Production repo `tims-SP/koma-motion` untouched; Draft only.