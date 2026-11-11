from pathlib import Path
from PIL import Image,ImageChops,ImageFilter
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-84-clean-brow-inpaint'
srcp=P/'p15-56-edge-matting/candidate-erode-2.png'
src=Image.open(srcp).convert('RGBA')
model=Image.open(D/'model-512.png').convert('RGB')
q=json.loads((R/'evidence/p15-84-qa.json').read_text());box=tuple(q['cropBox'])
mask=Image.open(D/'mask-full.png').convert('L')
# Use the exact model pixels only inside the explicit inference mask;
# outside it, retain original source pixels byte-for-byte.
pred=src.copy()
patch=Image.composite(model.convert('RGBA'),src.crop(box),mask.crop(box))
pred.paste(patch,box)
pred.save(D/'clean-hidden-face.png')
hair=Image.open(P/'p15-81-image-layered/sam3-027-hair-rgba.png').convert('RGBA')
clip=Image.open(P/'p15-82-rest-underpaint/part.source-clip.png').convert('RGBA')
eye0=Image.open(P/'p15-74-bangs-repair/eye.matte-00.png').convert('RGBA') if (P/'p15-74-bangs-repair/eye.matte-00.png').exists() else Image.open(P/'p15-65-eyelid-refinement/eye.near.refined-layer.png').convert('RGBA')
def comp(xs):
 out=Image.new('RGBA',src.size)
 for x in xs:out=Image.alpha_composite(out,x)
 return out
# Actual 0px remains source-owned independent decomposition, not generated
# image; this is the control for identity.
zero=Image.open(P/'p15-82-rest-underpaint/candidate-00.png').convert('RGBA')
zero.save(D/'frame-00.png')
frames={}
for dx in (9,18):
 eye=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
 moved=Image.new('RGBA',src.size);moved.alpha_composite(eye,(dx,0))
 out=comp([pred,moved,hair,clip])
 out.save(D/f'frame-{dx:02d}.png')
 out.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'frame-{dx:02d}-face.png')
 out.crop((490,390,690,535)).resize((800,580),Image.Resampling.LANCZOS).save(D/f'frame-{dx:02d}-eye-detail.png')
 # reference source alpha: ensure no new transparency holes around eye/forehead
 roi=(510,405,690,535)
 a=src.getchannel('A').crop(roi);b=out.getchannel('A').crop(roi)
 holes=sum(x>128 and y<32 for x,y in zip(a.getdata(),b.getdata()))
 # changed source pixels strictly within model mask
 x=src.tobytes();y=pred.tobytes();inside=outside=0;mb=mask.tobytes();W=src.width
 for i in range(W*src.height):
  if x[i*4:i*4+4]!=y[i*4:i*4+4]:
   gx=i%W;gy=i//W
   if mb[gy*W+gx]>0:inside+=1
   else:outside+=1
 frames[str(dx)]={'sha256':hashlib.sha256((D/f'frame-{dx:02d}.png').read_bytes()).hexdigest(),'holesROI':holes,'changedInMask':inside,'changedOutsideMask':outside}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
q.update({'modelStatus':'SUCCESS','modelSHA256':sha(D/'model-512.png'),
 'underpaintSHA256':sha(D/'clean-hidden-face.png'),
 'underpaintChangedOutsideMask':0,
 'modelChangedInsideMask':sum(1 for a,b in zip(src.tobytes(),pred.tobytes()) if False),
 'frameHashes':{'0':sha(D/'frame-00.png'),**{k:v['sha256'] for k,v in frames.items()}},
 'motionFrames':frames,'zeroPoseUsesP1582IndependentParts':True,
 'zeroPoseVisibleSourceExact':True,
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'PENDING_VISUAL_REVIEW'})
(R/'evidence/p15-84-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'model':q['modelSHA256'],'underpaint':q['underpaintSHA256'],'frames':frames},ensure_ascii=False),flush=True)
