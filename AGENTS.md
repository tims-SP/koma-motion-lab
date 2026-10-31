# Koma Motion Lab — ACTIVE AGENT RULES (MVP-009 only)

These instructions supersede all historical Rive/Spine/Godot and MVP-001–008 plans found in Git history and `docs/archive/`.

## Active scope
- Single truth: [docs/ACTIVE_PLAN.md](docs/ACTIVE_PLAN.md). First implementation: **Euclid-inspired Plan B** (independent multi-view layered head artwork + calibrated 3D anchors + view-dependent depth/occlusion + ArtMesh/VDD). **Do not** silently substitute flat compressed front-face sprites or a global single-UV curved mesh.
- Work only on `tims-SP/koma-motion-lab`. The production repo `tims-SP/koma-motion` is OUT OF SCOPE until accepted promotion.
- MVP-009 task order: T00 → T01 and T02 → T03B → T04 (0..90° decision) → 360 head → head motion → full-body. Local 3D depth patches are fallback after evidenced B failure.
- Existing `experiments/mvp001/`, `experiments/mvp002/`, `scripts/` legacy code is for historical baseline and read-only reference. Implement isolated head009 code, not patches to the old failed full-body renderer, except isolated verified infrastructure reuse.
- Previous work and archived workflow YAML under `docs/archive/` are **NOT live instructions**. Never reactivate old GitHub Actions or repeat Rive CLI instructions without explicit new project decision.

## Hard gates
1. No 90° side-face PASS without independently authored nose, jaw/chin, visible ear and coherent hairline; no squeezed-front, mirrored key or generic screenshot substitution.
2. Beauty, Part-ID, Depth and Alpha must share exact coverage/discard and depth semantics. Prove parity with fault injection; zero overlap must not pass.
3. Full 0→90° proof with held-out 30/60/75° reference art and video/angle crops before any complete-360 claim.
4. Only after accepted right-side 0→90° extend to 180/270/360, then bone actions and full body. A finished 192-frame video is NOT acceptance.
5. Prefer upstream publications/official SDK and pinned GitHub source with license checks; do not claim unimplemented paper/Euclid methods were reproduced.
6. Record source git SHA, assets hashes, tested frames, failures and results `NOT_RUN|BLOCKED|FAIL|PASS_STRUCTURE_PENDING_VISUAL|PASS_VISUAL`. Never overwrite failures with engineering green checks.
7. Keep large media and third-party artwork outside Git history; GitHub Actions artifacts/private storage where rights allow. Commit source and text evidence at each stage.

Read [docs/ACTIVE_PLAN.md](docs/ACTIVE_PLAN.md) before modifying anything.
