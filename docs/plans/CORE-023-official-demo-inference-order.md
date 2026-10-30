# CORE-023 Task C — one real bounded official-demo inference attempt

ISSUED by supervisor 2026-10-30. This explicitly authorizes a single public-input
inference attempt beyond Task B metadata. Do not edit Task A/B code or reports.

Goal: test the actual ADR-003 M3 decomposition with the official See-through
ZeroGPU demo, rather than concluding it is blocked solely from absent local GPU.
Public input: source_A_aka_front.png from the license-clear Aka PSD by seagetch,
CC BY 4.0, SHA256 c22f2af3f426d4e79745e28a1244750d1c46b41d82f46570be63b9543aedb4e4.
Only this public image may be uploaded to the official demo; no private files.

Official host observed from upstream README/Space page:
https://24yearsold-see-through-demo.hf.space . Config GET was HTTP 200 in Task B.
Use maintained official gradio_client (https://www.gradio.app/docs/python-client/client),
not a hand-written inference protocol. Gradio 6 renamed hf_token to token; inspect
the installed client signature/API rather than guessing parameters. The official
guide supports Client, handle_file, view_api, submit, job.result(timeout), cancel.

You may create an isolated venv under out/core023/demo-runtime and install only
gradio_client and its normal PyPI dependencies there. Do not alter main project
requirements or dependency lockfiles. Do not inspect or reuse login tokens/cache;
run anonymously with explicit token=False when supported and
HF_HUB_DISABLE_IMPLICIT_TOKEN=1. No login, accounts, paid duplicate/rent/upgrade,
credentials, modified TLS checks, endpoint hopping or repeated inference attempts.

Use actual advertised /inference signature from view_api/config, record its public
parameter schema, and derive non-image arguments from advertised defaults.
Submit once using the verified source image. Bound waiting to 240 seconds and
cancel a still-queued job on timeout when possible. If auth/quota/network errors
block it, save the exact non-secret error and stop; do not claim site permanently
unusable, anonymous success, or successful decomposition from metadata alone.

Allowed new reusable code: experiments/reference-factory/try_official_decomposition.py.
All outputs/environment/downloaded results remain under out/core023/demo/ or
out/core023/demo-runtime/. Report JSON must include input/output hashes, exact
client versions, public API signature, elapsed time, actual stage reached, error
classification and no-production-approval flag. On successful PSD output, verify
magic/layer count using the already available psd-tools in the primary interpreter
and list actual layer names/bounds. Do not claim quality PASS merely for PSD layers.

Write docs/research/CORE-023-official-demo-attempt.md with actual results after
running the script. No Task A/B changes, commit/push or delegation. Never infer
human design approval or complete 360. Final response: actual command/exit,
observable result, output location, blockers and remaining quality evaluation.
