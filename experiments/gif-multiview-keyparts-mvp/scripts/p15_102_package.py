#!/usr/bin/env python3
"""Package source-owned neck, eye, profile and emblem correspondence research."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-102-neck-eye-profile'
sha=lambda p:sha256(p.read_bytes()).hexdigest()
m=json.loads((R/'evidence/p15-102-neck-mesh-qa.json').read_text())
face=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
renderFile=R/'evidence/p15-102-render-qa.json'
r=json.loads(renderFile.read_text())
goldFile=R/'evidence/p15-102-jewel-qa.json'
g=json.loads(goldFile.read_text())
revFile=R/'evidence/p15-102-review-qa.json'
v=json.loads(revFile.read_text())
br=json.loads((R/'evidence/p15-102-browser-qa.json').read_text())
assert m['nonfolding'] and len(m['sampleAngles'])==9
assert r['bodyMeshSHA256']==g['neckMeshSHA256']==m['meshSHA256']
assert br['status']=='PASS' and len(br['checks'])==144
assert len(v['methods'])==8 and all(len(items)==9 for items in v['methods'].values())
base=r['metrics']['p15-101-head_alpha_blend']
baselineGold=g['metrics']['P15-101-head_alpha_blend']
r['visualReview']={
 'performed':True,'selectedBaseline':'P15-101 head_alpha_blend',
 'neckMeshGeometry':'28 source-owned vertices, 36 triangles; 9 sampled yaw angles with positive areas',
 'sourceEye':'actual P15-99 SAM3 mask and source pixels with reconstructed underdraw',
 'sourceGoldEmblem':'native gold color connected components and measured per-view centers',
 'baseline':{'collarMaxAdjacentRGBMAE':base['neck_collar']['maxAdjacentRGBMAE'],
   'eyeMaxAdjacentRGBMAE':base['eye']['maxAdjacentRGBMAE'],
   'emblemMaxAdjacentRGBMAE':baselineGold['jewel']['maxAdjacentRGBMAE']},
 'candidateMetrics':{
  'neckMeshCollarMaxAdjacentRGBMAE':r['metrics']['neck_mesh']['neck_collar']['maxAdjacentRGBMAE'],
  'eyeDissolveMaxAdjacentRGBMAE':r['metrics']['neck_eye_dissolve']['eye']['maxAdjacentRGBMAE'],
  'emblemStaticOwnerMaxAdjacentRGBMAE':g['metrics']['gold_owner_static']['jewel']['maxAdjacentRGBMAE']},
 'visualFindings':{
  'neckAndCollar':'warp alone does not align unique collar and shoulder ink textures across views',
  'nearEye':'eye ownership removes some local double-iris ambiguity but source masks/underpaint remain incomplete',
  'noseAndJaw':'single source nose contour introduces a view-switch difference',
  'jewel':'centers measured from source; source-owner switch introduces a sharp emblem appearance change'},
 'visualAccepted':False,'engineeringReproducibility':'PASS',
 'nextCriticalAction':'semantic collar and bow layers with shared correspondences and explicit viewpoint-consistent occlusion'}
r['fullVisualAccepted']=False
r['visualGate']='COLLAR_BOW_TOPOLOGY_AND_EYE_PROFILE_HIDDEN_SURFACE_CORRESPONDENCE'
renderFile.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
g['visualReview']={'actualSourceEmblemDetected':True,
   'independentEmblemLayerExtracted':True,
   'selectedBaseline':'P15-101 head_alpha_blend',
   'visualAcceptance':False}
goldFile.write_text(json.dumps(g,indent=2,ensure_ascii=False)+'\n')
files=[]
for view in ('60','75'):
 files.extend([
  f'private-assets/exports/p15-97-multiview-motion/yaw{view}-frame-06.png',
  f'private-assets/exports/p15-101-shared-head-mesh/mesh-yaw{view}.png',
  f'private-assets/exports/p15-102-neck-shoulder-mesh/mesh-yaw{view}.png',
  f'private-assets/exports/p15-102-neck-eye-profile/yaw{view}-eye-clean-undercoat.png',
  f'private-assets/exports/p15-102-neck-eye-profile/yaw{view}-eye-profile-undercoat.png',
  f'private-assets/exports/p15-102-neck-eye-profile/yaw{view}-profile-line.png',
  f'private-assets/exports/p15-102-neck-eye-profile/yaw{view}-emblem.png',
  f'private-assets/exports/p15-102-neck-eye-profile/yaw{view}-clean-torso.png',
  f'private-assets/exports/p15-99-topology/yaw{view}/eye_near.png',
  f'private-assets/exports/p15-99-topology/yaw{view}/face_contour.png',
  f'private-assets/exports/p15-101-head-render/yaw{view}-body.png'
 ])
files += [
 'private-assets/exports/p15-101-shared-head-mesh/head-hair-shared-mesh.json',
 'private-assets/exports/p15-102-neck-shoulder-mesh/neck-shoulder-mesh.json',
 'private-assets/exports/p15-102-neck-eye-profile/index.html',
 'private-assets/exports/p15-102-neck-eye-profile/neck-eye-profile-contact.jpg',
 'private-assets/exports/p15-102-neck-eye-profile/jewel-ownership-contact.jpg',
 'private-assets/exports/p15-102-neck-eye-profile/browser-desktop.png',
 'private-assets/exports/p15-102-neck-eye-profile/browser-mobile.png'
]
for info in v['animations'].values():files.append(info['path'])
for method,frames in face['methods'].items():
 if method=='head_alpha_blend':
  for record in frames.values():files.append(record['relativePath'])
for collection in (r['methods'],g['methods']):
 for frames in collection.values():
  for record in frames.values():files.append(record['relativePath'])
for f in ['p15-99-eye-mask-qa.json','p15-99-topology-qa.json','p15-101-mesh-qa.json',
          'p15-101-render-qa.json','p15-102-neck-mesh-qa.json','p15-102-render-qa.json',
          'p15-102-jewel-qa.json','p15-102-review-qa.json','p15-102-browser-qa.json']:
 files.append('evidence/'+f)
files=list(dict.fromkeys(files))
for f in files:
 if not (R/f).is_file():raise FileNotFoundError(f)
dest=P/'p0-character-001-p15-102-neck-eye-correspondence-review.zip'
readme=('P0 Character · 60°–75° neck, near-eye, nose contour and gold emblem correspondence\n'
 'Review entry: private-assets/exports/p15-102-neck-eye-profile/index.html\n'
 'The neck/collar UV mesh is 28 vertices / 36 indexed triangles; the shared head/hair mesh is retained from P15-101.\n'
 'Comparison includes source-owned iris and profile layers, source gold jewellery detection, and source-view garment anchor warps.\n'
 'Eight review methods, nine yaw angles each, source original keyframes, RGB region metrics and actual Chromium checks.\n'
 'The established P15-101 head_alpha_blend is preserved as the source visual benchmark.\n'
 'The result is a traceable 2D correspondence experiment. Full body/face artistic continuity requires further component-specific matching.\n')
with ZipFile(dest,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for f in files:z.write(R/f,f)
with ZipFile(dest) as z:
 assert z.testzip() is None
 nfiles=len(z.namelist())
task=R/'tasks.json'
j=json.loads(task.read_text(encoding='utf-8'))
j['p15_102NeckEyeProfileCorrespondence']={
 'status':'SOURCE_NECK_EYE_EMBLEM_CORRESPONDENCE_EVIDENCE_VERIFIED',
 'characterId':'p0_character_001','sourceAngles':[60,75],
 'anglesRendered':r['angles'],'headMeshSHA256':r['headMeshSHA256'],
 'neckMeshSHA256':m['meshSHA256'],'neckMeshVertices':m['vertices'],
 'neckMeshTriangles':m['triangles'],'neckMeshSampledFoldCount':sum(x['foldCount'] for x in m['sampleAngles']),
 'eyeSource':'P15-99 actual SAM3 native eye layer',
 'goldEmblemNativeCenters':{view:rec['centerMeasured'] for view,rec in g['sourceRealEmblemLandmarks'].items()},
 'visualComparisonMethodCount':len(v['methods']),
 'fullResolutionCandidateFrames':sum(len(frames) for frames in v['methods'].values()),
 'unitTestsPass':14,'browserChecksPass':144,
 'sourceEndpointPixelExact':True,
 'geometryAndAssetReproducibilityVerified':True,
 'currentVisualBaseline':'P15-101 head_alpha_blend',
 'continuousYawVisualAccepted':False,
 'formalHeadShoulderArtMeshApproved':False,
 'visualGate':r['visualGate'],
 'review':v['entry'],
 'package':{'path':str(dest.relative_to(R)),'bytes':dest.stat().st_size,
            'sha256':sha(dest),'entries':nfiles},
 'evidence':['evidence/p15-102-neck-mesh-qa.json','evidence/p15-102-render-qa.json',
             'evidence/p15-102-jewel-qa.json','evidence/p15-102-review-qa.json',
             'evidence/p15-102-browser-qa.json'],
 'next':'Establish source-owned collar, bow, jacket and neck silhouette ArtMesh correspondences before rerendering full character yaw'
}
j['status']='P15_102_NECK_EYE_CORRESPONDENCE_EVIDENCE_READY_ART_REVIEW_PENDING'
j['lastCompleted']='P15-102 source-owned neck mesh, native near-eye/profile and gold bow landmark registration with Chromium visual QA'
task.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
print('PACKAGE',dest,'bytes',dest.stat().st_size,'entries',nfiles,'sha256',sha(dest))
print('TASK',j['status'])
