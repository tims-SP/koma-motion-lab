# CORE-022 — First executed Reference Factory checkpoint

2026-10-30. Research only, on `feature/koma-25d-core-021`, following ADR-003.

The source-acquisition → identity-reference → deterministic structural-render →
QA → encoded/decoded preview path was actually executed in the Work environment.
This is a reference-preparation checkpoint, not a completed Aka 2.75D character.

## Actual sources

- Aka original PSD at inochi2d-docs revision
  `593c657855d5679f01443ef311346298fd25e117`, SHA-256
  `979fa62702b25f8af25414637d9ba6c36cbc9eb03bfa0c454470c73bdf51e55e`.
- Aka original INX at example-models revision
  `cd95dd00ddff63b1f7d2b84a19914c3c70d05945`, SHA-256
  `dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f`.
  Artist/rigger seagetch, CC BY 4.0. All 76 native ArtMeshes indexed with source
  node UUIDs and immutable source mesh/UV hashes. No mesh editing performed.
- pixiv three-vrm source revision `3caf7a21ee68f0d5dfa363ab3d577450bbf60136`,
  `VRM1_Constraint_Twist_Sample.vrm`, SHA-256
  `12c2b97e95e700783a6a550dc0eee2d7880aeedccef9ae67bc4c5a2f0f2631a2`.
  Embedded author pixiv Inc.; VRM Public License 1.0 plus embedded use conditions,
  modification/redistribution allowed. **Not CC0.** This generic human has no fox
  ears and its shape is not registered to Aka.

## Implemented and observed

`experiments/reference-factory/prepare.py` verifies every source hash, reuses the
existing genuine PSD-part extractor, freezes 16 source-part examples, retains
native topology identity, and records exact rounded resize/paste coordinate
matrices with inverse. Coordinate round-trip maximum error: 0.0 px in the local
check; this does not imply lossless image cropping/resampling.

Source PSD expression is open mouth. It is explicitly not called neutral and
does not certify the full native INX renderer's default composition.

The structural renderer loads the actual VRM through upstream `@pixiv/three-vrm`
and Three.js GLTFLoader, excludes source Body meshes for HEAD_ONLY, rotates the
character about +Y, and uses a fixed orthographic camera. +90° points the nose
to image right. Nine angles: 0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180.

Each angle emits beauty, binary silhouette, diagnostic linear view-depth,
camera-space normals and exact source-part IDs: **45 actual PNGs**. Source hair
continues through the camera's lower boundary; this head crop is not a complete
long-hair silhouette. RGB8 depth has only 10–17 occupied values per angle, and
is a diagnostic reference, not precision depth for surface fitting.

Repeated renders in the same browser and **two independent Chromium processes**
produced identical hashes for all 45 images. Environment: Three.js r180,
Chromium 141.0.7390.37, ANGLE Vulkan SwiftShader. This is an environment-scoped
determinism claim, not cross-GPU pixel identity or source-art fidelity.

## Failures caught and corrected

The first diagnostic silhouette accidentally retained source texture color.
After explicit color replacement, a second defect caused the part-ID shader to
reuse the silhouette program because `onBeforeCompile` closures share function
text. Per-pass/per-category `customProgramCacheKey` fixed program identity.

QA now verifies exact binary silhouette values, exact ID colors, identical
coverage between structural passes, grayscale depth with real geometric
variation, unit-length normals, head top/side framing, source/contract/file
hashes, and per-image repeat equality. A deliberate corrupted ID-color test
was rejected **even when the image's manifest hash was updated to match**.

## Real video and visual review

Generated an actual 1024×560, 24 fps, 108-frame H.264. It shows **nine held
structural anchors, each for 12 frames**, rather than continuous motion.
SHA-256 `7cf6d7ade76015dae0d771712f85553f1e692a599c57b607b86834a548447b9f`.
Decoded actual final H.264 frames 0/48/96, assembled and opened the decoded
contact plus the 45-map contact. Confirmed true front/profile/rear progression,
generic sample appearance and consistent normal/occlusion maps.

## Actual image generation pilot

Two fresh built-in imagegen calls were executed, with actual inputs and prompts
retained. A: Aka front identity only. C: Aka front + genuine PSD detail plate +
generic exact-profile task example + silhouette, explicitly forbidding copying
the generic character's long brown hair or identity. These are **one candidate
per arm**, not the ADR's multi-candidate A/B/C/D benchmark. B/MV-Adapter and D/
lineart-transfer have not run. No causal method ranking is possible.

Both outputs visibly retained orange bob, fox ears, leaf, neckband and one
near eye in a right-facing profile. Both have inferred hidden anatomy and
uncalibrated camera. Both are **1254×1254 instead of requested 1024×1024**, with
ink-threshold top margin 25/27 px instead of at least 48 px. Absolute framing
gate: FAIL. Ranking: NONE_ACCEPTED. No source or Golden asset was overwritten.
Provider exposed no exact model version, seed or request ID; those are recorded
as unavailable instead of invented. Prompt and reference/output hashes retained.

## Acceptance matrix

| Gate | Status |
|---|---|
| Pinned source acquisition and actual source identity/detail extraction | PASS |
| Explicit coordinate camera/color contract and coordinate inverse | PASS, research profile |
| Nine-angle structural-map generation and separate-process hash repeat | PASS, generic VRM only |
| Encode/decode actual structural preview and direct review | PASS |
| Generic reference registered to Aka anatomy/fox ears | NOT_TESTED |
| Full source bank with Midori and distinct structures | NOT_TESTED beyond one sample |
| See-through decomposition benchmark against original layers | NOT_TESTED |
| Full multi-candidate A/B/C/D trial | NOT_TESTED |
| Two pilot generated-image framing gates | FAIL |
| Human-approved profile/hidden design and Golden version | NOT_TESTED |
| Full-front native default source parity | NOT_TESTED; CORE-021 remains ear-only |
| Multi-view UV, shallow shells, rig/IK and continuous Aka 360° | NOT_BUILT |

Next: normalize generation framing through an explicit canonicalization step,
build/validate Aka-compatible skull/fox-ear structure, execute the decomposition
and complete controlled candidate comparison, then obtain design acceptance
before freezing a Golden profile and building surface/UV correspondence.
