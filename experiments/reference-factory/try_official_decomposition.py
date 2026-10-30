#!/usr/bin/env python3
"""CORE-023 Task C — one bounded anonymous official-demo inference attempt.

Runs the official See-through ZeroGPU demo (https://24yearsold-see-through-demo.hf.space)
through the maintained official ``gradio_client`` package, using the endpoint
signature advertised by the Space's own ``/config`` metadata.

Safety rules enforced here:
  * anonymous only — no login, no account, no token, no paid rent/upgrade;
  * exactly ONE inference submission (no retries of inference);
  * bounded wait (default 240s) with cancellation of a still-queued job on timeout;
  * uploads only the license-clear public Aka front image;
  * all outputs stay under out/core023/demo/ ;
  * never treats PSD layer presence as a quality PASS.

Run it with the isolated venv interpreter, e.g.:

    HF_HUB_DISABLE_IMPLICIT_TOKEN=1 \
      out/core023/demo-runtime/venv/bin/python \
      experiments/reference-factory/try_official_decomposition.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
import traceback
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = REPO_ROOT / "experiments/reference-factory/out/identity/source_A_aka_front.png"
DEFAULT_OUTDIR = REPO_ROOT / "out/core023/demo"
DEFAULT_REPORT = REPO_ROOT / "out/core023/demo/official_demo_attempt.json"

DEFAULT_SPACE_URL = "https://24yearsold-see-through-demo.hf.space"
API_NAME = "/inference"
EXPECTED_SOURCE_SHA256 = "c22f2af3f426d4e79745e28a1244750d1c46b41d82f46570be63b9543aedb4e4"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class BoundaryError(RuntimeError):
    """Raised for a request-boundary violation detected before any client action."""


def validate_space_url(space: str) -> str:
    """Only the official demo host may be contacted. No other endpoint allowed.

    Pure string check: no network, no client construction.
    """
    if space != DEFAULT_SPACE_URL:
        raise BoundaryError(
            f"unsupported space endpoint: {space!r} "
            f"(only the official {DEFAULT_SPACE_URL!r} is allowed)")
    return space


def check_source_hash(path: Path, expected: str = EXPECTED_SOURCE_SHA256) -> str:
    """Only the pinned public input hash may proceed to upload. No override."""
    digest = sha256_file(path)
    if digest != expected:
        raise BoundaryError(f"source sha256 mismatch: got {digest}, expected {expected}")
    return digest


def client_kwargs(space: str, outdir: Path, timeout: float = 120.0) -> dict:
    """Build the anonymous Client kwargs without importing gradio_client.

    ``token=False`` prohibits implicit token resolution (it is handled
    explicitly by huggingface_hub.get_token_to_send before any token cache
    lookup), and the space is validated to the official host only.
    """
    validate_space_url(space)
    return {
        "space": space,
        "token": False,
        "verbose": False,
        "download_files": str(outdir / "downloads"),
        "httpx_kwargs": {"timeout": timeout},
    }


def classify_error(exc: BaseException) -> tuple[str, str]:
    """Map an exception onto a coarse, non-secret error classification."""
    name = type(exc).__name__
    text = str(exc)
    low = text.lower()
    if isinstance(exc, TimeoutError) or "timeout" in low or "timed out" in low:
        return "TIMEOUT", f"{name}: {text}"
    for key in ("401", "403", "unauthorized", "forbidden", "invalid token", "authentication"):
        if key in low:
            return "AUTH_ERROR", f"{name}: {text}"
    for key in ("429", "quota", "rate limit", "too many requests"):
        if key in low:
            return "QUOTA_ERROR", f"{name}: {text}"
    for key in ("proxy", "connect", "connection", "dns", "network", "resolve", "unreachable"):
        if key in low:
            return "NETWORK_ERROR", f"{name}: {text}"
    if "not found" in low or "404" in low:
        return "ENDPOINT_ERROR", f"{name}: {text}"
    return "UNKNOWN_ERROR", f"{name}: {text}"


def summarize_api(api: dict[str, Any]) -> dict[str, Any]:
    """Extract the public, non-secret parameter schema for /inference."""
    endpoints = api.get("named_endpoints") or {}
    ep = endpoints.get(API_NAME)
    if not ep:
        return {"present": False, "endpoint_name": API_NAME,
                "advertised_endpoints": sorted(endpoints.keys())}
    params = []
    for p in ep.get("parameters", []):
        params.append({
            "parameter_name": p.get("parameter_name"),
            "label": p.get("label"),
            "python_type": (p.get("python_type") or {}).get("type"),
            "parameter_has_default": p.get("parameter_has_default"),
            "parameter_default": p.get("parameter_default"),
            "description": (p.get("type") or {}).get("description"),
        })
    return {
        "present": True,
        "endpoint_name": API_NAME,
        "advertised_endpoints": sorted(endpoints.keys()),
        "parameters": params,
        "returns": [r.get("label") for r in ep.get("returns", [])],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--space", default=DEFAULT_SPACE_URL,
                    help="must be the official demo host; no other endpoint is allowed")
    ap.add_argument("--timeout", type=int, default=240, help="bounded wait for the job result")
    args = ap.parse_args()

    # Anonymous, no-token operation. Never read or reuse any local HF credential.
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ.pop("HF_TOKEN", None)
    os.environ.pop("HUGGING_FACE_HUB_TOKEN", None)

    started = time.monotonic()
    report: dict[str, Any] = {
        "schema": "koma-core023-official-demo-attempt/1",
        "task": "CORE-023 Task C — one bounded anonymous official-demo inference attempt",
        "generated_by": "experiments/reference-factory/try_official_decomposition.py",
        "space_url": args.space,
        "api_name": API_NAME,
        "constraints_observed": [
            "anonymous only: token=None, HF_HUB_DISABLE_IMPLICIT_TOKEN=1, no local token read",
            "exactly one inference submission, no inference retries",
            "bounded wait with cancellation on timeout",
            "no login, account, payment, rent/upgrade, duplicate space, TLS change, endpoint hopping",
            "no production approval inferred, no 360 claimed",
            "no delegation, no commit, no push",
            "no install into the global environment",
        ],
        "input": {},
        "client_versions": {},
        "public_api_signature": None,
        "submitted_arguments": None,
        "elapsed_s": None,
        "stage_reached": "START",
        "status": "FAIL",
        "error_classification": None,
        "error": None,
        "outputs": [],
        "output_hashes": {},
        "production_approval": False,
        "notes": [],
    }

    def finish(code: int) -> int:
        report["elapsed_s"] = round(time.monotonic() - started, 2)
        args.outdir.mkdir(parents=True, exist_ok=True)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({k: report[k] for k in (
            "status", "stage_reached", "error_classification", "elapsed_s",
            "production_approval")}, indent=2))
        if report.get("error"):
            print("error:", report["error"], file=sys.stderr)
        return code

    # --- input ------------------------------------------------------------
    src = args.source
    if not src.is_file():
        report["status"] = "FAIL"
        report["stage_reached"] = "INPUT_CHECK"
        report["error_classification"] = "INPUT_ERROR"
        report["error"] = f"source image not found: {src}"
        return finish(2)
    src_hash = sha256_file(src)
    report["input"] = {
        "path": str(src),
        "sha256": src_hash,
        "bytes": src.stat().st_size,
        "expected_sha256": EXPECTED_SOURCE_SHA256,
        "license": "CC BY 4.0, PSD by seagetch (public, license-clear)",
        "hash_matches_expected": src_hash == EXPECTED_SOURCE_SHA256,
    }
    if src_hash != EXPECTED_SOURCE_SHA256:
        report["status"] = "FAIL"
        report["stage_reached"] = "INPUT_CHECK"
        report["error_classification"] = "INPUT_ERROR"
        report["error"] = f"source sha256 mismatch: got {src_hash}"
        return finish(2)

    # --- client -----------------------------------------------------------
    try:
        import gradio_client
        import httpx
        from gradio_client import Client, handle_file
    except Exception as exc:  # pragma: no cover - import failure is a hard stop
        report["status"] = "FAIL"
        report["stage_reached"] = "IMPORT"
        report["error_classification"], report["error"] = classify_error(exc)
        return finish(3)

    report["client_versions"] = {
        "gradio_client": getattr(gradio_client, "__version__", None),
        "httpx": getattr(httpx, "__version__", None),
        "python": platform.python_version(),
        "python_executable": sys.executable,
    }

    # --- metadata / advertised signature ---------------------------------
    client = None
    try:
        report["stage_reached"] = "CLIENT_CONNECT"
        # Endpoint guard runs before any client construction or upload action.
        validate_space_url(args.space)
        kwargs = client_kwargs(args.space, args.outdir)
        client = Client(
            kwargs["space"],
            token=kwargs["token"],
            verbose=kwargs["verbose"],
            download_files=kwargs["download_files"],
            httpx_kwargs={"timeout": httpx.Timeout(120.0)},
        )
        report["stage_reached"] = "API_SCHEMA"
        api = client.view_api(print_info=False, return_format="dict")
        signature = summarize_api(api)
        report["public_api_signature"] = signature
        if not signature.get("present"):
            report["status"] = "FAIL"
            report["stage_reached"] = "API_SCHEMA"
            report["error_classification"] = "ENDPOINT_ERROR"
            report["error"] = f"{API_NAME} not advertised; endpoints={signature.get('advertised_endpoints')}"
            return finish(4)

        # Derive non-image arguments from the advertised defaults.
        derived: dict[str, Any] = {}
        for p in signature["parameters"]:
            name = p["parameter_name"]
            if name == "image":
                continue
            if p["parameter_has_default"]:
                derived[name] = p["parameter_default"]
        report["submitted_arguments"] = {
            "image": "<handle_file(source_A_aka_front.png)>",
            "non_image_args_from_advertised_defaults": derived,
        }
        report["notes"].append(
            "Non-image arguments were taken verbatim from the Space's own advertised "
            "parameter defaults; no value was guessed.")
    except Exception as exc:
        report["status"] = "FAIL"
        report["error_classification"], report["error"] = classify_error(exc)
        report["notes"].append(traceback.format_exc(limit=3))
        return finish(4)

    # --- single inference submission --------------------------------------
    job = None
    try:
        report["stage_reached"] = "SUBMIT"
        args.outdir.mkdir(parents=True, exist_ok=True)
        image_arg = handle_file(str(src))
        job = client.submit(image_arg, api_name=API_NAME, **derived)
        report["stage_reached"] = "QUEUED"
        report["notes"].append("Job submitted once; waiting with bounded timeout.")
        report["elapsed_s"] = round(time.monotonic() - started, 2)
        try:
            result = job.result(timeout=args.timeout)
        except Exception as exc:
            # Try to cancel a still-queued job, then stop.
            cancelled = False
            try:
                if job is not None:
                    job.cancel()
                    cancelled = True
            except Exception:
                cancelled = False
            report["notes"].append(f"Job cancel attempted: {cancelled}")
            report["status"] = "FAIL"
            report["stage_reached"] = "WAIT"
            report["error_classification"], report["error"] = classify_error(exc)
            report["notes"].append(traceback.format_exc(limit=4))
            return finish(5)
        report["stage_reached"] = "RESULT_RECEIVED"
        report["result_repr"] = repr(result)[:2000]
    except Exception as exc:
        report["status"] = "FAIL"
        report["error_classification"], report["error"] = classify_error(exc)
        report["notes"].append(traceback.format_exc(limit=4))
        return finish(5)

    # --- collect outputs ---------------------------------------------------
    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    collected: list[dict[str, Any]] = []
    candidates: list[str] = []
    if isinstance(result, (list, tuple)):
        for item in result:
            if isinstance(item, dict):
                p = item.get("path")
                if p:
                    candidates.append(p)
            elif isinstance(item, str):
                candidates.append(item)
    elif isinstance(result, dict):
        p = result.get("path")
        if p:
            candidates.append(p)

    seen: set[str] = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        try:
            p = Path(c)
            if not p.is_file():
                continue
            dest = outdir / p.name
            if p.resolve() != dest.resolve():
                dest.write_bytes(p.read_bytes())
            h = sha256_file(dest)
            collected.append({
                "name": dest.name,
                "path": str(dest),
                "bytes": dest.stat().st_size,
                "sha256": h,
                "suffix": dest.suffix.lower(),
            })
            report["output_hashes"][dest.name] = h
        except OSError:
            continue

    report["outputs"] = collected
    psd_files = [c for c in collected if c["suffix"] == ".psd"]
    if not psd_files:
        report["status"] = "FAIL"
        report["stage_reached"] = "RESULT_RECEIVED"
        report["error_classification"] = "NO_PSD_OUTPUT"
        report["error"] = "job returned no .psd file payload"
        return finish(6)

    report["status"] = "PASS" if collected else "FAIL"
    report["stage_reached"] = "OUTPUT_COLLECTED"
    report["notes"].append(
        "PSD layers were NOT quality-validated here; layer presence alone is not a "
        "quality PASS. Deformation/visual quality still requires evaluation.")
    return finish(0 if collected else 6)


if __name__ == "__main__":
    sys.exit(main())
