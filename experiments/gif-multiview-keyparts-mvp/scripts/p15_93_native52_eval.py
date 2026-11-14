#!/usr/bin/env python3
"""Normalize new image-generated 52.5 degree keyart and compare two shorter flow spans."""
from pathlib import Path
from PIL import Image,ImageDraw
import sys,hashlib,json
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"scripts"))
from flow_render import get_flow,morph
A=R/'private-assets';P=A/'exports/p15-92-angle-keyart'
D=A/'exports/p15-93-yaw0525-review';D.mkdir(parents=True,exist_ok=True)
SRC=A/'p15-93-yaw0525/yaw0525-native.png'
prov=json.loads((A/'p15-93-yaw0525/generation-result.json').read_text(encoding="utf-8"))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert prov.get('sha256')==sha(SRC)
assert bool(prov.get('actual_image_tool_used'))
with Image.open(SRC) as src:
 assert src.size==(1254,1254) and 'A' in src.getbands()
 original=np.asarray(src.convert('RGBA'))
 normalized=np.asarray(src.convert('RGBA').resize((1024,1024),Image.Resampling.LANCZOS)).copy()
normalized[:,:,3][normalized[:,:,3]>=249]=255
new=D/'yaw052p5-registered.png';Image.fromarray(normalized,'RGBA').save(new)
angles={45:P/'yaw045-reference.png',52.5:new,60:P/'yaw060-registered.png'}
pre={}
for a,p in angles.items():
 pre[a]=np.asarray(Image.open(p).convert('RGBA').resize((512,512),Image.Resampling.LANCZOS)).copy()
yy,xx=np.indices((512,512),dtype=np.float32)
grid=np.stack((xx,yy),axis=2)
frames={}
for a,b in ((45,52.5),(52.5,60)):
 ab,ba=get_flow(pre[a],pre[b],"dis")
 at=(a+b)/2
 im=morph(pre[a],pre[b],ab,ba,.5,grid)
 out=Image.fromarray(im,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
 dest=D/f"yaw{str(at).replace('.','p')}-blend.png";out.save(dest)
 frames[str(at)]={"path":str(dest.relative_to(R)),"sha256":sha(dest),"interpolation":"OpenCV DIS bidirectional optical flow",
   "sourceAngles":[a,b]}
items=[('45° source',angles[45]),('48.75° interp',D/'yaw48p75-blend.png'),
       ('52.5° native',new),('56.25° interp',D/'yaw56p25-blend.png'),
       ('60° source',angles[60])]
contact=Image.new('RGB',(370*len(items),415),'white');draw=ImageDraw.Draw(contact)
for i,(tag,p) in enumerate(items):
 im=Image.open(p).convert('RGBA');white=Image.new('RGBA',im.size,'white');white.alpha_composite(im)
 contact.paste(white.convert('RGB').resize((370,385),Image.Resampling.LANCZOS),(i*370,25))
 draw.text((i*370+8,6),tag,fill='black')
contact.save(D/'five-angle-contact.jpg',quality=93)
old=P/'yaw052p5.png'
comparison=Image.new('RGB',(410*3,445),'white');dr=ImageDraw.Draw(comparison)
for i,(tag,p) in enumerate((('old 52.5 DIS blend',old),('new 52.5 native',new),('60 source',angles[60]))):
 im=Image.open(p).convert('RGBA');white=Image.new('RGBA',im.size,'white');white.alpha_composite(im)
 comparison.paste(white.convert('RGB').resize((410,415),Image.Resampling.LANCZOS),(410*i,25))
 dr.text((410*i+7,5),tag,fill='black')
comparison.save(D/'old-new-compare.jpg',quality=93)
mask=normalized[:,:,3]>128
ys,xs=np.where(mask)
qa={"schema":"KOMA-P15-93-INDEPENDENT_YAW52_IMAGEGEN_V1",
    "model":"Codex CLI built-in image_gen.imagegen",
    "nativeSourceSHA256":sha(SRC),"registeredSourceSHA256":sha(new),
    "nativeDimensions":[1254,1254],"registeredDimensions":[1024,1024],
    "alpha128Pixels":int(mask.sum()),"alpha128BBox":[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],
    "independentSourceAngles":[45,52.5,60],
    "interpolatedAngles":[48.75,56.25],"frames":frames,
    "actualYawVerified":False,"formalArtMeshAccepted":False,
    "formalKeyframeAccepted":False,
    "visualGate":"INDEPENDENT_52_5_KEYART_VISUAL_REVIEW_REQUIRED",
    "contact":str((D/'five-angle-contact.jpg').relative_to(A))}
(R/'evidence/p15-93-native52-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({"nativeSHA256":qa["nativeSourceSHA256"],"registeredSHA256":qa["registeredSourceSHA256"],
"alpha128Pixels":qa["alpha128Pixels"],"subspanFrames":len(frames),
"visualGate":qa["visualGate"]},indent=2))
