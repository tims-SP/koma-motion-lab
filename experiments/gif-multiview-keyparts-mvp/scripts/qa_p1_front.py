#!/usr/bin/env python3
"""P1 real-art acceptance checks: sources, complete geometry, semantic isolation and eye motion."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from p1_front_semantic import DEPTH, SEMANTIC, alpha_over, rescale_visible, ownership, make_ellipse

CANVAS=1024

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return np.array(Image.open(path).convert("RGBA"))


def run(root,output):
    root=Path(root).resolve()
    manifest=json.loads((root/"p1-front/parts.json").read_text())
    prev=json.loads((root/"p1-front/qa.json").read_text())
    checks=[]
    def check(name,condition,details=None):
        checks.append({"gate":name,"pass":bool(condition),"detail":details})
    check("manifest_schema",manifest.get("schema")=="KOMA-P0-ARTMESH-MANIFEST-V1")
    check("identity",manifest.get("characterId")=="p0_character_001")
    check("full_canvas",manifest.get("canvas")==[CANVAS,CANVAS])
    parts=manifest.get("parts",[])
    keys={p.get("semanticId") for p in parts}
    check("part_slots",len(parts)==len(SEMANTIC) and keys==set(SEMANTIC),len(parts))
    groups={"whole":root/"whole/head-turn-8view.gif",
            "face":root/"gifs/face.gif","hair":root/"gifs/hair.gif"}
    valid_hashes={k:sha(v) for k,v in groups.items() if v.exists()}
    check("whole_source_sha",valid_hashes.get("whole")==prev.get("sourceWholeSha256"))
    check("recovered_frame_count",len(list((root/"recovered-review/frames/head_8").glob("*.png")))==8)
    layers={}
    for p in parts:
        k=p["semanticId"]
        rel=p["path"]; file=(root/rel).resolve()
        check("contained_path:"+k,file.is_relative_to(root),rel)
        if not file.is_file():
            check("exists:"+k,False)
            continue
        check("sha:"+k,sha(file)==p.get("frameSha256"))
        with Image.open(file) as im:
            check("native_rgba:"+k,im.format=="PNG" and im.mode=="RGBA")
            check("size:"+k,im.size==(CANVAS,CANVAS),im.size)
        pix=load(file);layers[k]=pix
        alpha=pix[:,:,3]
        check("nonempty:"+k,np.count_nonzero(alpha)>=15,int(np.count_nonzero(alpha)))
        # Outer corners should be transparent for the per-part PNG except when
        # original drawing overlaps canvas (must then be documented explicitly).
        check("transparent_top:"+k,int(alpha[0,0])==0 and int(alpha[0,-1])==0)
        check("partial_alpha:"+k,int(np.count_nonzero((alpha>0)&(alpha<255)))>0)
        mesh=p.get("mesh",{})
        check("mesh_7x7:"+k,len(mesh.get("vertexIds",[]))==49 and
              len(mesh.get("triangles",[]))==72 and len(mesh.get("vertices",[]))==49)
        check("anchors:"+k,len(p.get("anchors",[]))>=5)
        check("depth_order:"+k,p.get("depthOrder")==DEPTH[k])
    if len(layers)!=len(SEMANTIC):
        result={"status":"FAIL_ASSET_MISSING","checks":checks}
        Path(output).write_text(json.dumps(result,indent=2));return result

    front=layers["hair.front"]
    gold=cv2.cvtColor(front[:,:,:3],cv2.COLOR_RGB2HSV)
    candidate=(front[:,:,3]>25)&(gold[:,:,0]>=8)&(gold[:,:,0]<=40)&(gold[:,:,1]>90)
    clip=layers["hair.clip.cross_gold"]
    clipbox=[p["bbox"] for p in parts if p["semanticId"]=="hair.clip.cross_gold"][0]
    check("clip_is_separate",np.count_nonzero(candidate)<25,int(np.count_nonzero(candidate)))
    check("single_clip",bool(clipbox) and
          (clipbox[2]-clipbox[0])<150 and (clipbox[3]-clipbox[1])<150,clipbox)
    ahoge=[p["bbox"] for p in parts if p["semanticId"]=="hair.ahoge"][0]
    check("ahoge_isolated",bool(ahoge) and ahoge[1]<75 and ahoge[3]<150,ahoge)
    eye_bboxes={k:next(p["bbox"] for p in parts if p["semanticId"]==k)
                for k in ("eye.near","eye.far")}
    near,far=eye_bboxes["eye.near"],eye_bboxes["eye.far"]
    check("physical_eyes_ordered",near[0]<far[0] and near[2]<far[0],eye_bboxes)
    check("one_eye_per_layer",(near[2]-near[0])<190 and (far[2]-far[0])<190,eye_bboxes)
    check("physical_eyes_visible",int((layers["eye.near"][:,:,3]>100).sum())>1000 and
          int((layers["eye.far"][:,:,3]>100).sum())>1000)
    skin=layers["face.skin"]
    check("skin_underpainting",next(p["underpaintNativePixels"] for p in parts
          if p["semanticId"]=="face.skin")>=6500)
    hair_back=next(p["visibleNativePixels"] for p in parts
                   if p["semanticId"]=="hair.back")
    check("back_hair_visible",hair_back>=5000,hair_back)

    original=np.array(Image.open(root/"recovered-review/frames/head_8/yaw000_whole.png")
                      .convert("RGBA")).copy()
    original[original[:,:,3]==0]=0
    authored_owner,_=ownership(root,original)
    eye_core_pixels={str(c):int(np.count_nonzero(
        make_ellipse(c,(19,16)) & (authored_owner==DEPTH["hair.front"])))
        for c in ((190,196),(271,196))}
    check("hair_iris_core_exclusive",all(n==0 for n in eye_core_pixels.values()),
          eye_core_pixels)
    ref=rescale_visible(original)
    def composite_with(near_shift_x=0):
        comp=np.zeros_like(ref)
        for key in SEMANTIC:
            a=layers[key]
            if key=="eye.near" and near_shift_x:
                transform=np.float32([[1,0,near_shift_x],[0,1,0]])
                a=cv2.warpAffine(a,transform,(CANVAS,CANVAS),
                                 flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT,
                                 borderValue=(0,0,0,0))
            comp=alpha_over(comp,a)
        return comp

    comp=composite_with()
    difference=np.abs(comp.astype(np.int16)-ref.astype(np.int16))
    changed=int(np.any(difference>1,axis=2).sum())
    mean=float(difference.mean())
    src_a=ref[:,:,3]>32; comp_a=comp[:,:,3]>32
    overlap=int((src_a&comp_a).sum());union=int((src_a|comp_a).sum())
    iou=overlap/max(1,union)
    check("static_color_match",changed<=900 and mean<0.015,
          {"changedPixelCount":changed,"meanAbsChannel":round(mean,5)})
    check("static_silhouette_match",iou>=0.9999,round(iou,7))
    static_holes=int(((ref[:,:,3]>=250)&(comp[:,:,3]<245)).sum())
    check("static_opaque_surface_coverage",static_holes==0,static_holes)
    # ArtMesh independence smoke test: moving only one eye must preserve the
    # underlying skin where the original eye becomes uncovered.
    moved=composite_with(near_shift_x=10)
    x0,y0,x1,y1=near
    roi=(slice(max(0,y0-6),min(1024,y1+6)),
         slice(max(0,x0-12),min(1024,x1+12)))
    original_alpha=ref[roi][:,:,3]
    moved_alpha=moved[roi][:,:,3]
    new_holes=int(((original_alpha>=252)&(moved_alpha<245)).sum())
    check("near_eye_reposition_coverage",new_holes<=18,new_holes)
    # Distinct identity: moving near eye leaves far-eye pixels stable.
    # Compare the far iris core, not its broad ArtMesh bounding padding: near
    # eye motion may legitimately approach the far sclera's outer fringe.
    far_region=(slice(far[1]+12,far[3]-12),
                slice(far[0]+28,far[2]-28))
    far_change=int(np.abs(moved[far_region].astype(np.int16)-
                           comp[far_region].astype(np.int16)).max())
    check("far_eye_is_independent",far_change==0,far_change)
    Image.fromarray(moved,"RGBA").save(root/"p1-front/diagnostics/eye-near-motion-check.png")
    report={
       "schema":"KOMA-P0-P1-FRONT-GATE-V1","characterId":"p0_character_001",
       "yawDeg":0,"sourceHashes":valid_hashes,
       "checks":checks,"passed":sum(c["pass"] for c in checks),
       "failed":sum(not c["pass"] for c in checks),
       "measures":{"staticChangedPixelCount":changed,"staticMeanAbsChannel":round(mean,5),
                   "staticSilhouetteIoU":round(iou,7),"staticOpaqueHoles":static_holes,"eyeMoveX":10,
                   "eyeMoveNewTransparentHoles":new_holes,
                   "farEyeMaxChannelDifference":far_change},
       "visualStatus":"REQUIRES_MANUAL_P0_SOURCE_AND_MOTION_REVIEW",
       "status":"PASS_STRUCTURAL_ENGINEERING" if all(c["pass"] for c in checks) else
                "FAIL_STRUCTURAL_ENGINEERING"}
    dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in
                      ("status","passed","failed","measures")},indent=2))
    for c in checks:
        if not c["pass"]:print("FAILED:",c["gate"],c["detail"])
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    r=run(args.root,args.output)
    raise SystemExit(0 if r["failed"]==0 else 2)
