#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageChops
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-85-outer-eye-seam'
qpath=R/'evidence/p15-85-qa.json';q=json.loads(qpath.read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=Image.open(P/'p15-84-clean-brow-inpaint/clean-hidden-face.png').convert('RGBA')
model=Image.open(D/'model-512.png').convert('RGBA')
mask=Image.open(D/'semantic-residual-mask.png').convert('L')
box=(380,300,892,812)
new=base.copy();patched=Image.composite(model,base.crop(box),mask.crop(box));new.paste(patched,box)
new.save(D/'revised-hidden-face.png')
a=base.tobytes();b=new.tobytes();m=mask.tobytes()
changed=sum(a[i*4:i*4+4]!=b[i*4:i*4+4] for i in range(len(m)))
outside=sum(a[i*4:i*4+4]!=b[i*4:i*4+4] for i,v in enumerate(m) if not v)
assert outside==0 and changed>0
hair=Image.open(P/'p15-81-image-layered/sam3-027-hair-rgba.png').convert('RGBA')
clip=Image.open(P/'p15-82-rest-underpaint/part.source-clip.png').convert('RGBA')
src=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
frameqa={}
for dx in (0,9,18):
 if dx==0:
  frame=Image.open(P/'p15-82-rest-underpaint/candidate-00.png').convert('RGBA')
 else:
  eye=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
  moved=Image.new('RGBA',src.size);moved.alpha_composite(eye,(dx,0))
  frame=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(new,moved),hair),clip)
 frame.save(D/f'frame-{dx:02d}.png')
 frame.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'frame-{dx:02d}-face.png')
 frame.crop((500,395,690,515)).resize((950,600),Image.Resampling.NEAREST).save(D/f'frame-{dx:02d}-detail.png')
 ref=Image.open(P/f'p15-84-clean-brow-inpaint/frame-{dx:02d}.png').convert('RGBA')
 fa=frame.tobytes();fb=ref.tobytes()
 diff=sum(fa[i*4:i*4+4]!=fb[i*4:i*4+4] for i in range(src.width*src.height))
 roi=(510,405,690,535)
 holes=sum(x>128 and y<32 for x,y in zip(src.getchannel('A').crop(roi).getdata(),frame.getchannel('A').crop(roi).getdata()))
 frameqa[str(dx)]={'sha256':sha(D/f'frame-{dx:02d}.png'),'changedAgainstP1584':diff,'newTransparentHolesROI':holes}
new.crop((500,395,690,515)).resize((950,600),Image.Resampling.NEAREST).save(D/'revised-underpaint-detail.png')
q.update({'status':'MODEL_RETURNED','eventId':'e59787e9697c430ba934535b10b53aeb',
 'modelSHA256':sha(D/'model-512.png'),'modelBytes':(D/'model-512.png').stat().st_size,
 'revisedUnderpaintSHA256':sha(D/'revised-hidden-face.png'),
 'changedInsideMaskPixels':changed,'changedOutsideMaskPixels':outside,'frames':frameqa,
 'zeroPoseUsesIndependentSourceLayers':True,
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'PENDING_ACTUAL_VISUAL_INSPECTION'})
qpath.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'changedPixels':changed,'outside':outside,'frames':frameqa},ensure_ascii=False))
