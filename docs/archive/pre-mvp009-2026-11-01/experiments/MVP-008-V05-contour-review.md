# MVP-008 V05 — deformed head contour matte verification

Date: 2026-10-31

## Reproducible source and evidence

- Source code: [2895f5f](https://github.com/tims-SP/koma-motion-lab/commit/2895f5f5f1d41bfbaa4d838ceb54bb926fd1553c)
- Full 192-frame render: [Actions 41206130892](https://github.com/tims-SP/koma-motion-lab/actions/runs/41206130892)
- Real video, two transition strips, original ID/mask/depth passes: [artifact 13044700423](https://github.com/tims-SP/koma-motion-lab/actions/runs/41206130892/artifacts/13044700423)
- SHA-matched independent occlusion review and original video frame JPEGs: [Actions 41206308861](https://github.com/tims-SP/koma-motion-lab/actions/runs/41206308861), [artifact 13044364166](https://github.com/tims-SP/koma-motion-lab/actions/runs/41206308861/artifacts/13044364166)
- Baseline old frame review: [Actions 41205200317](https://github.com/tims-SP/koma-motion-lab/actions/runs/41205200317)

## Implementation

Replaces the former straight X wipe with six deformed facial contour sections at chin/jaw/cheek/nose/temple/hairline heights, interpolated using the actual independently rotating head yaw. Face, eyes and fringe are all clipped against the same physical X/Y head contour in a shader. The review pipeline now strictly ties downloaded MP4 to its producing Git commit. Transition strips are produced during the actual rendering run, not reconstructed from stale artifacts.

## Measurements

| Metric | Baseline | V05 |
|---|---:|---:|
| Structural dynamic checks | 10/10 | 11/11 |
| Time delta peak/median | 2.2382 | 1.7515 |
| Peak frame | 132 | 133 |
| Local overlapping occlusion cases | 10/10 | 10/10 |
| Full visual acceptance | FAIL | **FAIL** |

## Actual new/old pixel visual review

Examined new decoded JPEG frames 40, 43, 130, 132 and 134, compared directly against old frames 40, 132 and 134.

- At 40, the old extruding forehead slice is shorter, but the side face appears narrow with an abrupt edge.
- At 132, there is less obvious detached rectangular fringe geometry, but a near-vertical facial boundary still emerges independently of the hairline.
- At 134, side-face transition appears somewhat cleaner, but true cheek/temple/hair contact is still not represented.
- Arm profile still looks like a thin rigid plane; foot remains an elevated-height-only constraint.
- Numerical improvement alone does not mean visual quality is acceptable.

**Root cause remaining:** the 11-point ArtMesh boundary encodes the *outer* face/head silhouette. It does not encode independently authored inner skin/hair contact curves. The new algorithm cannot recover those absent semantic correspondences automatically. This is not repairable by further alpha or fixed-X tweaking.

## Required next core implementation — V06

1. Extend the four keyed head assets with named *inner* hairline landmarks (forehead, temple, cheek, jaw, chin) for both left and right side; stable semantic IDs across all four orientations.
2. Create a separate occlusion seam in head local coordinates, interpolate it along each face/hair morph, and apply the same seam to the front hair/facial mask. Verify no isolated face component in the actual ID masks around frames 38–45 and 128–136.
3. Compare actual cropped pixel strips against V05 on the same 192-frame timeline; run exact same 11 structural checks plus explicit inner-boundary conformance. **Model visual acceptance remains a separate manual gate.**
4. Only after head turn looks coherent, work on arm profile foreshortening and planted-foot IK.

**Stage verdict: PASS_STRUCTURE_PENDING_VISUAL / FAIL_VISUAL. General camera 360° and production quality remain NOT_ACCEPTED.**
