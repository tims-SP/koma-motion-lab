# CORE-003: UV, View Skin and Visual Inspection Results

Date: 2026-10-29.
Status: STRUCTURAL DIAGNOSTIC PASS; ANIME ART NOT ACCEPTED.

## Evidence
- Latest successful rendering: https://github.com/tims-SP/koma-motion-lab/actions/runs/40905627579
- Owner-visible Draft Release: https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-15b68d4d20dcf7b9433b
- 73 frames, 960x540, 24fps, yaw 0–180 deg; original MIT Godot GBot Polygon2D source.
- Visual inspector accessed the ACTUAL 2-row contact sheet via small JPEG embedded in CI logs.

## What works

1. Source front triangles retain the original 2D UV, side/back faces use independent UV coordinates.
2. tools/register_views.py accepts externally supplied PNGs and per-mesh UV registration. Invalid mesh names, UV lengths, domains and wrong image formats are rejected. The resulting manifest is REGISTERED_UNREVIEWED; never production_accepted=true.
3. At zero yaw, the diagnostic shell is hidden and gradually revealed with a smooth angle-dependent fade. The SAME Three.js source-front-only and shell-enabled images are identical under this screenshot comparator (0.0 changed-pixel fraction). THIS IS NOT native Godot renderer pixel parity.
4. Canaries demonstrate side/back surface texturing, but ARE NOT authentic new character artwork.

## Critical visual failure discovered and repaired

Actual contact-sheet inspection exposed an unattached floating jaw tile. Source Godot Chin Polygon2D has offset = Vector2(-516, -603), omitted in the earlier importer. Applying both Polygon2D position and offset to the vertex coordinates while retaining source UVs restored the chin.

A new Head/Chin bbox regression now catches the missing-offset failure. This defect was missed by the earlier all-green structural QA. Continuous image inspection remains mandatory.

## Latest measured metrics

Screen-space coverage excludes the HTML overlay; RGB thresholding is not anime-art acceptance.

| Test | Value |
|---|---:|
| 0 deg coverage | 10.20% |
| 45 deg coverage | 9.85% |
| 90 deg coverage | 3.19% |
| 135 deg coverage | 9.66% |
| 180 deg coverage | 10.59% |
| Source front changed by added shell at 0 deg | 0.00% |
| Largest adjacent-frame coverage jump | 0.643 percentage points |
| 90 deg canary vs original front-only diff | 3.09% |
| 135 deg canary vs original front-only diff | 9.47% |
| 180 deg canary vs original front-only diff | 10.64% |

At 90 degrees, the figure is still a narrow strip. At 135–180 degrees, diagnostic checkerboard colors dominate. This is NOT Japanese-animation quality.

## Gates NOT accepted

- Pixel/pose parity vs original Godot renderer: NOT TESTED.
- Genuine face/hair/clothing appearance across new views: FAIL (absent original art).
- Profile silhouette and volumetric anatomical credibility at 90 degrees: FAIL.
- Texture seams and skinned joint continuity: NOT TESTED.
- Complex 3D actions and IK: NOT TESTED.
- Japanese-animation visual quality: FAIL.

## Next milestone

Do not expand animation libraries yet. Obtain one LICENSED front/side/back model sheet with per-part correspondence, or author an independently reproducible controlled reference, and test side geometry and true multiview UV registration. Require original Godot front reference, seam quality, dynamic skinning and true profile silhouette. All binary data remains in Draft Releases; leave the experimental PR unmerged.
