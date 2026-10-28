# UTTU Asset Reuse — Production Intake Decision

Date: 2026-10-28
Source: https://uttu.merui.net/
Scope: 2.75D Anime Studio / Koma Motion Lab personal, non-commercial exploration.

## Executive result

**NO-GO for direct Rive asset ingestion as of this verification.** UTTU is an unofficial fan archive, not an official reusable character asset supplier. Its Live2D and Spine rigs are not native Rive projects. Browsing and JS delivery work from a GitHub Actions runner, but a real headless Chromium page visit returned HTTP 403, so no model resource was loaded, no gameplay rig was imported, and no animation video was produced.

This is a compatibility and access verdict, **not** a conclusion that any specific private use is automatically forbidden.

## Grounded evidence

1. [UTTU About](https://uttu.merui.net/about/) says the archive is fan-made, unaffiliated with the game developer and game assets belong to **Bluepoch**. It names Live2D Cubism for character Live2D previews and Spine for Spine animations.
2. [Actions #1](https://github.com/tims-SP/koma-motion-lab/actions/runs/40694116891) verified five public pages from ordinary HTTP requests: homepage, sandbox, NPC Jailer, Fatutu profile, About — HTTP 200.
3. [Actions #4](https://github.com/tims-SP/koma-motion-lab/actions/runs/40694436688) inspected the actual publicly served UTTU Astro player JavaScript in memory. The player scripts include references to `.model3.json`, `.skel`, `.atlas` formats. No original source bundles or game assets were archived.
4. [Actions #5](https://github.com/tims-SP/koma-motion-lab/actions/runs/40694773423) launched headless Chromium on GitHub Actions. NPC page and Sandbox both responded HTTP 403; no model file succeeded, no canvas appeared. This browser test is **BLOCKED**, despite the GitHub Actions job infrastructure succeeding.

## Asset-level capability matrix

| Source format | Original engine | Can play without conversion (when legally held) | Native Rive import | Reusable for unrelated poses |
|---|---|---|---|---|
| `.model3.json` + `.moc3` + textures + motion/physics | Live2D Cubism | Yes, with Cubism SDK and compatible model set | **No established native importer** | Bounded by original authored parameters, geometry and views |
| `.skel` + `.atlas` + textures | Spine | Yes, matching Spine Runtime/version/license | **No established native importer** | Bounded by source rig, attachments and animations |
| Extracted sprite/atlas PNG | PNG / raster | Yes as a 2D image | **Yes as image**, rig not retained | Requires new mesh, bone and weights |
| Original layered PSD owned/licensed for edits | PSD/raster layers | N/A | **Rive can import PSD layers** | New rig/corrections needed |
| Screen-captured/recorded motion | Video/sprite frames | Yes as pre-rendered video/sprites if use authorized | Can import individual images; does not preserve source controls | Only recorded poses/timing |

The latter rows describe technical format possibilities, not a grant of third-party material rights.

## Hard blockers

- **Rights:** UTTU does not license Bluepoch's game model data to downstream users. Public access does not itself grant reuse rights.
- **Format:** Rive's published import formats do not include Cubism `.model3.json/.moc3` or Spine `.skel/.atlas`.
- **Access:** GitHub hosted browser receives HTTP 403 for the two sample pages. Do not disable access controls, spoof sessions or bypass site protections.
- **Motion coverage:** Finished game idle Live2D assets do not automatically offer sitting, deep crouches, body recline or new cinematic poses.

## Production decision

Do **not** implement a universal converter based on UTTU or import archived game assets into the public lab repository. Keep Rive as the leading agent-authored animation back-end for **original or appropriately licensed layered characters**, producing reference shots in the existing no-editor CI workflow. UTTU can act as **visual reference and engine-compatibility case study**.

If assets are legitimately available for the intended private use from an authorized source, consider a separate native playback adapter for Cubism/Spine or frame-baking only for existing motions. This is not a Rive replacement nor an editable Rive rig. Validate permissions before any reuse outside the strictly private test.

## Evidence and reproduction

- [Bounded public HTTP script](../../scripts/uttu_asset_probe.py)
- [Real Chromium browser script](../../scripts/uttu_browser_probe.py)
- [GitHub Actions workflow](../../.github/workflows/uttu-assets.yml)
- [Last runner evidence (JSON + Markdown only)](https://github.com/tims-SP/koma-motion-lab/actions/runs/40694773423/artifacts/12818402886)
- Official reference: https://docs.live2d.com/en/cubism-sdk-manual/model-web/
- Official reference: https://esotericsoftware.com/spine-player
- Official reference: https://rive.app/features

**Production readiness status: BLOCKED for using UTTU characters directly in Rive.**
