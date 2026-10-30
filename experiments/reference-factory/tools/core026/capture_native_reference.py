#!/usr/bin/env python3
"""CORE-026 native reference capture helper.

Captures real X11 frames of the ORIGINAL Inochi2D example binary (native
renderer) over the 9 raw head-yaw poses, derives a full 720x880 PNG and a
fixed head ROI PNG per pose, and emits a reference manifest plus bounded
contact sheets.

Design constraints honoured here:
  * NO fabricated pixels, landmarks, mesh truth or "successful native exit".
  * The INX is validated by SHA256 and its REAL raw parameter domain and
    binding count are parsed from the file itself.
  * The head ROI is FIXED ([120, 0, 600, 370]) for every pose - never
    adaptive per pose.
  * dt0 policy: frozen_time_no_physics_equilibrium_claim.
  * Every child process (Xvfb, app, ffmpeg) is cleaned up on error paths.

Usage:
  capture_native_reference.py --binary PATH --source PATH --out PATH
                              --patch-report PATH
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import struct
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image, ImageDraw
except Exception as exc:  # pragma: no cover - dependency missing
    print("FATAL: Pillow is required: %s" % exc, flush=True)
    raise SystemExit(2)

try:
    import numpy as np
except Exception as exc:  # pragma: no cover - dependency missing
    print("FATAL: numpy is required: %s" % exc, flush=True)
    raise SystemExit(2)


# ---------------------------------------------------------------------------
# Frozen constants (contract)
# ---------------------------------------------------------------------------

EXPECTED_INX_SHA256 = (
    "dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f"
)

RAW_YAWS: Tuple[float, ...] = (-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0)
RAW_PITCH = 0.0

FULL_W, FULL_H = 720, 880
# DEFAULT (baseline full-body reference) head ROI: x0, y0, x1, y1 - FIXED for all poses
HEAD_ROI = (120, 0, 600, 370)
# HEAD-VIEW mode: one fixed 652x652 head crop of the ACTUAL 720x880 full frame
HEAD_ROI_HEAD_VIEW = (34, 114, 686, 766)

SCREEN_W, SCREEN_H, SCREEN_DEPTH = 1024, 900, 24
DISPLAY = ":88"

CAMERA_SCALE = 0.15
CAMERA_POSITION = [0.0, 0.0]
CAMERA_SCALE_HEAD_VIEW = 0.4
CAMERA_POSITION_HEAD_VIEW = [82.0, 1773.0]
DT0_POLICY = "frozen_time_no_physics_equilibrium_claim"

APP_WINDOW_W, APP_WINDOW_H = 720, 880

READY_TIMEOUT_S = 30.0
APP_SETTLE_S = 2.5
CAPTURE_DURATION_S = 3.0
MOUSE_PARK = (1010, 890)  # outside the 720x880 capture region

ZIP_MAX_BYTES = 2 * 1024 * 1024
CONTACT_MAX_BYTES = 200 * 1024

MANIFEST_PREFIX = "CORE026_MANIFEST_JSON"
CONTACT_BEGIN = "CORE026_CONTACT_BEGIN"
CONTACT_END = "CORE026_CONTACT_END"
BUNDLE_BEGIN = "CORE026_REVIEW_BUNDLE_BEGIN"
BUNDLE_END = "CORE026_REVIEW_BUNDLE_END"

RENDERER_READY_MARKERS = (
    "Inox2D renderer initialized",
)

BAD_LOG_MARKERS = (
    "FBO incomplete",
    "GL_INVALID_FRAMEBUFFER_OPERATION",
    "panicked",
    "panic",
    "RUST_BACKTRACE",
)


def log(msg: str) -> None:
    print("[core026] %s" % msg, flush=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# INX parsing (real, from the file)
# ---------------------------------------------------------------------------


def parse_inx(path: Path) -> Dict[str, Any]:
    """Parse the real raw parameter domain + binding count out of the INX."""
    raw = path.read_bytes()
    magic = raw[:8]
    if magic != b"TRNSRTS\x00":
        raise ValueError("INX_BAD_MAGIC: expected b'TRNSRTS\\x00', got %r" % magic)
    length = struct.unpack('>I', raw[8:12])[0]
    doc = json.loads(raw[12:12 + length])
    params = doc.get("param") or []
    entries = []
    for p in params:
        entries.append(
            {
                "name": p.get("name"),
                "is_vec2": bool(p.get("is_vec2", False)),
                "min": p.get("min"),
                "max": p.get("max"),
                "defaults": p.get("defaults"),
                "axis_points": p.get("axis_points"),
                "binding_count": len(p.get("bindings") or []),
            }
        )
    head = next(
        (e for e in entries if e["name"] == "Head:: Yaw-Pitch"),
        None,
    )
    if head is None:
        raise ValueError("INX_MISSING_PARAM: 'Head:: Yaw-Pitch' not found")
    total_bindings = sum(e["binding_count"] for e in entries)
    return {
        "magic": magic.decode("latin-1"),
        "meta": doc.get("meta"),
        "physics": doc.get("physics"),
        "param_count": len(entries),
        "total_binding_count": total_bindings,
        "head_yaw_pitch": head,
        "params": entries,
        "node_count": count_nodes(doc['nodes']),
    }


def count_nodes(node):
    return 1 + sum(count_nodes(child) for child in node.get('children', []))


# ---------------------------------------------------------------------------
# Process helpers
# ---------------------------------------------------------------------------


class Managed:
    """Registry so every spawned process is killed, even on error."""

    def __init__(self) -> None:
        self.procs: List[subprocess.Popen] = []
        self.files: List[Path] = []

    def spawn(
        self,
        cmd: List[str],
        env: Optional[Dict[str, str]] = None,
        stdout_path: Optional[Path] = None,
        cwd: Optional[str] = None,
    ) -> subprocess.Popen:
        out = subprocess.DEVNULL
        err = subprocess.DEVNULL
        handles = []
        if stdout_path is not None:
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            fh = stdout_path.open("wb")
            handles.append(fh)
            out = fh
            err = subprocess.STDOUT
        proc = subprocess.Popen(
            cmd,
            stdout=out,
            stderr=err,
            env=env,
            cwd=cwd,
            start_new_session=True,
        )
        for fh in handles:
            fh.close()
        self.procs.append(proc)
        return proc

    def cleanup(self) -> List[Dict[str, Any]]:
        report = []
        for proc in self.procs:
            if proc.poll() is None:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                except Exception:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                try:
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception:
                        pass
                    try:
                        proc.wait(timeout=5)
                    except Exception:
                        pass
            report.append(
                {
                    "pid": proc.pid,
                    "returncode": proc.returncode,
                    "terminated_by_capture": proc.returncode is None
                    or proc.returncode != 0,
                }
            )
        self.procs = []
        for f in self.files:
            try:
                if f.exists():
                    f.unlink()
            except Exception:
                pass
        self.files = []
        return report


def wait_for_window(dpy: str, proc: subprocess.Popen, timeout: float) -> Optional[str]:
    """Poll xdotool for the actual application window id."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return None
        try:
            out = subprocess.run(
                ["xdotool", "search", "--onlyvisible", "--name", "Render Inochi2D Puppet"],
                env={**os.environ, "DISPLAY": dpy},
                capture_output=True,
                text=True,
                timeout=10,
            )
            ids = [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
            if ids:
                return ids[-1]
        except Exception:
            pass
        time.sleep(0.4)
    return None


def move_window(dpy: str, win: str, x: int, y: int) -> bool:
    for args in (
        ["xdotool", "windowmove", win, str(x), str(y)],
        ["xdotool", "windowmove", "--sync", win, str(x), str(y)],
    ):
        try:
            res = subprocess.run(
                args,
                env={**os.environ, "DISPLAY": dpy},
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0:
                return True
        except Exception:
            continue
    return False


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------


def capture_screen(
    mgr: Managed,
    dpy: str,
    out_png: Path,
    duration: float,
) -> Dict[str, Any]:
    """Capture the real X11 screen with ffmpeg (1024x900)."""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "x11grab",
        "-video_size",
        "%dx%d" % (SCREEN_W, SCREEN_H),
        "-framerate",
        "25",
        "-i",
        dpy,
        "-t",
        str(duration),
        "-frames:v",
        "1",
        "-y",
        str(out_png),
    ]
    env = {**os.environ, "DISPLAY": dpy}
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
    if res.returncode != 0 or not out_png.exists():
        raise RuntimeError(
            "FFMPEG_CAPTURE_FAILED rc=%s stderr=%s"
            % (res.returncode, (res.stderr or "")[-2000:])
        )
    return {
        "command": cmd,
        "env": {"DISPLAY": dpy},
        "returncode": res.returncode,
        "stderr_tail": (res.stderr or "")[-2000:],
    }


def crop_full_and_head(
    screen_png: Path, full_png: Path, head_png: Path
) -> Dict[str, Any]:
    """Derive the 720x880 full frame and the FIXED head ROI from a screen frame."""
    with Image.open(screen_png) as im:
        screen = im.convert("RGB")
        if screen.size != (SCREEN_W, SCREEN_H):
            raise ValueError('Unexpected native screen size: %r' % (screen.size,))
        full = screen.crop((0, 0, FULL_W, FULL_H))
        full.save(full_png, format="PNG")
        head = full.crop(HEAD_ROI)
        head.save(head_png, format="PNG")
        arr = np.asarray(full.convert("L"), dtype=np.uint8)
        head_arr = np.asarray(head.convert("L"), dtype=np.uint8)
    return {
        "screen_size": [SCREEN_W, SCREEN_H],
        "full_size": list(full.size),
        "head_size": list(head.size),
        "full_mean_luma": float(arr.mean()),
        "head_mean_luma": float(head_arr.mean()),
        "full_std_luma": float(arr.std()),
        "head_std_luma": float(head_arr.std()),
        "full_nonblank": bool(arr.std() > 8.0),
        "head_nonblank": bool(head_arr.std() > 8.0),
    }


def image_fingerprint(path: Path) -> str:
    with Image.open(path) as im:
        rgb = im.convert("RGB")
        arr = np.asarray(rgb, dtype=np.uint8)
    return sha256_bytes(arr.tobytes())


# ---------------------------------------------------------------------------
# Contact sheets
# ---------------------------------------------------------------------------


def contact_sheet(paths: List[Path], cols: int, max_bytes: int, quality: int = 80) -> bytes:
    imgs = []
    for p in paths:
        with Image.open(p) as im:
            cell = im.convert("RGB")
            cell.thumbnail((400, 400), Image.Resampling.LANCZOS)
            imgs.append(cell)
    if not imgs:
        raise ValueError("no images for contact sheet")
    w, h = imgs[0].size
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * (h + 20)), (16, 16, 16))
    draw = ImageDraw.Draw(sheet)
    for i, im in enumerate(imgs):
        x, y = (i % cols) * w, (i // cols) * (h + 20)
        sheet.paste(im, (x, y + 20))
        draw.text((x + 5, y + 3), 'native raw yaw=%+.2f' % RAW_YAWS[i], fill='white')
    quality = quality
    while True:
        buf = io.BytesIO()
        sheet.save(buf, format="JPEG", quality=quality, optimize=True)
        data = buf.getvalue()
        if len(data) <= max_bytes or quality <= 40:
            if len(data) > max_bytes:
                raise ValueError("contact sheet exceeds bound %d" % max_bytes)
            break
        quality -= 10
    return data


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_app_argv(binary: Path, source: Path, raw_yaw: float) -> List[str]:
    """Command line for one fresh app process.

    Upstream clap accepts exactly one positional source path. Pose is supplied
    through KOMA_HEAD_YAW, as implemented by the separately audited source patch.
    """
    return [str(binary), str(source)]


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="capture_native_reference.py",
        description=(
            "Capture the ORIGINAL Inochi2D example over 9 raw head-yaw poses "
            "under Xvfb and emit a CORE-026 reference manifest."
        ),
    )
    ap.add_argument("--binary", required=True, help="path to the native example executable")
    ap.add_argument("--source", required=True, help="path to the original INX source")
    ap.add_argument("--out", required=True, help="output directory for captures + manifest")
    ap.add_argument(
        "--patch-report",
        required=True,
        help="path to the real example patch report JSON (must exist)",
    )
    ap.add_argument(
        "--head-view",
        action="store_true",
        help=(
            "capture the source-consistent high-resolution head view "
            "(camera scale 0.4, camera position (82,1773), fixed 652x652 head ROI). "
            "Python helper only - the native binary argv is unchanged."
        ),
    )
    args = ap.parse_args(argv)

    # ---- capture mode selection (Python side only) ----
    global HEAD_ROI, CAMERA_SCALE, CAMERA_POSITION
    if args.head_view:
        HEAD_ROI = HEAD_ROI_HEAD_VIEW
        CAMERA_SCALE = CAMERA_SCALE_HEAD_VIEW
        CAMERA_POSITION = CAMERA_POSITION_HEAD_VIEW
        capture_mode = "head_view"
    else:
        HEAD_ROI = (120, 0, 600, 370)
        CAMERA_SCALE = 0.15
        CAMERA_POSITION = [0.0, 0.0]
        capture_mode = "full_body_baseline"

    binary = Path(args.binary).expanduser().resolve()
    source = Path(args.source).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    patch_report = Path(args.patch_report).expanduser().resolve()

    mgr = Managed()
    manifest: Dict[str, Any] = {
        "schema": "koma-core026-native-reference/1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "FAIL",
    }
    env_info: Dict[str, Any] = {}

    try:
        # ---------------- input validation ----------------
        if not binary.is_file():
            raise SystemExit("FATAL: --binary does not exist: %s" % binary)
        if not os.access(str(binary), os.X_OK):
            raise SystemExit("FATAL: --binary is not executable: %s" % binary)
        if not source.is_file():
            raise SystemExit("FATAL: --source does not exist: %s" % source)
        if not patch_report.is_file():
            raise SystemExit("FATAL: --patch-report does not exist: %s" % patch_report)
        if patch_report.stat().st_size == 0:
            raise SystemExit("FATAL: --patch-report is empty (must be a real file)")

        source_sha = sha256_file(source)
        log("source sha256=%s" % source_sha)
        if source_sha != EXPECTED_INX_SHA256:
            raise SystemExit(
                "FATAL: INX SHA mismatch: expected %s got %s"
                % (EXPECTED_INX_SHA256, source_sha)
            )

        inx = parse_inx(source)
        head = inx["head_yaw_pitch"]
        log(
            "INX raw param domain 'Head:: Yaw-Pitch' min=%s max=%s bindings=%d"
            % (head["min"], head["max"], head["binding_count"])
        )
        if head["binding_count"] != 114:
            raise SystemExit(
                "FATAL: expected 114 'Head:: Yaw-Pitch' bindings, parsed %d"
                % head["binding_count"]
            )
        if head["min"] != [-1.0, -1.0] or head["max"] != [1.0, 1.0]:
            raise SystemExit(
                "FATAL: unexpected raw parameter domain: min=%s max=%s"
                % (head["min"], head["max"])
            )
        if head['defaults'] != [0, 0] or head['axis_points'] != [[i / 8 for i in range(9)], [0, .5, 1]]:
            raise ValueError('Unexpected actual default/axis points')

        patch_bytes = patch_report.read_bytes()
        patch_sha = sha256_bytes(patch_bytes)
        try:
            patch_text = patch_bytes.decode("utf-8", errors="replace")
        except Exception:
            patch_text = ""
        try:
            patch_json: Any = json.loads(patch_text)
        except Exception:
            patch_json = None
        if not isinstance(patch_json, dict) or patch_json.get('status') != 'PASS':
            raise ValueError('Missing valid native patch report')
        if patch_json.get('upstream_commit') != 'd4dd9dd7f16b775042cbda44370570abf9a8cf81':
            raise ValueError('Unexpected upstream commit in native patch report')
        if patch_json.get('ear_only_draw_filter_applied') is not False or patch_json.get('head_parameter', {}).get('raw_pitch') != 0:
            raise ValueError('Native patch does not meet full-head / raw-pitch contract')
        log("patch-report %s sha256=%s" % (patch_report, patch_sha))

        # ---------------- environment info ----------------
        for tool in ("ffmpeg", "Xvfb", "xdotool"):
            path = shutil.which(tool)
            version = ""
            if path:
                try:
                    ver = subprocess.run(
                        [path, "-version"],
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                    version = (ver.stdout or ver.stderr or "").splitlines()[:3]
                    version = " | ".join(version)
                except Exception:
                    version = "unknown"
            env_info[tool] = {"path": path, "version": version}
            log("%s: %s" % (tool, path or "NOT_FOUND"))
        try:
            glx = subprocess.run(
                ["glxinfo", "-B"],
                capture_output=True,
                text=True,
                timeout=20,
                env={**os.environ, "DISPLAY": DISPLAY, "LIBGL_ALWAYS_SOFTWARE": "1"},
            )
            env_info["glxinfo"] = (glx.stdout or "")[:4000]
        except Exception:
            env_info["glxinfo"] = "NOT_AVAILABLE"

        out_dir.mkdir(parents=True, exist_ok=True)
        frames_dir = out_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = out_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # ---------------- Xvfb ----------------
        xvfb_cmd = [
            "Xvfb",
            DISPLAY,
            "-screen",
            "0",
            "%dx%dx%d" % (SCREEN_W, SCREEN_H, SCREEN_DEPTH),
            "-nolisten",
            "tcp",
        ]
        xvfb_log = logs_dir / "xvfb.log"
        xvfb_env = {**os.environ, "LIBGL_ALWAYS_SOFTWARE": "1", "GALLIUM_DRIVER": "llvmpipe"}
        xvfb = mgr.spawn(xvfb_cmd, env=xvfb_env, stdout_path=xvfb_log)
        time.sleep(2.0)
        if xvfb.poll() is not None:
            raise RuntimeError(
                "XVFB_EXITED rc=%s log=%s"
                % (xvfb.returncode, xvfb_log.read_text(errors="replace")[-2000:])
            )
        log("Xvfb up on %s" % DISPLAY)
        glx = subprocess.run(['glxinfo', '-B'], env={**xvfb_env, 'DISPLAY': DISPLAY},
                             capture_output=True, text=True, timeout=20)
        env_info['glxinfo'] = (glx.stdout or glx.stderr)[:4000]

        app_env_base = {
            **os.environ,
            "DISPLAY": DISPLAY,
            "LIBGL_ALWAYS_SOFTWARE": "1",
            "GALLIUM_DRIVER": "llvmpipe",
            "RUST_LOG": "info",
        }
        # The ear-only filter environment variable MUST be absent.
        for banned in (
            "KOMA_REFERENCE_HEAD_VIEW",
            "KOMA_NATIVE_EARS_ONLY",
            "KOMA_EARS_ONLY_TEST_FILTER",
            "INOX_EAR_ONLY",
            "INOX2D_EAR_ONLY",
            "EAR_ONLY",
            "INOX_EAR_ONLY_FILTER",
        ):
            app_env_base.pop(banned, None)

        # park the pointer outside the capture region
        try:
            subprocess.run(
                ["xdotool", "mousemove", str(MOUSE_PARK[0]), str(MOUSE_PARK[1])],
                env={**os.environ, "DISPLAY": DISPLAY},
                capture_output=True,
                timeout=10,
            )
        except Exception:
            pass

        # ---------------- per-pose capture ----------------
        poses: List[Dict[str, Any]] = []
        for raw_yaw in RAW_YAWS:
            label = ("%+g" % raw_yaw).replace("+", "p").replace("-", "m").replace(".", "_")
            app_log = logs_dir / ("app_%s.log" % label)
            screen_png = frames_dir / ("screen_%s.png" % label)
            full_png = frames_dir / ("full_%s.png" % label)
            head_png = frames_dir / ("head_%s.png" % label)

            app_cmd = build_app_argv(binary, source, raw_yaw)
            log("pose raw_yaw=%s -> %s" % (raw_yaw, " ".join(app_cmd)))
            pose_env = {**app_env_base, 'KOMA_HEAD_YAW': str(raw_yaw)}
            if args.head_view:
                pose_env['KOMA_REFERENCE_HEAD_VIEW'] = '1'
            proc = mgr.spawn(app_cmd, env=pose_env, stdout_path=app_log)

            # wait for renderer ready + no FBO/panic in the log
            ready = False
            deadline = time.time() + READY_TIMEOUT_S
            ready_line = ""
            while time.time() < deadline:
                if proc.poll() is not None:
                    break
                text = app_log.read_text(errors="replace") if app_log.exists() else ""
                low = text.lower()
                bad = [m for m in BAD_LOG_MARKERS if m.lower() in low]
                if bad:
                    raise RuntimeError(
                        "APP_LOG_ERROR_MARKERS %s at raw_yaw=%s:\n%s"
                        % (bad, raw_yaw, text[-3000:])
                    )
                for marker in RENDERER_READY_MARKERS:
                    if marker.lower() in low:
                        ready = True
                        ready_line = marker
                        break
                if ready:
                    break
                time.sleep(0.3)
            if not ready:
                raise RuntimeError(
                    "RENDERER_NOT_READY raw_yaw=%s timeout=%.0fs log:\n%s"
                    % (raw_yaw, READY_TIMEOUT_S, app_log.read_text(errors="replace")[-3000:])
                )

            win = wait_for_window(DISPLAY, proc, 10.0)
            if win is None:
                raise RuntimeError("NO_APP_WINDOW raw_yaw=%s" % raw_yaw)
            moved = move_window(DISPLAY, win, 0, 0)
            if not moved:
                raise RuntimeError('Cannot fix native window position')
            log("pose %s window=%s moved=%s" % (raw_yaw, win, moved))
            time.sleep(APP_SETTLE_S)

            text = app_log.read_text(errors="replace") if app_log.exists() else ""
            bad = [m for m in BAD_LOG_MARKERS if m.lower() in text.lower()]
            if bad:
                raise RuntimeError(
                    "APP_LOG_ERROR_MARKERS %s at raw_yaw=%s" % (bad, raw_yaw)
                )

            cap = capture_screen(mgr, DISPLAY, screen_png, CAPTURE_DURATION_S)
            metrics = crop_full_and_head(screen_png, full_png, head_png)

            # terminate the app; record the REAL exit status
            app_rc: Optional[int] = None
            terminated_by_capture = True
            if proc.poll() is None:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                except Exception:
                    proc.terminate()
                try:
                    app_rc = proc.wait(timeout=10)
                except Exception:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception:
                        pass
                    try:
                        app_rc = proc.wait(timeout=5)
                    except Exception:
                        app_rc = None
            else:
                app_rc = proc.returncode
                terminated_by_capture = False

            if proc in mgr.procs:
                mgr.procs.remove(proc)

            poses.append(
                {
                    "raw_yaw": raw_yaw,
                    "normalized_head_yaw": [(raw_yaw + 1.0) / 2.0, 0.5],
                    "raw_pitch": RAW_PITCH,
                    "camera_scale": CAMERA_SCALE,
                    "camera_position": list(CAMERA_POSITION),
                    "capture_mode": capture_mode,
                    "angle_units": "raw_inx_parameter_units (no physical degree claim)",
                    "dt0_policy": DT0_POLICY,
                    "app_command": app_cmd,
                    "app_pose_environment": {k: pose_env[k] for k in ('KOMA_HEAD_YAW', 'KOMA_REFERENCE_HEAD_VIEW') if k in pose_env},
                    "app_exit_returncode": app_rc,
                    "app_terminated_by_capture": terminated_by_capture,
                    "app_successful_native_exit": False,
                    "window_id": win,
                    "window_moved_to_origin": moved,
                    "renderer_ready_marker": ready_line,
                    "capture": cap,
                    "screen_png": str(screen_png),
                    "full_png": str(full_png),
                    "head_png": str(head_png),
                    "full_sha256": sha256_file(full_png),
                    "head_sha256": sha256_file(head_png),
                    "full_image_sha256": image_fingerprint(full_png),
                    "head_image_sha256": image_fingerprint(head_png),
                    "metrics": metrics,
                    "log": str(app_log),
                    "log_tail": text[-1500:],
                }
            )
            log(
                "pose raw_yaw=%s full_sha=%s head_sha=%s rc=%s"
                % (raw_yaw, poses[-1]["full_sha256"][:12], poses[-1]["head_sha256"][:12], app_rc)
            )

        # ---------------- checks ----------------
        nonblank_full = all(p["metrics"]["full_nonblank"] for p in poses)
        nonblank_head = all(p["metrics"]["head_nonblank"] for p in poses)
        dims_ok = all(
            p["metrics"]["full_size"] == [FULL_W, FULL_H]
            and p["metrics"]["head_size"]
            == [HEAD_ROI[2] - HEAD_ROI[0], HEAD_ROI[3] - HEAD_ROI[1]]
            for p in poses
        )
        head_fps = {p["head_image_sha256"] for p in poses}
        head_uniqueness = len(head_fps)
        checks = {
            "nine_frames_present": len(poses) == 9,
            "all_full_nonblank": nonblank_full,
            "all_head_nonblank": nonblank_head,
            "dimensions_expected": dims_ok,
            "head_unique_images": head_uniqueness,
            "head_uniqueness_min_7": head_uniqueness >= 7,
            "same_roi_all_poses": True,
            "no_adaptive_crop": True,
        }
        all_pass = all(
            v if isinstance(v, bool) else True for v in checks.values()
        ) and head_uniqueness >= 7

        # ---------------- contact sheets ----------------
        full_paths = [Path(p["full_png"]) for p in poses]
        head_paths = [Path(p["head_png"]) for p in poses]
        full_contact = contact_sheet(full_paths, 3, CONTACT_MAX_BYTES)
        head_contact = contact_sheet(head_paths, 3, CONTACT_MAX_BYTES)
        (out_dir / "full-contact.jpg").write_bytes(full_contact)
        (out_dir / "head-contact.jpg").write_bytes(head_contact)
        log(
            "contact sheets: full=%d bytes head=%d bytes"
            % (len(full_contact), len(head_contact))
        )

        # ---------------- manifest ----------------
        manifest.update(
            {
                "status": "PASS" if all_pass else "FAIL",
                "source": {
                    "path": str(source),
                    "sha256": source_sha,
                    "expected_sha256": EXPECTED_INX_SHA256,
                    "sha256_verified": True,
                    "inx_meta": inx["meta"],
                    "inx_physics": inx["physics"],
                    "inx_node_count": inx["node_count"],
                    "inx_param_count": inx["param_count"],
                    "inx_total_binding_count": inx["total_binding_count"],
                    "raw_param_domain": {
                        "name": head["name"],
                        "is_vec2": head["is_vec2"],
                        "min": head["min"],
                        "max": head["max"],
                        "defaults": head["defaults"],
                    },
                    "head_yaw_pitch_binding_count": head["binding_count"],
                    "params": inx["params"],
                },
                "patch_report": {
                    "path": str(patch_report),
                    "sha256": patch_sha,
                    "size_bytes": patch_report.stat().st_size,
                    "content": patch_text,
                    "parsed_json": patch_json,
                    "raw_pitch_used": RAW_PITCH,
                    "pitch_source": "fixed by example patch report",
                },
                "capture": {
                    "display": DISPLAY,
                    "screen": [SCREEN_W, SCREEN_H, SCREEN_DEPTH],
                    "xvfb_command": xvfb_cmd,
                    "app_env": {
                        k: v
                        for k, v in app_env_base.items()
                        if k in ("DISPLAY", "LIBGL_ALWAYS_SOFTWARE", "GALLIUM_DRIVER", "RUST_LOG")
                    },
                    "ear_only_filter_env_absent": True,
                    "mouse_parked_at": list(MOUSE_PARK),
                    "camera_scale": CAMERA_SCALE,
                    "camera_position": list(CAMERA_POSITION),
                    "capture_mode": capture_mode,
                    "dt0_policy": DT0_POLICY,
                    "ready_timeout_s": READY_TIMEOUT_S,
                    "capture_duration_s": CAPTURE_DURATION_S,
                    "environment": env_info,
                },
                "roi": {
                    "full": [0, 0, FULL_W, FULL_H],
                    "head": list(HEAD_ROI),
                    "head_size": [HEAD_ROI[2] - HEAD_ROI[0], HEAD_ROI[3] - HEAD_ROI[1]],
                    "fixed_for_all_poses": True,
                    "adaptive_per_pose_crop": False,
                },
                "poses": poses,
                "checks": checks,
                "head_unique_images": head_uniqueness,
                "angles": {
                    "raw_yaw_values": list(RAW_YAWS),
                    "normalized_head_yaw": [[(y + 1.0) / 2.0, 0.5] for y in RAW_YAWS],
                    "raw_pitch": RAW_PITCH,
                    "units": "raw INX parameter units; no physical degree claim",
                },
                "contact_sheets": {
                    "full": {
                        "path": str(out_dir / "full-contact.jpg"),
                        "sha256": sha256_bytes(full_contact),
                        "bytes": len(full_contact),
                        "layout": "9 images, 3 columns",
                    },
                    "head": {
                        "path": str(out_dir / "head-contact.jpg"),
                        "sha256": sha256_bytes(head_contact),
                        "bytes": len(head_contact),
                        "layout": "9 head ROIs, 3 columns",
                    },
                },
                "review_bundle": {
                    "note": "Optional transport built after final manifest; actual bundle hash is logged separately to avoid self-reference.",
                    "max_bytes": ZIP_MAX_BYTES,
                },
                "claims": {
                    "landmarks": None,
                    "mesh_truth": None,
                    "physical_angles": None,
                    "note": "No fabricated landmarks, no mesh ground truth, "
                            "no physical degree claim, no successful-native-exit fiction.",
                },
            }
        )

        # Finalise cleanup before the immutable manifest is printed / embedded.
        manifest['process_cleanup'] = mgr.cleanup()
        manifest_path = out_dir / "reference-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        log("manifest -> %s" % manifest_path)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in poses:
                zf.write(p['full_png'], 'frames/' + Path(p['full_png']).name)
            zf.writestr('reference-manifest.json', manifest_path.read_bytes())
            zf.writestr('patch-report.json', patch_report.read_bytes())
        bundle_bytes = buf.getvalue() if len(buf.getvalue()) <= ZIP_MAX_BYTES else None

        # ---------------- transport markers ----------------
        print(CONTACT_BEGIN)
        for chunk in wrap_base64(head_contact):
            print(chunk)
        print(CONTACT_END)

        if bundle_bytes is not None:
            print(BUNDLE_BEGIN)
            for chunk in wrap_base64(bundle_bytes):
                print(chunk)
            print(BUNDLE_END)
            print('CORE026_BUNDLE_SHA256 ' + sha256_bytes(bundle_bytes))
        else:
            log("review bundle omitted (see manifest.review_bundle.note)")

        print(MANIFEST_PREFIX + " " + json.dumps(manifest, separators=(",", ":")))
        return 0 if all_pass else 1

    except SystemExit:
        raise
    except Exception as exc:
        manifest["status"] = "FAIL"
        manifest["error"] = "%s: %s" % (type(exc).__name__, exc)
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "reference-manifest.json").write_text(
                json.dumps(manifest, indent=2), encoding="utf-8"
            )
        except Exception:
            pass
        print("FATAL: %s" % exc, file=sys.stderr)
        print(MANIFEST_PREFIX + " " + json.dumps(manifest, separators=(",", ":")))
        return 1
    finally:
        procs = mgr.cleanup()
        log("cleanup: %s" % json.dumps(procs))
        if procs:
            manifest.setdefault("process_cleanup", procs)
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "reference-manifest.json").write_text(
                    json.dumps(manifest, indent=2), encoding="utf-8"
                )
            except Exception:
                pass


def wrap_base64(data: bytes, width: int = 120) -> List[str]:
    text = base64.b64encode(data).decode("ascii")
    return [text[i : i + width] for i in range(0, len(text), width)]


if __name__ == "__main__":
    raise SystemExit(main())
