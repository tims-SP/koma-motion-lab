#!/usr/bin/env python3
"""Pin/patch a tiny upstream Inox2D sample; preserve actual native rendering.

This does not rewrite Inochi rendering. It changes only the test parameter
and window dimensions in upstream Rust OpenGL demo. All other source code is
upstream unchanged. Display and MP4 are captured by Xvfb + ffmpeg.
"""
import argparse,json,re
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--checkout",type=Path,required=True)
ap.add_argument("--report",type=Path,required=True)
a=ap.parse_args()
main=a.checkout/"examples/render-opengl/src/main.rs"
assert main.is_file(), "Missing upstream example"
src=main.read_text()
before='.set("Head:: Yaw-Pitch", Vec2::new(t.cos(), t.sin()));'
after='''.set("Head:: Yaw-Pitch", Vec2::new({
                    // Fixed-camera positive-yaw arc. Model param units [-1,1]
                    // are NOT guaranteed physical degrees.
                    let phase = (((t % 6.0) - 0.7).max(0.0) / 4.0).clamp(0.0, 1.0);
                    (phase * std::f32::consts::PI).sin() * 0.85
                }, 0.0));'''
assert src.count(before)==1, "Upstream sample changed; refuse silent fallback"
src=src.replace(before,after)
assert src.count("Vec2::splat(0.15)")==1, "Unexpected upstream camera source"
# Keep upstream source camera. It was demonstrated to work for Aka.
assert src.count('WindowBuilder::new()')==1
src=src.replace("PhysicalSize::new(600, 800)","PhysicalSize::new(720, 880)")
# Upstream app starts width/height = 0; Mesa under Xvfb may never emit
# an initial Resized event before the first draw. This creates 0x0 FBOs
# and GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT (depth/stencil).
assert src.count("width: 0,")==1 and src.count("height: 0,")==1
src=src.replace("width: 0,","width: 720,").replace("height: 0,","height: 880,")
main.write_text(src)
a.report.parent.mkdir(parents=True,exist_ok=True)
report={
  "status":"PATCHED_EXACT_PINNED_UPSTREAM_OPENGL_EXAMPLE",
  "source_repository":"Inochi2D/inox2d",
  "source_commit":"d4dd9dd7f16b775042cbda44370570abf9a8cf81",
  "parameter":"Head:: Yaw-Pitch",
  "param_start":0,"param_max":0.85,
  "param_pitch":0,
  "duration_control":"REPEATING 6s arc, 0.7s front plus 4.0s positive yaw and return; independent of GUI startup delay",
  "screen":"720x880",
  "patched_zero_size_window":True,
  "why":"Prevent 0x0 depth-stencil FBO on Mesa/Xvfb before first resize callback",
  "official_inx_reference_engine":"INOX2D_RUST_PORT_NOT_CANONICAL_D_SDK",
  "preserved_native_rig":"YES",
  "pose_degrees":"NOT_CALIBRATED",
  "image_generation":"NONE",
  "limitations":["Inox2D does not implement every Inochi feature",
    "Head Yaw parameter is not a metric 3D rotation angle",
    "Source example render is dynamic screen recording under Xvfb"]
}
a.report.write_text(json.dumps(report,indent=2)+"\n")
print("CORE008_NATIVE_PATCH",json.dumps(report))
