# P15-29 · Recover pre-fade P0 far eye and gold clip; anchor nasal-bridge candidate

Executed 2026-11-11 UTC+08 on VPS using ChatGPT VPS Bridge Worker.

## Actual original art recovery

- Original P0 45° far-eye transparent PNG exists; SHA-256 5a0888c5cc3334e039314afa37c9f05adc27a0c653e0a2e492904690a97e4a2f verified.
- Original 45° crossed gold hairclip is SHA verified.
- P8 applies known smoothstep whole-layer opacity fade: 52°–75° far eye, 48°–70° hairclip.
- Inverse-normalized five intermediate P15-21 alpha maps using the exact P8 schedule while preserving stored source RGB.

| Yaw | Eye fade | Legacy alpha mass | Restored mass | Bridge candidate visible |
|---|---:|---:|---:|---:|
| 55° | .953399 | 15813.65 | 16571.78 | 69.610% |
| 57.5° | .855798 | 14193.96 | 16571.23 | 62.681% |
| 60° | .721213 | 11979.05 | 16572.09 | 56.152% |
| 62.5° | .565053 | 9375.46 | 16571.99 | 50.133% |
| 65° | .402729 | 6704.69 | 16572.10 | 44.629% |

Recovered shape IoU to registered P0 45° eye alpha is about 0.964. This demonstrates whole-layer fade domination but does not imply lossless reconstruction of every source pixel.

## Geometry and hairclip mounting

- P15-12 P0 camera anchors determine a tilted 2D nasal-bridge cutline between nose and far iris. This is an explicit 2.5D proxy hypothesis, NOT verified 3D head geometry or artist approved.
- Generated five full-scene comparisons: legacy fade, inverse restored, and bridge-proxy clipping, preserving 13-layer depth order.
- Hairclip inverse fade recovers alpha mass about 3251–3260, close to original 45°.
- Restored clip overlaps combined front/side hair alpha by 95.72–96.66% but clip centroid-to-camera anchor drift increases: 12.903, 16.075, 19.310, 22.585, 25.876 pixels across the five angles. Hair overlap is NOT proof of correct physical-side attachment.

## Verification and gates

- Native P15-21 443px baseline re-composition verified pixel exact.
- 9 Python unit tests passed; 10 Chromium viewport/angle cases with 120 images loaded and zero errors.
- Interactive HTML five-angle image viewer includes P0 originals, whole-frame alternatives and clip/eye transparent candidates.
- ZIP: private-assets/exports/p15-29-defade-geometry-review.zip.
- Visual 60° three-way comparison inspected. Old and restored identity linework is retained, but the proxy has no signed-off face-surface geometry.
- No original assets or formal P15-21 production renderer modified.

Formal result: **DEFADE ENGINEERING PASS; PHYSICAL OCCLUSION AND VISUAL ART APPROVAL PENDING**.

Next: use P0 measured anchors to correct clip position and physical far-eye outline across frames, then retest continuous VDD. Avoid fake global fading.
