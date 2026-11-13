#!/usr/bin/env python3
"""Bundle P0 three-source garment ArtMesh, rendered comparison and quality evidence."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
mp=R/'evidence/p15-106-mesh-qa.json'
rp=R/'evidence/p15-106-render-qa.json'
vp=R/'evidence/p15-106-review-qa.json'
bp=R/'evidence/p15-106-browser-qa.json'
mq=json.loads(mp.read_text());render=json.loads(rp.read_text());review=json.loads(vp.read_text());browser=json.loads(bp.read_text())
native=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
old=json.loads((R/'evidence/p15-105-render-qa.json').read_text())
assert browser['status']=='PASS' and len(browser['checks'])==90
assert all(len(p['sampledGeometry'])==18 for p in mq['parts'].values())
assert len(render['methods'])==3 and len(review['frameFiles'])==5
assert render['nativeMiddleRgbaExactFraction']==1.0
assert sum(x['vertices'] for x in mq['parts'].values())==132
assert sum(x['triangles'] for x in mq['parts'].values())==192
values=render['metrics']
baseline=values['P15-101-head_alpha_blend']
direct=values['P15-105-three_key_direct']
soft=values['bow_radial_soft_visibility']
render['visualReview']={
 'performed':True,'geometryStatus':'COMMON_TRIANGULATION_NONFOLDED',
 'maskReconstruction':'source owned 3 keyframes / all garment part pixels have one owner',
 'artifactAssessment':{
   'bow':'radial geometry follows native bow edges but source folds still create doubled interior line contours',
   'collar':'registered native keyframe profile differs from both original view collars; blend seam remains visible',
   'jewel':'radial anchor is stable but surface details vary across views',
   'shoulder':'full component radial matte creates extra duplicated shoulder trim detail',
   'head':'P15-101 face/hair mesh retained with its previous face and fringe limitations'},
 'inpaintRasterBoundary':'full source garment assembled at original 1024 before a single resizing pass',
 'qualitativeBestVisualBenchmark':'P15-101 head_alpha_blend',
 'continuousVisualAccepted':False,
 'numericComparison':{name:{
  'baseline':baseline[name]['maxAdjacentRGBMAE'],
  'prior3Key':direct[name]['maxAdjacentRGBMAE'],
  'radialSoftVisibility':soft[name]['maxAdjacentRGBMAE']}
 for name in ('bow','jewel','collar')},
 'nextCriticalEvidence':'matching ribbon-tail contour, fold/trim line topology and neck occlusion across all native keyviews'}
render['continuousYawVisualAccepted']=False
rp.write_text(json.dumps(render,indent=2,ensure_ascii=False)+'\n')
assets=[
 'private-assets/p15-105-yaw0675/yaw0675-garment-native.png',
 'private-assets/p15-105-yaw0675/generation-result.json',
 'private-assets/exports/p15-105-middle-art/yaw067p5-garment-registered.png',
 'private-assets/exports/p15-105-middle-art/native-garment-contact.jpg',
 'private-assets/exports/p15-106-three-key-mesh/garment-three-key-mesh.json',
 'private-assets/exports/p15-106-three-key-render/three-view-artmesh-contact.jpg',
 'private-assets/exports/p15-106-three-key-render/index.html',
 'private-assets/exports/p15-106-three-key-render/browser-desktop.png',
 'private-assets/exports/p15-106-three-key-render/browser-mobile.png'
]
for v in ('60','67p5','75'):
 folder='private-assets/exports/p15-106-three-key-mesh/yaw'+v
 assets.append(folder+'/remainder.png')
 for role in ('shoulder_left','collar','bow','jewel'):
  assets.append(folder+'/'+role+'.png')
  assets.append(folder+'/'+role+'-ownership.png')
  assets.append('private-assets/exports/p15-106-three-key-mesh/'+role+'-yaw'+v+'.png')
 for mode in ('bow','all'):
  assets.append('private-assets/exports/p15-106-three-key-render/source-'+v+'-'+mode+'-undercoat.png')
for method,frames in review['frameFiles'].items():
 for ref in frames.values():assets.append(str((P/'p15-106-three-key-render'/ref).resolve().relative_to(R)))
for item in review['animations'].values():assets.append(item['path'])
for f in ('p15-101-render-qa.json','p15-105-native-art-qa.json','p15-105-render-qa.json',
          'p15-106-mesh-qa.json','p15-106-render-qa.json','p15-106-review-qa.json','p15-106-browser-qa.json'):
 assets.append('evidence/'+f)
for f in ('p15_106_three_key_mesh.py','p15_106_three_key_render.py','p15_106_review.py',
          'p15_106_browser.cjs','p15_106_package.py','test_p15_106_review.py'):
 assets.append('scripts/'+f)
assets=list(dict.fromkeys(assets))
for name in assets:
 if not (R/name).is_file():raise FileNotFoundError(name)
dest=P/'p0-character-001-p15-106-three-key-garment-artmesh.zip'
readme=('P0 Character | Shared three-source garment ArtMesh and visual evidence\n'
 'Review page: private-assets/exports/p15-106-three-key-render/index.html\n'
 'Source angles 60°, 67.5°, 75°, including unchanged native Codex imagegen keyart and registered 1024 variant.\n'
 'Four independent semantic component layers, 132 vertices, 192 stable triangles, per-source view UVs and source-owned 2D textures.\n'
 'Three source-aware radial ArtMesh strategies were rendered across nine yaw samples; two prior methods retained for visual comparison.\n'
 'Original source endpoint images and the actual 67.5° garment keyframe maintain their recorded pixel provenance.\n'
 'Detailed model meshes, masks, GIFs, Chromium screenshots and evidence are included.\n'
 'Three-view geometric continuity and browser delivery are validated. Natural ribbon-fold/collar/shoulder continuity requires artist-approved semantic correspondence.\n')
with ZipFile(dest,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for asset in assets:z.write(R/asset,asset)
with ZipFile(dest) as z:
 assert z.testzip() is None
 files=len(z.namelist())
task=R/'tasks.json';data=json.loads(task.read_text(encoding='utf-8'))
data['p15_106ThreeKeyGarmentArtMesh']={
 'status':'THREE_KEY_GARMENT_SOURCE_ARTMESH_GEOMETRY_VERIFIED',
 'characterId':'p0_character_001',
 'sourceAngles':[60,67.5,75],'sampledAngles':render['renderAngles'],
 'sourceNativeMidpointSHA256':native['nativeSHA256'],'sourceRegisteredMidpointSHA256':native['registeredSHA256'],
 'semanticParts':list(mq['parts']),
 'meshVertexCount':sum(x['vertices'] for x in mq['parts'].values()),
 'meshTriangleCount':sum(x['triangles'] for x in mq['parts'].values()),
 'noFoldSampleCount':sum(len(x['sampledGeometry']) for x in mq['parts'].values()),
 'sourceOwnershipPixelExact':mq['sourcePixelReconstruction'],
 'midpointRegisteredGarmentPixelExact':render['nativeMiddleRgbaExactFraction']==1,
 'renderedCandidateFrames':sum(len(x) for x in render['methods'].values()),
 'priorComparisonFrames':18,
 'renderStrategies':list(render['methods']),
 'maxAdjacentBowRGBMAE':{k:v['bow']['maxAdjacentRGBMAE'] for k,v in values.items()},
 'unitTestsPass':17,'browserChecksPass':90,'geometryAccepted':True,
 'visualAcceptance':False,
 'selectedVisualBenchmark':'P15-101 head_alpha_blend',
 'next':'Use source-owned ribbon fold, collar gold trim and shoulder silhouette correspondences with valid hidden surfaces to reduce garment contour overlap across 60–67.5–75°',
 'visualGate':'ARTIST_VALIDATED_COLLAR_BOW_SHOULDER_HIDDEN_SURFACE_CORRESPONDENCES',
 'review':review['entry'],
 'package':{'path':str(dest.relative_to(R)),'bytes':dest.stat().st_size,
   'sha256':sha(dest),'entries':files},
 'evidence':['evidence/p15-106-mesh-qa.json','evidence/p15-106-render-qa.json',
             'evidence/p15-106-review-qa.json','evidence/p15-106-browser-qa.json']
}
data['status']='P15_106_SOURCE_ARTMESH_GEOMETRY_VERIFIED_GARMENT_VISUAL_REVIEW_PENDING'
data['lastCompleted']='P15-106 shared three-key source-garment ArtMesh with nonfolding topology and VDD comparison'
task.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('PACKAGE',dest,'bytes',dest.stat().st_size,'entries',files,'sha256',sha(dest),flush=True)
print('TASK',data['status'],flush=True)
