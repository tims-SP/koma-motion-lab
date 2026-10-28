# RIVE-RIG-001 — actual experiment record (2026-10-28)

## Scope

All experiments executed with GitHub Actions on `ubuntu-24.04`, without opening Rive Editor. Official Rive CLI version **1.8.0** was installed on disposable runners; CLI binaries are **not** committed or redistributed. The lab is public; no private model assets or credentials are included.

## Execution record

| Run | Outcome | Evidence |
| --- | --- | --- |
| [#1](https://github.com/tims-SP/koma-motion-lab/actions/runs/40689957576) | FAIL | Rive installation succeeded but libEGL.so.1 was missing; not a Rive feature failure |
| [#2](https://github.com/tims-SP/koma-motion-lab/actions/runs/40690132521) | PASS | Linux dependencies fixed; CLI create/verify/compile/headless PNG/schemas |
| [#3](https://github.com/tims-SP/koma-motion-lab/actions/runs/40690323763) | PASS | Bone, RootBone, Mesh, MeshVertex, Weight, IK schemas captured |
| [#4](https://github.com/tims-SP/koma-motion-lab/actions/runs/40690504041) | PASS | Official CLI bundled rigging documents and samples enumerated |
| [#5](https://github.com/tims-SP/koma-motion-lab/actions/runs/40690718862) | PASS | Real RML syntax, Tendon bind poses, packed weights confirmed |
| [#6](https://github.com/tims-SP/koma-motion-lab/actions/runs/40690993436) | FAIL | First vector rig missed required root Rive/Backboard; corrected by using official scaffold |
| [#7](https://github.com/tims-SP/koma-motion-lab/actions/runs/40691220888) | PASS | Two-bone skinned **vector** arm, 0/45/90/135°; verify/build/inspect/PNG all exit 0 and no inspect problems |
| [#8](https://github.com/tims-SP/koma-motion-lab/actions/runs/40691615761) | FAIL | Test harness shell newline typo (not Rive); fixed |
| [#9](https://github.com/tims-SP/koma-motion-lab/actions/runs/40691792698) | PASS | PNG pixel checks detect nonblank distinct actual renders for all four poses |

## Confirmed capabilities

- CLI runs in headless Linux GitHub Actions after installing EGL/GLES/X11 libraries.
- RML authored without the Editor creates valid RootBone, Bone, Skin, Tendon, PointsPath and per-vertex Weight objects.
- The built Rive file preserves six weighted path vertices, two Tendons and the actual skinned vector shape, with no errors reported by `rive inspect --summary`.
- Positioning the forearm at 0°, 45°, 90° and 135° changes rendered pixels; pose outputs are nonblank and pairwise distinct.

Pixel-change counts relative to 0°: 45° = **4,171**, 90° = **4,934**, 135° = **5,188**. The four screenshots are 480x320 RGBA PNGs.

## What is **not** proven

- Auto generation of joints/mesh from character art, transparent PNGs or layered PSDs.
- Image `Mesh` and UV deformation (the accepted fixture uses a skinned vector `PointsPath`).
- CLI access to Rive Editor Auto-Trace / Auto-Weights algorithms.
- Automatic weighting of clothing/hair/joints at anime production quality.
- IK, dynamic action timeline, image-shape occlusion, natural bend, or full-character rig.
- High-quality anime aesthetic, benchmark automation cost, or fully offline signed release export.

## Next gate — RIVE-RIG-002

1. Generate a permissively usable synthetic RGBA limb image *inside CI* (no private art needed).
2. Use official `rive docs assets` and `rive docs rigging` to author an actual **Image + Mesh + ContourMeshVertex + Weight + Skin + Tendon** fixture.
3. Validate that image pixels deform under the two-bone chain, and that all four pose renders are nonblank/distinct.
4. Replace hand-authored vertex weights with a small deterministic weight generator, validate against a known pose.
5. Only then attempt full character layer decomposition + bone placement + automatic rig corrections; do not call the existing vector smoke test 'automatic rigging'.

## Reproduction

- Workflow: [RIVE-RIG-001](../../.github/workflows/rive-rig-001.yml)
- [CLI probe](../../scripts/rive_probe.sh)
- [Weighted vector arm](../../scripts/rive_weighted_arm.sh)
- [PNG image pixel verification](../../scripts/assert_pose_pixels.py)
- [Successful evidence artifact, #9](https://github.com/tims-SP/koma-motion-lab/actions/runs/40691792698/artifacts/12817143308)

Status: **CLI environment PASS; coded vector-bone/skin PASS; pixel motion PASS; image auto-rig NOT_TESTED.**
