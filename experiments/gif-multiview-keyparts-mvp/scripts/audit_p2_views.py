#!/usr/bin/env python3
"""Audit recovered P0 45°/90° physical-part identity before VDD art acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parents[1]
ANGLES=(45,90)
NEEDS=("face.skin","eye.near","eye.far","ear.near","ear.far",
       "hair.front","hair.side","hair.back","hair.ahoge","hair.clip.cross_gold")

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def components(path, min_pixels=80):
    arr=np.array(Image.open(path).convert("RGBA"))
    mask=np.uint8(arr[:,:,3]>24)
    number,labels,stats,centroids=cv2.connectedComponentsWithStats(mask,8)
    items=[]
    for i in range(1,number):
        if int(stats[i,4])<min_pixels:continue
        items.append({"pixels":int(stats[i,4]),"centroid":[round(float(x),2) for x in centroids[i]],
                      "bbox":[int(x) for x in stats[i,:4]]})
    return sorted(items,key=lambda x:x["pixels"],reverse=True)

def render_contact(root,destination):
    images=[]
    for yaw in ANGLES:
        for key,filename in [
          ("whole",f"recovered-review/frames/head_8/yaw{yaw:03d}_whole.png"),
          ("eye",f"recovered-review/frames/face_15/yaw{yaw:03d}_eye.near.png"),
          ("ear",f"recovered-review/frames/face_15/yaw{yaw:03d}_ear.near.png"),
          ("hair.front",f"recovered-review/frames/hair_9/yaw{yaw:03d}_hair.front.png"),
          ("clip",f"recovered-review/frames/accessories_6/yaw{yaw:03d}_hair.clip.cross_gold.png"),
          ("registered",f"candidate-v2/whole/yaw{yaw:03d}.png")]:
            images.append((yaw,key,root/filename))
    width,height=270,330
    canvas=Image.new("RGB",(width*6,height*2),(24,34,48))
    draw=ImageDraw.Draw(canvas)
    for i,(yaw,label,path) in enumerate(images):
        if not path.is_file():continue
        original=Image.open(path).convert("RGBA")
        original.thumbnail((246,280),Image.Resampling.LANCZOS)
        x=(i%6)*width+12
        y=(i//6)*height+12
        board=Image.new("RGBA",(246,280),(63,74,91,255))
        board.alpha_composite(original,((246-original.width)//2,(280-original.height)//2))
        canvas.paste(board.convert("RGB"),(x,y))
        draw.text((x,y+286),f"{yaw}deg  {label}",fill="#f6f7fa")
    destination.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(destination,quality=93)

def audit(root,out):
    root=Path(root).resolve();out=Path(out)
    slotjson=json.loads((root/"parts.json").read_text())
    partMap={(p.get("yawDeg"),p.get("semanticId")):p for p in slotjson["parts"]}
    checks=[];actual={}
    def record(name,passed,detail=None):
        checks.append(dict(gate=name,passed=bool(passed),detail=detail))
    source=root/"recovered-review"
    actual["sourceWholeGIFSHA256"]=digest(source/"sources/head-turn-8view.gif")
    actual["sourceFaceGIFSHA256"]=digest(source/"sources/face-semantic-0-45-90.gif")
    for yaw in ANGLES:
        for name in NEEDS:
            rec=partMap.get((yaw,name))
            record(f"registration_{yaw}_{name}",bool(rec))
            if rec:
                rawpath=root/rec.get("path","")
                record(f"source_png_{yaw}_{name}",rawpath.is_file(),str(rawpath.relative_to(root)) if rawpath.is_relative_to(root) else str(rawpath))
                if rawpath.is_file():record(f"sha256_{yaw}_{name}",digest(rawpath)==rec.get("frameSha256"))
        for key in ("eye.near","ear.near"):
            frame=source/f"frames/face_15/yaw{yaw:03d}_{key}.png"
            detected=components(frame)
            actual[f"{yaw}_{key}_originalGIFComponents"]=detected
            # The near eye semantic GIF must be split into physical eyes at 45°.
            expected_count=(2 if yaw==45 and key=="eye.near" else 1)
            record(f"semantic_gif_physical_count_{yaw}_{key}",
                   len(detected)==expected_count,
                   {"actual":len(detected),"expected":expected_count})
        expectedHidden=["ear.far"] if yaw==45 else ["eye.far","ear.far","hair.clip.cross_gold"]
        for key in expectedHidden:
            slot=partMap.get((yaw,key))
            record(f"occlusion_{yaw}_{key}",bool(slot and slot.get("visibility")=="hidden"))
        if yaw==45:
            record("45_clip_visible",partMap[(45,"hair.clip.cross_gold")].get("visibility")=="visible")
        else:
            record("90_near_eye_visible",partMap[(90,"eye.near")].get("visibility")=="visible")
        # Candidate-v2 is exact endpoint partition of whole view, not semantic
        # complete anatomy. Underpainting is required for dynamic turn.
    for partName in ("hair.front","hair.back","face.skin","eye.near"):
        for yaw in ANGLES:
            record(f"occluded_interior_authored_{yaw}_{partName}",False,
                   "The current whole-view partition lacks authored texture under occluded surfaces.")
    board=out.parent/"p2-view-semantic-contact.jpg"
    render_contact(root,board)
    result={
      "schema":"KOMA-P0-P2-MULTIVIEW-SEMANTIC-AUDIT-V1",
      "characterId":"p0_character_001","views":[45,90],
      "sourceRole":"restored_38frame_GIF_and_registered_whole_view_partition",
      "sourceHashes":actual,
      "semanticSlotsReviewed":len(ANGLES)*len(NEEDS),
      "checks":checks,"passed":sum(x["passed"] for x in checks),
      "failed":sum(not x["passed"] for x in checks),
      "contactSheet":str(board),"contactSheetSha256":digest(board),
      "status":"SOURCE_VIEW_REGISTRY_READY_ARTMESH_INTERIORS_PENDING",
      "nextRequiredArt":{
       "45":"each physical eye, face and back/front hair interior underpainting",
       "90":"profile eye/ear, nose/silhouette, behind fringe hair; clip hidden",
       "both":"common anatomical ID/mesh correspondence and VDD holdout visual approval"
      }
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({x:result[x] for x in ("status","semanticSlotsReviewed","passed","failed","contactSheetSha256")},ensure_ascii=False,indent=2))
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    audit(args.root,Path(args.output))
