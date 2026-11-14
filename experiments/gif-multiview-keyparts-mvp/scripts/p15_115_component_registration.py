#!/usr/bin/env python3
"""P15-115 measured shared garment ink registration and per-side trim ownership.

The actual original 67.5-degree source supplies canonical visible ink for bow,
jewel and left shoulder trim. Right trim keeps native view artwork where
physical visibility becomes partial. Source files remain immutable.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import numpy as np,cv2,json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-115-component-art';D.mkdir(parents=True,exist_ok=True)
Q=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
views=['60','67.5','75'];S=512;source='67.5'
roles=['bowFabric','jewel','goldTrimLeft','goldTrimRight']
srcMask={};data={}
def mask(view,role):
 material='goldTrim' if role.startswith('goldTrim') else role
 p=R/Q['views'][view]['layers'][material]['maskPath']
 a=np.asarray(Image.open(p).convert('L').resize((S,S),Image.Resampling.NEAREST))>128
 if role=='goldTrimLeft':a[:,342:]=False
 if role=='goldTrimRight':a[:,:342]=False
 return a
def iou(a,b):
 return round(float(np.count_nonzero(a&b))/max(1,np.count_nonzero(a|b)),5)
def center(a):
 y,x=np.where(a)
 if len(x)<25:raise ValueError('insufficient visible native contour')
 return np.array([x.mean(),y.mean()])
for role in roles:
 srcMask[role]=mask(source,role)
 basePath=R/Q['views'][source]['layers']['goldTrim' if role.startswith('goldTrim') else role]['texturePath']
 base=np.asarray(Image.open(basePath).convert('RGBA'))
 if role.startswith('goldTrim'):
  base=base.copy()
  if role=='goldTrimLeft':base[:,684:,:]=0
  else:base[:,:684,:]=0
 data[role]=(base,basePath)
result={'schema':'KOMA_P15_115_REGISTERED_GARMENT_PARTS_V1',
 'characterId':'p0_character_001','sourceView':source,
 'targetViews':views,'roles':roles,
 'method':'native 512-matte ECC alignment with explicit per-part source owner, inverse 1024 affine',
 'sourceArtImmutable':True,'registered':{},'sourceMatteIoU':{},
 'sourceOwnerPolicy':{'bowFabric':'67.5 native source throughout','jewel':'67.5 native source throughout',
  'goldTrimLeft':'67.5 native source throughout','goldTrimRight':'source-owned where correspondence supports it; native target art for 75-degree sparse trim'},
 'sourcePaintStatus':'native original material ink and colors, translated/deformed by measured affine only',
 'artistVisualApproved':False}
contact=Image.new('RGB',(400*3,390*5),'white');pen=ImageDraw.Draw(contact)
for ri,role in enumerate(roles):
 result['registered'][role]={}
 for vi,v in enumerate(views):
  src=srcMask[role];dst=mask(v,role)
  if v==source:
   W=np.float32([[1,0,0],[0,1,0]]);cc=1.0
  else:
   delta=center(dst)-center(src)
   init=np.float32([[1,0,-delta[0]],[0,1,-delta[1]]])
   signalA=cv2.GaussianBlur(src.astype(np.float32),(0,0),1.7 if role.startswith('gold') else 2.5)
   signalB=cv2.GaussianBlur(dst.astype(np.float32),(0,0),1.7 if role.startswith('gold') else 2.5)
   try:
    cc,W=cv2.findTransformECC(signalB,signalA,init,cv2.MOTION_AFFINE,
       (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,220,1e-7))
   except cv2.error as err:
    raise RuntimeError(f'{role} {v} registration unavailable: {err}') from err
  predicted=cv2.warpAffine(np.uint8(src)*255,W,(S,S),
       flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP)>128
  overlap=iou(predicted,dst)
  det=float(np.linalg.det(W[:,:2]))
  nativeFallback=(role=='goldTrimRight' and v=='75')
  if not nativeFallback and (det<.72 or det>1.60 or overlap<.30):
   raise ValueError(f'{role} {v} unstable correspondence: det {det} IoU {overlap}')
  # The right 75° strip is source owned instead of stretching an almost hidden
  # jacket design across a real depth/visibility change.
  owner='nativeTarget' if nativeFallback else 'canonical67.5'
  if nativeFallback:
   native=np.asarray(Image.open(R/Q['views'][v]['layers']['goldTrim']['texturePath']).convert('RGBA')).copy()
   native[:,:684,:]=0
   output=native
  else:
   W1024=W.copy();W1024[:,2]*=2
   output=cv2.warpAffine(data[role][0],W1024,(1024,1024),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,
      borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
  file=D/(role+'-yaw'+v.replace('.','p')+'.png')
  Image.fromarray(output,'RGBA').save(file)
  record={'source':str(data[role][1].relative_to(R)),'sourceSHA256':sha(data[role][1]),
   'targetMask':Q['views'][v]['layers']['goldTrim' if role.startswith('goldTrim') else role]['maskPath'],
   'targetMaskSHA256':sha(R/Q['views'][v]['layers']['goldTrim' if role.startswith('goldTrim') else role]['maskPath']),
   'sourceOwner':owner,'inverseAffine512':W.tolist(),'jacobianDeterminant':round(det,5),
   'ECC':round(float(cc),6),'sourceToNativeMaskIoU':overlap,
   'registeredPath':str(file.relative_to(R)),'registeredSHA256':sha(file)}
  result['registered'][role][v]=record
  print(role,v,'IoU',overlap,'det',round(det,3),'owner',owner,flush=True)
  backdrop=Image.new('RGBA',(1024,1024),'white')
  backdrop.alpha_composite(Image.fromarray(output,'RGBA'))
  crop=backdrop.convert('RGB').crop((400,630,820,1030)).resize((400,370),Image.Resampling.LANCZOS)
  contact.paste(crop,(vi*400,ri*390+20));pen.text((vi*400+6,ri*390+2),role+' '+v+' '+owner+' IoU '+str(overlap),fill='black')
result['sourceArtSHA256']={role:sha(data[role][1]) for role in roles}
# Source ink ownership at each angle is explicit, including deliberate native source fallback.
result['contact']=str((D/'component-registration-contact.jpg').relative_to(R))
contact.save(D/'component-registration-contact.jpg',quality=94)
(R/'evidence/p15-115-source-qa.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
