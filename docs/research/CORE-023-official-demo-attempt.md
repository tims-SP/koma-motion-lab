# CORE-023 Task C — official-demo inference attempt (actual result)

Date: 2026-10-30
Author: agent (Task C, executed under `docs/plans/CORE-023-official-demo-inference-order.md`)
Target: `https://24yearsold-see-through-demo.hf.space` (official See-through ZeroGPU demo)

## Outcome

**FAIL — blocked by the official demo's anonymous ZeroGPU quota.** The attempt reached the
real server, was accepted for execution, and was then refused at the GPU-allocation stage.
No PSD was produced, so **no decomposition result was obtained**.

This is not a claim that the demo is permanently unusable. It is a statement that a single
anonymous attempt, at this moment, could not obtain a GPU allocation.

## Exact command and exit

```
HF_HUB_DISABLE_IMPLICIT_TOKEN=1 \
  out/core023/demo-runtime/venv/bin/python \
  experiments/reference-factory/try_official_decomposition.py --timeout 240
```

Exit code: `5` (failure during the wait/submit stage). Elapsed: `23.21 s`.

Report JSON: `out/core023/demo/official_demo_attempt.json`
Downloads directory: `out/core023/demo/downloads/` (empty — no payload was served)

## Exact error (non-secret, as returned by the app)

```
AppError: You have exceeded your ZeroGPU quota (180s requested vs. 26s left).
Try again in 0:34:34. Authenticate with a Hugging Face token for more quota -
https://huggingface.co/settings/tokens
```

Error classification recorded: `QUOTA_ERROR`. Stage reached: `WAIT`.
Job cancel was attempted after the failure, per the order.

## Observable result

The submission was genuinely made and the space genuinely processed it far enough to
evaluate a GPU budget: it requested `180s` of ZeroGPU time and only `26s` remained in the
anonymous per-visitor quota. The refusal is therefore an **anonymous quota ceiling**, not a
schema error, not an auth wall on the endpoint, and not a broken request. The payload was
never computed, so `outputs` is empty and no layer structure could be inspected.

## Advertised public API signature (from the Space's own `/config`)

Only one named endpoint is advertised: `/inference`.

| parameter | type | has default | default | label |
|---|---|---|---|---|
| `image` | filepath (`ImageData`) | no | – | Upload image (non-square images will be padded) |
| `resolution` | float | yes | `768` | Resolution (numeric value between 768 and 1280) |
| `seed` | float | yes | `42` | Seed (numeric value between 0 and 9999) |
| `tblr_split` | bool | yes | `false` | Split arms, eyes and ears into left/right layers |

Returns: `Download layered PSD`, `Separated layers`.

The submitted call used the advertised defaults verbatim for all non-image arguments
(`resolution=768`, `seed=42`, `tblr_split=false`) and `handle_file(...)` for the image.
No parameter value was guessed.

## Input actually uploaded

- Path: `experiments/reference-factory/out/identity/source_A_aka_front.png`
- SHA256: `c22f2af3f426d4e79745e28a1244750d1c46b41d82f46570be63b9543aedb4e4`
- Matches the pinned expectation from the order: **yes**
- Bytes: `405265`
- License: CC BY 4.0, PSD by `seagetch` — public and license-clear

Only this public image was uploaded. No private file was sent.

## Client / environment versions

- `gradio_client` **2.7.2** (official maintained package, installed from PyPI into an
  isolated venv — the global environment and project requirements/lockfiles were untouched)
- `httpx` 0.28.1, `huggingface-hub` 2.4.0, Python 3.12.14
- venv: `out/core023/demo-runtime/venv`
- Anonymous mode: `Client(..., token=None)` with `HF_HUB_DISABLE_IMPLICIT_TOKEN=1`;
  `HF_TOKEN`/`HUGGING_FACE_HUB_TOKEN` removed from the environment. No local credential
  cache was read or reused.

Note on API shape: in this installed client the parameter is `token: str | None`, not a
`hf_token`/`token=False` boolean, so "explicit anonymous" was expressed as `token=None`
plus `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` rather than `token=False`.

## PSD verification

**Not applicable.** No `.psd` was returned, so there is no magic-byte check, no layer
count, and no layer-name/bounds listing to report. `psd-tools 1.10.9` is confirmed
available in the primary interpreter and ready for the post-success check, but it had
nothing to read.

## Constraint compliance

| constraint | status |
|---|---|
| Anonymous, no login/account/credentials | PASS |
| No payment, no rent/upgrade/duplicate space | PASS |
| No modified TLS checks | PASS (default `ssl_verify=True`) |
| No endpoint hopping | PASS (single advertised host + `/inference`) |
| Exactly one inference submission | PASS |
| Bounded wait ≤240 s, cancel attempted on failure | PASS |
| Output confined to `out/core023/demo/` + `out/core023/demo-runtime/` | PASS |
| No install into global env; no requirements/lockfile change | PASS |
| No Task A/B code or report edits | PASS |
| No commit, no push, no delegation | PASS |
| Production approval inferred / 360 claimed | **NO** (`production_approval: false`) |

## Blockers and remaining work

1. **Blocker:** the anonymous ZeroGPU quota at the official demo is exhausted
   (26 s left against a 180 s request). The order forbids login, tokens, paid quota and
   repeated attempts, so the correct action here is to stop and report. A future attempt
   after the quota window resets could still be attempted, but that would be a *new*
   attempt and needs fresh authorization.
2. **Still unvalidated:** whether the demo's ADR-003 M3 decomposition actually produces a
   usable layered PSD for this input. Nothing about decomposition quality, layer naming,
   or bone/mesh suitability can be claimed from this run.
3. **Still unvalidated:** the downstream RIVE-RIG-001 skinning/deformation gates, which
   depend on obtaining an actual PSD.
4. Local GPU inference and the official HF demo were the two compute paths checked
   this round. Local execution remains `BLOCKED` (no torch, no visible CUDA).
   The upstream README also lists a ModelScope demo; that service was not tested.

## Supervisor follow-up

The historical single request used `token=None` with implicit tokens disabled
before importing the client. The reusable runner has since been hardened to use
explicit `token=False`, reject alternate endpoints and remove the source-hash
override. Offline boundary tests cover these guards. No second inference was
submitted, and the historical request JSON has been retained unchanged.
Any later one-shot task may be issued by the supervisor under the ongoing user
request; this report does not create a separate requirement to ask the user again.

## Files

- New script: `experiments/reference-factory/try_official_decomposition.py`
- Report JSON: `out/core023/demo/official_demo_attempt.json`
- Runtime (venv, packages): `out/core023/demo-runtime/`
- This document: `docs/research/CORE-023-official-demo-attempt.md`
