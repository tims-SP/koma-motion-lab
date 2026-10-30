# CORE-019 · True GPU-versus-CPU Aka original EAR ArtMesh raster audit

**2026-10-30 · Source native ear-only OpenGL PASS · same-part parity comparison executed and independently inspected · exact 0° pixel parity FAIL.**

## Established method and actual source code

Used pinned [Inox2D Rust OpenGL](https://github.com/Inochi2D/inox2d) commit `d4dd9dd7f16b775042cbda44370570abf9a8cf81` and real complete `Aka.inx` SHA256 `dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f`, original seagetch CC BY 4.0. Model source contains 76 ArtMeshes, of which the two ears have original 57/59 vertices, 89/93 triangles and real TGA/UV. No original UV, weights, mesh or param data replaced.

**Critical design change from CORE-018:** patch the native Inox2D OpenGL *DRAW TEXTURED MESH* dispatch to render ONLY node IDs `3424078890` (`Ear:: Left`) and `3453251657` (`Ear:: Right`) while **keeping the complete original puppet tree, ancestor transforms, all bindings and mask rendering**, so the native GPU and custom CPU both depict two original ears. The patcher fails closed if upstream commit source shape changes. It also fixes native HeadYaw x to env-supplied 0.50/1.00, pitch to true neutral 0.50 (not 0), avoids zero-sized FBO, fixed window 720×880. The independent CPU renderer is original 2D ArtMesh with exact source vertices, triangles, UV/TGA and original inherited HeadYaw interpolation; not a redrawn sprite.

**GitHub Actions [#41013516588](https://github.com/tims-SP/koma-motion-lab/actions/runs/41013516588) SUCCESS:** compiled actual OpenGL Rust, ran Xvfb/Mesa on authentic INX, generated two 720×880 pixel PNGs `gpu_ears_neutral.png` and `gpu_ears_maximum.png`, actual-pixel nonblack/orange bounds QA and saved normal downloadable artifact `CORE019-real-Inox-Aka-native-ear-only-GL-frames`.

Source GPU PNG hashes:
- neutral `128d113e203ca51d37addd40409ef9b19ff906ba57e2339beee70ce4adce5116`; visible original ear pixels ~6,643; **no torso, hair or other model parts**.
- maximum `556b624ce1692f4bc9ff9b66f5de8d235f05dc488888cfea6b1c400cd0a7d2b8`; visible original ear pixels ~6,653. Source screen fractional change >18 RGB 1.06818% (mostly black frame, not art quality).

## Independent actual image-to-image CPU/GPU metrics, not inferred

Both sets of real PNG files loaded in local sandbox and measured against original independently rendered CPU ear mesh/UV images (no full-puppet occlusion). Mask defined on real screen region x120:555, y0:260, with red-orange visible pixels from GPU and source RGBA pixels from CPU. **ONE global XY offset derived on neutral only** and held constant for maximum: (-9,+2) px.

| Native HeadYaw | GPU vs CPU IoU without fit | After ONE neutral fit | overlap RGB MAE /255 |
|---|---:|---:|---:|
| 0.50 neutral | 0.5324 | **0.8934** | **10.16** |
| 1.00 max | 0.6347 | **0.8059** | **13.39** |

GPU reference and CPU independent source ear-only images were directly compared visually. Green on the diagnostic is overlap, red GPU only, cyan CPU only. Neutral 0.50 ear tips largely agree after one offset, but contour and source colors still show disagreements. Max 1.00 diverges more, especially lower ear tips and edge antialiasing/deformation.

**This is a more defensible metric than CORE-018's ear vs full-puppet screenshot**; however it is NOT exact pixel parity. No per-ear or per-pose independent shifts were used. More isolation is still required: homogeneous camera transform, native GL vs OpenCV sampling at UV borders, RGB premultiplication and texture alpha, inherited node/world transform interpretation, ear vertex deform bindings, masking and affine triangle interpolation.

### Local actual encoded movie

Created **97-frame 24fps 1260×386 H.264 MP4**, SHA256 `3a3d1f8f394e100e72134ea9c9d36668156b0aea1568113318359faa7e9ac2f9`, and re-decoded/factually visually inspected frames `0/12/24/36/48/60/72/84/96`. Left shows **HOLD of one of TWO genuinely rendered fixed-pose native GPU ear screenshots**, middle original INX CPU ear texture/UV/deformer interpolated continuously in normalized x=.5→1→.5, right overlay; **do not call the left a continuously GPU-rendered animation**. The source frame at 1.0 and returning neutral hold visible motion and correct label. No native 3D, no 360 skin.

## Actual binary outputs and reproduction

User-visible local package `/mnt/data/CORE019_Aka_native_GPU_cpu_ear_parity_QA.zip` contains normal Actions native GPU PNGs/logs, independent original CPU source ArtMesh PNGs and original two ear INX textures/mesh/param JSON, independent full Python renderer source, GPU/CPU comparator, H264 video generator, video, decoded keyframes, true visual IoU diagnostics, QA and README. **These binary assets are NOT Git blobs and not claimed generated in GitHub Actions** (except the native real two GPU reference PNGs).

Committed text only:
- `experiments/koma-25d-core/tools/patch_inox_ears_only19.py`
- `experiments/koma-25d-core/tools/qa_native_ears_only19.py`
- `experiments/koma-25d-core/tools/compare_ear_gpu_cpu19.py`
- `.github/workflows/koma-25d-core-019.yml`

## Acceptance and next phase

| Gate | CORE-019 |
|---|---|
| Real original 2-ear source full parent and original HeadYaw evaluated by actual native GPU | **PASS** |
| Native only-ears OpenGL PNGs, two poses, normal Actions artifact | **PASS** |
| True same-part GPU/CPU per-pixel difference and decoded H264 | **PASS as measurement** |
| Both pose silhouettes exact (IoU=1) | **FAIL: 0.8934 and 0.8059** |
| GPU/CPU source paint identical (RGB MAE=0) | **FAIL: 10.16 and 13.39** |
| Full 76-part source rig vs official D SDK | NOT PROVEN |
| New high-quality side/back ear paintings, UV and volumetric surface | **MISSING** |
| 360° anime-quality rotating Aka character | **NOT IMPLEMENTED** |

**CORE-020:** First make common camera origin an explicit fixed upstream invariant rather than optimizing an offset. Compare native GPU-pixel and independent CPU generated vertex barycentric UV under same sampling rule (GL_LINEAR, CLAMP_TO_BORDER zero alpha, premultiplied blend) and true inherited matrix/deform values, one error source at a time. Render native GPU 0.5/0.625/0.75/0.875/1.0 independently for a stronger parameter curve benchmark. New side/rear art only after source 0° parity. Keep Draft, `tims-SP/koma-motion` production untouched.