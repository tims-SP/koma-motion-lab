#!/usr/bin/env python3
"""Register Codex-generated independent yaw60 P0 illustration and build multi-view evidence."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,hashlib,json,shutil
R=Path(__file__).resolve().parents[1]
A=R/'private-assets'
D=A/'exports/p15-92-angle-keyart';D.mkdir(parents=True,exist_ok=True)
C=A/'p15-92-codex'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p45=A/'p2-views/whole/yaw045.png';p90=A/'p2-views/whole/yaw090.png'
native=C/'yaw060-native.png'
prov=json.loads((C/'generation-result.json').read_text(encoding='utf-8'))
assert prov.get('sha256')==sha(native)
assert prov.get('tool')=='image_gen.imagegen'
with Image.open(native) as source:
 assert source.size==(1254,1254) and source.mode=='RGBA'
 raw=np.asarray(source)
 rgb=source.resize((1024,1024),Image.Resampling.LANCZOS)
# Most interior model alpha is 252-254; restore full opacity while preserving antialiased edges.
ra=np.asarray(rgb).copy();mask=ra[:,:,3]>=249
ra[:,:,3][mask]=255
registered=Image.fromarray(ra,'RGBA')
registered.save(D/'yaw060-registered.png')
for source,target in ((p45,D/'yaw045-reference.png'),(p90,D/'yaw090-reference.png')):
 shutil.copyfile(source,target)
def metrics(p):
 with Image.open(p) as i:
  a=np.asarray(i.convert('RGBA'))[:,:,3];nz=a>128
  ys,xs=np.where(nz)
  return {'size':[i.width,i.height],'mode':i.mode,'alpha128Pixels':int(nz.sum()),
  'alpha128BBox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],
  'alpha254Pixels':int((a>=254).sum()),'transparentPixels':int((a==0).sum())}
q={'schema':'KOMA-P15-92-CODEX_ANGLE_SOURCE_V1','characterId':'p0_character_001',
   'generator':'Codex CLI built-in image_gen.imagegen','requestedYaw':60,
   'actualYawVerified':False,'inputSourceHashes':{'yaw045':sha(p45),'yaw090':sha(p90)},
   'nativeOutputSHA256':sha(native),'registeredOutputSHA256':sha(D/'yaw060-registered.png'),
   'registeredSize':[1024,1024],
   'alphaNormalization':'fully opaque for native post-resample alpha >= 249, preserve semitransparent edges',
   'sourceMetrics':{'45':metrics(p45),'60':metrics(D/'yaw060-registered.png'),'90':metrics(p90)},
   'identityReferenceVerified':False,'formalKeyframeAccepted':False,'formalArtMeshAccepted':False,
   'visualGate':'INDEPENDENT_60_KEYART_FOR_VISUAL_REVIEW'}
m=q['sourceMetrics'];s=m['60']['alpha128Pixels'];assert m['90']['alpha128Pixels']<s<m['45']['alpha128Pixels']
# Figure displays original 45/90 independent raster sources and registered 60.
w,h=420,450
sheet=Image.new('RGB',(w*3,h),'white');draw=ImageDraw.Draw(sheet)
for idx,(key,p) in enumerate((('45',D/'yaw045-reference.png'),('60',D/'yaw060-registered.png'),('90',D/'yaw090-reference.png'))):
 fg=Image.open(p).convert('RGBA');bg=Image.new('RGBA',fg.size,'white');bg.alpha_composite(fg)
 tile=bg.convert('RGB').resize((420,420),Image.Resampling.LANCZOS)
 sheet.paste(tile,(idx*w,28))
 draw.text((idx*w+8,8),f'Independent original view: {key} deg',fill='black')
sheet.save(D/'source-triple-contact.jpg',quality=92)
q['contact']='private-assets/exports/p15-92-angle-keyart/source-triple-contact.jpg'
(R/'evidence/p15-92-native-keyart-qa.json').write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:q[k] for k in ('nativeOutputSHA256','registeredOutputSHA256','requestedYaw','actualYawVerified','sourceMetrics')},indent=2))
