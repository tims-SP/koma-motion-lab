# CORE-023 final boundary correction — small, offline, mcode execution

The supervisor verified A2's 23 passing tests but found three empty-string config
settings are still accepted: transform, color_handling, coordinate_domain. Their
SUPPORTED_* constants are strings; `value not in string` tests substring membership.
Use exact equality for these scalar contracts, and test empty/partial strings.
Do not relax existing config tests or rewrite the module.

The actual Task C one-shot request is complete and was QUOTA_ERROR (180 s needed,
26 s available). Preserve its JSON/report and do not run inference again. Its
executed source has been snapshotted in repo-root out/core023/demo/executed-runner-v1.py.
Harden the reusable runner before acceptance:
- Remove --allow-source-hash-mismatch entirely; only the pinned public input hash
  may proceed to upload. Do not provide an escape hatch for private/arbitrary input.
- Restrict --space to DEFAULT_SPACE_URL (official host), failing before any client
  or upload action on other endpoints.
- Use explicit token=False in Client to prohibit implicit token resolution. Although
  installed gradio_client 2.7.2 annotates token as str|None, its build_hf_headers calls
  huggingface_hub.get_token_to_send(bool|str|None), which explicitly handles False
  before any token-cache operation. Keep HF_HUB_DISABLE_IMPLICIT_TOKEN=1 too.
- Add a small offline test file for invalid source hash / unsupported endpoint /
  absence of the override / explicit anonymous client kwargs, without importing
  gradio_client or doing network calls. A pure parser/kwargs helper is acceptable.
- Add a short note to the C report: actual historical attempt used token=None
  with implicit tokens disabled before import, reusable runner now hardened, no
  second inference performed. Never rewrite historical observed request data.

Allowed changes only canonicalize_candidates.py, tests/test_canonicalize.py,
try_official_decomposition.py, a new tests/test_official_demo_boundaries.py, and the
short Task C report note. Do not touch Task B, workflow, requirements or inputs.
Run all tests raw. No network GET, installs, inference, credentials, delegation,
commit/push. Keep this narrow: exact string checks and request-boundary guards.
