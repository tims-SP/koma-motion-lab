# Koma Motion Lab

## Latest result — MVP-005 detailed four-view RGBA + face close-up (2026-10-31)

**[Successful real render #41194923884](https://github.com/tims-SP/koma-motion-lab/actions/runs/41194923884)** · **[Actual 6-second MP4](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-29dfef1130728dc814a9/integrated-6sec.mp4)** · **[16 transparent source-art tiles](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-29dfef1130728dc814a9/key-art-contact.png)** · **[MVP-005 engineering and honest visual QA](docs/experiments/MVP-005-detailed-art-and-closeup.md)**

The same TypeScript/Three.js six-module character now has authored 512×512 RGBA per-angle layers, additional eye/face/hair/jacket/skirt details, proper premultiplied-alpha shader cross-view sampling, and a true close-up near the end of the original 6s / 144-frame action clip. **ENGINEERING PASS, ANIME-VISUAL QUALITY FAIL.** These are original programmatically authored Canvas art layers, *not* independent polished multi-view illustrations. The next stage must obtain actual professionally styled consistent keyview artwork instead of further polishing generic programmatic gradients/strokes.

## Current result — MVP-004 registered multi-view RGBA art (2026-10-31)

**[Successful full video render #41193779622](https://github.com/tims-SP/koma-motion-lab/actions/runs/41193779622)** · **[Corrected 6s MP4](https://github.com/tims-SP/koma-motion-lab/releases/download/untagged-23fb286da4223fc7629f/integrated-6sec.mp4)** · **[16 transparent key-art PNGs and clip](https://github.com/tims-SP/koma-motion-lab/actions/runs/41193779622/artifacts/13039753564)** · **[Engineering and visual QA](docs/experiments/MVP-004-rgba-result.md)**

The single original TypeScript 2.75D character scene now uses four keyed transparent RGBA paintings per part and registered canonical UVs while retaining VDD, anchor-based articulation, 3D IK, alpha-tested occlusion, art-directed lighting, and browser MP4. **PASS_ENGINEERING_TEXTURE_PIPELINE; VISUAL_QUALITY_FAIL** — input art is still simple hand-coded Canvas drawings, not polished anime layered illustrations. Do not start extra Spine/Live2D basic replay experiments; next improve real multiview illustration and facial/hand quality on this same character.

## Current result — MVP-003 six modules in ONE TypeScript shot (2026-10-31)

**[Successful actual browser render #41192559514](https://github.com/tims-SP/koma-motion-lab/actions/runs/41192559514)** · **[One-shot MP4 and contact sheet (owner Draft Release)](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-1950b50997738b4e881f)** · **[Honest engineering/visual QA report](docs/experiments/MVP-003-six-modules-result.md)**

One minimal original three-keyview, 12-part character runs through **360 yaw → 3D IK arm crossing torso depth → blink/VDD/local ArtMesh + animated art-shadow and particles** in a single deterministic 6s/144-frame 960×540 TypeScript render. **PASS_ENGINEERING_ONLY**. Real frame captures reviewed: **NOT high-quality Japanese anime art**; real multi-view RGBA texture registration, refined linework, complex alpha masks, complete skeletal animation still pending. Complex Reverse1999 assets remain optional references, not blockers. Legacy T00–T11/K0–K2 tests are not prerequisites.

## Current primary research track — MVP-002 core-first integrated TypeScript (2026-10-31)

**[Authoritative MVP-002 plan & results](docs/experiments/MVP-002-core-first.md)** · **[Successful integrated render](https://github.com/tims-SP/koma-motion-lab/actions/runs/41191491411)** · **[Three videos in Draft Release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-cbdcb29f362bf38e3849)**

Old study documents (historical, not prerequisites):

**[V2 master plan](docs/experiments/MVP-001-V2-master-plan.md)** · **[V2 task status](docs/experiments/MVP-001-V2-status.md)** · [Existing asset audit](docs/experiments/MVP-001-assets-research.md)

New direction: existing anime character assets first (Reverse-1999 Spine/Live2D), TypeScript-only own code, keyed layered 2.5D art + bone/IK + view-dependent deformation + art-directed light/FX. Goal: one consistent character package for 360-degree full-body turn, full-body action, and high-fidelity anime closeup.

M0 had a real **infrastructure-only** pass: [Actions 41188109729](https://github.com/tims-SP/koma-motion-lab/actions/runs/41188109729). T00–T11 of V2 are **CANCELLED AS PREREQUISITES**; MVP-002 integrated render is **PASS_ENGINEERING_RENDER_ONLY**, **VISUAL QUALITY NOT VERIFIED**. The legacy Rive/Spine/Godot runs below remain historical evidence, *not* dependencies or acceptance for the new track.

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
