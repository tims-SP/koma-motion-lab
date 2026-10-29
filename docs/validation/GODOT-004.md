# GODOT-004 — 1080p genuine Live2D nod/body-idle and contrast audit

Date: 2026-10-29
Source: `myssal/Reverse-1999-CN-Asset/live2d/roles/301003_x`
Result: **PASS_HIRES_MULTIMOTION_REVIEW_REQUIRED**. Official Cubism renderer parity **NOT TESTED**.

## Completed verified run

- [GitHub Actions run 95](https://github.com/tims-SP/koma-motion-lab/actions/runs/40847823845): `completed / success`, all workflow steps passed.
- Owner-only [GODOT-004 draft Release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-d42b8e04c08b065bdb31) includes original-character 1080p nod and body-idle videos plus close-up contact sheets; draft must not be published.
- Environment: official Godot 4.7.2, GDCubism v0.9.1, CubismNativeFramework 5-r.1 with open-source PurismCore v5 ABI replacement, Xvfb + Mesa llvmpipe OpenGL, Ubuntu GitHub Actions CPU runner.
- Original `301003_x.moc3`, original texture atlases, original original-motion curve/segment data. **Only mismatched `.motion3.json` `Meta` count values are recomputed in the temporary runner**; originals never modified or stored in Git. No AI-generated replacement character or re-rigging.
- `nod` = upstream `motions/b_diantou.motion3.json` (3.167s); output 90 frames, 1920x1080, 30fps, 3.0s H.264 MP4. Independent FFprobe decoded 90/90 frames.
- `idle` = upstream **`motions/b_idle.motion3.json`** (9.0s); output 270 frames, 1920x1080, 30fps, 9.0s H.264 MP4. Independent FFprobe decoded 270/270 frames.
- Both motions' original parameter curves were preserved; no automatic action invention or skinning edits were used.

## A mistaken asset test was corrected, not concealed

[Run 87](https://github.com/tims-SP/koma-motion-lab/actions/runs/40847135537) successfully rendered a 1080p nod and the upstream `t_idle` action but failed the visible-motion acceptance threshold: subject-region RGB difference was only 0.0095. Inspection of original JSON showed `t_idle` has only six curves, with two moving mouth-form/open parameters, and is a **facial micro-motion**, not a suitable **whole-body idle animation**.

`b_idle` has **126 curves**, 9s duration, and substantial head/body parameters. In run 95 it replaced `t_idle` for body-motion validation, while retaining `t_idle` in the temporarily staged model under distinct `face_idle` group for potential later inspection. The change was a corrected **test selection**, not a lower motion threshold.

## Independent 1080p metrics from run 95

| Check | Result |
| --- | --- |
| Static 8-frame same-camera baseline | Exact RGB mean difference `0.0` |
| Background corner on dark slate | `[18,28,43]` |
| Background corner on white | `[250,250,250]` |
| Real static character bbox | `[760,80,1092,976]` in 1920x1080 |
| Visible foreground coverage (body in 16:9 frame) | `0.02135` (not a fidelity percentage) |
| Nod subject-ROI mean RGB change vs static (sample max) | `2.3982` |
| Body idle subject-ROI mean RGB change vs static (sample max) | `4.4394` |
| Body idle global mean RGB change (sample max) | `0.6397` |
| Independent audit reported errors | `[]` |
| Audit result | `PASS_HIRES_MULTIMOTION_REVIEW_REQUIRED` |

### Actual image inspection

Inspected the genuine `mask-contrast-head.jpg`, `nod-head-detail.jpg` and `idle-head-detail.jpg` returned by GitHub Actions. Both dark and bright backgrounds visibly retain hair strands, face, masks, and coat silhouette; no gross tearing or missing body parts in sampled closeups. `b_idle` clearly produces progressive head/hair/facial posture changes at frames 60/120/190/269. **A finite set of JPEG contact sheets cannot prove exact alpha, draw order or mesh correctness.** The original character remains relatively small in a wide 16:9 full-body video; zoomed detail sheets are for inspection and are not separate 1080p native character renders.

## Scope that remains unproven

1. **Official reference parity**: no matched-time frames from a licensed official Live2D Cubism Core renderer have yet been obtained. Therefore no SSIM/PSNR/pixel difference claims against the proprietary reference.
2. **Fine art-mesh and clipping/masking equivalence**: visual review reveals no *obvious* failure at inspected times, but is not a formal correctness certificate across every layer or time.
3. **Multiple character models**: one authentic 301003_x model is not enough to claim generic importer compatibility.
4. **Full physics/expression tracks, action transitions, nonstandard poses, scene occlusions and multi-character 3D/2D interaction** have not been validated.
5. **CPU software throughput**: run 95 logged about 8 seconds to record 90 nod PNG frames and 25 seconds to record 270 body-idle frames; it is a specific environment cost, not a guaranteed production throughput.

## Decision

**GODOT-004 technical target passed for a full-size 1080p original-character nod + body-idle video.** Preserve this validation as a repeatable, text-only workflow in `koma-motion-lab`. Do not merge into the main production repository until official Cubism visual reference comparison and multiple independent MOC3 models pass.

Game-derived video and image files remain in **owner-only draft Releases**. Git tracks scripts, workflow code and text reports only. Temporary Actions Artifacts are short-lived transfer copies, not an alternative permanent distribution channel.
