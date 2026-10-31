# CORE-023 work order — mcode executes, supervisor accepts

Status: ISSUED, 2026-10-30. Base branch feature/koma-25d-core-021,
base commit 564a07e9b3a5ed2e722ec8069c80ba7db33da002.

Read AGENTS.md, ADR-003 sections 14 and 22, the CORE-022 report, and
experiments/reference-factory/audit_candidates.py before implementation.

## Task A — deterministic candidate canonicalization

The previous two generated profiles exist in experiments/reference-factory/out/candidates/:
pilot-A-001.png and pilot-C-001.png. Obtain their expected SHA256 values from the
committed evidence/local-2026-10-30/candidate-manifest.json, never invent a hash.
Original identity exists at
out/identity/source_A_aka_front.png. Verify these inputs against prior recorded
hashes before any processing; never overwrite original/source files.

Implement a small offline Pillow/NumPy canonicalization tool inside
experiments/reference-factory. This is explicitly deterministic image processing,
not AI redrawing. Use one versioned dedicated config, leaving contract.json and
the existing 45-map structural renderer untouched.

Required behavior:
- Explicit --input-dir/--output-dir or equivalent injectable paths for independent tests.
- Same 1024x1024 opaque white canvas and minimum 48-pixel diagnostic-ink margin
  for source identity plus A/C. Fit the ENTIRE source canvas using uniform scale
  and letterboxing; no foreground-based crop, local warp, inpainting or redesign.
- One affine source→canonical and inverse matrix, explicit edge-coordinate domain
  with pixel centers at i+0.5, declared resampling/alpha/color handling and tool versions.
- Preserve original bytes; output new versioned derivative names. Record parent
  SHA256, original framing FAIL, derivative SHA256 and config/algorithm identity.
- Frame PASS is separate from anatomy/identity/angle/style/human approval; all
  untested artistic gates remain NOT_TESTED or MANUAL_REVIEW_REQUIRED.
  Never mark APPROVED/GOLDEN, never replace earlier acceptance records, keep
  benchmark ranking NONE_ACCEPTED and full A/B/C/D NOT_TESTED.
- Fail closed on missing required input, hash mismatch, blank candidate, invalid
  transform/config or insufficient resulting margin. Do not silently skip candidates.
- Emit a source/A/C before-and-after contact sheet and JSON report.
- Add meaningful small unittest coverage for coordinate round trip, original-byte
  preservation, deterministic output, missing/hash-mismatch/blank failures,
  framing checks and no artistic promotion. Run the tests and actual tool.

Allowed code changes: new canonicalization tool/config/tests; focused README
addition explaining this stage. Write runtime outputs only under out/core023/.
Do not change existing source hashes, original images, structural main.js,
contract.json, source topology/UV, requirements or dependency lockfiles.

## Execution and reporting boundary

Use native mcode local file/shell tools to implement and run the task. Do not
delegate to another agent, inspect auth/config/credentials, install packages,
delete existing work, commit/push, or write to the production repository.
Do not create/approve hidden design or claim 360 completion. If blocked, report
the exact failed operation. Final response must list edited files, commands,
actual output locations, tests and remaining failures. The supervisor independently
inspects diffs, reruns the program/tests and reviews images before acceptance.

## Follow-up feasibility check after Task A

Next open asset gate is ADR-003 M3: benchmark semantic decomposition against real
Aka layers. After Task A is independently accepted, inspect the actual upstream
See-through implementation and its checkpoints/runtime; do not invent a PSD
splitter or count manually selected original layers as an AI decomposition result.
