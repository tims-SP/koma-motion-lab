from pathlib import Path
import hashlib,json,cv2,numpy as np
from PIL import Image
from p15_32_mesh_vdd import read,write,over
R=Path(__file__).resolve().parents[1];P=R/'private-assets';O=P/'exports/p15-41-profile-candidate';O.mkdir(parents=True,exist_ok=True)
S=P/'p15-independent-candidates/yaw065-artmesh/layers';G=P/'p15-independent-candidates/yaw065-artmesh/qa.json'
B=P/'p15-38-p0-registered-arc';Z=R/'evidence/p15-41-profile-qa.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
g=json.loads(G.read_text());roles=[r['semanticId'] for r in g['semanticLayerRecords']];layers={}
for item in g['semanticLayerRecords']:
 p=S/(item['semanticId']+'.png');assert sha(p)==item['sha256'];layers[item['semanticId']]=read(p)
assert len(layers)==13 and not layers['hair.clip.cross_gold'][:,:,3].any()
clip=np.asarray(Image.fromarray(read(B/'yaw65/hair.clip.cross_gold.png'),'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
y,x=np.indices(clip.shape[:2]);a=clip[:,:,3].astype(float);cx=(x*a).sum()/a.sum();cy=(y*a).sum()/a.sum()
clip=cv2.warpAffine(clip,np.float32([[1,0,690-cx],[0,1,295-cy]]),(1024,1024),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0))
layers['hair.clip.cross_gold']=clip
comp=np.zeros((1024,1024,4),np.uint8);(O/'layers').mkdir(exist_ok=True)
for role in roles:
 write(O/'layers'/(role+'.png'),layers[role]);comp=over(comp,layers[role])
write(O/'candidate.png',comp)
for out,src in [('source-60.png',B/'yaw60/composite.png'),('source-65.png',B/'yaw65/composite.png'),('independent-source.png',P/'p15-independent-candidates/yaw065-source-rgba.png')]: (O/out).write_bytes(src.read_bytes())
write(O/'clip.png',clip)
qa={'schema':'KOMA-P15-41-INDEPENDENT-PROFILE-CANDIDATE-V1','characterId':'p0_character_001','sourceRegistrySHA256':sha(G),'sourceIndependentArtSHA256':sha(P/'p15-independent-candidates/yaw065-source-rgba.png'),'roles':roles,'layerCount':len(roles),'clipSourceSHA256':sha(B/'yaw65/hair.clip.cross_gold.png'),'clipAnchor':[690,295],'candidateSHA256':sha(O/'candidate.png'),'heroSourceApproved':False,'yaw65PoseApproved':False,'hiddenInkApproved':False,'visualArtApproved':False}
Z.write_text(json.dumps(qa,indent=2)+'\n');print(json.dumps({'roles':len(roles),'candidate':qa['candidateSHA256']}))
