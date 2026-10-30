#!/usr/bin/env python3
"""Patch ONLY the pinned upstream Inox2D OpenGL example (render-opengl/src/main.rs)
so the native reference capture is deterministic and reproducible.

Guarantees enforced by this script:
  * exact upstream source patterns must be present (assert count == 1 each);
  * fixed 720x880 window AND fixed initial framebuffer size (720x880, never 0x0);
  * "Head:: Yaw-Pitch" raw parameter driven by KOMA_HEAD_YAW (float in [-1,1]),
    raw pitch fixed to 0.0 (native raw units, NOT degrees);
  * puppet.end_frame(scene_ctrl.dt()) -> puppet.end_frame(0.0) so the time policy
    is "no simulated time advance" (dt = 0);
  * scene_ctrl.update(camera) removed and the unused `t` line removed, so the
    camera is a FIXED camera (declared scale 0.15) with no interactive motion;
  * init_physics() and all native nodes / rendering pipeline stay untouched;
  * NO ear-only draw filter is applied here.

Physical (degree) interpretation of the raw parameter values is UNKNOWN: this
patch never claims a measured physical angle.
"""
import argparse
import hashlib
import json
from pathlib import Path

REPLACEMENTS = []


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sub(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    assert count == 1, f"Unexpected upstream source for {label!r}: found {count} occurrences"
    REPLACEMENTS.append({"id": label, "occurrences": count})
    return text.replace(before, after)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkout", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    a = ap.parse_args()

    file = a.checkout / "examples/render-opengl/src/main.rs"
    assert file.is_file(), f"upstream main.rs not found under {a.checkout}"
    original = file.read_text()
    before_sha = sha256_bytes(original.encode("utf-8"))
    text = original

    # 0) physics + native pipeline must remain exactly as upstream
    assert text.count("model.puppet.init_physics();") == 1, "init_physics() must be preserved"
    assert text.count("model.puppet.init_rendering();") == 1
    assert text.count("model.puppet.init_params();") == 1

    # 1) fixed window + fixed initial framebuffer size (720x880)
    text = sub(text, "width: 0,", "width: 720,", "initial_fbo_width_720")
    text = sub(text, "height: 0,", "height: 880,", "initial_fbo_height_880")
    text = sub(
        text,
        "winit::dpi::PhysicalSize::new(600, 800)",
        "winit::dpi::PhysicalSize::new(720, 880)",
        "window_physical_size_720x880",
    )

    # 2) fixed camera: declare the scale explicitly, drop the interactive update
    text = sub(
        text,
        "renderer.camera.scale = Vec2::splat(0.15);",
        "let fixed_camera_scale: f32 = 0.15;\n\t\t\t\trenderer.camera.scale = Vec2::splat(fixed_camera_scale);",
        "declare_fixed_camera_scale_0_15",
    )
    text = sub(text, "\t\tscene_ctrl.update(&mut renderer.camera);\n", "", "remove_scene_ctrl_update")
    text = sub(
        text,
        "let Some((renderer, scene_ctrl)) = &mut self.on_window else {",
        "let Some((renderer, _)) = &mut self.on_window else {",
        "drop_unused_scene_ctrl_binding_in_draw",
    )
    text = sub(text, "\t\tlet t = scene_ctrl.current_elapsed();\n", "", "remove_unused_t_line")

    # 3) deterministic raw head parameter from KOMA_HEAD_YAW (raw pitch = 0.0)
    text = sub(
        text,
        '.set("Head:: Yaw-Pitch", Vec2::new(t.cos(), t.sin()));',
        '.set("Head:: Yaw-Pitch", Vec2::new({\n'
        "                    let yaw = std::env::var(\"KOMA_HEAD_YAW\")\n"
        "                        .expect(\"KOMA_HEAD_YAW must be explicitly supplied\")\n"
        "                        .parse::<f32>()\n"
        "                        .expect(\"Invalid KOMA_HEAD_YAW\");\n"
        "                    assert!((-1.0..=1.0).contains(&yaw), \"KOMA_HEAD_YAW out of range [-1,1]\");\n"
        "                    yaw\n"
        "                }, 0.0));",
        "head_yaw_pitch_from_env_raw_pitch_zero",
    )

    # 4) deterministic time policy: dt = 0 (no simulated time advance)
    text = sub(text, "puppet.end_frame(scene_ctrl.dt());", "puppet.end_frame(0.0);", "end_frame_dt_zero")

    # 5) no ear-only draw filter is introduced by this patch
    assert "KOMA_NATIVE_EARS_ONLY" not in text, "ear-only draw filter must not be applied"
    assert text.count('std::env::var("KOMA_HEAD_YAW")') == 1, "KOMA_HEAD_YAW must be read exactly once"

    after_sha = sha256_bytes(text.encode("utf-8"))
    file.write_text(text)

    report = {
        "status": "PASS",
        "tool": "tools/core026/patch_native_reference.py",
        "target_file": "examples/render-opengl/src/main.rs",
        "upstream_repo": "Inochi2D/inox2d",
        "upstream_commit": "d4dd9dd7f16b775042cbda44370570abf9a8cf81",
        "source_sha256_before": before_sha,
        "source_sha256_after": after_sha,
        "source_changed": before_sha != after_sha,
        "replacements": REPLACEMENTS,
        "replacement_count": len(REPLACEMENTS),
        "fixed_window": [720, 880],
        "initial_fbo_dimensions": "720x880_not_0x0",
        "head_parameter": {
            "axis": "Head:: Yaw-Pitch",
            "yaw_env": "KOMA_HEAD_YAW",
            "yaw_range": [-1.0, 1.0],
            "yaw_units": "native_raw_parameter_units",
            "raw_pitch": 0.0,
        },
        "time_policy": "puppet.end_frame(0.0) — dt = 0, no simulated time advance",
        "camera": "fixed camera, declared scale 0.15, scene_ctrl.update removed",
        "physics_equilibrium_validated": False,
        "physical_yaw_degrees": "UNKNOWN",
        "physical_pitch_degrees": "UNKNOWN",
        "physical_angle_note": (
            "Raw native parameter values are NOT calibrated to degrees; physical angles are UNKNOWN. "
            "dt=0 means the physics state is the freshly initialised state, NOT a validated equilibrium."
        ),
        "init_physics_preserved": True,
        "native_nodes_and_rendering_preserved": True,
        "ear_only_draw_filter_applied": False,
    }
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + "\n")
    print("CORE026_NATIVE_REFERENCE_PATCH " + json.dumps(report))


if __name__ == "__main__":
    main()
