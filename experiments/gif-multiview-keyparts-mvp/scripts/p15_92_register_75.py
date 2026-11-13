#!/usr/bin/env python3
"""Register independent 75-degree P0 native illustration for four-keyview VDD study."""
from pathlib import Path
from PIL import Image
import numpy as np,hashlib,json
R=Path(__file__).resolve().parents[1]
A=R/'private-assets';D=A/'exports/p15-92-angle-keyart'
src=A/'p15-92-yaw075/yaw075-native.png'
provenance=json.loads((A/'p15-92-yaw075/generation-result.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert provenance['sha256']==sha(src)
assert provenance['actual_image_tool_used']=='image_gen.imagegen'
with Image.open(src) as f:
 assert f.size==(1254,1254) and f.mode=='RGBA'
 im=f.resize((1024,1024),Image.Resampling.LANCZOS)
arr=np.asarray(im).copy()
arr[:,:,3][arr[:,:,3]>=249]=255
out=D/'yaw075-registered.png'
Image.fromarray(arr,'RGBA').save(out)
foreground=arr[:,:,3]>128
y,x=np.where(foreground)
metrics={'size':[1024,1024],'mode':'RGBA',
 'alpha128Pixels':int(foreground.sum()),
 'alpha128BBox':[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)],
 'alpha254Pixels':int((arr[:,:,3]>=254).sum()),'transparentPixels':int((arr[:,:,3]==0).sum())}
p=R/'evidence/p15-92-native-keyart-qa.json'
qa=json.loads(p.read_text())
qa['nativeYaw75SHA256']=sha(src)
qa['registeredYaw75SHA256']=sha(out)
qa['sourceMetrics']['75']=metrics
qa['sourceAngles']=[45,60,75,90]
qa['nativeSourcesVerified']=4
m=qa['sourceMetrics']
qa['yaw75SilhouetteAreaBetweenSources']=m['90']['alpha128Pixels']<metrics['alpha128Pixels']<m['60']['alpha128Pixels']
qa['formalKeyframeAccepted']=False
qa['visualGate']='FOUR_INDEPENDENT_SOURCE_ANGLES_VISUAL_REVIEW_REQUIRED'
p.write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'src':sha(src),'registered':sha(out),'metrics75':metrics,
 'areaBracketed':qa['yaw75SilhouetteAreaBetweenSources']},indent=2))
