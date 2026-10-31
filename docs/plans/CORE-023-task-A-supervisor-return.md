# CORE-023 Task A — supervisor revision after independent tests

The standard-mode implementation produced actual derivatives and 12 tests pass
when independently rerun (27.932 s). The CLI hit its timeout before a final reply.
Do not claim the whole deliverable accepted yet. The supervisor found additional
real defects; fix them using mcode tools. No Task B file changes.

1. Fully transparent indexed-color PNG is mishandled: creating P-mode image with
   palette[0]=black and PNG transparency=0 then calling load_rgb returns black,
   whereas the promised alpha-over-white behavior requires white. Composite all
   source modes through RGBA over white before RGB conversion. Add this regression
   plus blank transparent-candidate rejection with consistent expected hash.
2. Identity expected hash currently comes from mutable out/identity/reference_manifest.json,
   so replacing both the image and that manifest bypasses prior-source verification.
   Use committed evidence/local-2026-10-30/source_freeze.json identity_sha256 as
   authority, checking runtime manifest consistency too. Update synthetic fixtures
   and prove a forged runtime manifest cannot bypass the committed hash.
3. canonicalize_file must reject source/output aliases (same path or symlink)
   before writing. Add a test proving originals remain byte-identical on rejection.
4. Replace the hand-written NumPy cubic resampler with maintained Pillow
   Image.transform(..., Image.Transform.AFFINE, inverse_edge_coefficients,
   resample=Image.Resampling.BICUBIC, fillcolor=white). No extra half-pixel shift:
   the supervisor independently tested a 4x4 source marker at index (1,1), scale=4,
   translation=4; inverse tuple (0.25,0,-1,0,0.25,-1) produces output block x/y
   8..11 and centroid 9.5 exactly as edge-coordinate math predicts. Do not build
   another image resampling engine. Keep a small documented guard inset if needed.
5. Source identity derivative must carry SOURCE_TRUTH parent provenance and an
   explicit derived-reference role, not be labeled GENERATED_CANDIDATE like A/C.
   Never promote candidate art; ranking remains NONE_ACCEPTED.
6. Validate actual supported config schema/types/ranges and reject unsupported
   transforms or color settings rather than recording ignored settings as honored.
7. Preserve rejected v1 output/config already snapshotted under out/core023/rejected-A1.
   Use a new config/canonicalization-v2.json and derivative v2 names. Update tests
   and README default command to the accepted algorithm. Do not remove original
   input files, rejected evidence or Task B files.

Allowed implementation changes: canonicalize_candidates.py, its config(s),
tests/test_canonicalize.py and focused README stage text. Runtime outputs only
out/core023/. Run raw unittest without a tail/tee pipeline hiding exit code,
then actual source/A/C inputs and repeat in a separate output directory. Report
test result, margins, exact outputs and any remaining blocker. No installs,
source hash/UV edits, inference, credentials, delegation, commit/push.
