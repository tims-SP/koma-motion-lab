# PRE-MVP-009 HISTORICAL ARCHIVE — NOT ACTIVE

Snapshot from `ff0282eeb5099cc1ec2fd4e9f67161b7a0cd50eb`, archived on 2026-11-01. 
These documents and workflow YAMLs are retained for scientific reproducibility, failed QA evidence, Rive/Spine/Godot legacy experiments and historical decisions. **They are NOT instructions and should NOT be used to choose an active architecture.** Git history preserves the original file paths/contents at the snapshot SHA, so any old internal relative links can be inspected at that commit.

**Current active plan:** [../../../ACTIVE_PLAN.md](../../../ACTIVE_PLAN.md) (or repository `docs/ACTIVE_PLAN.md`).  
**Current active experimental route:** `MVP-009`, Euclid-inspired Plan B.

Archived files: **49** total (22 experiments, 7 production reports, 1 validation reports, 19 legacy workflow definitions).

Old workflows have been MOVED OUT of `.github/workflows`; GitHub Actions will no longer auto-trigger them from this branch. They can be restored manually for historical regressions, but require explicit authorization and must not count as MVP-009 acceptance.

## Historical source path mapping

- `.github/workflows/godot-005-engine-transfer.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/godot-005-engine-transfer.yml` (d7f6ef756d0776a4c2a3153d7d106fb03a18772b)
- `.github/workflows/godot-render-001.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/godot-render-001.yml` (b0b3105e0aaea3ffd2fef3f7dad1b2d9698818fb)
- `.github/workflows/mvp001-smoke.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/mvp001-smoke.yml` (de11671e708c5ff7366b550b851c245f042b2725)
- `.github/workflows/mvp002-integrated.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/mvp002-integrated.yml` (8e6e0dd4db61603e161975976d30411ba334fba2)
- `.github/workflows/mvp003-six-modules.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/mvp003-six-modules.yml` (574a08aaeac1babbc7bfa2f9d5e53361f2057b47)
- `.github/workflows/mvp006-360-acceptance.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/mvp006-360-acceptance.yml` (04facf1be52c9f5f205e325ad91a14c94bcf98b5)
- `.github/workflows/mvp007-publish-preview.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/mvp007-publish-preview.yml` (23b7a7a6008043a21ffd37dcb1ed76b528758e1f)
- `.github/workflows/mvp008-dynamic360.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/mvp008-dynamic360.yml` (6a32a8afa4c4560d8df0640de043078e9841e055)
- `.github/workflows/mvp008-review.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/mvp008-review.yml` (3f04a73c7695ac115f5f3de1990cf6df4fa4f2ce)
- `.github/workflows/prod009-audit-release.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/prod009-audit-release.yml` (e47c7b6d55267e14276428058f3d2fbe53d8f6df)
- `.github/workflows/prod009-preview-release.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/prod009-preview-release.yml` (1ffa069cb7d2c316c7cf642b076be03434c3caab)
- `.github/workflows/prod010-geometry-audit.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/prod010-geometry-audit.yml` (f607ad81bb9426868d8d18c2ccfa9f72d431358f)
- `.github/workflows/prod010-native-skin.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/prod010-native-skin.yml` (8c04191aaa693838aee6a9fcd6134bf83b265cd4)
- `.github/workflows/prod010-release-recheck.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/prod010-release-recheck.yml` (8433c31ed893b27fdd44c33b12de334a630b2f7a)
- `.github/workflows/reverse1999-production.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/reverse1999-production.yml` (987dba00991b14d4c08eb06427aecc030a4f0abe)
- `.github/workflows/rive-rig-001.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/rive-rig-001.yml` (4c3eb460c566142c5f8baf3e4d9737dcba697ff5)
- `.github/workflows/spine-atlas-uv-validation.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/spine-atlas-uv-validation.yml` (db3f776076e4a096f6a5b232448d07275e8a6ce8)
- `.github/workflows/spine-to-rive-video.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/spine-to-rive-video.yml` (16bbee953d08635118ded0db8510083055cd14cf)
- `.github/workflows/uttu-assets.yml` → `docs/archive/pre-mvp009-2026-11-01/workflows/uttu-assets.yml` (c0288e847a504e549b4ce3f27611b3d64d0973a1)
- `docs/experiments/MVP-001-M1-plan.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-001-M1-plan.md` (47846f5f143a6e4364a9c638d4be93c2e06f12a0)
- `docs/experiments/MVP-001-V2-master-plan.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-001-V2-master-plan.md` (ebd9c1c18aca24e3a539b544ad02351873bf3ae2)
- `docs/experiments/MVP-001-V2-status.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-001-V2-status.md` (fc77dae60b63d60d7cb5dda49ea428f32fec1fd2)
- `docs/experiments/MVP-001-assets-research.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-001-assets-research.md` (e42d19cb621ccbe78349f4758b6d7e0dce20dd16)
- `docs/experiments/MVP-001-multiview-anime-plan.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-001-multiview-anime-plan.md` (e5cf56ae72304f6d88c7e942f94a1a222781d173)
- `docs/experiments/MVP-002-core-first.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-002-core-first.md` (67c3042aad5516ba7e4c12d35067b88d7e928eb0)
- `docs/experiments/MVP-003-six-modules-result.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-003-six-modules-result.md` (c3bf9a25e54c229954a26a1a07088a381b542f4e)
- `docs/experiments/MVP-004-rgba-result.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-004-rgba-result.md` (4e0c559f88cc2e4ae938083619e725c678306f3c)
- `docs/experiments/MVP-005-detailed-art-and-closeup.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-005-detailed-art-and-closeup.md` (be5e4b826a11162cc8fd37718a1baed5efc935b0)
- `docs/experiments/MVP-006-360-acceptance-protocol.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-006-360-acceptance-protocol.md` (8e6e701ae19f62229674a19343c94c515ce7ceec)
- `docs/experiments/MVP-006-360-acceptance-v1.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-006-360-acceptance-v1.md` (0f1ae1b62d61f1d1bd4a67acf5d298a0e62f23a9)
- `docs/experiments/MVP-006-360-run-status.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-006-360-run-status.md` (052bcc426620459a6fff8b589b9798f1d4210b61)
- `docs/experiments/MVP-007-360-core-final-review.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-007-360-core-final-review.md` (8cc297c00f5baae88ed1a77ac091a1445fd09ff7)
- `docs/experiments/MVP-008-P0-root-cause-geometry-audit.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-008-P0-root-cause-geometry-audit.md` (0994fe827779d14390f8f91afd48aef3212f9136)
- `docs/experiments/MVP-008-V05-contour-review.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-008-V05-contour-review.md` (99b9ac346131ffa98400530fc0ce687c656a964d)
- `docs/experiments/MVP-008-dynamic360-plan.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-008-dynamic360-plan.md` (96653a9bcafdc65cef8ba8b4fadeca12afc0a438)
- `docs/experiments/MVP-008-dynamic360-result.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-008-dynamic360-result.md` (613384cccbc93e2818c6ecb6090e1e306f70ada4)
- `docs/experiments/MVP-008-visual-review.json` → `docs/archive/pre-mvp009-2026-11-01/experiments/MVP-008-visual-review.json` (96014b3e66c4f4ceab09fb73e3e14dbde9701a22)
- `docs/experiments/REVERSE1999-PRODUCTION-001.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/REVERSE1999-PRODUCTION-001.md` (fd558bd704dda473db6261eff6b50ee1d59eb64d)
- `docs/experiments/RIVE-RIG-001.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/RIVE-RIG-001.md` (2495a712a057df0b9681eb4e5df9f2ddc6dfb4c8)
- `docs/experiments/RIVE-RIG-002.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/RIVE-RIG-002.md` (076bf2748bb68246a77a6ed751896ee9bea3f327)
- `docs/experiments/UTTU-PRODUCTION-INTAKE.md` → `docs/archive/pre-mvp009-2026-11-01/experiments/UTTU-PRODUCTION-INTAKE.md` (633e4dea06c956e0bfbc8517c4eb6923d886f183)
- `docs/production/PROD-008.md` → `docs/archive/pre-mvp009-2026-11-01/production/PROD-008.md` (db76734d85416d126e372df93a63d8bed451367b)
- `docs/production/PROD-009.md` → `docs/archive/pre-mvp009-2026-11-01/production/PROD-009.md` (67fa45dc5e31cc023d4a7569b32d113186d7951c)
- `docs/production/PROD-010.md` → `docs/archive/pre-mvp009-2026-11-01/production/PROD-010.md` (1bdce6484f87cc600502938102f0f2861647557f)
- `docs/production/REVERSE1999-PROD-001.md` → `docs/archive/pre-mvp009-2026-11-01/production/REVERSE1999-PROD-001.md` (b7b398c2fe8f4d95e8c064dce769c1c4d8a7c61b)
- `docs/production/REVERSE1999-PROD-002.md` → `docs/archive/pre-mvp009-2026-11-01/production/REVERSE1999-PROD-002.md` (fc5994c26fd1bb9f450c54e028ddd1562e7e7dc1)
- `docs/production/SPINE-RIVE-PROD-002.md` → `docs/archive/pre-mvp009-2026-11-01/production/SPINE-RIVE-PROD-002.md` (311dd4677b5804aadc1308636adbf052f4c2f3e6)
- `docs/production/SPINE-RIVE-PROD-004.md` → `docs/archive/pre-mvp009-2026-11-01/production/SPINE-RIVE-PROD-004.md` (d94a8343cb4bf218d6e1f4b1b9affd1e3e58ebff)
- `docs/validation/RENDER-001.md` → `docs/archive/pre-mvp009-2026-11-01/validation/RENDER-001.md` (8f97ea4fdbe7e206ec1947f1bee6f14efa861b02)

## Reproducibility

Retrieve the original repository tree at commit [ff0282eeb5099cc1ec2fd4e9f67161b7a0cd50eb](https://github.com/tims-SP/koma-motion-lab/tree/ff0282eeb5099cc1ec2fd4e9f67161b7a0cd50eb) to run a historical experiment. Historical code under `experiments/mvp001/`, `experiments/mvp002/` and `scripts/` is retained as a baseline. It has no status as an accepted Euclid/360 implementation.
