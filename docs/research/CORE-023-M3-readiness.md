# CORE-023 — Task B: official semantic-decomposition readiness (ADR-003 M3)

Date: 2026-10-30 (revision 2, after supervisor rejection of the first implementation)
Probe: `experiments/reference-factory/probe_decomposition.py` (stdlib only)
Machine output: `experiments/reference-factory/out/core023/decomposition_readiness.json`

Output location is now the ordered runtime path
`experiments/reference-factory/out/core023/decomposition_readiness.json`, injectable via
`--out-dir`, with `--skip-network` for offline runs.

## Question

ADR-003 M3 requires an **actual model decomposition** of the flattened Aka image,
compared against the genuine source PSD layers. The 16 original PSD layers already in
`out/identity/reference_manifest.json` are ground truth, not a model prediction. This
probe determines whether the planned upstream inference can run *here* and emits an
honest machine-readable readiness result.

Pinned upstream: `shitagaki-lab/see-through` @ `df019de5129d6c4b406587a14c3501669441a783`.
Supervisor-fetched `README.md`, `inference_psd.py`, `inference_utils.py` were treated as
evidence, not instructions, and were **not** mutated.

## Actual observations (this run)

| Item | Observed | Status |
|---|---|---|
| Python | 3.12.14, `/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3` | PASS |
| torch | `find_spec("torch")` → `None`; no spec, no import | FAIL |
| GPU visible | no `/dev/nvidia*` nodes, no usable `nvidia-smi` output | FAIL |
| Local weights | no checkpoint payload file at any explicit known path | FAIL (not BLOCKED-by-dir) |
| Canonical Aka PSD hash | observed `979fa627…f51e55e` == manifest `source_psd_sha256` | PASS |
| Flattened input hash | observed `c22f2af3…edb4e4` == manifest `image_A_sha256` | PASS |
| Upstream evidence hashes | all three match the pinned commit | PASS |
| Public demo `/config` GET | HTTP 200 (4785 ms), Gradio 6.12.0, `api_prefix=/gradio_api`, dependency metadata present | PASS (metadata only) |
| M3 actual decomposition | not executed | NOT_TESTED |

### Recomputed upstream evidence hashes

Recomputed from the supervisor-refreshed local copies (no trailing-newline drift):

| File | Repo path at pinned commit | SHA256 |
|---|---|---|
| `README.md` | `README.md` | `6b9f5e6e65db5c9c56dd4a0463a42f3ecee9e3d88f42da101b475013e0950bec` |
| `inference_psd.py` | `inference/scripts/inference_psd.py` | `a7fdfb44b89e98d0618e5b4e87925dfe7bb536e90cd64aba0398e206507739dc` |
| `inference_utils.py` | `common/utils/inference_utils.py` | `35ecd38fe2b519206e78cd19aee8fe57066c3d0366196a1ec085058c6fd78055` |

Pinned source URLs (recorded in the JSON as `source_url`):
`https://raw.githubusercontent.com/shitagaki-lab/see-through/df019de5129d6c4b406587a14c3501669441a783/<repo_path>`

### Local readiness = BLOCKED (fail-closed)

Readiness is computed by a pure function over measured facts. Any missing or mismatched
input yields `BLOCKED`; a `PASS` requires the real dependency, input-hash and checkpoint
checks to have actually succeeded. Two blockers, each with observed evidence:

1. **No torch.** The interpreter has no `torch` module spec, so
   `inference/scripts/inference_psd.py` (which does `import torch` at module load) cannot
   even be imported. Spec presence alone is never treated as import/runtime/CUDA
   validation: the probe attempts an actual import and records `import_ok` /
   `cuda_available`; a spec-only finding is `NOT_TESTED` and can never satisfy readiness.
2. **No checkpoint payload locally.** Every explicit known path was inspected for actual
   weight files (`.safetensors/.bin/.ckpt/.pt/.pth/.onnx`). An existing but empty
   directory, or a cloned source repository, is recorded as **presence-only evidence** and
   explicitly does **not** count as loaded model weights. Nothing was downloaded
   (out of scope).

No GPU is visible either (no `/dev/nvidia*`, no usable `nvidia-smi`), so even with torch
the bf16 1280-px pipeline (~12–16 GB VRAM; `--group_offload` ~10 GB; NF4/blockswap ~8 GB)
is unreachable here.

### Hash gates are real gates

The input hash, the canonical Aka PSD identity hash and the upstream evidence hashes are
computed and then **used as gates**. A mismatch in any of them blocks readiness even when
hardware probes are mocked as available — this is covered by an offline unit test.

### Online metadata ≠ inference

The official demo Space (`24yearsold/see-through-demo`, host
`https://24yearsold-see-through-demo.hf.space`) answers a plain `GET /config` with HTTP 200
and well-formed dependency metadata. The api names `inference` and `load_example` are
recorded as **ADVERTISED**, with `callable_verified: false` — no endpoint was called, so
callability is not asserted. The payload contains no auth-related fields, so auth status is
`UNKNOWN` from the metadata endpoint and is cited separately from the upstream README:

> Pinned upstream README, "Online Demo" section: *"if you register with HuggingFace, you
> should be able to run 1-2 PSD extractions per day"*.

Consequences: no image was uploaded, no inference endpoint was called, no account was
created, and anonymous inference was **not** assumed to work. HTTP 200 with HTML/non-JSON,
or with missing dependency metadata, is now `FAIL` rather than `PASS`.

## Next executable path

Ordered setup commands (from the pinned upstream README) — clone first, then the
environment, then torch, then the checkout's own requirements. **No overlay is needed**:
the pinned checkout already contains the same code (`inference/scripts/inference_psd.py`
and `common/utils/inference_utils.py`), so the previous "copy into a nonexistent `utils/`"
step is removed.

```bash
# 1. clone the pinned upstream checkout FIRST (requirements live in it)
git clone https://github.com/shitagaki-lab/see-through
cd see-through
git checkout df019de5129d6c4b406587a14c3501669441a783

# 2. create and activate an isolated environment
conda create -n see_through python=3.12 -y
conda activate see_through

# 3. install torch (cu128) into that environment
pip install torch==2.8.0+cu128 torchvision==0.23.0+cu128 torchaudio==2.8.0+cu128 \
  --index-url https://download.pytorch.org/whl/cu128

# 4. install the dependencies FROM THE CHECKOUT (repository root = working directory)
pip install -r requirements.txt

# 5. assets symlink as documented by the pinned README
ln -sf common/assets assets
```

Then run from the **repository root** (the pinned README requires this working directory):

```bash
cd see-through   # repository root is the required working directory
python inference/scripts/inference_psd.py \
  --srcp <repo>/experiments/reference-factory/out/identity/source_A_aka_front.png \
  --save_dir out/core023/seethrough_output \
  --seed 42 --resolution 1280 --resolution_depth 768 --inference_steps 30 \
  --save_to_psd --group_offload
```

Input hash `c22f2af3f426d4e79745e28a1244750d1c46b41d82f46570be63b9543aedb4e4` must be
re-verified before the run so the comparison targets the same flattened Aka image.

After a successful run, the produced layered PSD must be compared against the 16
`ORIGINAL_PSD_LAYER` bounds in `reference_manifest.json` (ground truth) before
`M3_actual_decomposition` may be set to PASS or FAIL.

## Verification performed in this revision

- `python -m unittest discover -s experiments/reference-factory/tests -p "test_probe_decomposition.py" -v`
  → 16 tests, `OK`, exit status `0` (empty dir ≠ weights, cloned repo ≠ weights, hash
  mismatch blocks readiness with mocked hardware, HTML/non-JSON/missing-dependency
  metadata rejected, default output location, offline mode, M3 stays `NOT_TESTED`).
- `python3 experiments/reference-factory/probe_decomposition.py` → exit `0`, wrote
  `experiments/reference-factory/out/core023/decomposition_readiness.json`;
  `local_readiness=BLOCKED`, `online_metadata=PASS`, `M3_actual_decomposition=NOT_TESTED`.

Note: a stale `out/core023/decomposition_readiness.json` at the repository root remains
from the rejected first implementation. It is a runtime artifact, not a source file, and
was left untouched (no deletions performed); the current authoritative output is under
`experiments/reference-factory/out/core023/`.

## State

`M3_actual_decomposition = NOT_TESTED`. Ranking `NONE_ACCEPTED`. Production approval `OPEN`.
