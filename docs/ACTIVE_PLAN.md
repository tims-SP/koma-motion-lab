# ACTIVE PLAN — 2.75D Anime Studio / Koma Motion Lab

**SINGLE SOURCE OF TRUTH | 2026-11-01 | MVP-009 | STATUS: PLANNED_NOT_IMPLEMENTED**

## Chosen route

**Euclid-inspired multiview 2.5D hybrid, with Plan B as the FIRST and ONLY active implementation.** One consistent character's independent key-view layered art determines face and silhouette; local 3D anchors and view-dependent depth/occlusion provide spatial structure; semantic correspondences and VDD produce intermediate views. Small 3D nose/ear/scalp patches are **conditionally allowed only if Plan B fails with reproducible visual + cost evidence**. Full 3D mesh and single-UV skin are NOT active requirements.

Current predecessor MVP-008 is **FAIL_VISUAL** and cannot be repurposed as a passing proof of B or a finished 360 engine.

## Authoritative document order (highest first)

1. `docs/ACTIVE_PLAN.md` — current authority and stop rules.
2. `docs/experiments/MVP-009-Euclid-route-decision.md` — approved route B first / 3D patch fallback.
3. `docs/experiments/MVP-009-plan-b-multiview-depth.md` — concrete B00-B08 technical implementation.
4. `docs/experiments/MVP-009-gates-and-tasks.json` — machine-readable status and gates.
5. `docs/experiments/MVP-009-head360-representation-plan.md` — background constraints, subordinate where conflicting.

**Everything in `docs/archive/` is historical and has no planning authority.** The old workflow definitions live there as disabled artifacts. The original `experiments/mvp002` render code is historical evidence, **not** current model code.

## Next steps and hard stop

| Order | Task | No-Go |
|---|---|---|
| 1 | T00 snapshot previous real FAIL, freeze source and baselines | cannot reproduce baseline |
| 2 | T01 same coverage/depth logic Beauty/ID/Depth/Alpha + malicious fault injections | negative controls do not FAIL or 0-overlap falsely PASS |
| 3 | T02 independent same-character right-side 0/45/90 authored layered refs + 30/60/75 holdouts; stable anatomical IDs | no real nose/chin/ear/hairline profile or no independent evidence |
| 4 | T03B implement minimal head with view-dependent depth, 3D anchors and ArtMesh; 0..90 true camera-relative views | false side profile, depth reversal, invalid mask, ghost face or failed heldout comparison |
| 5 | T04 B go/no-go after exact structural + visual review and measured key-view repair cost | any FAIL stops before 360; trigger local 3D patch A/B only on documented B no-go |
| 6 | 180/270 and dense 90/270 head 360 tests, then independent head action | head360 unverified |
| 7 | full body bone/IK/foot contact and cinematic output | head/pose not visually accepted |

**Only the head 0→90° test is immediately authorized.** No full-body render/FX, no global architecture rewrite, no automatic B→A switching, no reliance on stale old CI.

Head profile crop >=512 px; explicit independent reference source SHA, per-part anatomical landmarks, fixed pose, original side silhouette, 30/60/75 heldout angles, accurate face/ear/front/back hair occlusion, paired Beauty/ID/Depth/Alpha pixel QA, full contiguous transition review. Machine numeric PASS **never** overrides FAIL_VISUAL.

## Repository maintenance

- Lab: `tims-SP/koma-motion-lab` (only write target).
- Production: `tims-SP/koma-motion` (no write).
- Historical docs and disabled old workflows: [archive index](archive/pre-mvp009-2026-11-01/README.md).
- Preserve old source tests only as reproducible references and keep large binaries / licensed art out of Git.
- Any proposed route change requires an explicit new user decision, a side-by-side evidence report and updating THIS file **before** coding.

Current tasks have not passed any MVP-009 stage; do not infer status from old MVP-008 CI.
