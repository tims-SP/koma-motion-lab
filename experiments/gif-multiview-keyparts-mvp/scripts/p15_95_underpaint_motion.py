#!/usr/bin/env python3
"""P0 yaw60: model-authored hidden-face underpaint behind SAM3-owned front hair."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFilter
import hashlib,json,statistics,numpy as np
R=Path(__file__).resolve().parents[1]
A=R/"private-assets"; P=A/"exports"
G=A/"p15-95-underpaint";D=P/"p15-95-yaw060-motion"
D.mkdir(parents=True,exist_ok=True)
sourcePath=P/"p15-92-angle-keyart/yaw060-registered.png"
nativePath=G/"face-underpaint-native.png"
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=Image.open(sourcePath).convert("RGBA")
native=Image.open(nativePath).convert("RGBA")
assert src.size==(1024,1024) and native.size==(1254,1254)
model=Image.open(G/"registered-translation.png").convert("RGB")
assert model.size==(1024,1024)
box=(450,275,870,695)
crop=model.resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS)
registered=src.copy()
registered.paste(crop.convert("RGBA"),box[:2])
registered.save(D/"generated-face-aligned.png")
sam=Image.open(P/"p15-94-sam3-yaw060/hair-candidate-0-alpha1024.png").convert("L")
guard=Image.open(G/"source-underpaint-mask-1024.png").convert("L")
# Semantic source hair support intersected with face-region ownership.
candidate=ImageChops.darker(sam,guard)
variants={
 "semantic":candidate,
 "inset":candidate.point(lambda p:255 if p>247 else 0).filter(ImageFilter.GaussianBlur(0.45)),
}
raw_source=np.asarray(src)
assert raw_source.shape==(1024,1024,4)
roi=(485,290,835,670)
def composite(*layers):
 out=Image.new("RGBA",src.size,(0,0,0,0))
 for im in layers:out=Image.alpha_composite(out,im)
 return out
def metrics(a,b,box):
 aa=np.asarray(a.crop(box).convert('RGB'),dtype=np.float32)
 bb=np.asarray(b.crop(box).convert('RGB'),dtype=np.float32)
 return round(float(np.abs(aa-bb).mean()),4)
qa={"schema":"KOMA-P15-95-CODEX_SAM3_YAW60_UNDERPAINT_V1",
    "characterId":"p0_character_001",
    "sourceSHA256":sha(sourcePath),"sam3MaskSHA256":sha(P/"p15-94-sam3-yaw060/hair-candidate-0-alpha1024.png"),
    "nativeModelSHA256":sha(nativePath),"registeredTranslationModelSHA256":sha(G/"registered-translation.png"),
    "nativeImageDimensions":[1254,1254],"sourceCanvas":[1024,1024],
    "cropBox":list(box),"modelMaskedEditingGuaranteed":False,
    "sourceOwnedFrontHair":True,"formalArtMeshAccepted":False,
    "formalKeyframeAccepted":False,"visualGate":"PENDING_MODEL_UNDERPAINT_MOTION_REVIEW","variants":{}}
sheet=Image.new("RGB",(4*350,2*420),"white");draw=ImageDraw.Draw(sheet)
for key,mask in variants.items():
 layer=Image.new("RGBA",src.size,(0,0,0,0))
 # Copy the exact source RGB under semantic hair; pixel opacity comes from original alpha and mask.
 layer.paste(src,(0,0))
 rgba=np.array(layer)
 rgba[:,:,3]=((rgba[:,:,3].astype(np.uint16)*np.asarray(mask,dtype=np.uint16)+127)//255).astype(np.uint8)
 hair=Image.fromarray(rgba,"RGBA")
 hair.save(D/f"{key}-front-hair.png")
 mask.save(D/f"{key}-mask.png")
 base=Image.composite(registered,src,mask)
 base.save(D/f"{key}-underpaint.png")
 rawRest=composite(base,hair)
 rawRest.save(D/f"{key}-reconstruction.png")
 # Visual movement: exact source rest, then dynamic hair layer over the underpaint.
 frameData={};frames=[];prev=src
 for dx in range(0,13):
  shifted=Image.new("RGBA",src.size,(0,0,0,0))
  shifted.paste(hair,(dx,0))
  corrected=src.copy() if dx==0 else composite(base,shifted)
  baseline=src.copy() if dx==0 else composite(src,shifted)
  fp=D/f"{key}-frame-{dx:02}.png";corrected.save(fp)
  if dx in (0,4,8,12):
   baseline.save(D/f"{key}-baseline-{dx:02}.png")
  rgb=np.asarray(corrected.crop(roi).convert("RGB"))
  sourceAlpha=np.asarray(src.getchannel("A").crop(roi))
  correctedAlpha=np.asarray(corrected.getchannel("A").crop(roi))
  holes=int(np.logical_and(sourceAlpha>128,correctedAlpha<32).sum())
  changed=np.any(np.asarray(corrected)!=raw_source,axis=2)
  # The changed region must be confined to the source face guard plus translated hair support.
  allowed=np.asarray(mask)>0
  moved=np.zeros_like(allowed)
  if dx:moved[:,dx:]=allowed[:,:-dx]
  permitted=allowed|moved
  outside=int((changed & (~permitted)).sum())
  frameData[str(dx)]={"sha256":sha(fp),"changedPixels":int(changed.sum()),
     "changesOutsideGuardAndTranslatedHair":outside,"newTransparentHoles":holes,
     "adjacentRGBMAE":metrics(prev,corrected,roi) if dx>0 else 0}
  prev=corrected
  frames.append(corrected.crop(roi).convert("RGB").resize((350,380),Image.Resampling.LANCZOS))
 frames[0].save(D/f"{key}-motion.gif",save_all=True,append_images=frames[1:],duration=130,loop=0)
 restDifferences=int(np.any(np.asarray(src)!=np.asarray(rawRest),axis=2).sum())
 qa["variants"][key]={"maskSHA256":sha(D/f"{key}-mask.png"),
 "modelBackgroundSHA256":sha(D/f"{key}-underpaint.png"),
 "frontHairSHA256":sha(D/f"{key}-front-hair.png"),
 "modelRestComparedToSourceChangedPixels":restDifferences,
 "sourceRestPoseUsedExact":True,"frames":frameData,
 "firstTransitionRatioVsLaterMedian":round(frameData["1"]["adjacentRGBMAE"]/
    max(.00001,statistics.median(frameData[str(i)]["adjacentRGBMAE"] for i in range(2,13))),3)}
row=0
for name,im in [("Source",src),("Generated face",registered),
                 ("Semantic underpaint",Image.open(D/"semantic-underpaint.png").convert("RGBA")),
                 ("Inset underpaint",Image.open(D/"inset-underpaint.png").convert("RGBA"))]:
   img=Image.new("RGBA",im.size,"white");img.alpha_composite(im)
   tile=img.convert("RGB").crop(roi).resize((350,385),Image.Resampling.LANCZOS)
   x=row*350
   sheet.paste(tile,(x,28))
   draw.text((x+6,8),name,fill="black")
   row+=1
for idx,dx in enumerate((4,8,12)):
 for name in ("baseline","underpaint"):
  tag="semantic"
  fp=D/f"{tag}-baseline-{dx:02}.png" if name=="baseline" else D/f"{tag}-frame-{dx:02}.png"
  im=Image.open(fp).convert("RGB").crop(roi).resize((220,385),Image.Resampling.LANCZOS)
  # separate candidate frame summary below rather than conflating with comparison contact
  im.save(D/f"semantic-{name}-{dx:02}-crop.png")
sheet.save(D/"underpaint-source-contact.jpg",quality=93)
compare=Image.new("RGB",(4*350,2*410),"white");dr=ImageDraw.Draw(compare)
for col,dx in enumerate((0,4,8,12)):
 for row,name in enumerate(("baseline","underpaint")):
  if dx==0:out=src
  else:out=Image.open(D/f"semantic-{'baseline' if name=='baseline' else 'frame'}-{dx:02}.png").convert("RGBA")
  tile=Image.new("RGBA",out.size,"white");tile.alpha_composite(out)
  compare.paste(tile.convert("RGB").crop(roi).resize((350,380),Image.Resampling.LANCZOS),(col*350,row*410+27))
  dr.text((col*350+6,row*410+6),f"{name} dx={dx}",fill="black")
compare.save(D/"dynamic-contact.jpg",quality=94)
qa["modelContact"]="private-assets/exports/p15-95-yaw060-motion/underpaint-source-contact.jpg"
qa["motionContact"]="private-assets/exports/p15-95-yaw060-motion/dynamic-contact.jpg"
(R/"evidence/p15-95-underpaint-motion-qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
summary={n:{k:obj[k] for k in ("modelRestComparedToSourceChangedPixels","firstTransitionRatioVsLaterMedian")}|
 {'frame12Changes':obj['frames']['12']['changedPixels'],
  'frame12Outside':obj['frames']['12']['changesOutsideGuardAndTranslatedHair'],
  'frame12Holes':obj['frames']['12']['newTransparentHoles']}
 for n,obj in qa["variants"].items()}
print(json.dumps(summary,indent=2))
