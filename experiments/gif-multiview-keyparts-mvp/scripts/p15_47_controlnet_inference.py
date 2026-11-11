#!/usr/bin/env python3
"""Run one reproducible 65-degree controlled inpainting candidate through Gradio API."""
import argparse
import hashlib
import json
import os
import re
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parents[1]
P = R / "private-assets"
SPACE = "https://hugging-apps-qwen-image-2-1-controlnet-union-demo.hf.space"
PROMPT = (
    "A premium clean hand-drawn Japanese 2D anime key visual of the SAME character already in the "
    "inpainting source. Right-facing 65 degree facial yaw, not mirrored; a realistic foreshortened "
    "far eye behind nose bridge, smaller and partially occluded than the near eye, not a symmetrical "
    "frontal face. Exact facial geometry follows the supplied LINEART face and hair edges. "
    "Short dusty rose lavender bob, side-swept bangs, exactly one ahoge and gold crossed hair clip on "
    "image right, pink-purple eyes, dark navy uniform, red bow. One coherent anime nose with "
    "correct bridge, small mouth and sharp jaw. Do not change unmasked background, clothes or hair."
)
NEGATIVE = "front view, symmetrical eyes, mirror image, left-facing, missing eye, misplaced hair clip, malformed facial anatomy, extra hair"

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def request(url, *, obj=None, data=None, content_type=None, timeout=90):
    payload = json.dumps(obj).encode() if obj is not None else data
    headers = {"User-Agent": "koma-p15-47-review/1"}
    if obj is not None:
        headers["Content-Type"] = "application/json"
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=65445)
    parser.add_argument("--steps", type=int, default=24)
    parser.add_argument("--evidence-stage", default="p15-47")
    args = parser.parse_args()
    assert 0 <= args.seed < 2147483647
    assert re.fullmatch(r"p15-\d{2}", args.evidence_stage), "invalid stage"
    control = P / "exports/p15-46-anchor-guides/facial-geometry-guide-65.png"
    mask = P / "exports/p15-46-anchor-guides/face-mask-narrow-65.png"
    src = P / "p15-38-p0-registered-arc/yaw65/composite.png"
    paths = [control, src, mask]
    boundary = "----komaP1547" + uuid.uuid4().hex
    body = bytearray()
    for file in paths:
        body += ("--" + boundary + "\r\n").encode()
        body += (f'Content-Disposition: form-data; name="files"; filename="{file.name}"\r\n'
                 'Content-Type: image/png\r\n\r\n').encode()
        body += file.read_bytes()
        body += b"\r\n"
    body += ("--" + boundary + "--\r\n").encode()
    uploaded = json.loads(request(SPACE + "/gradio_api/upload", data=bytes(body),
                                  content_type="multipart/form-data; boundary=" + boundary, timeout=120))
    assert len(uploaded) == 3
    filedata = lambda p: {"path": p, "meta": {"_type": "gradio.FileData"}}
    values = [
        PROMPT, filedata(uploaded[0]), "None (already a control map)",
        {"background": filedata(uploaded[1]), "layers": [], "composite": None},
        filedata(uploaded[2]), 1.0, 1024, args.steps, args.seed, False, NEGATIVE, 1.0,
    ]
    evidence = {
        "schema": "KOMA-P15-47-REAL-INFERENCE-V1",
        "timeUTC": datetime.now(timezone.utc).isoformat(),
        "space": SPACE,
        "api": "/gradio_api/call/generate",
        "inputs": [
            {"name": file.name, "sha256": digest(file), "bytes": file.stat().st_size}
            for file in paths
        ],
        "seed": args.seed, "steps": args.steps, "scale": 1.0,
        "target": "right-facing yaw65",
        "status": "SUBMITTED",
    }
    qpath = R / ("evidence/" + args.evidence_stage + "-inference-qa.json")
    def save(): qpath.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    save()
    start = request(SPACE + "/gradio_api/call/generate", obj={"data": values}, timeout=120)
    event_id = json.loads(start)["event_id"]
    evidence["eventId"] = event_id
    print("submitted", event_id, flush=True)
    save()
    stream = request(SPACE + "/gradio_api/call/generate/" + event_id, timeout=360).decode("utf-8", "replace")
    (R / ("evidence/" + args.evidence_stage + "-raw-sse.txt")).write_text(stream)
    events = [line.removeprefix("event: ") for line in stream.splitlines() if line.startswith("event: ")]
    evidence["events"] = events
    if "error" in events or "complete" not in events:
        evidence["status"] = "INFERENCE_REJECTED_OR_FAILED"
        evidence["error"] = stream[-1200:]
        save()
        print(json.dumps({"status": evidence["status"], "reason": evidence["error"]}), flush=True)
        return 2
    arr = json.loads([line[6:] for line in stream.splitlines() if line.startswith("data: ")][-1])
    assert isinstance(arr, list) and len(arr) >= 3 and arr[2] == args.seed
    out = P / f"exports/{args.evidence_stage}-qwen21-controlled-seed-{args.seed}.png"
    out.write_bytes(request(arr[0]["url"], timeout=120))
    preview = P / f"exports/{args.evidence_stage}-control-preview-seed-{args.seed}.webp"
    preview.write_bytes(request(arr[1]["url"], timeout=120))
    evidence.update({
        "status": "REAL_GENERATION_RETURNED",
        "output": str(out.relative_to(P)), "outputSHA256": digest(out), "outputBytes": out.stat().st_size,
        "preview": str(preview.relative_to(P)), "previewSHA256": digest(preview),
        "formalArtAccepted": False,
    })
    save()
    print(json.dumps({"status": evidence["status"], "output": str(out), "sha256": digest(out)}), flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
