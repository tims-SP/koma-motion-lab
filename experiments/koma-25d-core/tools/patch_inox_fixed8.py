#!/usr/bin/env python3
"""Modify only pinned Inox2D OpenGL demo so its actual INX parameter is fixed.

Configured through env KOMA_HEAD_YAW in [-1,1], KOMA_HEAD_PITCH=0. Does NOT
map these 2D parameter values to measured degrees. Original mesh, topology,
textures, native parameter bindings and rendering pipeline remain upstream.
"""
import argparse,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--checkout",type=Path,required=True)
ap.add_argument("--report",type=Path,required=True)
a=ap.parse_args()
file=a.checkout/"examples/render-opengl/src/main.rs"
text=file.read_text()
before='.set("Head:: Yaw-Pitch", Vec2::new(t.cos(), t.sin()));'
after='''.set("Head:: Yaw-Pitch", Vec2::new({
                    let yaw = std::env::var("KOMA_HEAD_YAW")
                        .expect("KOMA_HEAD_YAW must be explicitly supplied")
                        .parse::<f32>()
                        .expect("Invalid KOMA_HEAD_YAW");
                    assert!((-1.0..=1.0).contains(&yaw), "Parameter out of range");
                    yaw
                }, 0.0));'''
assert text.count(before)==1,"Unexpected upstream source: prevent silent patch"
text=text.replace(before,after)
assert text.count("width: 0,")==1 and text.count("height: 0,")==1
text=text.replace("width: 0,","width: 720,").replace("height: 0,","height: 880,")
assert text.count("PhysicalSize::new(600, 800)")==1
text=text.replace("PhysicalSize::new(600, 800)","PhysicalSize::new(720, 880)")
file.write_text(text)
a.report.parent.mkdir(parents=True,exist_ok=True)
d={"status":"EXACT_PINNED_UPSTREAM_OPENGL_FIXED_PARAMETER_PATCH",
 "upstream":"Inochi2D/inox2d","commit":"d4dd9dd7f16b775042cbda44370570abf9a8cf81",
 "original_asset":"Aka.inx by seagetch CC BY 4.0",
 "pose_axis":"Head:: Yaw-Pitch", "yaw_env":"KOMA_HEAD_YAW",
 "pitch_normalized":0,"yaw_grid":[0,0.25,0.5,0.75,1.0],
 "display":"Xvfb + llvmpipe OpenGL", "fixed_window":[720,880],
 "initial_fbo_dimensions":"720x880_not_0x0",
 "source_geometry":"UNMODIFIED_NATIVE_INX_ARTMESH",
 "physical_yaw_degrees":"UNKNOWN",
 "native_D_sdk_pixel_parity":"NOT_TESTED",
 "approach":"Launch a FRESH original renderer process for each parameter, capture screen; no frame-interpolation or AI-generated art"}
a.report.write_text(json.dumps(d,indent=2)+"\n")
print("CORE008_FIXED_POSE_PATCH",json.dumps(d))
