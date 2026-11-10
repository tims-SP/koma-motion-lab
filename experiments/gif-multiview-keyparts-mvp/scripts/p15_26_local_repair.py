#!/usr/bin/env python3
"""P15-26 localized source-preserving repair of failed P15-25 parts.

Use canonical VDD original RGBA, edit only small details, do NOT substitute
painted wholesale chunks. These are retouch candidates, not new standalone art.
"""
import hashlib,json
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from p1_front_semantic import alpha_over
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
Q21=json.loads((R/'evidence/p15-21-intermediate-components-qa.json').read_text())
OUT=P/'p15-26-localized-repair';OUT.mkdir(exist_ok=True)
ANG=[55,57.5,60,62.5,65]
ROLES=['hair.side','hair.ahoge','eye.far']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def slug(a):return 'yaw'+(str(int(a)) if a%1==0 else str(a).replace('.','p'))
def edit_side(a,angle):
 b=a.copy()
 h,w=b.shape[:2]
 mask=a[:,:,3]>80
 # Add a narrow pink-lavender highlight along existing texture INSIDE true hair alpha.
 ys,xs=np.where(mask)
 if not len(xs):raise ValueError('empty side hair')
 x0,x1=np.percentile(xs,[21,65]);y0,y1=np.percentile(ys,[29,83])
 guide=np.zeros((h,w),np.uint8)
 points=np.array([[round(x0+12),round(y0)],[round(x0+24),round(y0+(y1-y0)*.3)],
                  [round(x1-14),round(y1)]],np.int32)
 cv2.polylines(guide,[points.reshape(-1,1,2)],False,205,2,cv2.LINE_AA)
 guide=(guide.astype(np.float32)/255)*mask.astype(np.float32)
 # Only tint up to 8/255 channel values. No new alpha or silhouette changes.
 tint=np.array([225,172,204],np.float32)
 mix=(guide*.16)[:,:,None]
 rgb=b[:,:,:3].astype(np.float32)
 b[:,:,:3]=np.clip(rgb*(1-mix)+tint*mix,0,255).astype(np.uint8)
 return b
def edit_ahoge(a,angle):
 # Thin only tiny alpha halo artifacts, preserve original slender silhouette.
 b=a.copy();alpha=a[:,:,3]
 eroded=cv2.erode(alpha,np.ones((3,3),np.uint8),iterations=1)
 # 14% soft nibble, preserving most source art and inner stroke.
 b[:,:,3]=np.round(.86*alpha.astype(np.float32)+.14*eroded).astype(np.uint8)
 return b
def edit_far_eye(a,angle):
 b=a.copy()
 alpha=a[:,:,3].astype(np.float32)
 ys,xs=np.where(alpha>16)
 if len(xs)==0:raise ValueError('empty far eye')
 # Continuous small attenuation at nose-facing portion, not a disappearing eye.
 x0,x1=float(xs.min()),float(xs.max())
 center=(x0+x1)/2;spread=max(10,(x1-x0)*.45)
 X=np.arange(a.shape[1],dtype=np.float32)[None,:]
 t=(angle-55)/10
 factor=1-(.04+.09*t)*np.clip((X-center)/spread,0,1)
 b[:,:,3]=np.round(alpha*factor).clip(0,255).astype(np.uint8)
 return b
EDIT={'hair.side':edit_side,'hair.ahoge':edit_ahoge,'eye.far':edit_far_eye}
def run():
 frames=[]
 for angle in ANG:
  name=slug(angle)
  info=next(x for x in Q21['frames'] if x['yaw']==angle)
  dest=OUT/name;dest.mkdir(exist_ok=True)
  repaired={};roles=[]
  for role in ROLES:
   p=P/'p15-21-intermediate-components'/name/(role+'.png')
   old=np.asarray(Image.open(p).convert('RGBA'))
   new=EDIT[role](old,angle)
   if np.array_equal(new,old):raise AssertionError('No edit '+role)
   out=dest/(role+'.png');Image.fromarray(new,'RGBA').save(out)
   a=old[:,:,3]>16;b=new[:,:,3]>16
   union=int(np.count_nonzero(a|b));intersection=int(np.count_nonzero(a&b))
   rgb_changed=int(np.count_nonzero(np.any(np.abs(old[:,:,:3].astype('int16')-new[:,:,:3].astype('int16'))>1,axis=2)&(a|b)))
   alpha_changed=int(np.count_nonzero(old[:,:,3]!=new[:,:,3]))
   roles.append({'role':role,'sourceSHA256':sha(p),'sha256':sha(out),
      'path':str(out.relative_to(P)),'rgbChangedPixels':rgb_changed,
      'alphaChangedPixels':alpha_changed,'alphaIoU':round(intersection/max(1,union),6),
      'sourcePreserved':True,'newIndependentArt':False})
   repaired[role]=np.asarray(Image.fromarray(new,'RGBA').resize((443,443),Image.Resampling.LANCZOS))
  oldnative=np.zeros((443,443,4),np.uint8);modified=np.zeros_like(oldnative)
  for layer in info['roles']:
   img=np.asarray(Image.open(P/layer['native']).convert('RGBA'))
   oldnative=alpha_over(oldnative,img)
   modified=alpha_over(modified,repaired.get(layer['role'],img))
  old1024=np.asarray(Image.fromarray(oldnative,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
  source1024=np.asarray(Image.open(P/'p15-21-layered-anatomy'/(name+'.png')).convert('RGBA'))
  if not np.array_equal(old1024,source1024):raise AssertionError('Source changed')
  outcomp=dest/'diagnostic-local-repair.png'
  img=Image.fromarray(modified,'RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
  img.save(outcomp)
  pix=np.asarray(img)
  a=pix[:,:,3]>16;b=source1024[:,:,3]>16
  frames.append({'angle':angle,'roles':roles,'diagnostic':str(outcomp.relative_to(P)),
    'diagnosticSHA256':sha(outcomp),'baselineRoundtripExact':True,
    'compositeAlphaIoU':round(np.count_nonzero(a&b)/max(1,np.count_nonzero(a|b)),6),
    'rgbChangedPixelsVsBaseline':int(np.count_nonzero(np.any(np.abs(pix[:,:,:3].astype('int16')-source1024[:,:,:3].astype('int16'))>2,axis=2)))})
 report={'schema':'KOMA-P15-26-LOCAL-SOURCE-PRESERVING-RETOUCH-V1',
  'characterId':'p0_character_001','angles':ANG,'roles':ROLES,
  'sourceReference':'P15-21 approved engineering ArtMesh layout, not artist approved intermediate views',
  'method':'LOCAL_TINT_AND_ALPHA_REFINEMENT_OF_SOURCE_VDD_TEXTURE',
  'independentPaintingProduced':False,'formalArtAccepted':False,
  'sourcePixelProvenancePreserved':True,'productionVddChanged':False,
  'visualIssueFromP15_25':'FAILED_FULL_REPLACEMENT_HARD_SIDE_HAIR_LARGE_FAR_EYE_LOOP_AHOGE',
  'frames':frames,'next':'review close-up identity, anatomy and true hidden underpaint; seek approved standalone keypart paintings'}
 (R/'evidence/p15-26-local-repair-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'frames':len(frames),'editedParts':sum(len(x['roles']) for x in frames),
  'alphaIoU':[f['compositeAlphaIoU'] for f in frames],
  'rgbChanges':[f['rgbChangedPixelsVsBaseline'] for f in frames],
  'baselineExact':all(f['baselineRoundtripExact'] for f in frames)},ensure_ascii=False))
if __name__=='__main__':run()
