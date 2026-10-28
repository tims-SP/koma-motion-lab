#!/usr/bin/env python3
"""PROD-006: Bake source Spine weighted-vertex motion into native Rive Mesh frames.

This is a production fallback when the native Rive Skin/Tendon binding does not
render. It uses actual original Spine mesh influences, UVs and decoded animation
bone rotations. Every frame is a newly rendered RML Mesh in official Rive CLI.
It does NOT claim a reusable native Rive weighted rig or complete Spine parity.
Original copyrighted assets, RML and MP4 stay only in runner scratch storage.
"""
from __future__ import annotations
import hashlib,json,math,os,shutil,subprocess,sys
from pathlib import Path
from PIL import Image
import spine_textured_rive as src

ROOT=src.ROOT
OUT=src.OUT
REPORT={"experiment":"PROD-006 Spine weighted mesh bake to Rive", "status":"NOT_STARTED",
        "limitations":["Not a reusable skinned .riv","Spine non-rotation timelines not sampled",
          "IK/path/transform constraints and FFD not solved",
          "Simple linear source key interpolation, not cubic Bezier",
          "Does not prove exact frame equivalence to Spine runtime"],
        "source_art_uploaded":False}

def main():
    # Existing PROD-004 created this path with an RML file. Avoid duplicate IDs.
    shutil.rmtree(ROOT/"source-mesh-rive",ignore_errors=True)
    tree,project,bones,objects,doc,imported=src.construct()
    root=tree.getroot()
    action=doc.get("animations",{}).get("idle_room")
    if action is None:raise RuntimeError("Source idle_room action missing")
    tracks={name:timeline["rotate"] for name,timeline in action.get("bones",{}).items()
        if isinstance(timeline,dict) and isinstance(timeline.get("rotate"),list)}
    skins=doc.get("skins",[])
    entries=skins[0].get("attachments",{}) if isinstance(skins,list) else skins.get("default",{})
    slot_lookup={slot["name"]:slot for slot in doc["slots"]}
    active={}
    for image in root.iter("Image"):
        name=image.get("name","")
        if not name.startswith("src_"):continue
        slot=name[4:]
        if slot not in slot_lookup:continue
        att_name=slot_lookup[slot].get("attachment")
        att=entries.get(slot,{}).get(att_name)
        if not isinstance(att,dict):continue
        mesh=next((m for m in image if m.tag=="Mesh"),None)
        if mesh is None:continue
        for skin in list(mesh.findall("Skin")):mesh.remove(skin)
        vertices=mesh.findall("ContourMeshVertex")
        for vert in vertices:
            for w in list(vert.findall("Weight")):vert.remove(w)
        active[slot]={"mesh":mesh,"vertices":vertices,"attachment":att,
                      "bone":slot_lookup[slot]["bone"]}
    if not active:raise RuntimeError("No active Spine meshes to bake")
    REPORT["source_mesh_slots"]=len(active)
    REPORT["source_weighted_slots"]=sum(len(x["attachment"].get("vertices",[]))>len(x["attachment"].get("uvs",[])) for x in active.values())
    REPORT["original_source_rotation_channels"]=len(tracks)
    duration=2.0;fps=12;count=24
    hashes=[];changed_vertex_count=[]
    previous=None
    frames=ROOT/"source-weight-baked-frames"
    frames.mkdir(exist_ok=True)
    for frame in range(count):
        t=duration*frame/(count-1)
        sample_bones=[dict(b) for b in bones]
        for bone in sample_bones:
            if bone["name"] in tracks:
                bone["rotation"]=float(bone.get("rotation",0))+src.frame_value(tracks[bone["name"]],t)
        world=src.world_transform(sample_bones)
        updates=0;vertices_now=[]
        for slot,info in active.items():
            geometry=src.parse_attachment(info["attachment"],sample_bones,world,info["bone"])
            if geometry is None:continue
            xyz=geometry["vertex"]
            if len(xyz)!=len(info["vertices"]):raise RuntimeError(f"Mesh topology changed: {slot}")
            for vert,(x,y,weights) in zip(info["vertices"],xyz):
                vert.set("x",f"{x:.8g}")
                vert.set("y",f"{y:.8g}")
                updates+=1
                vertices_now.append((round(x,5),round(y,5)))
        if not updates:raise RuntimeError("No vertices baked at frame "+str(frame))
        if previous is not None:
            changed_vertex_count.append(sum(a!=b for a,b in zip(previous,vertices_now)))
        previous=vertices_now
        tree.write(project/"scene.rml",encoding="unicode")
        if frame==0:
            src.run(["rive",str(project),"--verify"])
            ins=src.run(["rive","inspect",str(project),"--summary"]).stdout
            REPORT["rive_inspect_problems"]=json.loads(ins).get("problems",[])
        dest=frames/f"{frame:04d}.png"
        src.run(["rive",str(project),f"--screenshot={dest}","--viewport=640x360","--advance=0s"])
        with Image.open(dest) as image:
            px=image.convert("RGBA").tobytes()
        hashes.append(hashlib.sha256(px).hexdigest())
    REPORT.update({"rendered_frames":count,"unique_rendered_frames":len(set(hashes)),
        "animation_duration_seconds":duration,"fps":fps,
        "total_mapped_vertices":sum(len(x["vertices"]) for x in active.values()),
        "frames_with_changed_vertices":sum(x>0 for x in changed_vertex_count),
        "max_changed_vertices":max(changed_vertex_count or [0]),
        "native_rive_skinning":False,
        "real_source_weighted_deformation_baked":True})
    if len(set(hashes))<6:raise RuntimeError("Rive renders do not show mesh motion")
    if REPORT["frames_with_changed_vertices"]<16:raise RuntimeError("Animation samples have insufficient changing source vertices")
    mp4=ROOT/"actual-source-weight-baked-private.mp4"
    src.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-framerate",str(fps),
            "-i",str(frames/"%04d.png"),"-c:v","libx264","-pix_fmt","yuv420p",str(mp4)])
    REPORT["private_mp4_size"]=mp4.stat().st_size
    REPORT["private_mp4_sha256"]=hashlib.sha256(mp4.read_bytes()).hexdigest()
    REPORT["status"]="PASS_BAKED_SOURCE_WEIGHT_MOTION"

def finish():
    (OUT/"weighted-bake-result.json").write_text(json.dumps(REPORT,indent=2,ensure_ascii=False)+"\n")
    s=["# PROD-006 · Real Spine weighted animation baked into Rive headless frames","",
        "**Status:** "+REPORT["status"],"",
        "| Check | Result |","|---|---|"]
    for k in ("source_mesh_slots","source_weighted_slots","original_source_rotation_channels",
              "total_mapped_vertices","rendered_frames","unique_rendered_frames",
              "frames_with_changed_vertices","max_changed_vertices","native_rive_skinning","private_mp4_size"):
        s.append(f"| {k} | {REPORT.get(k,'NOT_TESTED')} |")
    s+=["","**Technical distinction:** Source Spine mesh weights and original bone-rotation tracks are",
        "used to compute vertex locations per frame. Rive draws the resulting Mesh images.",
        "This is real source-weighted pose deformation, but is NOT a live native Rive Skin.",
        "The source game-art MP4 stays private to the ephemeral GitHub runner.",
        "","Failure detail: "+str(REPORT.get("error","none"))]
    (OUT/"weighted-bake-summary.md").write_text("\n".join(s)+"\n")
    print((OUT/"weighted-bake-summary.md").read_text(),flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        REPORT["status"]="FAIL";REPORT["error"]=repr(e)
    finish()
    if REPORT["status"]!="PASS_BAKED_SOURCE_WEIGHT_MOTION":sys.exit(1)
