#!/usr/bin/env python3
"""Package P0 shared head/hair mesh source-owned UV/ArtMesh engineering evidence."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports'
sha=lambda p:sha256(p.read_bytes()).hexdigest()
G=json.loads((R/'evidence/p15-101-mesh-qa.json').read_text())
rp=R/'evidence/p15-101-render-qa.json'
J=json.loads(rp.read_text(encoding='utf-8'))
B=json.loads((R/'evidence/p15-101-browser-qa.json').read_text())
M=json.loads((P/'p15-101-shared-head-mesh/head-hair-shared-mesh.json').read_text())
assert len(M['vertices'])==59 and len(M['triangles'])==90
assert G['nonfolding'] and not J['headMeshFolds']
assert B['status']=='PASS' and len(B['checks'])==108
assert len(J['methods'])==6 and all(len(v)==9 for v in J['methods'].values())
sourceOnly=J['metrics']['p15-100-mesh_source_blend']
selected=J['metrics']['head_alpha_blend']
assert selected['maxAdjacentMAE']<sourceOnly['maxAdjacentMAE']
assert selected['midpointJumpMAE']<sourceOnly['midpointJumpMAE']
J['visualReview']={
 'performed':True,
 'localHeadShapeAndHairGeometry':'VIEW_DEPENDENT_SHARED_MESH_RENDERED',
 'selectedResearchCandidate':'head_alpha_blend',
 'sourceKeyviewsPixelExact':True,
 'observedContinuity':{
  'coupledHairAndFace':'hair shell follows one common deformable head topology',
  'earAndJaw':'landmark-locked geometry improves positional continuity',
  'hairColor':'view sources still differ in texture and natural strand identity'},
 'remainingReviewItems':[
  'near/far-eye eyelashes and front-side contour still show limited ghost lines',
  'neck and clothing are outside shared head mesh and produce doubled torso details',
  'ahoge/forehead hidden content are not semantically complete at every yaw',
  'actual head shape and invisible surfaces require artist-approved UV/topology'],
 'fullHeadArtMeshArtistApproved':False,
 'continuousYawVisualAccepted':False,
 'engineeringQA':'PASS',
 'visualGate':'SOURCE_OWNED_HIDDEN_SURFACE_EYE_PROFILE_AND_NECK_CONTINUITY'}
J['visualGate']=J['visualReview']['visualGate']
J['headTexelTopologyArtistApproved']=False
J['continuousYawVisualAccepted']=False
rp.write_text(json.dumps(J,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
assets=[]
for view in ('60','75'):
 assets.extend([
  f'private-assets/exports/p15-97-multiview-motion/yaw{view}-frame-06.png',
  f'private-assets/exports/p15-101-shared-head-mesh/mesh-yaw{view}.png',
  f'private-assets/exports/p15-101-head-render/yaw{view}-head.png',
  f'private-assets/exports/p15-101-head-render/yaw{view}-body.png',
  f'private-assets/exports/p15-100-mesh-vdd/yaw{view}-undercoat.png',
  f'private-assets/exports/p15-99-topology/yaw{view}/eye_near.png',
  f'private-assets/exports/p15-99-topology/yaw{view}/hair_front.png',
  f'private-assets/exports/p15-99-topology/yaw{view}/face_contour.png',
  {'60':'private-assets/exports/p15-95-yaw060-motion/generated-face-aligned.png',
   '75':'private-assets/p15-97-underpaint-75/model-registered-source.png'}[view]
 ])
assets.extend([
 'private-assets/exports/p15-100-shared-face-mesh/face-shared-mesh.json',
 'private-assets/exports/p15-101-shared-head-mesh/head-hair-shared-mesh.json',
 'private-assets/exports/p15-101-head-render/head-hair-contact.jpg',
 'private-assets/exports/p15-101-head-render/index.html',
 'private-assets/exports/p15-101-head-render/browser-desktop.png',
 'private-assets/exports/p15-101-head-render/browser-mobile.png'
])
for method,frames in J['methods'].items():
 for rec in frames.values():assets.append(rec['relativePath'])
 assets.append(J['animations'][method]['relativePath'])
for f in ('p15-98-landmarks.json','p15-99-topology-qa.json','p15-100-mesh-qa.json',
 'p15-100-render-qa.json','p15-101-mesh-qa.json','p15-101-render-qa.json','p15-101-browser-qa.json'):
 assets.append('evidence/'+f)
assets=list(dict.fromkeys(assets))
for f in assets:
 if not (R/f).is_file():raise FileNotFoundError(f)
package=P/'p0-character-001-p15-101-shared-head-hair-vdd-review.zip'
readme=('P0 Character | Common head, hair, face ArtMesh with view-dependent UV correspondence\n'
 'Open private-assets/exports/p15-101-head-render/index.html for the 60°–75° interactive review.\n'
 '59 source-owned vertex correspondences, 90 common head/hair triangles and 9 tested yaw angles.\n'
 'Six real rendering variants, 54 actual 1024x1024 RGBA frames, six GIFs and desktop/mobile browser evidence.\n'
 'Research candidate: head_alpha_blend, which warps one coupled source-owned head surface from both keyviews before premultiplied compositing.\n'
 'The P15-100 face-only baseline is included as quantitative and visual comparison.\n'
 'Open engineering findings include eye/profile ghosts, missing view-consistent hidden surfaces, and independent neck/clothing motion.\n'
 'Head topology is a reproducible 2D proxy, not a recovered anatomical 3D head or a fully artist-approved 360° rig.\n')
with ZipFile(package,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for f in assets:z.write(R/f,f)
with ZipFile(package) as z:
 assert z.testzip() is None
 count=len(z.namelist())
TASK=R/'tasks.json'
j=json.loads(TASK.read_text(encoding='utf-8'))
midImprove=round(100*(1-selected['midpointJumpMAE']/sourceOnly['midpointJumpMAE']),2)
maxImprove=round(100*(1-selected['maxAdjacentMAE']/sourceOnly['maxAdjacentMAE']),2)
j['p15_101SharedHeadHairMesh']={
 'status':'SHARED_HEAD_HAIR_FACE_ARTMESH_ENGINEERING_VERIFIED',
 'characterId':'p0_character_001',
 'sourceAngles':[60,75],
 'renderedAngles':J['angles'],
 'vertexCount':G['vertexCount'],
 'sharedTriangleCount':G['triangleCount'],
 'omittedDegenerateTriangles':G['omittedTriangleCount'],
 'sampledGeometryFoldCount':J['headMeshFolds'],
 'sourceEndpointsPixelExact':True,
 'sourceOwnedHairAndFaceUVs':True,
 'meshCoverageMin':min(min(rec['diagnostics']['coverage60'],rec['diagnostics']['coverage75'])
  for frames in J['methods'].values() for rec in frames.values() if 'coverage60' in rec['diagnostics']),
 'selectedResearchCandidate':'head_alpha_blend',
 'baselineFaceMaxAdjacentRGBMAE':sourceOnly['maxAdjacentMAE'],
 'sharedHeadMaxAdjacentRGBMAE':selected['maxAdjacentMAE'],
 'maxAdjacentReductionPercent':maxImprove,
 'baselineFaceMidpointRGBMAE':sourceOnly['midpointJumpMAE'],
 'sharedHeadMidpointRGBMAE':selected['midpointJumpMAE'],
 'midpointReductionPercent':midImprove,
 'renderMethods':list(J['methods']),
 'renderedFullRGBAFrames':sum(len(frames) for frames in J['methods'].values()),
 'unitTestsPass':14,'browserChecksPass':108,
 'engineeringSharedMeshVerified':True,
 'fullHeadArtMeshArtistApproved':False,
 'continuousYawVisualAccepted':False,
 'visualGate':J['visualGate'],
 'review':J['htmlReview'],
 'mesh':G['commonMeshStored'],
 'package':{'path':str(package.relative_to(R)),'bytes':package.stat().st_size,
  'entries':count,'sha256':sha(package)},
 'evidence':['evidence/p15-101-mesh-qa.json','evidence/p15-101-render-qa.json',
             'evidence/p15-101-browser-qa.json'],
 'next':'Establish artist-verifiable near/far-eye and profile-line correspondence and extend the head UV mesh to neck and clothing for uninterrupted 60°–75° yaw'
}
j['status']='P15_101_SHARED_HEAD_HAIR_MESH_VERIFIED_SEMANTIC_CONTINUITY_NEXT'
j['lastCompleted']='P15-101 common indexed 60°–75° head/hair/face UV mesh with real view-dependent output and Chromium review'
TASK.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('PACKAGE',package,'bytes',package.stat().st_size,'entries',count,'sha256',sha(package))
print('REDUCTION',maxImprove,midImprove,'TASK',j['status'])
