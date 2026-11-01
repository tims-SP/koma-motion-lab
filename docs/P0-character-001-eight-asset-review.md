# P0 · Character 001 eight-artwork source quality review

Date: 2026-11-01. Local isolated-container visual inspection and independent pixel checks. The eight incoming PNGs remain unmodified.

## Source scope

Four separate 1254×1254 RGBA character views: front, face-left 90°, face-right 90°, rear. Four distinct isolated drawings: anatomical left eye, anatomical right eye, side nose and smiling mouth. These are **design references**, not yet ArtMesh-ready source layers. This batch includes no approved ±45° original paintings.

## Technical image findings

| Source | Native ≥32-alpha margin L/T/R/B (px) | Border pixels ≥32 at bottom | Alpha≥1 tiny components (1–9px) | Design status |
|---|---|---:|---:|---|
| Front | 238/1/245/0 | 768 | 1283 | Identity reference |
| Facing left profile | 310/8/249/0 | 476 | 1002 | Anatomical-side rework |
| Facing right profile | 213/8/300/0 | 517 | 600 | Anatomical-side rework |
| Back | 233/1/233/0 | 750 | 774 | Rear-hair reference |
| Left eye | 130/346/40/297 | 0 | 625 | Whole-eye design only |
| Right eye | 48/305/173/328 | 0 | 524 | Whole-eye design only |
| Profile nose | 389/216/438/215 | 0 | 233 | Re-author to match face |
| Smile mouth | 231/581/231/424 | 0 | 1758 | Re-author to match face |

All files decode as RGBA and have transparent corners. The four torso portraits intentionally continue off the bottom edge: suitable for bust-angle study, but insufficient for filling/rigging anatomy under the crop. Character hair reaches the top boundary with little safety margin. Sparse, nearly transparent pink/red pixels form false fragments near hair, eye and lip edges; a normal checkerboard preview is insufficient to certify compositing quality. Many apparently opaque original pixels have alpha 253 rather than 255, which requires a later straight-alpha compositing/halo gate.

Hair paint statistics (heuristically masked median RGB, lighting-sensitive; not a validated palette): front 194/118/150, face-left 212/132/167, face-right 208/128/168, back 196/112/149. Visual coherence needs a locked source paint palette and references.

## Semantic source gate

At front, the golden crossed hairclip and shield emblem are on character-local anatomical left, screen-right. Under the standard camera-facing rotation convention, the profile facing screen left exposes that anatomical left side, whereas a profile facing screen right exposes the character's anatomical right side. The face-left asset omits the clip while the face-right asset has the clip. This is a source-level identity mismatch and cannot be repaired by simply mirroring the PNG. Cross-view ear anchors, fringe and back-hair lock correspondences also need explicit semantic IDs.

Both isolated eyes contain the eye white, iris, pupil, highlights, eyelids and lashes in a single RGBA image, preventing independent gaze/blink ArtMesh behavior. The detached high-profile nose shape is substantially taller and more volumetric than the integrated character nose; the glossy lip asset likewise differs from the character's thin mouth stroke. These assets should be regenerated or reconstructed from matched face sources prior to layer binding.

## Current decision and next source tasks

**Acceptance state: source-only reference; no production-approved multiview rigging assets.** Existing local validation proves decoded RGBA and inspected source defects. It does not prove character identity against the approved Hero bytes, anatomical correspondence or concealed image completion.

Priority: (1) lock Hero and ±yaw anatomical convention; (2) reconcile side-specific crossed hairclip and uniform crest location, ears and hair locks; (3) create two genuinely distinct ±45° drawings; (4) re-author face-consistent nose and mouth; (5) separate eyes and other anatomy into layers with hidden areas painted; (6) validate composite reconstruction, alpha edges and held-out angles before using as ArtMesh/VDD production source.

Local detailed pixel statistics and an eight-image checkerboard montage are generated for inspection at `P0_eight_asset_audit/eight_asset_metrics.json` and `P0_eight_asset_audit/eight_asset_contact_sheet.png` in the isolated validation output.
