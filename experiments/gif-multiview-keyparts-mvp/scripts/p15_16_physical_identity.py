#!/usr/bin/env python3
"""P15-16: physical near/far anchor routing verification for original PSD roles.

P15-15 splits are reversible; this stage repairs physical side identity where
supported by measured P5 anchors, retaining ambiguity rather than inventing art.
"""
import hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
PRIVATE=ROOT/'private-assets'
OLD=json.loads((ROOT/'evidence/p15-15-role-routing-qa.json').read_text())
CAM=json.loads((ROOT/'evidence/p15-12-camera-proxy-qa.json').read_text())
DEST=PRIVATE/'p15-16-physical-identity'
REPORT=ROOT/'evidence/p15-16-physical-identity-qa.json'
ROLES=OLD['views'][0]['roles']
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(path):return np.asarray(Image.open(path).convert('RGBA')).copy()
def write(path,a):
 path.parent.mkdir(parents=True,exist_ok=True)
 Image.fromarray(a,'RGBA').save(path)
def main():
 frame45=next(f for f in CAM['frames'] if f['yaw']==45)
 nearx=frame45['anchors']['eye.near.iris']['xy'][0]*.75
 farx=frame45['anchors']['eye.far.iris']['xy'][0]*.75
 earx=frame45['anchors']['ear.near']['xy'][0]*.75
 if not nearx<farx: raise AssertionError('Near/far physical orientation changed')
 output=[]
 for v in OLD['views']:
  angle=v['yaw']
  if angle=='yaw045':confidence='P5_ANCHOR_SUPPORTED'
  elif angle=='yaw000':confidence='CONTINUITY_HEURISTIC_NOT_ANCHOR_VERIFIED'
  else:confidence='SINGLE_EYE_UNRESOLVED'
  rolepaths={r['role']:PRIVATE/r['path'] for r in v['roles']}
  corrected={role:read(path) for role,path in rolepaths.items()}
  # P15-15 labels left side far and right side near. Fix for 0/45.
  if angle in ('yaw000','yaw045'):
   for cat in ('eye','ear'):
    a,b=cat+'.near',cat+'.far'
    corrected[a],corrected[b]=corrected[b],corrected[a]
  outfolder=DEST/angle
  role_rows=[]
  for role,data in corrected.items():
   filename=outfolder/(role+'.png')
   write(filename,data)
   original=read(rolepaths[role])
   changed=not np.array_equal(data,original)
   role_rows.append({'role':role,'path':str(filename.relative_to(PRIVATE)),
       'sha256':sha(filename),'pixels':int(np.count_nonzero(data[:,:,3]>16)),
       'reassignedComparedToP15':changed,
       'roleIdentityStatus':('P5_ANCHOR_VERIFIED_SIDE' if confidence=='P5_ANCHOR_SUPPORTED' and
                            (role.startswith('eye.') or role.startswith('ear.')) else
                            'REVIEW_REQUIRED')})
  # P15-15 source identity can be conserved at near+far pixel level
  split_tests={}
  for cat in ('eye','ear'):
   na=corrected[cat+'.near'];fa=corrected[cat+'.far']
   originalna=read(rolepaths[cat+'.near']);originalfa=read(rolepaths[cat+'.far'])
   split_tests[cat]=bool(np.array_equal(np.maximum(na,fa),np.maximum(originalna,originalfa)))
  assert all(split_tests.values())
  output.append({'view':angle,'physicalSideConfidence':confidence,
    'nearEyeAnchorX768':round(nearx,2) if angle=='yaw045' else None,
    'farEyeAnchorX768':round(farx,2) if angle=='yaw045' else None,
    'nearEarAnchorX768':round(earx,2) if angle=='yaw045' else None,
    'conservesNearFarPixelSets':split_tests,
    'roles':role_rows,'acceptedNewPainting':0})
 report={'schema':'KOMA-P15-16-PHYSICAL-ROLE-REGISTRATION-V1',
  'characterId':'p0_character_001','sourceP15RoleRoutingSHA256':
  sha(ROOT/'evidence/p15-15-role-routing-qa.json'),
  'cameraSourceSHA256':sha(ROOT/'evidence/p15-12-camera-proxy-qa.json'),
  'physicalNearEyeLeftOfFarEyeAt45':True,
  'artisticAcceptance':False,'underpaintArtAcceptance':False,
  'approvedIndependentPaintedLayers':0,'views':output,
  'next':'Verify physical eye/ear side for front and 77.5, paint missing sidehair/ahoge and clip, test hidden underpaint'}
 REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':'PHYSICAL_IDENTITY_45_DETERMINISTIC',
    'views':len(output),'newRoleFiles':sum(len(v['roles']) for v in output),
    'pixelConservation':all(all(v['conservesNearFarPixelSets'].values()) for v in output),
    'uncertainViews':[v['view'] for v in output if v['physicalSideConfidence']!='P5_ANCHOR_SUPPORTED']},ensure_ascii=False))
if __name__=='__main__':main()
