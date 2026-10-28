#!/usr/bin/env python3
"""Diagnose zero-pixel Rive skinned real-game Mesh, without publishing source art.

Tests original RML and alternative bind-pose/tendon transform conventions.
Each variant runs inside ephemeral GitHub Actions. Safe JSON counts only.
A visible skinned result is not fidelity proof.
"""
from __future__ import annotations
import copy,json,math,os,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
import spine_textured_rive as src

ROOT=src.ROOT
OUT=src.OUT
REPORT={"stage":"PROD-005 real Spine textured skin investigation","probes":{},
        "notes":"PNG and original source RML are NOT uploaded; diagnostics are pixel counts only"}

def matmul(a,b):
    A,B,C,D,X,Y=a; E,F,G,H,U,V=b
    return (A*E+C*F,B*E+D*F,A*G+C*H,B*G+D*H,A*U+C*V+X,B*U+D*V+Y)
ID=(1.,0.,0.,1.,0.,0.)
def rot(a,x=0,y=0):
    return (math.cos(a),math.sin(a),-math.sin(a),math.cos(a),x,y)
def rive_bone_pose(root):
    """Bone bind matrix in the same group-local coordinates as image vertices."""
    result={}
    def descend(node,parent_transform,tip=0.):
        for child in list(node):
            if child.tag not in ("Bone","RootBone"):
                continue
            r=float(child.get("rotation",0))
            if child.tag=="RootBone":
                local=rot(r,float(child.get("x",0)),float(child.get("y",0)))
            else:
                local=rot(r,tip,0)
            trans=matmul(parent_transform,local)
            result[child.get("id")]=trans
            descend(child,trans,float(child.get("length",0)))
    group=next(x for x in root.iter("Node") if x.get("name")=="SpineRoot")
    descend(group,ID)
    return result
def set_matrix(t,m):
    a,b,c,d,x,y=m
    for k,v in zip(("xx","xy","yx","yy","tx","ty"),m):
        t.set(k,f"{v:.9g}")
def visible(path):
    with Image.open(path) as im:
        px=im.convert("RGBA").tobytes()
        corner=px[:4]
        return sum(px[i:i+4]!=corner for i in range(0,len(px),4))
def main():
    tree,project,bones,objects,doc,imported=src.construct()
    template=copy.deepcopy(tree)
    variants=["original","original-no-scale","rive-local-pose","rive-local-pose-no-scale",
              "identity-tendons","zero-tendon-xy","one-source-mesh","one-source-mesh-rive-local",
              "half-meshes-rive-local"]
    for kind in variants:
        probe=copy.deepcopy(template)
        root=probe.getroot()
        group=next(x for x in root.iter("Node") if x.get("name")=="SpineRoot")
        if "no-scale" in kind:
            group.set("scaleX","1")
            group.set("scaleY","1")
            group.set("x","320")
            group.set("y","180")
        bind=rive_bone_pose(root)
        meshs=list(root.iter("Mesh"))
        if kind.startswith("one-source-mesh"):
            for m in meshs[1:]:
                parent=next((e for e in root.iter("Image") if m in list(e)),None)
                if parent is not None:
                    p=next((e for e in root.iter() if parent in list(e)),None)
                    if p is not None:p.remove(parent)
        if kind=="half-meshes-rive-local":
            for m in meshs[len(meshs)//2:]:
                parent=next((e for e in root.iter("Image") if m in list(e)),None)
                if parent is not None:
                    p=next((e for e in root.iter() if parent in list(e)),None)
                    if p is not None:p.remove(parent)
        updated=0
        for tendon in root.iter("Tendon"):
            if kind in ("rive-local-pose","rive-local-pose-no-scale","one-source-mesh-rive-local","half-meshes-rive-local"):
                m=bind.get(tendon.get("boneId"))
                if m:
                    set_matrix(tendon,m)
                    updated+=1
            elif kind=="identity-tendons":
                set_matrix(tendon,ID);updated+=1
            elif kind=="zero-tendon-xy":
                tendon.set("tx","0");tendon.set("ty","0");updated+=1
        # All original artwork stays on temporary runner.
        probe.write(project/"scene.rml",encoding="unicode")
        f=ROOT/f"skinning-{kind}.png"
        try:
            src.run(["rive",str(project),f"--screenshot={f}","--viewport=640x360","--advance=0s"])
            REPORT["probes"][kind]={"status":"PASS","visible_pixels":visible(f),
                "tendon_updated":updated}
        except Exception as exc:
            REPORT["probes"][kind]={"status":"ERROR","error":str(exc)[-250:],
                "tendon_updated":updated}
        print(kind,REPORT["probes"][kind],flush=True)
    records=[(k,v["visible_pixels"]) for k,v in REPORT["probes"].items()
             if v.get("visible_pixels",0)>400]
    REPORT["skinned_visible_variants"]=records
    REPORT["status"]="SKIN_RENDER_PRESENT" if any(k!="original" for k,p in records) else "STILL_BLOCKED"
    (OUT/"skin-diagnostics.json").write_text(json.dumps(REPORT,indent=2,ensure_ascii=False)+"\n")
    (OUT/"skin-diagnostics.md").write_text("# Real Spine skinning diagnostics\n\n"+
        f"**{REPORT['status']}**\n\n"+
        "| Variant | Rendered pixels | Status |\n|---|---:|---|\n"+
        "".join(f"| {k} | {v.get('visible_pixels','?')} | {v['status']} |\n"
                for k,v in REPORT["probes"].items())+
        "\nSuccess of a diagnostic variant does not establish accurate source animation/rig parity.\n")
    print((OUT/"skin-diagnostics.md").read_text())
if __name__=="__main__":
    try:main()
    except Exception as e:
        REPORT["status"]="ERROR";REPORT["error"]=repr(e)
        (OUT/"skin-diagnostics.json").write_text(json.dumps(REPORT,indent=2)+"\n")
        raise
