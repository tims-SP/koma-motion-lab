#!/usr/bin/env python3
"""Package P0 source-owned common ArtMesh, view UVs and verified visual review."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
M=json.loads((P/'p15-100-shared-face-mesh/face-shared-mesh.json').read_text())
G=json.loads((R/'evidence/p15-100-mesh-qa.json').read_text())
RPATH=R/'evidence/p15-100-render-qa.json'
J=json.loads(RPATH.read_text())
B=json.loads((R/'evidence/p15-100-browser-qa.json').read_text())
assert G['meshTrianglesNonFolded'] and G['vertexCount']==22 and G['triangleCount']==28
assert B['status']=='PASS' and len(B['checks'])==72
assert len(J['methods'])==4 and all(len(v)==9 for v in J['methods'].values())
assert J['geometryFoldCount']==0
J['visualReview']={
 'performed':True,
 'structuralMeshIntegrity':'PASS',
 'keyframesSourcePixelExact':True,
 'continuousFaceGeometry':'POSITIVE_TRIANGLE_AREAS_ON_9_SAMPLED_YAWS',
 'quantitativeTemporalResult':{
  'baselineMidpointJumpRGBMAE':J['metrics']['p15-99-topology_staged']['midpointJumpMAE'],
  'meshSourceBlendMidpointJumpRGBMAE':J['metrics']['mesh_source_blend']['midpointJumpMAE'],
  'baselineMaxAdjacentRGBMAE':J['metrics']['p15-99-topology_staged']['maxAdjacentMAE'],
  'meshSourceBlendMaxAdjacentRGBMAE':J['metrics']['mesh_source_blend']['maxAdjacentMAE']
 },
 'observedArtifacts':{
  'faceSurfaceBoundary':'visible blend seam around cheek and forehead',
  'hairOcclusion':'rear hair and fringe transitions do not share face mesh support',
  'profile':'ghost contour next to nose and jaw in intermediate views',
  'textureSurface':'model-derived underpaint cannot recover unobserved anatomy'
 },
 'engineeringQA':'PASS','visualQA':'REQUIRES_SHARED_HEAD_HAIR_SURFACE',
 'fullArtMeshAccepted':False,'continuousYawAccepted':False}
J['continuousYawVisualAccepted']=False
J['visualGate']='SHARED_HEAD_HAIR_MESH_AND_VISIBILITY_CORRESPONDENCE'
RPATH.write_text(json.dumps(J,indent=2,ensure_ascii=False)+'\n')
assets=[]
for view in ('60','75'):
 assets.extend([
  f'private-assets/exports/p15-97-multiview-motion/yaw{view}-frame-06.png',
  f'private-assets/exports/p15-100-shared-face-mesh/mesh-yaw{view}.png',
  f'private-assets/exports/p15-100-mesh-vdd/yaw{view}-source.png',
  f'private-assets/exports/p15-100-mesh-vdd/yaw{view}-undercoat.png',
  f'private-assets/exports/p15-99-topology/yaw{view}/reconstructed.png',
 ])
 for role in ['other.rear','face.skin','face.contour','eye.far','eye.near','hair.front','hair.clip']:
  name=role.replace('.','_')
  assets.append(f'private-assets/exports/p15-99-topology/yaw{view}/{name}.png')
 assets.append({'60':'private-assets/exports/p15-95-yaw060-motion/generated-face-aligned.png',
                '75':'private-assets/p15-97-underpaint-75/model-registered-source.png'}[view])
assets.extend([
 'private-assets/exports/p15-100-shared-face-mesh/face-shared-mesh.json',
 'private-assets/exports/p15-100-mesh-vdd/mesh-vdd-contact.jpg',
 'private-assets/exports/p15-100-mesh-vdd/index.html',
 'private-assets/exports/p15-100-mesh-vdd/browser-desktop.png',
 'private-assets/exports/p15-100-mesh-vdd/browser-mobile.png'])
for mode,frameData in J['methods'].items():
 for item in frameData.values():assets.append(item['path'])
 assets.append(J['animations'][mode]['relativePath'])
for fn in ('p15-98-landmarks.json','p15-99-topology-qa.json','p15-99-topology-vdd-qa.json',
           'p15-100-mesh-qa.json','p15-100-render-qa.json','p15-100-browser-qa.json'):
 assets.append('evidence/'+fn)
assets=list(dict.fromkeys(assets))
for a in assets:
 if not (R/a).is_file():raise FileNotFoundError(a)
package=P/'p0-character-001-p15-100-shared-face-mesh-review.zip'
readme=('P0 Character — Common Face ArtMesh and View-Dependent UV correspondence\n'
 'Open private-assets/exports/p15-100-mesh-vdd/index.html for interactive review.\n'
 '22 common indexed surface vertices, 28 stable triangles, 2 endpoint view UVs, source-owned face and hair/eye layers.\n'
 'Face geometry samples nine yaw angles 60°–75°; both endpoint frames preserve original registered RGBA exactly.\n'
 'Four actual mesh-rendered variants, 36 full-resolution frames, four GIFs, Chromium screenshots and structured evidence included.\n'
 'Geometry is an explicitly bounded 2D correspondence proxy, not a recovered anatomical 3D face; visual head/hair continuity requires independent approval.\n')
with ZipFile(package,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for a in assets:z.write(R/a,a)
with ZipFile(package) as z:
 assert z.testzip() is None
 count=len(z.namelist())
TASK=R/'tasks.json'
j=json.loads(TASK.read_text(encoding='utf-8'))
j['p15_100SharedFaceMesh']={
 'status':'SOURCE_OWNED_SHARED_FACE_MESH_AND_VIEW_UV_GEOMETRY_VERIFIED',
 'characterId':'p0_character_001',
 'sourceAngles':[60,75],
 'renderedAngles':J['interpolatedAngles'],
 'vertexCount':G['vertexCount'],'validTriangles':G['triangleCount'],
 'explicitlyExcludedThinTriangles':G['excludedTriangleCount'],
 'sampledFaceMeshFoldedTriangles':J['geometryFoldCount'],
 'faceCoverageFractionMin':min(rec['geometry']['maskCoverage'] for info in J['methods'].values()
         for rec in info.values() if not rec['geometry'].get('endpoint')),
 'sourceEndpointPixelsExact':True,
 'viewDependentUVStored':True,'sourceOwnedEyeHairInput':True,
 'faceMaterialGeometry':'regularized 2D Delaunay piecewise-affine shared triangle map',
 'renderedCandidateCount':sum(len(frames) for frames in J['methods'].values()),
 'methodNames':list(J['methods']),
 'faceMaxAdjacentRGBMAE':{m:r['maxAdjacentMAE'] for m,r in J['metrics'].items()},
 'midpointAdjacentRGBMAE':{m:r['midpointJumpMAE'] for m,r in J['metrics'].items()},
 'unitTestsPass':13,'browserChecksPass':72,
 'localFaceGeometryAccepted':True,
 'fullHeadArtMeshAccepted':False,'continuousYawVisualAccepted':False,
 'visualGate':J['visualGate'],
 'next':'Align source-owned rear hair, fringe, profile contour and occluded face surfaces to the same shared head mesh, validating inter-layer texture seams in 60°–75° yaw',
 'review':J['htmlReview'],'mesh':G['meshJSON'],
 'package':{'path':str(package.relative_to(R)),'sha256':sha(package),'bytes':package.stat().st_size,
  'entries':count},
 'evidence':['evidence/p15-100-mesh-qa.json','evidence/p15-100-render-qa.json',
             'evidence/p15-100-browser-qa.json']}
j['status']='P15_100_SHARED_FACE_MESH_VERIFIED_HEAD_HAIR_CORRESPONDENCE_PENDING'
j['lastCompleted']='P15-100 shared 2D face mesh correspondence with persistent view UVs and four real VDD render comparisons'
TASK.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('PACKAGE',package,'bytes',package.stat().st_size,'entries',count,'sha256',sha(package))
print('TASK',j['status'])
