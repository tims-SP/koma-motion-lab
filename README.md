# Koma Motion Lab

## Current 2.75D research checkpoint — CORE-022 (2026-10-30)

- [Executed source/reference/structural-map report](docs/research/CORE-022-reference-factory-first-execution.md).
- [Successful Actions run](https://github.com/tims-SP/koma-motion-lab/actions/runs/41034480617): pinned Aka PSD/INX preparation, nine real generic-VRM angles, 45 structural maps, independent-process repeat, H.264 encode/decode.
- [Owner-only Draft Release evidence](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-34c8042721642fcd5cce): original source archive, actual rendered images, decoded review sheets, video and JSON. Git stays text-only.
- Work-vs-Actions comparison: all 45 PNG hashes match for this pair of environments; encoded MP4 hashes differ. No universal cross-machine/encoder determinism claim.
- [Actual MiniMax Code collaboration record](docs/research/CORE-022-mcode-collaboration.md): Work OAuth and real model verified; targeted shader-cache review completed, two broader review attempts timed out.
- Two fresh built-in imagegen profile candidates were generated and reviewed. Both fail requested canvas/margin gates; full A/B/C/D benchmark, approved Aka profile, per-view UV and continuous Aka 360° remain open. **Research checkpoint only, not character-production acceptance.**

## Current experimental preview — PROD-009 (2026-10-29)

- [GitHub Actions run #2](https://github.com/tims-SP/koma-motion-lab/actions/runs/40778781058): **RENDERED, QUALITY GATE FAILED**.
- [DRAFT Release preview](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-8d225fef6491014e9a15) (repository owner access): source-action video, eight experimental common-pose video, contact sheet, JSON report and Rive RML rig scaffold ZIP.
- Source artwork, generated videos, screenshots and RML assets are **Release-only**. Git history is text-only, enforced in CI and `.gitignore`.
- **Independent audit FAILED**: [inspection run](https://github.com/tims-SP/koma-motion-lab/actions/runs/40781670993) sampled 36 actual frames and found the prone pose mostly outside the viewport, sit cropped, and the original rig ZIP missing Bone/Mesh/Skin nodes. Rig packaging has since been fixed in code, but a replacement release must be revalidated. **Do not treat the previous draft release as accepted.**
- Videos are **Rive mesh-baked experiments**, not an editable native Rive animation transfer or original-Spine-runtime fidelity claim. A signed `.riv` was not exported.
- [PROD-009 report](docs/production/PROD-009.md).

## Current production milestone — PROD-008 (2026-10-29)

**Spine 4.2.36 game asset -> Rive weighted Mesh motion bake** has run successfully in the headless Linux Actions pipeline. The last passing Actions run is [#31](https://github.com/tims-SP/koma-motion-lab/actions/runs/40773868508).

- One real character (`300401_hongnujian`) from [Reverse-1999-CN-Asset](https://github.com/myssal/Reverse-1999-CN-Asset).
- Source binary decoded into 85 bones, 101 source mesh attachments and 8 source actions; the Rive conversion currently handles a **51-mesh subset, including 27 weighted meshes and 843 vertices**.
- Four original actions (`idle_room`, `walk`, `sleep`, `hit`) were transformed by original bone rotate/translate/scale/shear channel samples and rendered as **Rive** frame sequences + temporary MP4 clips (12 frames each).
- **Not yet a complete or lossless conversion:** IK, constraints, source Bezier easing, FFD, slot switching and source Spine-runtime parity are not yet implemented.
- The upstream repo contains copyrighted game assets without a root redistribution license. No source art / derived game video is distributed through public Actions artifacts.

Detailed findings: [PROD-008](docs/production/PROD-008.md) · [Production workflow](.github/workflows/spine-to-rive-video.yml).


Experimental/validation repository for [koma-motion](https://github.com/tims-SP/koma-motion). This is **not** the production repository.

## RIVE-RIG-001 — Agent-first, no-editor rigging gate

This lab tests whether Rive's official Linux CLI can create, inspect, verify, and render animation projects without the Rive Editor. The first GitHub Actions run installs the official Rive CLI on an ephemeral Ubuntu runner, records its version and binary hash, scaffolds a known-good project, gathers rigging/schema documentation, and attempts a headless screenshot.

**Important:** A successful CLI smoke test is **not** proof of automatic rigging. Automatic bone hierarchy, mesh triangles, per-vertex skin weights, deformation, and a complete multi-pose character remain independent acceptance gates.

### Run

Go to **Actions → RIVE-RIG-001 — CLI probe → Run workflow** (or push changes to the workflow/scripts).

Download `rive-rig-001-evidence-<run-number>` from the Actions run. Evidence includes:
- official installer SHA-256 (not redistributing the proprietary CLI executable);
- Rive CLI version and diagnostic logs;
- generated scaffold, RML, CLI rigging schema/docs queries;
- verification/build logs, screenshot when supported;
- `summary.md` with PASS/FAIL/NOT_TESTED claims.

### Decision rules

1. Never claim automatic rigging succeeded based only on `rive create`, `--verify`, or screenshot.
2. Capture CLI errors as experiment evidence; do not silently mask missing support.
3. Do not store login credentials, access tokens, proprietary binaries, or giant generated artifacts in git.
4. Use Rive CLI/RML as the first test subject. Retain Spine and other auto-rig solutions as fallbacks.
5. This repository is public: generated evidence must contain no personal content or credentials.

Official references: https://rive.app/docs/cli/getting-started , https://rive.app/agents
