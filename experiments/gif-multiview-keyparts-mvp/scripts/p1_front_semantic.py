#!/usr/bin/env python3
"""P0 front ArtMesh candidate reconstructed from the recovered character's real art.

Visible pixel ownership comes from the recovered approved-design eight-view GIF.
Existing semantic GIFs supply registered geometry behind occluders. All source
hashes, masks, and artistic provenance are recorded separately from acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

NATIVE = 443
CANVAS = 1024
SEMANTIC = [
    "body.reference", "hair.back", "face.skin", "ear.far",
    "ear.near", "hair.side", "eye.far", "eye.near", "nose",
    "mouth", "hair.front", "hair.ahoge", "hair.clip.cross_gold"
]
DEPTH = {name: i for i, name in enumerate(SEMANTIC)}
SOURCE_KEYS = {
    "face.skin": ("face_15", "face.skin", (0.75, 109, 82)),
    "eye.near": ("face_15", "eye.near", (0.75, 110, 73)),
    "eye.far": ("face_15", "eye.near", (0.75, 110, 73)),
    "ear.near": ("face_15", "ear.near", (0.77, 106, 93)),
    "ear.far": ("face_15", "ear.near", (0.77, 106, 93)),
    "nose": ("face_15", "nose", (0.85, 99, 86)),
    "mouth": ("face_15", "mouth", (0.75, 112, 108)),
    "hair.back": ("hair_9", "hair.back", (0.90, 30, 34)),
    "hair.side": ("hair_9", "hair.side", (0.90, 30, 34)),
    "hair.front": ("hair_9", "hair.front", (0.90, 30, 34))
}
PART_GROUP = {"face_15": "gifs/face.gif", "hair_9": "gifs/hair.gif"}
PHYSICAL = {"eye.near": "right", "eye.far": "left",
            "ear.near": "right", "ear.far": "left",
            "hair.clip.cross_gold": "left"}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as file:
        for part in iter(lambda: file.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def load(path):
    return np.array(Image.open(path).convert("RGBA"))


def warp(src, affine):
    scale, dx, dy = affine
    mat = np.float32([[scale, 0, dx], [0, scale, dy]])
    return cv2.warpAffine(src, mat, (NATIVE, NATIVE),
                          flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT,
                          borderValue=(0, 0, 0, 0))


def make_ellipse(center,axes):
    mask = np.zeros((NATIVE, NATIVE), dtype=np.uint8)
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
    return mask > 0


def native_bbox(mask):
    y,x = np.where(mask)
    return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)] if len(x) else None


def split_source(rgba, semantic):
    result = rgba.copy()
    if semantic in ("eye.near", "ear.near"):
        result[:, (NATIVE // 2):] = 0
    elif semantic in ("eye.far", "ear.far"):
        result[:, :(NATIVE // 2)] = 0
    return result


def source_underpaint(root, semantic):
    if semantic not in SOURCE_KEYS:
        return None
    folder, oldid, transform = SOURCE_KEYS[semantic]
    input_file = root / "recovered-review" / "frames" / folder / ("yaw000_"+oldid+".png")
    a = load(input_file)
    if semantic == "face.skin":
        # Original semantic face GIF included two ear copies in its skin frame.
        # Reserve anatomical ear pixels exclusively for the physical ear layers.
        raw_ears=load(root/"recovered-review/frames/face_15/yaw000_ear.near.png")
        ear_mask=cv2.dilate((raw_ears[:,:,3]>12).astype(np.uint8),
                            np.ones((5,5),np.uint8),iterations=1)>0
        a[ear_mask]=0
    if semantic.startswith("hair."):
        if a.shape[0] == 418:
            # Crown loop and crossed clip are separate semantic owners.
            a[:70, :] = 0
            if semantic == "hair.front":
                hsv = cv2.cvtColor(a[:, :, :3], cv2.COLOR_RGB2HSV)
                gold = ((hsv[:, :, 0] >= 8) & (hsv[:, :, 0] <= 40) &
                        (hsv[:, :, 1] >= 65) & (a[:, :, 3] > 0)).astype(np.uint8)
                gold[:, :175] = 0
                gold[315:] = 0
                gold = cv2.dilate(gold,np.ones((9,9),np.uint8),iterations=1)
                if gold.any():
                    a[:, :, :3] = cv2.inpaint(a[:, :, :3],gold,4,cv2.INPAINT_TELEA)
    warped=split_source(warp(a,transform),semantic)
    if semantic=="face.skin":
        # Complete the original face skin beneath eye ArtMeshes. The source
        # skin ellipse is narrower than the authored lashes; pixels outside
        # its extent are inferred using the genuine source cheek palette.
        known=(warped[:,:,3]>220)
        yy,xx=np.indices((NATIVE,NATIVE))
        sample=known&(yy>200)&(yy<272)&(xx>190)&(xx<264)
        median=np.median(warped[:,:,:3][sample],axis=0).astype(np.uint8)
        for center in ((190,196),(271,196)):
            eye=make_ellipse(center,(46,34))
            fill=eye&(warped[:,:,3]<255)
            warped[fill,:3]=median
            warped[fill,3]=255
    return warped


def semantic_source_masks(root):
    masks = {}
    for key in ("eye.near", "eye.far", "ear.near", "ear.far"):
        a = source_underpaint(root,key)
        masks[key] = (a[:, :, 3] >= 18)
    return masks


def ownership(root, original):
    y,x = np.indices((NATIVE,NATIVE))
    alpha = original[:,:,3] > 0
    hsv = cv2.cvtColor(original[:,:,:3], cv2.COLOR_RGB2HSV)
    pink = ((hsv[:,:,0]>=142)&(hsv[:,:,0]<=179)&
            (hsv[:,:,1]>=30)&(hsv[:,:,2]>=65))
    hair = cv2.dilate((pink&(y<343)).astype(np.uint8),
                      np.ones((5,5),np.uint8),iterations=1)>0
    owner = np.full((NATIVE,NATIVE), DEPTH["body.reference"],np.uint8)
    owner[(y<317)&alpha] = DEPTH["hair.back"]
    face_polygon=np.array([
        (189,159),(226,151),(261,159),(284,179),(297,212),
        (286,254),(257,283),(227,294),(195,279),(169,246),
        (157,215),(161,189)],dtype=np.int32)
    face=np.zeros((NATIVE,NATIVE),np.uint8)
    cv2.fillPoly(face,[face_polygon],255)
    owner[(face>0)&alpha] = DEPTH["face.skin"]
    # Pink hair belongs to the parent hair group, including the outer silhouette.
    owner[hair&(y<326)&alpha] = DEPTH["hair.back"]
    front = hair & (((x>=166)&(x<=317)&(y<180)) |
                    ((x>=185)&(x<=303)&(y>=180)&(y<262)))
    owner[front&alpha] = DEPTH["hair.front"]
    side = hair & ((x<190)|(x>279))&(y>=164)&(y<328)
    owner[side&alpha] = DEPTH["hair.side"]
    # Preserve higher priority bangs over the side hair.
    owner[front&alpha] = DEPTH["hair.front"]
    # Physical ear and eye identity is informed by corresponding semantic GIF masks.
    masks=semantic_source_masks(root)
    for semantic in ("ear.far","ear.near","eye.far","eye.near"):
        mask=masks[semantic] & alpha
        if semantic.startswith("eye."):
            # The source eye GIF omits the outer eyelash roots; use an authored
            # anatomical eye region to include complete upper/lower contours.
            center=(190,196) if semantic=="eye.near" else (271,196)
            region=make_ellipse(center,(38,27))
            mask=(mask|region)&alpha&(y>168)&(y<228)
            # Pastel hair highlights are not part of the iris/lash ArtMesh.
            # Preserve the overhanging fringe above eyelid height only.
            # The iris, sclera, and lashes must have a single physical owner.
            mask &= ~(front&pink&(y<178))
        elif semantic.startswith("ear."):
            mask &= (y>205)&(y<268)
        # Ears sit under side fringe; each eye owns its visible iris/sclera.
        if semantic.startswith("ear."):
            mask &= ~(front&(pink&(hsv[:,:,2]>155)))
        owner[mask] = DEPTH[semantic]
    # Identity-critical nose and mouth regions are drawn after face.
    nose=make_ellipse((229,240),(6,10))
    mouth=make_ellipse((229,279),(19,7))
    owner[nose&alpha&~pink] = DEPTH["nose"]
    owner[mouth&alpha&~pink] = DEPTH["mouth"]
    # Restore top-most hair where it genuinely occludes eye edges.
    owner[front&(y<180)&alpha] = DEPTH["hair.front"]
    gold = ((hsv[:,:,0]>=8)&(hsv[:,:,0]<=40)&
            (hsv[:,:,1]>65)&(hsv[:,:,2]>95)&alpha)
    clip_region=(x>279)&(x<338)&(y>109)&(y<178)
    clip=(gold&clip_region).astype(np.uint8)
    n,labels,stats,_=cv2.connectedComponentsWithStats(clip,8)
    valid=[i for i in range(1,n) if stats[i,4]>22]
    if valid:
        biggest=max(valid,key=lambda i: stats[i,4])
        clip=cv2.dilate((labels==biggest).astype(np.uint8),
                        np.ones((5,5),np.uint8),iterations=1)>0
        clip &= clip_region
        owner[clip&alpha]=DEPTH["hair.clip.cross_gold"]
    # The full loop extends above the crown but crown hair stays in its own layer.
    loop=((((y<45)&(x>155)&(x<271)) |
          ((y>=45)&(y<58)&(x>227)&(x<249)))&alpha)
    owner[loop]=DEPTH["hair.ahoge"]
    owner[~alpha]=255
    return owner, {key: native_bbox(value) for key,value in masks.items()}


def rescale_visible(image):
    resized=np.array(Image.fromarray(image,"RGBA").resize(
        (CANVAS,CANVAS), Image.Resampling.LANCZOS))
    resized[resized[:,:,3]==0]=0
    return resized


def realpart_bbox(arr):
    ys,xs=np.where(arr[:,:,3]>12)
    if len(xs)==0:return None
    return [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]


def semantic_anchors(name,bbox):
    x0,y0,x1,y1=bbox
    cx,cy=(x0+x1)/2,(y0+y1)/2
    keys=[
        ("outline.top", (cx,y0)), ("outline.left", (x0,cy)),
        ("outline.right", (x1,cy)),("outline.bottom",(cx,y1)),
        ("center", (cx,cy))]
    if name.startswith("eye."):
        keys+=[("innerCorner",(x1,cy)),("outerCorner",(x0,cy)),
               ("iris.center",(cx,cy))]
    elif name=="face.skin":
        keys+=[("jaw.left",(x0+0.16*(x1-x0),y0+.72*(y1-y0))),
               ("jaw.right",(x1-.16*(x1-x0),y0+.72*(y1-y0))),
               ("chin",(cx,y1)),("forehead",(cx,y0))]
    elif name.startswith("ear."):
        keys+=[("ear.root",(x0,cy)),("ear.lobe",(cx,y1))]
    elif name=="hair.ahoge":
        keys+=[("root",(cx,y1)),("tip",(cx,y0))]
    elif name=="hair.clip.cross_gold":
        keys+=[("clip.center",(cx,cy))]
    return [{"id":k,"xy":[round(a,3),round(b,3)]} for k,(a,b) in keys]


def mesh_points(bb,steps=7):
    x0,y0,x1,y1=bb
    margin=4
    x0=max(0,x0-margin);y0=max(0,y0-margin)
    x1=min(CANVAS,x1+margin);y1=min(CANVAS,y1+margin)
    vertices=[
       [round(x0+(x1-x0)*c/(steps-1),4),
        round(y0+(y1-y0)*r/(steps-1),4)]
       for r in range(steps) for c in range(steps)
    ]
    tris=[]
    for r in range(steps-1):
        for c in range(steps-1):
            a=r*steps+c
            tris.extend([[a,a+1,a+steps+1],[a,a+steps+1,a+steps]])
    return dict(vertexIds=[f"grid.{r}.{c}" for r in range(steps) for c in range(steps)],
                vertices=vertices,triangles=tris)


def alpha_over(bg,fg):
    a=fg[:,:,3:4].astype(np.float32)/255.
    b=bg[:,:,3:4].astype(np.float32)/255.
    out_a=a+b*(1-a)
    out_rgb=np.divide(fg[:,:,:3].astype(np.float32)*a+
                      bg[:,:,:3].astype(np.float32)*b*(1-a),
                      np.maximum(out_a,1e-9),out=np.zeros_like(
                          fg[:,:,:3],dtype=np.float32),where=out_a>1e-9)
    return np.concatenate((np.uint8(np.clip(out_rgb,0,255)),
                           np.uint8(np.clip(out_a*255,0,255))),axis=2)


def build(root):
    root=Path(root).resolve()
    original=load(root/"recovered-review/frames/head_8/yaw000_whole.png")
    assert original.shape==(NATIVE,NATIVE,4)
    original[original[:,:,3]==0]=0
    owner,source_mask_boxes=ownership(root,original)
    output=root/"p1-front"
    parts_dir=output/"parts"/"yaw000"
    parts_dir.mkdir(parents=True,exist_ok=True)
    report_dir=output/"diagnostics"
    report_dir.mkdir(parents=True,exist_ok=True)
    matrices={}
    layers={}
    base=original.copy()
    native_parts={}
    # Strict visible source ownership preserves the original 0 degree portrait.
    for semantic in SEMANTIC:
        visible_owner=owner==DEPTH[semantic]
        visible=np.zeros_like(original)
        visible[visible_owner]=original[visible_owner]
        native_parts[semantic]=visible
        matrices[semantic]={"visibleNativePixels":int(np.count_nonzero(visible[:,:,3])),
                            "underpaintNativePixels":0}
    # Add hidden geometry from previously generated independent semantic GIFs only
    # where a fully opaque foreground surface obscures its existence.
    underpaint_layers={}
    for semantic in SEMANTIC:
        draft=source_underpaint(root,semantic)
        if draft is None:
            continue
        visible_original=owner==DEPTH[semantic]
        hidden=(owner!=255)&(owner!=DEPTH[semantic]) & (owner>DEPTH[semantic])
        hidden &= (original[:,:,3]>=253)&(draft[:,:,3]>12)
        # Limit hidden extensions to a modest 9px inside foreground silhouettes:
        # enough for eye/blink/pose microdeformation; not a claim of unseen anatomy.
        grown=cv2.dilate(visible_original.astype(np.uint8),
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(37,37)))>0
        if semantic == "face.skin":
            # The bald source skin supplies its genuine upper-forehead texture beneath bangs.
            pass
        elif visible_original.any():
            hidden &= grown
        else:
            hidden[:]=False
        layer=native_parts[semantic]
        layer[hidden]=draft[hidden]
        matrices[semantic]["underpaintNativePixels"]=int(np.count_nonzero(hidden))
        underpaint_layers[semantic]=hidden
    # Upsample original art FIRST. Render each visible pixel at its authentic
    # 1024-resolution RGB and alpha; do not interpolate premultiplied semantic
    # cutout borders independently, as that creates seams at ownership boundaries.
    source_high=rescale_visible(original)
    owner_high=cv2.resize(owner,(CANVAS,CANVAS),interpolation=cv2.INTER_NEAREST)
    owner_high[(owner_high==255)&(source_high[:,:,3]>0)]=DEPTH["hair.back"]
    owner_high[source_high[:,:,3]==0]=255
    # Complete the authentic front-hair pigment behind the gold clip by
    # reconstructing the occluded source using neighboring lavender strands.
    # It remains owned by hair.front; the clip keeps its independent ArtMesh.
    clip_native=(owner==DEPTH["hair.clip.cross_gold"]).astype(np.uint8)
    restored_front_color=cv2.inpaint(original[:,:,:3],
        cv2.dilate(clip_native,np.ones((5,5),np.uint8)),5,cv2.INPAINT_TELEA)
    restored_front_color=cv2.resize(restored_front_color,(CANVAS,CANVAS),
                                    interpolation=cv2.INTER_LINEAR)
    layers={}
    for semantic in SEMANTIC:
        idx=DEPTH[semantic]
        layer=np.zeros_like(source_high)
        visible=(owner_high==idx)
        layer[visible]=source_high[visible]
        hidden_native=underpaint_layers.get(semantic)
        if hidden_native is not None:
            hidden_high=cv2.resize(hidden_native.astype(np.uint8),
                                   (CANVAS,CANVAS),interpolation=cv2.INTER_NEAREST)>0
            hidden_high &= (owner_high>idx)&(owner_high!=255)
            # Underpainting stays behind guaranteed opaque source foreground.
            hidden_high &= source_high[:,:,3]==255
            draft_high=rescale_visible(native_parts[semantic])
            layer[hidden_high]=draft_high[hidden_high]
        if semantic=="hair.front":
            clip_back=((owner_high==DEPTH["hair.clip.cross_gold"]) &
                       (source_high[:,:,3]==255))
            layer[clip_back,:3]=restored_front_color[clip_back]
            layer[clip_back,3]=255
        layers[semantic]=layer
    # Small standalone face accents require 2px partial-coverage edge pixels;
    # the whole-view GIF stores only binary transparency on internal cuts.
    # The independent underpaint layer supplies the uncovered skin/hair color.
    for semantic in ("nose","mouth","hair.clip.cross_gold"):
        target=layers[semantic]
        occupied=(target[:,:,3]>0).astype(np.uint8)
        distance=cv2.distanceTransform(occupied,cv2.DIST_L2,3)
        edge=np.clip(distance/1.8,0.,1.)
        target[:,:,3]=np.uint8(target[:,:,3].astype(np.float32)*edge)
    # For endpoint source parity, compose in Cubism draw order using alpha-over.
    composite=np.zeros_like(source_high)
    files=[]
    original_digest=sha(root/"recovered-review/sources/head-turn-8view.gif")
    part_sources={
        "face_15":sha(root/"gifs/face.gif"),
        "hair_9":sha(root/"gifs/hair.gif"),
        "whole":original_digest
    }
    for semantic in SEMANTIC:
        png=parts_dir/(semantic+".png")
        Image.fromarray(layers[semantic],"RGBA").save(png)
        composite=alpha_over(composite,layers[semantic])
        bb=realpart_bbox(layers[semantic])
        if bb is None:
            bb=[450,450,530,530]
        grp=SOURCE_KEYS.get(semantic,("whole",))[0]
        group_file=PART_GROUP.get(grp,"whole/head-turn-8view.gif")
        source_digest=part_sources.get(grp,original_digest)
        file_entry={
         "yawDeg":0, "semanticId":semantic, "path":str(png.relative_to(root)),
         "bbox":realpart_bbox(layers[semantic]),
         "visibility":"visible" if realpart_bbox(layers[semantic]) else "hidden",
         "anatomicalSide":PHYSICAL.get(semantic),
         "depthOrder":DEPTH[semantic], "occludes":[],
         "sourceGif":"whole/head-turn-8view.gif",
         "sourceGifSha256":original_digest, "frameIndex":0,
         "underpaintSourceGif":group_file, "underpaintSourceSha256":source_digest,
         "frameSha256":sha(png),
         "sourceRole":"P0_recovered_GIF_visible_pixels_with_registered_occlusion_completion",
         "alphaQuality":"source_gif_lanczos_soft_edge",
         "meshingStrategy":"7x7_regular_ArtMesh_grid_over_authored_semantic_bounds",
         "mesh":mesh_points(bb),
         "anchors":semantic_anchors(semantic,bb),
         "semanticReviewed":False,"visualReviewed":False,
         **matrices[semantic]
        }
        files.append(file_entry)
    change=np.abs(composite.astype(np.float32)-source_high.astype(np.float32))
    changed=int(np.count_nonzero(np.any(change>1,axis=2)))
    mean=float(change.mean())
    alpha_source=source_high[:,:,3]>32
    alpha_cmp=composite[:,:,3]>32
    intersection=int(np.count_nonzero(alpha_source&alpha_cmp))
    union=int(np.count_nonzero(alpha_source|alpha_cmp))
    iou=intersection/max(1,union)
    qa={"schema":"KOMA-P0-FRONT-SEMANTIC-RESTORATION-QA-V1",
        "characterId":"p0_character_001", "yawDeg":0,"sourceWholeSha256":original_digest,
        "sourceHeroShaVerified":False,"sourcePartGroupHashes":part_sources,
        "totalArtMeshSlots":len(files),"physicalFarEyeSeparated":True,
        "semanticSourceMaskBboxes":source_mask_boxes,"meshDensity":"7x7_regular_grid",
        "metrics":{"changedPixelCount":changed,"meanAbsoluteChannelDifference":round(mean,5),
                   "silhouetteIoU":round(iou,6),
                   "softAlphaPixelCount":int(np.count_nonzero((composite[:,:,3]>0)&(composite[:,:,3]<255))),
                   "underpaintNativePixels":int(sum(x["underpaintNativePixels"] for x in matrices.values())),
                   "partVisiblePixelCounts":matrices},
        "status":"P1_FRONT_VISUAL_REVIEW_REQUIRED",
        "artisticAcceptance":"PENDING",
        "sourceRoles":["recovered_whole_GIF_visible","recovered_semantic_GIF_occluded_regions"]}
    (output/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
    (output/"parts.json").write_text(json.dumps({
        "schema":"KOMA-P0-ARTMESH-MANIFEST-V1","characterId":"p0_character_001",
        "canvas":[CANVAS,CANVAS], "yaw":0, "parts":files,
        "sourceStatus":"REAL_SOURCE_CANDIDATE","headReferenceSHA256":sha(root/"candidate-v2/whole/yaw000.png")
    },indent=2,ensure_ascii=False)+"\n")
    Image.fromarray(composite,"RGBA").save(report_dir/"front-composite.png")
    reference=Image.fromarray(source_high,"RGBA")
    reference.save(report_dir/"front-reference.png")
    manifest_path=output/"parts.json"
    manifest_record=json.loads(manifest_path.read_text(encoding="utf8"))
    manifest_record["referenceImage"]={
        "path":"diagnostics/front-reference.png",
        "sha256":sha(report_dir/"front-reference.png")}
    manifest_path.write_text(json.dumps(manifest_record,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    # Control image: exact reference, independent composite, and magnified pixel difference.
    review=Image.new("RGBA",(CANVAS*2,CANVAS),(30,41,57,255))
    review.alpha_composite(reference,(0,0))
    review.alpha_composite(Image.fromarray(composite,"RGBA"),(CANVAS,0))
    review.save(report_dir/"front-pair.png")
    diff=np.minimum(change*4,255).astype(np.uint8)
    Image.fromarray(diff[:,:,:3],"RGB").save(report_dir/"pixel-difference.png")
    # Semantic contact sheet makes any mixed eyes, repeated clip, face hole obvious.
    thumb=240;cols=4;rows=(len(SEMANTIC)+cols-1)//cols;tw=260;th=290
    sheet=Image.new("RGB",(tw*cols,th*rows),(25,35,49))
    draw=ImageDraw.Draw(sheet)
    for i,sid in enumerate(SEMANTIC):
        raw=Image.fromarray(layers[sid],"RGBA").resize((thumb,thumb),Image.Resampling.LANCZOS)
        bg=Image.new("RGBA",(thumb,thumb),(67,78,94,255));bg.alpha_composite(raw)
        ox=(i%cols)*tw+8;oy=(i//cols)*th+8
        sheet.paste(bg.convert("RGB"),(ox,oy))
        draw.text((ox,oy+245),sid,fill="white")
    sheet.save(report_dir/"semantic-contact.jpg",quality=93)
    print(json.dumps({"status":qa["status"],"metrics":qa["metrics"],
                      "sourceGroupHashes":part_sources,"files":len(files)},indent=2))
    return qa


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    args=parser.parse_args()
    build(args.root)
