# Koma Motion Lab — MVP-009 (single active route)

**Only active route:** **Euclid-inspired multiview 2.5D / Plan B FIRST**. Keep true independent key-view anime head art, per-part 3D anchors, view-dependent layered depth and masks; use VDD for art-driven correction. Small 3D geometry patches are a **conditional fallback** after a documented B failure, **not** a prerequisite and **not** permission to return to a global single-UV surface.

**Current status: PLANNED / NOT IMPLEMENTED / NOT ACCEPTED.** MVP-008 full-body 360 renders are historical engineering experiments, with **FAIL_VISUAL**. Any prior CI pass is NOT proof of correct profile or real 360° layers.

## Single current navigation

1. **[ACTIVE_PLAN — source of truth](docs/ACTIVE_PLAN.md)** — authoritative priority, active document order and stage gates.
2. **[MVP-009 Euclid route decision](docs/experiments/MVP-009-Euclid-route-decision.md)** — architecture selection: B first, only localized 3D fallback if needed.
3. **[MVP-009 Plan B detailed implementation](docs/experiments/MVP-009-plan-b-multiview-depth.md)** — head-only implementation & strict 0→90° acceptance.
4. **[MVP-009 machine task/gate matrix](docs/experiments/MVP-009-gates-and-tasks.json)** — all gates currently NOT_RUN; no invented PASS.
5. **[MVP-009 supporting representation plan](docs/experiments/MVP-009-head360-representation-plan.md)** — implementation and negative-control checklist.

## Execution contract

- Work **only** in `tims-SP/koma-motion-lab`; production repo `tims-SP/koma-motion` must not be changed before review and promotion.
- T00 baseline **then T01 truthful QA** (shared beauty/ID/depth/alpha and negative tests) **then T02 independently authored 0°,45°,90° head references**; then build **T03B head-only**. Do not start 360° full-body videos, IK, or FX before 0→90° profile actually passes.
- Strict acceptance: a genuine **90° side profile**, coherent ear/nose/chin/hairline, semantic correspondence, correct per-view occlusion, matching diagnostic pixels, independent held-out 30/60/75° references, and visual review of contiguous frames.
- All actual outputs bind to source commit / source asset SHA. Engineering tests are not visual acceptance.
- Existing `experiments/mvp001`, `experiments/mvp002`, `scripts/` and original assets/tests remain **read-only historical baselines**, not the new architecture. New head work goes in `experiments/mvp002/src/head009/` and dedicated head009 scripts. Reuse infrastructure only after validating it against the new spec.
- **All pre-MVP-009 plans, reports, and legacy workflow definitions are archived**, not authoritative: [historical index](docs/archive/pre-mvp009-2026-11-01/README.md). Archived workflows are NOT active under `.github/workflows/`.
- Do not revive Rive-first, Godot-first, old MVP-002, MVP-006, MVP-007, MVP-008 or 3D single-UV as current plan merely because old docs or past successful Actions exist.

This README intentionally contains no obsolete plan details or legacy result rankings.
