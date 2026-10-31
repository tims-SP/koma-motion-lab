# Legacy MVP-002–008 renderer — ARCHIVED BASELINE

**NOT THE CURRENT TECHNICAL PLAN.** This folder holds the original TypeScript/Three.js planar ArtMesh, temporal renderers, shader experiments and their known defects. These files are retained for reproducible regression comparisons, not as an approved 360° character implementation.

- Current plan and execution source: [../../docs/ACTIVE_PLAN.md](../../docs/ACTIVE_PLAN.md).
- Euclid-inspired Plan B: [../../docs/experiments/MVP-009-plan-b-multiview-depth.md](../../docs/experiments/MVP-009-plan-b-multiview-depth.md).
- Previous technical failure: [../../docs/archive/pre-mvp009-2026-11-01/experiments/MVP-008-P0-root-cause-geometry-audit.md](../../docs/archive/pre-mvp009-2026-11-01/experiments/MVP-008-P0-root-cause-geometry-audit.md).

**Known unsolved:** false side profile from face contour squash, flattened camera-facing ArtMesh, fake face/front-hair depth order, inconsistent beauty/ID shader masking, and visually unacceptable side turn. Previous CI/PASS labels only cover their own limited tests.

**Do not run old `npm run render` as an acceptance test or extend legacy `integrated.ts` to hide those defects.** New work is isolated under `src/head009/` and dedicated scripts, with independent side art and rigorous QA. The old code remains available for exact baseline replay when explicitly required.
