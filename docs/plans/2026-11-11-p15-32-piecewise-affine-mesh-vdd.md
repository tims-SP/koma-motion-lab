# P15-32 · 2D piecewise-affine mesh VDD pilot

Executed on the target VPS through ChatGPT VPS Bridge Worker.

## Scope

Move beyond P15-31 per-role premultiplied RGBA blending for three high-value roles over 55°–65°:
- `eye.far`
- `hair.clip.cross_gold`
- `hair.side`

The other ten semantic layers continue to use P15-31 per-role RGBA interpolation. Five P15-31 keyframes are preserved byte-for-byte in the review output.

## Geometry implementation

For each adjacent keyframe pair and each of the three selected roles:
1. Derive grayscale from premultiplied RGBA source pixels.
2. Estimate forward and backward Farneback optical flow between the two role images.
3. Sample flow on a regular 7×7 control grid covering the union alpha bounds.
4. Clamp per-vertex displacement to ±42 native pixels.
5. Construct 72 triangles and inverse-map each destination triangle into its source triangle using piecewise affine transforms.
6. Warp the left and right endpoint textures independently toward the midpoint, then blend their warped premultiplied RGBA values.
7. Composite all 13 roles with the canonical `p1_front_semantic.alpha_over` and P15-21 depth order.

This is an actual **2D image-derived mesh deformation** pilot. It is not a 3D head surface, physically constrained facial geometry, or artist-authored VDD. The optical flow is estimated from existing raster source images; no new original art was painted.

## Outputs

- Nine angles: 55°, 56.25°, 57.5°, 58.75°, 60°, 61.25°, 62.5°, 63.75°, 65°.
- Four geometry-deformed midpoint frames.
- Three mesh-deformed roles per midpoint; each role uses 7×7 vertices and 72 triangles.
- Other ten roles remain the P15-31 RGBA interpolation.
- HTML review includes P15-32 composite, P15-31 comparison, amplified difference image and the three independent mesh roles.
- Archive: `private-assets/exports/p15-32-mesh-vdd-review.zip`.

## Results

| Metric | Result |
|---|---:|
| Keyframe output | 5/5 exact source files |
| Midpoint mesh frames | 4 |
| Mesh-deformed roles | 3 |
| Triangles | 72 per role |
| Mesh vertex flips | 0 across tested meshes |
| Minimum triangle area ratio | 0.72154 |
| Maximum vertex displacement | 6.9903 px |
| Midpoint changed pixels vs P15-31 | 117,372–133,537 |
| Unit tests | 7/7 |
| Chromium viewport/frame checks | 18 |
| Browser image loads | 108 |
| Browser errors | 0 |

The ten non-mesh roles were verified pixel-identical to P15-31 midpoint layers. The three mesh roles show actual geometry-driven differences. The five keyframe composite files remain byte-identical to P15-31.

## Acceptance

**Engineering pilot PASS:** per-role optical-flow-driven piecewise-affine mesh warp, exact keyframe preservation, zero triangle flips, non-mesh layer invariance, test and browser checks.

**Art / production acceptance NOT PASSED:** 2D optical flow is not physical 3D depth; nasal bridge / far-eye occlusion remains a 2D proxy; gold clip mounting to a specific hair lock is not physically verified; no independent angle-specific P0 original paintings were added; anime line-art quality remains pending.

Production P15-21 VDD remains unchanged.

## Next P15-33

Replace generic optical-flow-only geometry with explicit semantic anchors and per-role constraints:
- Far eye: iris/eyelid/face-surface anchors and a constrained visibility boundary.
- Hair clip: two crossed-bar endpoints, intersection center, and attachment point on a named hair lock.
- Side hair: root attachment, silhouette landmarks and strand-end constraints.

Compare constrained mesh VDD against this P15-32 optical-flow baseline. Keep the physical 3D and original-art acceptance gates separate.
