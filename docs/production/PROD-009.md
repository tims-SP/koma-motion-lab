# PROD-009 — Rive preview delivery via GitHub DRAFT Release

Status: IMPLEMENTED_PENDING_CI (final status must be read from GitHub Actions and release assets)

## Scope
Source: [myssal/Reverse-1999-CN-Asset](https://github.com/myssal/Reverse-1999-CN-Asset), fixed commit 45e75248ba3b25053fd32e63ab13c2f9f54dd9df,
character 300401_hongnujian, room.skel (Spine 4.2.36).

Only code and structured **text** belong in the Git tree. Never commit .png, .mp4, .riv, .zip, source .skel, textures, build artifacts or binaries. The workflow uses an ephemeral runner for source artwork and intermediate frames and uploads ONLY the final previews/rig archive to a GitHub DRAFT Release owned by the lab repository.

## Launch

Automatic on changes to .github/workflows/prod009-preview-release.yml; manual via Actions > PROD-009 release preview > Run workflow.

The workflow installs the same upstream Spine 4.2 parser and official Rive CLI used in PROD-008. It produces:

- 01-source-actions-rive-baked.mp4 — source idle_room, walk, sleep, hit sampled against original time coordinates (up to 3 sec each). **This uses source bone transform curves with incomplete Spine constraints/Bezier handling, NOT official Spine runtime reference.**
- 02-common-poses-rive-baked.mp4 — neutral, raise_hand, wave, bow, lean_back, squat, sit, prone. These are automated **experimental** skeletal poses: visual plausibility is NOT guaranteed and there is no generated missing artwork.
- 03-common-poses-contact-sheet.png — eight middle-frame previews.
- rive-native-rig-scaffold.zip — Rive CLI/RML source rig + texture with native Bone/Mesh/Skin setup. **Does not contain native Rive animation tracks.**
- 04-prod009-metadata.json — automated measured diagnostics.

Release status defaults to DRAFT; the owner can view/download it while it is not publicly published. Do not publish without separately assessing distribution of third-party art.

## Engineering truth
- The MP4s are Rive CLI renders of source-weighted Mesh vertices per frame.
- A successful MP4 is not proof of native editable Rive animation, full Spine physics/constraints, or original-runtime pixel parity.
- No authenticated Rive CLI .riv export is performed; official Rive may require a login/export entitlement. The rig scaffold is an RML asset, **not** a finished signed .riv.
- Missing Spine IK, Path, Transform, FFD, attachment and draw-order semantics persist from PROD-008.
- All source asset files and RML with original textures remain in the runner/release, not tracked by Git.
- The preview build must fail before release on missing/invalid output. The workflow verifies all expected files exist.

## Acceptance
1. Git repository tracked files remain text only.
2. GitHub Actions build passes.
3. GitHub DRAFT Release exists and has both videos, contact sheet, rig scaffold, and diagnostics.
4. User manually watches videos, reports visual artifacts, and confirms whether subsequent pose repair/true native animation conversion is worth pursuing.

Results here should be amended after the run is verified, not inferred from the presence of a workflow file.
