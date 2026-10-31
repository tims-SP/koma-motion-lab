#!/usr/bin/env python3
"""CORE-023 Task B — bounded readiness probe for official see-through semantic decomposition.

Stdlib only. No installs, no downloads, no inference, no uploads, no credentials.
Default output: experiments/reference-factory/out/core023/decomposition_readiness.json

Statuses follow the lab contract vocabulary: PASS / FAIL / NOT_TESTED / BLOCKED.
Readiness is FAIL-CLOSED: any missing or mismatched input blocks a PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FACTORY_DIR = REPO_ROOT / "experiments" / "reference-factory"

# Ordered runtime output location (lab work order: write runtime outputs under
# experiments/reference-factory/out/core023/ — NOT the repository-root out/).
DEFAULT_OUT_DIR = FACTORY_DIR / "out" / "core023"
OUT_JSON_NAME = "decomposition_readiness.json"

UPSTREAM_DIR = FACTORY_DIR / "out" / "core023" / "upstream"
IDENTITY_DIR = FACTORY_DIR / "out" / "identity"
SOURCE_DIR = FACTORY_DIR / "out" / "source"

PINNED_UPSTREAM_COMMIT = "df019de5129d6c4b406587a14c3501669441a783"
PINNED_UPSTREAM_REPO = "shitagaki-lab/see-through"
PINNED_RAW_BASE = (
    "https://raw.githubusercontent.com/"
    + PINNED_UPSTREAM_REPO
    + "/"
    + PINNED_UPSTREAM_COMMIT
)

# Upstream evidence files fetched by the supervisor at the pinned commit, with the
# source path inside that checkout and the observed sha256 of the local copy.
UPSTREAM_EVIDENCE = {
    "README.md": {
        "repo_path": "README.md",
        "source_url": PINNED_RAW_BASE + "/README.md",
        "expected_sha256": "6b9f5e6e65db5c9c56dd4a0463a42f3ecee9e3d88f42da101b475013e0950bec",
    },
    "inference_psd.py": {
        "repo_path": "inference/scripts/inference_psd.py",
        "source_url": PINNED_RAW_BASE + "/inference/scripts/inference_psd.py",
        "expected_sha256": "a7fdfb44b89e98d0618e5b4e87925dfe7bb536e90cd64aba0398e206507739dc",
    },
    "inference_utils.py": {
        "repo_path": "common/utils/inference_utils.py",
        "source_url": PINNED_RAW_BASE + "/common/utils/inference_utils.py",
        "expected_sha256": "35ecd38fe2b519206e78cd19aee8fe57066c3d0366196a1ec085058c6fd78055",
    },
}

# Official model repository IDs, taken from the pinned upstream README and the
# argparse defaults of inference/scripts/inference_psd.py.
EXPECTED_CHECKPOINTS = {
    "repo_id_layerdiff": "layerdifforg/seethroughv0.0.2_layerdiff3d",
    "repo_id_depth": "24yearsold/seethroughv0.0.1_marigold",
    "sam_body_parsing": "24yearsold/l2d_sam_iter2",
}

# Explicit known paths only. No directory scanning of the user home.
KNOWN_CHECKPOINT_PATHS = [
    FACTORY_DIR / "models",
    FACTORY_DIR / "checkpoints",
    REPO_ROOT / "see-through",
    Path.home() / ".cache" / "huggingface" / "hub" / "models--layerdifforg--seethroughv0.0.2_layerdiff3d",
    Path.home() / ".cache" / "huggingface" / "hub" / "models--24yearsold--seethroughv0.0.1_marigold",
    Path.home() / ".cache" / "huggingface" / "hub" / "models--24yearsold--l2d_sam_iter2",
]

# A directory only counts as loaded weights when it actually contains checkpoint
# payload files. An empty directory or a cloned source repo is NOT weights.
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".ckpt", ".pt", ".pth", ".onnx")
INDEX_NAMES = ("index.json", "diffusion_pytorch_model.safetensors")

DEMO_SPACE = "24yearsold/see-through-demo"
DEMO_HOST = "https://24yearsold-see-through-demo.hf.space"
DEMO_CONFIG_URL = DEMO_HOST + "/config"
DEMO_TIMEOUT_S = 20

README_AUTH_CITATION = (
    "Pinned upstream README (out/core023/upstream/README.md, 'Online Demo' section): "
    "'if you register with HuggingFace, you should be able to run 1-2 PSD extractions per day'. "
    "Authentication is therefore required by the upstream authors' own statement; the "
    "/config payload itself does not advertise auth fields, so auth status stays UNKNOWN "
    "from the metadata endpoint and is cited separately from this README."
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_python() -> dict:
    return {
        "executable": sys.executable,
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "status": "PASS",
    }


def detect_torch() -> dict:
    """Torch detection.

    Spec presence alone is NOT import/runtime/CUDA validation, so a spec-only
    finding is recorded as NOT_TESTED and can never satisfy readiness.
    """
    info = {
        "spec_found": False,
        "spec_origin": None,
        "version": None,
        "import_ok": None,
        "import_error": None,
        "cuda_available": None,
        "status": "FAIL",
        "note": "",
    }
    try:
        spec = importlib.util.find_spec("torch")
    except (ImportError, ValueError):
        spec = None
    if spec is None:
        info["note"] = "torch module spec not found; upstream inference/scripts/inference_psd.py imports torch at module load"
        return info
    info["spec_found"] = True
    info["spec_origin"] = spec.origin
    try:
        for meta in spec.submodule_search_locations or []:
            vfile = Path(meta) / "version.py"
            if vfile.is_file():
                for line in vfile.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.startswith("__version__"):
                        info["version"] = line.split("=", 1)[1].strip().strip("\"'")
                        break
            break
    except OSError:
        pass

    # Actual runtime check (importing is not installing).
    try:
        import torch  # noqa: PLC0415

        info["import_ok"] = True
        info["version"] = info["version"] or getattr(torch, "__version__", None)
        try:
            info["cuda_available"] = bool(torch.cuda.is_available())
        except Exception as exc:  # noqa: BLE001 - driver errors are informative
            info["cuda_available"] = False
            info["note"] = f"torch.cuda.is_available() raised: {exc}"
    except Exception as exc:  # noqa: BLE001
        info["import_ok"] = False
        info["import_error"] = f"{type(exc).__name__}: {exc}"
        info["status"] = "NOT_TESTED"
        info["note"] = "torch spec present but import/runtime/CUDA compatibility was not verified"
        return info

    info["status"] = "PASS"
    info["note"] = "torch imported successfully"
    return info


def detect_gpu() -> dict:
    """Detect a *visible* GPU without installing anything."""
    info = {
        "nvidia_smi_on_path": None,
        "nvidia_smi_version": None,
        "nvidia_device_nodes": [],
        "cuda_visible_devices_env": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "status": "FAIL",
        "note": "",
    }
    smi = shutil.which("nvidia-smi")
    info["nvidia_smi_on_path"] = smi
    if smi:
        try:
            out = subprocess.run(
                [smi, "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=15, check=False,
            )
            info["nvidia_smi_version"] = out.stdout.strip() or None
        except (OSError, subprocess.SubprocessError) as exc:
            info["note"] = f"nvidia-smi invocation failed: {exc}"
    try:
        info["nvidia_device_nodes"] = sorted(p.name for p in Path("/dev").glob("nvidia*"))
    except OSError:
        info["nvidia_device_nodes"] = []
    if info["nvidia_device_nodes"] or (info["nvidia_smi_version"] and info["nvidia_smi_version"].strip()):
        info["status"] = "PASS"
        info["note"] = "GPU device visible"
    else:
        info["status"] = "FAIL"
        info["note"] = "no NVIDIA device nodes under /dev and no usable nvidia-smi output"
    return info


# --------------------------------------------------------------------------
# weights assessment (presence-only evidence, never "ready" from a directory)
# --------------------------------------------------------------------------
def inspect_checkpoint_path(path: Path) -> dict:
    info = {
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
        "bytes": None,
        "weight_files": [],
        "index_files": [],
        "holds_checkpoint_payload": False,
    }
    if not path.exists():
        return info
    if path.is_file():
        info["bytes"] = path.stat().st_size
        if path.suffix.lower() in WEIGHT_SUFFIXES:
            info["weight_files"] = [{"name": path.name, "bytes": info["bytes"]}]
            info["holds_checkpoint_payload"] = info["bytes"] > 0
        return info
    weights: list[dict] = []
    indexes: list[str] = []
    try:
        for child in sorted(path.rglob("*")):
            if not child.is_file():
                continue
            if child.suffix.lower() in WEIGHT_SUFFIXES and child.stat().st_size > 0:
                weights.append({"name": str(child.relative_to(path)), "bytes": child.stat().st_size})
            elif child.name in INDEX_NAMES:
                indexes.append(str(child.relative_to(path)))
    except OSError:
        pass
    info["weight_files"] = weights
    info["index_files"] = indexes
    info["holds_checkpoint_payload"] = bool(weights)
    return info


def assess_weights(paths=None) -> dict:
    """Assess local weight readiness — PRESENCE-ONLY, never PASS.

    This probe inspects explicit known paths for checkpoint payload files and
    records exact names/bytes as observations. It performs NO model/index
    integrity check and NO load validation, so raw file presence can never
    enable a PASS: weights_complete is always False and readiness stays blocked
    until a real validation is run.

    FAIL-CLOSED: an existing but empty directory (or a cloned source repo)
    is presence-only evidence and never counts as loaded weights.
    """
    paths = list(KNOWN_CHECKPOINT_PATHS if paths is None else paths)
    inspected = [inspect_checkpoint_path(Path(p)) for p in paths]
    payload = [i for i in inspected if i["holds_checkpoint_payload"]]
    empty_dirs = [i for i in inspected if i["exists"] and not i["holds_checkpoint_payload"]]
    if payload:
        status = "NOT_TESTED"
        note = (
            "checkpoint payload file(s) present at "
            + ", ".join(i["path"] for i in payload)
            + "; presence only — this probe performs no model/index integrity or load "
            "validation, so the weights are NOT verified complete and readiness stays blocked"
        )
    elif empty_dirs:
        status = "BLOCKED"
        note = (
            "path(s) exist but contain no checkpoint payload files "
            + ", ".join(i["path"] for i in empty_dirs)
            + "; an existing directory or cloned source repo is NOT loaded model weights"
        )
    else:
        status = "FAIL"
        note = "no see-through checkpoint payload at any explicit known path"
    return {
        "status": status,
        "note": note,
        "checkpoint_payload_found": bool(payload),
        "weights_complete": False,
        "payload_paths": [i["path"] for i in payload],
        "paths_inspected": inspected,
        "expected_checkpoints": dict(EXPECTED_CHECKPOINTS),
    }


# --------------------------------------------------------------------------
# identity / hash gates
# --------------------------------------------------------------------------
def verify_aka_identity(identity_dir: Path | None = None, source_dir: Path | None = None) -> dict:
    identity_dir = IDENTITY_DIR if identity_dir is None else identity_dir
    source_dir = SOURCE_DIR if source_dir is None else source_dir
    manifest_path = identity_dir / "reference_manifest.json"
    res = {
        "manifest_path": str(manifest_path),
        "manifest_present": manifest_path.is_file(),
        "status": "FAIL",
        "note": "",
        "recorded_source_psd_sha256": None,
        "observed_source_psd_sha256": None,
        "match": None,
    }
    if not manifest_path.is_file():
        res["note"] = "reference_manifest.json missing"
        return res
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        res["note"] = f"manifest unreadable: {exc}"
        return res
    recorded = manifest.get("source_psd_sha256")
    psd = source_dir / manifest.get("source_psd", "tutorial-aka.psd")
    observed = sha256_file(psd)
    res["recorded_source_psd_sha256"] = recorded
    res["observed_source_psd_sha256"] = observed
    res["psd_path"] = str(psd)
    res["psd_present"] = psd.is_file()
    res["part_count"] = manifest.get("part_count")
    res["character"] = manifest.get("character")
    if recorded and observed:
        res["match"] = recorded == observed
        res["status"] = "PASS" if recorded == observed else "FAIL"
        res["note"] = (
            "canonical Aka PSD hash matches prior recorded manifest hash"
            if recorded == observed
            else "canonical Aka PSD hash DIFFERS from prior recorded manifest hash"
        )
    else:
        res["note"] = "could not compare hashes (missing manifest entry or missing PSD file)"
    return res


def check_input_hash(identity_dir: Path | None = None) -> dict:
    identity_dir = IDENTITY_DIR if identity_dir is None else identity_dir
    manifest_path = identity_dir / "reference_manifest.json"
    input_png = identity_dir / "source_A_aka_front.png"
    observed = sha256_file(input_png)
    recorded = None
    if manifest_path.is_file():
        try:
            recorded = json.loads(manifest_path.read_text(encoding="utf-8")).get("image_A_sha256")
        except (OSError, ValueError):
            recorded = None
    if observed is None:
        status = "FAIL"
        note = "flattened input image missing"
    elif recorded is None:
        status = "FAIL"
        note = "manifest does not record image_A_sha256; input hash cannot be verified"
    elif observed == recorded:
        status = "PASS"
        note = "flattened input hash matches recorded manifest hash"
    else:
        status = "FAIL"
        note = "flattened input hash DIFFERS from recorded manifest hash"
    return {
        "flattened_aka_image": str(input_png),
        "input_sha256": observed,
        "recorded_input_sha256": recorded,
        "input_hash_matches_manifest": (observed == recorded) if (observed and recorded) else False,
        "status": status,
        "note": note,
    }


def upstream_evidence(upstream_dir: Path | None = None) -> dict:
    upstream_dir = UPSTREAM_DIR if upstream_dir is None else upstream_dir
    out = {}
    all_match = True
    for name, spec in UPSTREAM_EVIDENCE.items():
        p = upstream_dir / name
        observed = sha256_file(p)
        match = bool(observed) and observed == spec["expected_sha256"]
        all_match = all_match and match
        out[name] = {
            "path": str(p),
            "repo_path": spec["repo_path"],
            "source_url": spec["source_url"],
            "present": p.is_file(),
            "sha256": observed,
            "expected_sha256": spec["expected_sha256"],
            "bytes": p.stat().st_size if p.is_file() else None,
            "hash_matches_pinned": match,
        }
    return {"files": out, "all_match": all_match}


# --------------------------------------------------------------------------
# online metadata (bounded, read-only)
# --------------------------------------------------------------------------
AUTH_FIELD_CANDIDATES = (
    "auth_required", "requires_auth", "hf_token", "huggingface_token",
    "oauth", "login", "signed_in", "space_auth",
)


def parse_config_payload(body: bytes) -> dict:
    """Parse and validate a Gradio /config payload.

    HTTP 200 with HTML, non-JSON or missing dependency metadata is NOT a pass.
    """
    try:
        text = body.decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"body could not be decoded: {exc}"}
    stripped = text.lstrip()
    if stripped.startswith("<"):
        return {"ok": False, "reason": "config body was HTML, not JSON", "body_prefix": text[:120]}
    try:
        cfg = json.loads(text)
    except ValueError as exc:
        return {"ok": False, "reason": f"config body was not valid JSON: {exc}", "body_prefix": text[:120]}
    if not isinstance(cfg, dict):
        return {"ok": False, "reason": "config body was JSON but not an object", "body_prefix": text[:120]}
    deps = cfg.get("dependencies")
    if not isinstance(deps, list) or not deps:
        return {
            "ok": False,
            "reason": "config JSON has no usable 'dependencies' list; dependency metadata is missing",
            "config": cfg,
        }
    names = [d.get("api_name") for d in deps if isinstance(d, dict) and d.get("api_name")]
    if not names:
        return {
            "ok": False,
            "reason": "config JSON dependencies carry no api_name entries; callable metadata is missing",
            "config": cfg,
        }
    return {"ok": True, "config": cfg, "api_names": names}


def extract_auth_status(cfg: dict) -> dict:
    found = {k: cfg[k] for k in AUTH_FIELD_CANDIDATES if k in cfg}
    if found:
        return {"status": "REPORTED", "fields": found, "source": "config payload"}
    return {"status": "UNKNOWN", "fields": {}, "source": "config payload has no auth-related fields"}


def probe_demo_config(url: str = DEMO_CONFIG_URL, timeout: int = DEMO_TIMEOUT_S,
                      offline: bool = False) -> dict:
    """Bounded, read-only metadata GET. No upload, no inference, no login."""
    res = {
        "attempted": not offline,
        "url": url,
        "space": DEMO_SPACE,
        "timeout_s": timeout,
        "status": "NOT_TESTED",
        "http_status": None,
        "elapsed_ms": None,
        "api_prefix": None,
        "advertised_api_names": [],
        "callable_verified": False,
        "auth": {"status": "UNKNOWN", "fields": {}, "source": "not probed"},
        "error": None,
        "note": "",
    }
    if offline:
        res["note"] = "offline mode requested; no network request was made"
        return res
    start = time.monotonic()
    try:
        req = urllib.request.Request(
            url, method="GET",
            headers={"User-Agent": "koma-lab-core023-readiness-probe"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            res["http_status"] = resp.status
            res["elapsed_ms"] = int((time.monotonic() - start) * 1000)
        parsed = parse_config_payload(body)
        if not parsed.get("ok"):
            res["status"] = "FAIL"
            res["note"] = parsed.get("reason", "invalid metadata payload")
            res["error"] = res["note"]
            return res
        cfg = parsed["config"]
        res["api_prefix"] = cfg.get("api_prefix")
        res["gradio_version"] = cfg.get("version")
        res["advertised_api_names"] = parsed["api_names"]
        res["callable_verified"] = False  # advertised != verified callable
        res["auth"] = extract_auth_status(cfg)
        res["status"] = "PASS"
        res["note"] = "public /config metadata GET returned valid dependency metadata (advertised api names only)"
    except urllib.error.HTTPError as exc:
        res["http_status"] = exc.code
        res["elapsed_ms"] = int((time.monotonic() - start) * 1000)
        res["error"] = f"HTTPError {exc.code} {exc.reason}"
        res["status"] = "FAIL"
        res["note"] = "metadata endpoint returned an HTTP error"
    except (urllib.error.URLError, OSError, ValueError) as exc:
        res["elapsed_ms"] = int((time.monotonic() - start) * 1000)
        res["error"] = f"{type(exc).__name__}: {exc}"
        res["status"] = "FAIL"
        res["note"] = "metadata endpoint unreachable from this environment"
    return res


# --------------------------------------------------------------------------
# readiness evaluation (pure, testable)
# --------------------------------------------------------------------------
def evaluate_local_readiness(facts: dict) -> dict:
    """Fail-closed readiness evaluation from already-measured facts.

    facts keys: torch (dict), gpu (dict), weights (dict), aka (dict),
    input_hash (dict), upstream (dict).
    """
    torch = facts.get("torch", {})
    gpu = facts.get("gpu", {})
    weights = facts.get("weights", {})
    aka = facts.get("aka", {})
    inp = facts.get("input_hash", {})
    upstream = facts.get("upstream", {})

    blockers: list[str] = []

    torch_ok = bool(torch.get("import_ok"))
    if not torch_ok:
        if torch.get("spec_found"):
            blockers.append(
                "torch spec is present but import/runtime was not verified "
                f"({torch.get('import_error') or 'not attempted'}); spec presence is not compatibility validation"
            )
        else:
            blockers.append(
                "torch is not importable in this interpreter "
                f"({sys.executable}); upstream inference/scripts/inference_psd.py imports torch at module load"
            )
    if torch_ok and not gpu.get("status") == "PASS":
        blockers.append("torch imported but no usable CUDA device is visible")

    if not weights.get("weights_complete"):
        blockers.append(weights.get("note") or "local see-through weights are not loaded")

    if aka.get("status") != "PASS":
        blockers.append("canonical Aka PSD identity mismatch: " + str(aka.get("note")))
    if inp.get("status") != "PASS":
        blockers.append("flattened input hash gate failed: " + str(inp.get("note")))
    if not upstream.get("all_match"):
        blockers.append("upstream evidence hash mismatch or missing; pinned source not confirmed")

    status = "PASS" if not blockers else "BLOCKED"
    return {"status": status, "blockers": blockers}


# --------------------------------------------------------------------------
# setup instructions (ordered, no overlays)
# --------------------------------------------------------------------------
def setup_instructions() -> list[str]:
    return [
        "# 1. clone the pinned upstream checkout FIRST (requirements live in it)",
        "git clone https://github.com/shitagaki-lab/see-through",
        "cd see-through",
        "git checkout " + PINNED_UPSTREAM_COMMIT,
        "",
        "# 2. create and activate an isolated environment",
        "conda create -n see_through python=3.12 -y",
        "conda activate see_through",
        "",
        "# 3. install torch (cu128) into that environment",
        "pip install torch==2.8.0+cu128 torchvision==0.23.0+cu128 torchaudio==2.8.0+cu128 --index-url https://download.pytorch.org/whl/cu128",
        "",
        "# 4. install the dependencies FROM THE CHECKOUT (repo root as working directory)",
        "pip install -r requirements.txt",
        "",
        "# 5. assets symlink as documented by the pinned README",
        "ln -sf common/assets assets",
        "",
        "# NOTE: no overlay of inference_psd.py / inference_utils.py is required —",
        "# the pinned checkout already contains the same code",
        "# (inference/scripts/inference_psd.py and common/utils/inference_utils.py).",
        "# NOTE: always run inference from the repository root as the working directory.",
    ]


def upstream_command(input_png: Path) -> str:
    return (
        "cd see-through   # repository root is the required working directory\n"
        "python inference/scripts/inference_psd.py "
        "--srcp " + str(input_png) + " "
        "--save_dir out/core023/seethrough_output "
        "--seed 42 "
        "--resolution 1280 "
        "--resolution_depth 768 "
        "--inference_steps 30 "
        "--save_to_psd "
        "--group_offload"
    )


def build_report(out_dir: Path, offline: bool = False) -> dict:
    py = detect_python()
    torch = detect_torch()
    gpu = detect_gpu()
    aka = verify_aka_identity()
    inp = check_input_hash()
    weights = assess_weights()
    evidence = upstream_evidence()
    demo = probe_demo_config(offline=offline)

    facts = {
        "torch": torch, "gpu": gpu, "weights": weights,
        "aka": aka, "input_hash": inp, "upstream": evidence,
    }
    local = evaluate_local_readiness(facts)
    blockers = local["blockers"]

    result = {
        "schema": "koma-core023-decomposition-readiness/2",
        "task": "CORE-023 Task B — official semantic-decomposition readiness (ADR-003 M3)",
        "generated_by": "experiments/reference-factory/probe_decomposition.py",
        "constraints_observed": [
            "no package installs", "no checkpoint downloads", "no inference executed",
            "no image upload", "no account/login/credentials", "no commits", "no delegation",
            "stdlib only probe", "explicit known paths only, no home directory scanning",
            "readiness is fail-closed on missing or mismatched inputs",
        ],
        "pinned_upstream": {
            "repo": PINNED_UPSTREAM_REPO,
            "commit": PINNED_UPSTREAM_COMMIT,
            "evidence_files": evidence["files"],
            "all_evidence_hashes_match": evidence["all_match"],
        },
        "expected_checkpoints": dict(EXPECTED_CHECKPOINTS),
        "local_readiness": {
            "status": local["status"],
            "python": py,
            "torch": torch,
            "gpu": gpu,
            "weights": weights,
            "aka_identity": aka,
            "input_hash": inp,
            "blockers": blockers,
            "weights_interpretation": (
                "Weight assessment is PRESENCE-ONLY. checkpoint_payload_found records "
                "whether a checkpoint payload file exists at an explicit known path; "
                "weights_complete is always False because this probe performs no model/index "
                "integrity check and no load validation. Raw file presence can never yield "
                "PASS: a found payload is NOT_TESTED and readiness stays BLOCKED, and an "
                "absent payload remains BLOCKED/FAILED."
            ),
        },
        "online_metadata_status": {
            "status": demo["status"],
            "detail": demo,
            "auth_readme_citation": README_AUTH_CITATION,
            "interpretation": (
                "A successful /config metadata GET proves only that the public Space exposes a Gradio "
                "API surface and that dependency metadata is well formed. The api names are ADVERTISED, "
                "not verified callable: no endpoint was called, no image was uploaded, no inference was "
                "attempted, and no account was created. Anonymous inference is not inferred to work."
            ),
        },
        "M3_actual_decomposition": "NOT_TESTED",
        "M3_actual_decomposition_note": (
            "No model decomposition was run. Existing original PSD layers (16 parts) remain ground truth, "
            "not a model prediction. No inference was ordered for this task."
        ),
        "input": {
            "flattened_aka_image": inp["flattened_aka_image"],
            "input_sha256": inp["input_sha256"],
            "recorded_input_sha256": inp["recorded_input_sha256"],
            "input_hash_matches_manifest": inp["input_hash_matches_manifest"],
            "input_hash_status": inp["status"],
            "ground_truth_psd": aka.get("psd_path"),
            "ground_truth_psd_sha256": aka.get("observed_source_psd_sha256"),
            "ground_truth_part_count": aka.get("part_count"),
        },
        "requirements": setup_instructions(),
        "executable_upstream_command": upstream_command(Path(inp["flattened_aka_image"])),
        "upstream_run_defaults": {
            "repo_id_layerdiff": EXPECTED_CHECKPOINTS["repo_id_layerdiff"],
            "repo_id_depth": EXPECTED_CHECKPOINTS["repo_id_depth"],
            "seed": 42,
            "resolution": 1280,
            "resolution_depth": 768,
            "inference_steps": 30,
            "save_to_psd": True,
            "group_offload": True,
            "precision_paths": {
                "bf16_default": "~12-16 GB VRAM @1280 (upstream README)",
                "group_offload_12gb": "~10 GB VRAM @1280",
                "nf4_quantized_8gb": "~8 GB VRAM @1280 via requirements-inference-bnb.txt + inference_psd_quantized.py",
                "blockswap_8gb_bf16": "~8 GB VRAM @1280 via inference_psd_blockswap.py",
            },
        },
        "blocker_evidence": blockers,
        "next_executable_path": [
            "Obtain a CUDA-capable runner (>=12 GB VRAM for bf16, or >=8 GB with NF4/group-offload) and install the pinned upstream requirements.",
            "Clone shitagaki-lab/see-through at commit " + PINNED_UPSTREAM_COMMIT + " and install torch + requirements from that checkout (no overlay needed).",
            "Run the executable_upstream_command from the repository root on the flattened Aka front image (input_sha256 recorded above).",
            "Compare the produced layered PSD against the 16 original PSD layer bounds recorded in reference_manifest.json (ground truth).",
            "Only then set M3_actual_decomposition to PASS or FAIL with measured layer correspondence.",
        ],
        "ranking": "NONE_ACCEPTED",
        "production_approval": "OPEN",
    }
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="CORE-023 Task B decomposition readiness probe")
    parser.add_argument(
        "--out-dir", default=str(DEFAULT_OUT_DIR),
        help="output directory (default: experiments/reference-factory/out/core023)",
    )
    parser.add_argument(
        "--skip-network", action="store_true",
        help="offline mode: perform no network requests",
    )
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / OUT_JSON_NAME

    result = build_report(out_dir, offline=args.skip_network)
    result["output_path"] = str(out_json)
    result["offline_mode"] = bool(args.skip_network)

    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_json}")
    print(
        "local_readiness={} online_metadata={} M3_actual_decomposition=NOT_TESTED".format(
            result["local_readiness"]["status"], result["online_metadata_status"]["status"],
        )
    )
    for b in result["local_readiness"]["blockers"]:
        print("BLOCKER:", b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
