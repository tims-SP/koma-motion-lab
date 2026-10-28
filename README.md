# Koma Motion Lab

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
