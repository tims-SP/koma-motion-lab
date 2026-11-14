#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
from collections import Counter
import hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-73-interactive-sam';D.mkdir(parents=True,exist_ok=True)
srcp=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png';src=Image.open(srcp).convert('RGBA')
labelp=D/'sam-mask-1.png';label=Image.open(labelp).convert('RGB');target=(227,148,102);w,h=label.size
raw=Image.new('L',(w,h));raw.putdata([255 if c==target else 0 for c in label.getdata()]);px=raw.load();seen=set();components=[]
for y in range(h):
 for x in range(w):
  if not px[x,y] or (x,y) in seen:continue
  stack=[(x,y)];seen.add((x,y));comp=[]
  while stack:
   a,b=stack.pop();comp.append((a,b))
   for yy in range(max(0,b-1),min(h,b+2)):
    for xx in range(max(0,a-1),min(w,a+2)):
     if px[xx,yy] and (xx,yy) not in seen:seen.add((xx,yy));stack.append((xx,yy))
  components.append(comp)
main=max(components,key=len);mask=Image.new('L',(w,h));mp=mask.load()
for x,y in main:mp[x,y]=255
box=(350,125,862,637);crop=src.crop(box);alpha=ImageChops.multiply(mask,crop.getchannel('A'));haircrop=crop.copy();haircrop.putalpha(alpha)
hair=Image.new('RGBA',src.size,(0,0,0,0));hair.paste(haircrop,(box[0],box[1]))
base=src.copy();ba=base.getchannel('A');ba.paste(0,box,mask);base.putalpha(ba)
recon=Image.alpha_composite(base,hair);recondiff=ImageChops.difference(src,recon)
fullmask=Image.new('L',src.size);fullmask.paste(mask,(box[0],box[1]));tint=Image.new('RGBA',src.size,(20,220,80,0));tint.putalpha(fullmask.point(lambda a:int(a*.42)));overlay=Image.alpha_composite(src,tint)
raw.save(D/'front-bangs-mask-raw.png');mask.save(D/'front-bangs-mask-largest.png');hair.save(D/'front-bangs-rgba.png');base.save(D/'base-with-front-bangs-removed.png');recon.save(D/'reconstruction-0px.png');overlay.save(D/'mask-overlay.png')
# checkerboard preview of the isolated transparent layer
checker=Image.new('RGBA',src.size,(240,240,240,255));dr=ImageDraw.Draw(checker)
for y in range(0,src.height,32):
 for x in range(0,src.width,32):
  if ((x//32)+(y//32))%2:dr.rectangle((x,y,x+31,y+31),fill=(190,190,190,255))
checker.alpha_composite(hair);checker.convert('RGB').save(D/'front-bangs-checker.jpg',quality=93)
# compose the semantic hair candidate with existing approved face underpaint, eye, and gold clip
under=Image.open(R/'private-assets/exports/p15-70-seam-repair/forehead-seam-repaired.png').convert('RGBA')
eye=Image.open(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png').convert('RGBA')
clip=Image.open(R/'private-assets/exports/p15-69-clip-separation/hair-clip-gold-independent.png').convert('RGBA')
for dx in (0,9,18):
 moved=Image.new('RGBA',under.size);moved.alpha_composite(eye,(dx,0));frame=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(under,moved),hair),clip)
 frame.save(D/f'p15-73-composite-{dx:02d}.png');frame.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'p15-73-face-{dx:02d}.png')
# motion contact sheet
contact=Image.new('RGB',(1050,400),'#172638');draw=ImageDraw.Draw(contact)
for i,dx in enumerate((0,9,18)):
 im=Image.open(D/f'p15-73-composite-{dx:02d}.png').convert('RGBA').crop((445,265,795,605)).resize((350,360),Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im);contact.paste(bg.convert('RGB'),(i*350,30));draw.text((i*350+10,8),f'eye offset {dx}px',fill='white')
contact.save(D/'p15-73-motion-contact.jpg',quality=91)
# metrics
pos=[(250,245),(300,220),(340,260),(205,270)];neg=[(240,345),(250,415),(390,170),(400,390)]
inside=lambda p:mask.getpixel(p)>0
frames={};face_roi=(510,425,685,530);src_alpha=src.getchannel('A').crop(face_roi)
for dx in (0,9,18):
 f=Image.open(D/f'p15-73-composite-{dx:02d}.png').convert('RGBA');fa=f.getchannel('A').crop(face_roi);hole=ImageChops.subtract(src_alpha,fa);frames[str(dx)]={'alphaHoleBBox':list(hole.getbbox()) if hole.getbbox() else None,'alphaBBox':list(f.getchannel('A').getbbox()),'sha256':hashlib.sha256((D/f'p15-73-composite-{dx:02d}.png').read_bytes()).hexdigest()}
old=Image.open(R/'private-assets/exports/p15-70-seam-repair/eye-shift-00-seam-repaired.png').convert('RGBA')
new0=Image.open(D/'p15-73-composite-00.png').convert('RGBA');diffold=ImageChops.difference(new0,old);diffsrc=ImageChops.difference(new0,src)
ui_mask=Image.open(D/'ui-point-mask-38-0.png').convert('RGB');ui_colors=Counter(ui_mask.getdata())
q={'schema':'KOMA-P15-73-SAM-FRONT-BANGS-CANDIDATE-V1','characterId':'p0_character_001','source':'P15-56 same-view candidate-erode-2.png','sourceSHA256':hashlib.sha256(srcp.read_bytes()).hexdigest(),'samProvider':'basimbashir/segment_anything_webui','samModel':'SAM ViT-B CPU','usedMaskMethod':'SAM automatic instance segmentation; select instance by positive anchor coordinate, then verify negative anchor coordinates. This is not a point-conditioned mask.','selectedLabelRGB':list(target),'samLabelSHA256':hashlib.sha256(labelp.read_bytes()).hexdigest(),'rawMaskPixels':sum(raw.histogram()[1:]),'rawConnectedComponents8':len(components),'largestComponentPixels':len(main),'largestComponentBBox':list(mask.getbbox()),'positiveAnchorPointsInMask':all(inside(p) for p in pos),'negativeVerificationPointsOutsideMask':all(not inside(p) for p in neg),'eyeAndCheekAnchorsOutside':not inside((240,345)) and not inside((250,415)),'goldHairpinAnchorOutside':not inside((390,170)),'hairLayerSHA256':hashlib.sha256((D/'front-bangs-rgba.png').read_bytes()).hexdigest(),'hairLayerAlphaBBox':list(hair.getchannel('A').getbbox()),'hairLayerAlphaPixels':sum(hair.getchannel('A').histogram()[1:]),'sourceReconstructionDiffBBox':list(recondiff.getbbox()) if recondiff.getbbox() else None,'sourceReconstructionExact':recondiff.getbbox() is None,'p15_70CompositeDiffBBox':list(diffold.getbbox()) if diffold.getbbox() else None,'p15_56CompositeDiffBBox':list(diffsrc.getbbox()) if diffsrc.getbbox() else None,'motionFrames':frames,'uiPointPromptAttempt':'FAILED_OVERSEGMENTED_HEAD_MASK','uiPointPromptMaskColors':len(ui_colors),'uiPointPromptMaskForegroundPixels':sum(v for k,v in ui_colors.items() if k!=(255,255,255)),'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,'status':'PROVISIONAL_FRONT_BANGS_LAYER_CANDIDATE_PASS_0_9_18_REVIEW_PENDING','limitations':['SAM automatic instance selection rather than true multi-point conditioned mask','interactive UI point-prompt run returned a full-head mask and was rejected','0px composite discrepancy remains localized to independent gold hairpin region','small mask-edge speckles and source-alpha edge require final cleanup before formal ArtMesh'],'next':'P15-74 integrate this provisional front-bangs RGBA into the native VDD/ArtMesh prototype, test eye movement and head yaw, and refine the hairpin-localized 0px discrepancy without changing approved P0 identity'}
(R/'evidence/p15-73-mask-extraction-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');print(json.dumps(q,ensure_ascii=False,indent=2))
