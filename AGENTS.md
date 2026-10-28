# Lab Agent Contract

This repository is the **validation lab** for `tims-SP/koma-motion`. Do not write to the production repository from lab experiments.

## Mandate
- The human only directs and reviews; agents do all authoring, rigging, rendering, debugging and iteration.
- Prefer tested upstream GitHub code, official Rive docs, research papers and reference books over new engines.
- Use Rive CLI/RML first; do **not** assume Rive Editor-only operations have CLI equivalents.
- Maintain clear status distinctions: `PASS`, `FAIL`, `NOT_TESTED`, `BLOCKED`.
- A valid `.riv` scaffold or screenshot is *not* a successful auto-rig.
- Never commit Rive CLI binaries, third-party proprietary art, secrets, or huge generated files.
- Only export public-safe evidence to GitHub Actions artifacts.

## RIVE-RIG-001 acceptance gates
1. **CLI gate**: install/version/create/verify/headless screenshot all work on Actions.
2. **Authored-rig gate**: agent writes a weighted bone/mesh rig using RML without GUI.
3. **Skinning gate**: agent produces per-vertex weights from layered assets without manual painting.
4. **Deformation gate**: screenshots at straight, 90-degree, deep bend show no severe artifacts.
5. **Revision gate**: agent edits a failing pose and reproduces the new output without GUI.

Run `bash scripts/rive_probe.sh` in an environment with Rive CLI installed. Read `out/rive-rig-001/result.json` and corresponding logs before claiming results.

Sources:
- https://rive.app/docs/cli/getting-started
- https://rive.app/agents
- https://rive.app/use-cases/character-animation
