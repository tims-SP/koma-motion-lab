# GODOT-007 · Canonical-camera facial mesh acceptance — corrected

Date: 2026-10-29. Scope: original `301003_x.moc3` with official Godot 4.7.2 and compiled `gd_cubism` v0.9.1 + Purism Core 1.1.0 (v5 ABI) on isolated Linux Xvfb / Mesa software OpenGL.

## Correction and cause

GODOT-006 had incorrectly declared a mouth-parameter mesh-mapping blocker. Its annotation compared bounding boxes from a **1920×1080 full-body camera** against a **different 2.75× facial close-up camera**. That invalid cross-camera ROI produced `mouth_region_mae=0`, despite the deformation being at the correct location in the actual full-body camera. The prior annotation image and associated production-blocker verdict are **retracted**.

The precise source of the false positive was *evidence registration / camera transform mismatch*, NOT a proven bug in either Purism Core or GDCubism.

## Reproducible independent core proof

Without Godot rendering, `ctypes` invoked exported `csmGetParameterValues`, `csmUpdateModel`, `csmGetDrawableVertexPositions`, `csmGetDrawableOpacities` on the real MOC3 and native `gd_cubism.so`:

- Model parameter count: **137**; drawable count: **316**
- `ParamMouthForm` -1→1 changes **4** drawables; `ParamMouthOpenY` 0→1 changes **5** (ArtMesh191–195), including an opacity change
- `ParamEyeLOpen` 0→1 changes **8** drawables.
- The isolated Godot rendering with all 311 other drawables hidden visibly renders the real mouth fragment at the exact lips location using the same camera configuration.

## 1080p visual ROI gate (same view)

Strict camera: 1920×1080, 30 fps, `GODOT003_SWEEP=1`, zoom `1.0`, shift Y `210`, `GODOT004_HIRES=1`. Disabled motions for forced parameter comparisons; face_idle uses real 2.7s source `t_idle.motion3.json`.

| Gate | True crop (full-resolution pixels) | Sample frames | Mean absolute RGB difference (/255) | Pixels with per-channel max >10 | Result |
|---|---|---|---:|---:|---|
| Mouth form -1→1 | x935:995,y183:217 | 5,25 | **1.40899** | 58 | PASS |
| Mouth open 0→1 | x935:995,y183:217 | 5,25 | **5.98709** | 326 | PASS |
| Left eye open 0→1 | x955:1008,y142:196 | 5,25 | **7.22898** | 439 | PASS |
| Original face_idle frame 0→40 | x935:995,y183:217 | 0,40 | **1.93007** | 88 | PASS |

The earlier averaged full-head-ROI difference of 0.03–0.05 was diluted by a large mostly static background and was not proof of zero movement.

Execution: `scripts/godot_007_facial_roi_gate.py` with `--mouth-open`, `--mouth-form`, `--left-eye-open`, `--face-idle`, and `--out`. All CLI inputs are video paths and outputs a text-only JSON report. Core diff and source model stay local/private; do not store third-party art or binary in Git.

## Quality gate and limitations

- **PASS**: Parameter value changes reach Core; expected Drawable vertices change; same-view visible lips/eyes change. The specific allegation of spatial misregistration is **not supported**.
- **NOT CERTIFIED**: frame-identical fidelity against proprietary official Live2D Cubism Core or renderer, mesh weights, clipping masks, blend/opacity, and shader ordering. The official Core is **not hosted on GitHub** and requires independent installation under its license. A Purism Core→Godot self-consistency test cannot substitute for an official Cubism baseline.
- **Remaining production work**: get a licensed official Cubism Native SDK/Core reference under accepted terms; test the **same source model** and same parameter samples using independent original render outputs; compare per-drawable vertex coordinates, clipping masks, opacity, composition and final image. Avoid “fixing” already correctly placed mouth/eye meshes via hardcoded offsets.

## Prior evidence

- GODOT-006 source artifact GitHub Actions [run #99](https://github.com/tims-SP/koma-motion-lab/actions/runs/40851922127), [PR #9](https://github.com/tims-SP/koma-motion-lab/pull/9).
- GODOT-007 local corrected evidence is delivered via ChatGPT as a private downloadable ZIP. Do not publish original model-derived screenshots or videos to public GitHub Releases.
