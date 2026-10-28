#!/usr/bin/env python3
"""PROD-008: multi-action Spine transform timelines baked to Rive Mesh renders.

Preserves original Spine mesh UV/triangles/skin weights through the existing
converter. Advances beyond rotate-only by sampling translate/scale/shear
alongside rotation for a number of *real* source clips.

Intentionally excludes IK/transform/path solvers, slot draw-order changes,
deform/FFD timelines, source cubic curves and original Spine runtime parity.
All copyrighted media remain ONLY in the ephemeral GitHub Actions runner.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import hashlib, json, math, os, shutil, sys
import spine_textured_rive as src
from PIL import Image

ROOT=src.ROOT
OUT=src.OUT
VERSION="0.1"
REPORT={
    "experiment":"PROD-008",
    "status":"NOT_STARTED",
    "source":"myssal/Reverse-1999-CN-Asset 300401_hongnujian room.skel Spine 4.2.36",
    "source_original_runtime_parity":"NOT_TESTED",
    "output_render_engine":"Rive CLI",
    "native_rive_live_skin":False,
    "source_original_artifacts_uploaded":False,
    "source_visual_assets_exported":False,
    "unsupported":["Spine IK/transform/path/physics constraints", "deform/FFD timelines",
        "animated draw order and attachment switching", "Bezier exact interpolation",
        "source Spine runtime pixel parity", "other source skin variants"],
    "actions":{}
}

# Rive can render the original texture atlas and mesh coordinates, but this
# version computes skinned world vertices from the Spine rig per sampled frame.
# Source bone channels must therefore be evaluated before world_transform().
CHANNELS={
  "rotate":"rotation", "rotation":"rotation",
  "translate":"translation", "translatex":"translation", "translatey":"translation",
  "scale":"scale", "scalex":"scale", "scaley":"scale",
  "shear":"shear", "shearx":"shear", "sheary":"shear",
}

def timeline_times(value):
    if isinstance(value,list):
        for obj in value:
            yield from timeline_times(obj)
    elif isinstance(value,dict):
        if isinstance(value.get("time"),(int,float)):
            yield float(value["time"])
        for k,v in value.items():
            if k!="time":yield from timeline_times(v)

def interpolate(a,b,f):
    return a+(b-a)*f

def sample_value(keys,time,field,default=0.0,diag=None):
    """Step or linear sample of one axis; never pretend curve Bezier is exact."""
    points=[]
    for key in keys:
        if not isinstance(key,dict):continue
        raw=key.get(field,default)
        if isinstance(raw,(int,float)):points.append((float(key.get("time",0)),float(raw),key))
    if not points:return default
    points.sort(key=lambda x:x[0])
    if time<=points[0][0]:return points[0][1]
    for i in range(len(points)-1):
        t0,v0,k0=points[i];t1,v1,k1=points[i+1]
        if time<=t1:
            if t1==t0:return v1
            curve=k0.get("curve")
            if curve=="stepped":return v0
            if curve is not None and diag is not None:
                diag.add("source_curve_not_exactly_preserved")
            return interpolate(v0,v1,(time-t0)/(t1-t0))
    return points[-1][1]

def sample_pair(keys,t,axes,defaults,diag):
    ax,ay=axes
    return (
      sample_value(keys,t,ax,defaults[0],diag),
      sample_value(keys,t,ay,defaults[1],diag)
    )

def pose_source_bones(bones, tracks,t,diag):
    output=[dict(b) for b in bones]
    for bone in output:
        timelines=tracks.get(bone["name"],{})
        if not isinstance(timelines,dict):continue
        for typ, keys in timelines.items():
            if not isinstance(keys,list) or not keys:continue
            if typ not in CHANNELS:continue
            if typ in ("rotate","rotation"):
                bone["rotation"]=float(bone.get("rotation",0)) + sample_value(keys,t,"angle",0.,diag)
            elif typ=="translate":
                dx,dy=sample_pair(keys,t,("x","y"),(0.,0.),diag)
                bone["x"]=float(bone.get("x",0))+dx
                bone["y"]=float(bone.get("y",0))+dy
            elif typ=="translatex":
                bone["x"]=float(bone.get("x",0))+sample_value(keys,t,"x",0.,diag)
            elif typ=="translatey":
                bone["y"]=float(bone.get("y",0))+sample_value(keys,t,"y",0.,diag)
            elif typ=="scale":
                x,y=sample_pair(keys,t,("x","y"),(1.,1.),diag)
                bone["scaleX"]=float(bone.get("scaleX",1))*x
                bone["scaleY"]=float(bone.get("scaleY",1))*y
            elif typ=="scalex":
                bone["scaleX"]=float(bone.get("scaleX",1))*sample_value(keys,t,"x",1.,diag)
            elif typ=="scaley":
                bone["scaleY"]=float(bone.get("scaleY",1))*sample_value(keys,t,"y",1.,diag)
            elif typ=="shear":
                x,y=sample_pair(keys,t,("x","y"),(0.,0.),diag)
                bone["shearX"]=float(bone.get("shearX",0))+x
                bone["shearY"]=float(bone.get("shearY",0))+y
            elif typ=="shearx":
                bone["shearX"]=float(bone.get("shearX",0))+sample_value(keys,t,"x",0.,diag)
            elif typ=="sheary":
                bone["shearY"]=float(bone.get("shearY",0))+sample_value(keys,t,"y",0.,diag)
    return output

def setup_scene():
    # Avoid re-using stale RML from PROD-004 / PROD-006.
    shutil.rmtree(ROOT/"source-mesh-rive",ignore_errors=True)
    tree,project,bones,objects,doc,imported=src.construct()
    root=tree.getroot()
    # Preserve the unmodified, native Bone/Mesh/Skin RML before this
    # per-frame bake removes the native Skin and Weight elements.
    # PROD-009 packages this saved original RML, not the rive-create blank template.
    tree.write(ROOT/"spine-native-rig-scaffold.rml",encoding="unicode")
    skins=doc.get("skins",[])
    entries=skins[0].get("attachments",{}) if isinstance(skins,list) else skins.get("default",{})
    slots={x["name"]:x for x in doc["slots"]}
    active={}
    for image in root.iter("Image"):
        name=image.get("name","")
        if not name.startswith("src_"):continue
        slot=name[4:]
        if slot not in slots:continue
        a=entries.get(slot,{}).get(slots[slot].get("attachment"))
        mesh=next((m for m in image if m.tag=="Mesh"),None)
        if not isinstance(a,dict) or mesh is None:continue
        for s in list(mesh.findall("Skin")):mesh.remove(s)
        verts=mesh.findall("ContourMeshVertex")
        for vertex in verts:
            for w in list(vertex.findall("Weight")):vertex.remove(w)
        active[slot]={"vertices":verts,"attachment":a,"bone":slots[slot]["bone"]}
    if not active:raise RuntimeError("Rive converter created no source mesh images")
    return tree,project,bones,objects,doc,active

def clip_coverage(name,clip):
    tracks=clip.get("bones",{})
    channels=Counter()
    for d in tracks.values():
        if isinstance(d,dict):
            for k,v in d.items():
                if isinstance(v,list):channels[k]+=len(v)
    unsupported={k:len(v) if isinstance(v,(dict,list)) else 1 for k,v in clip.items()
                  if k not in ("bones","duration")}
    return {
       "channels_keys":dict(channels),
       "supported_source_key_count":sum(n for k,n in channels.items() if k in CHANNELS),
       "unsupported_bone_channels":{k:v for k,v in channels.items() if k not in CHANNELS},
       "nonbone_tracks":unsupported,
       "source_duration":max(timeline_times(clip),default=0.)
    }

def run():
    tree,project,bones,objects,doc,active=setup_scene()
    animations=doc.get("animations",{})
    if not animations:raise RuntimeError("No animations decoded")
    REPORT["all_source_animation_names"]=sorted(animations)
    REPORT["all_source_animation_count"]=len(animations)
    REPORT["source_mesh_slots_active"]=len(active)
    REPORT["source_vertex_total"]=sum(len(v["vertices"]) for v in active.values())
    REPORT["source_bone_count"]=len(bones)
    REPORT["coverage"]={a:clip_coverage(a,c) for a,c in animations.items()}
    ranked=[a for a in ("idle_room","walk","sleep","hit","click","idle") if a in animations]
    ranked=ranked[:4]
    if len(ranked)<3: ranked=(ranked+[x for x in animations if x not in ranked])[:4]
    REPORT["tested_actions"]=ranked
    frames=ROOT/"multichannel-baked-frames"
    frames.mkdir(exist_ok=True)
    all_frames=0
    for name in ranked:
        clip=animations[name]
        bone_tracks=clip.get("bones",{})
        duration=min(2.0,max(.5,REPORT["coverage"][name]["source_duration"]))
        fps=12;count=12
        local_dir=frames/name;local_dir.mkdir(exist_ok=True)
        used=set();image_hashes=[];verts_prev=None;vertex_changes=0
        for i in range(count):
            t=i*duration/(count-1)
            posed=pose_source_bones(bones,bone_tracks,t,used)
            world=src.world_transform(posed)
            positions=[]
            for slot,info in active.items():
                geo=src.parse_attachment(info["attachment"],posed,world,info["bone"])
                if geo is None or len(geo["vertex"])!=len(info["vertices"]):
                    raise RuntimeError("Source topology mismatch: "+slot)
                for vertex,(x,y,inf) in zip(info["vertices"],geo["vertex"]):
                    vertex.set("x",f"{x:.8g}");vertex.set("y",f"{y:.8g}")
                    positions.append((round(x,4),round(y,4)))
            if verts_prev is not None and positions!=verts_prev: vertex_changes+=1
            verts_prev=positions
            tree.write(project/"scene.rml",encoding="unicode")
            if i==0:
                src.run(["rive",str(project),"--verify"])
                parsed=json.loads(src.run(["rive","inspect",str(project),"--summary"]).stdout)
                if parsed.get("problems"):raise RuntimeError("Rive inspect errors for "+name)
            out=local_dir/f"{i:04d}.png"
            src.run(["rive",str(project),f"--screenshot={out}","--viewport=640x360","--advance=0s"])
            with Image.open(out) as im:
                px=im.convert("RGBA").tobytes()
            image_hashes.append(hashlib.sha256(px).hexdigest())
            all_frames+=1
        unique=len(set(image_hashes))
        mp4=ROOT/f"spine-{name}-multichannel-private.mp4"
        src.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                 "-framerate",str(fps),"-i",str(local_dir/"%04d.png"),
                 "-c:v","libx264","-pix_fmt","yuv420p",str(mp4)])
        REPORT["actions"][name]={
          "status":"RENDERED" if unique>=2 else "STATIC_OR_MISSING_MOTION",
          "source_timeline_channels":REPORT["coverage"][name]["channels_keys"],
          "sampled_frames":count,"unique_rasters":unique,
          "frames_with_changed_vertices":vertex_changes,
          "duration_sampled":duration,
          "interpolation_caveats":sorted(used),
          "private_mp4_bytes":mp4.stat().st_size,
          "source_art_uploaded":False
        }
        print(name,REPORT["actions"][name],flush=True)
    REPORT["total_rive_frames"]=all_frames
    REPORT["status"]="PASS_PARTIAL_MULTICHANNEL" if sum(x["unique_rasters"]>=2 for x in REPORT["actions"].values())>=2 else "FAIL_UNEXPECTED_STATIC"
    REPORT["preserved"]=["source mesh vertex identities","source UVs/triangles",
         "original static slot ordering for exported meshes",
         "source weighted skinning baked at sample times",
         "sampled rotate, translate, scale and shear bone channels"]
    REPORT["actual_native_rive_animation_tracks"]=False
    REPORT["actual_original_animation_fidelity"]="NOT_TESTED"
    # Several proprietary source assets are sampled; only de-identified
    # metadata/report is saved under the public GitHub workspace.

def finish():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"multichannel-result.json").write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n")
    s=["# PROD-008 · Spine multiple-action full-transform bake into Rive","",
       f"**Status:** {REPORT['status']}","",
       f"Source actions discovered: {REPORT.get('all_source_animation_count','?')}; sampled clips: {', '.join(REPORT.get('tested_actions',[]))}.","",
       "| Action | Source key channels | Rive frames | Unique rasters | Changed mesh frames |",
       "|---|---:|---:|---:|---:|"]
    for a,v in REPORT["actions"].items():
        n=sum(v["source_timeline_channels"].values())
        s.append(f"| {a} | {n} | {v['sampled_frames']} | {v['unique_rasters']} | {v['frames_with_changed_vertices']} |")
    s += ["","**This is a Rive-rendered frame bake**, not a complete editable Spine-rig-to-Rive animation conversion.",
      "IK/path/deform/Bezier/slot switching and independent source-runtime comparison remain outstanding.",
      "Videos with actual game art remain in the temporary runner. Only JSON summaries are uploaded.",
      "","Failure: "+str(REPORT.get("error","none"))]
    (OUT/"multichannel-summary.md").write_text("\n".join(s)+"\n")
    print((OUT/"multichannel-summary.md").read_text(),flush=True)

if __name__=="__main__":
    try:run()
    except Exception as exc:
        REPORT["status"]="FAIL"
        REPORT["error"]=repr(exc)
    finish()
    if REPORT["status"]!="PASS_PARTIAL_MULTICHANNEL":sys.exit(1)
