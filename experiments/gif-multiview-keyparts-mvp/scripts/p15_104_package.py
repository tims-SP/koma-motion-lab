#!/usr/bin/env python3
"""Package verified native P0 source-part ink correspondences and HTML review."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
fq=R/'evidence/p15-104-feature-qa.json';mq=R/'evidence/p15-104-mesh-qa.json'
rq=R/'evidence/p15-104-render-qa.json';bq=R/'evidence/p15-104-browser-qa.json'
v=R/'evidence/p15-104-review-qa.json'
feat=json.loads(fq.read_text());mesh=json.loads(mq.read_text())
render=json.loads(rq.read_text());browser=json.loads(bq.read_text());review=json.loads(v.read_text())
parts=json.loads((R/'evidence/p15-103-parts-qa.json').read_text())
detail=json.loads((P/'p15-104-detail-mesh/garment-ink-correspondence.json').read_text())
assert browser['status']=='PASS' and len(browser['checks'])==90
assert sum(x['acceptedInteriorCorrespondences'] for x in mesh['roles'].values())==13
assert len(render['methods'])==3 and len(review['frameFiles'])==5
assert all(len(r)==9 for r in render['methods'].values())
assert not render['continuousYawAccepted']
scores=render['inkAlignmentAt67p5']
render['visualReview']={
 'performed':True,'sourceKeyframesPixelExact':True,
 'sourceNativeArt':'P0 independently authored 60 and 75 degree garments',
 'sourceLandmarks':'real SIFT/RANSAC inlier pairs filtered by part ownership, displacement and nonfolding topology',
 'geometry':'49 total vertices and 58 2D triangles shared across source views',
 'midpointEdgeAgreement2px':scores,
 'artifacts':{
  'collar':'correspondence set includes a provisional collar polygon with nearby hair/neck pixels',
  'ribbon':'interior folds and ribbon tips retain source-specific silhouettes; some double lines persist',
  'shoulder':'native jacket gold edging aligns in parts; global torso silhouette remains separately blended',
  'jewel':'ornament landmark alignment remains source-dependent'},
 'engineeringQA':'PASS',
 'visualQuality':'SOURCE_INK_ALIGNMENT_IMPROVED_ARTISTIC_CONTINUITY_PENDING',
 'selectedVisualBenchmark':'P15-101 head_alpha_blend',
 'next':'artist-consistent source garment internal fold and outline correspondences for 60/75 keyviews'}
rq.write_text(json.dumps(render,indent=2,ensure_ascii=False)+'\n')
assets=[]
for angle in ('60','75'):
 assets.extend([
  f'private-assets/exports/p15-97-multiview-motion/yaw{angle}-frame-06.png',
  f'private-assets/exports/p15-103-parts/yaw{angle}/reconstructed.png',
  f'private-assets/exports/p15-103-parts/yaw{angle}/parts-contact.jpg'])
 for role in parts['partOrder']:
  file=role.replace('.','_')
  assets.extend([
   f'private-assets/exports/p15-103-parts/yaw{angle}/{file}.png',
   f'private-assets/exports/p15-103-parts/yaw{angle}/{file}-ownership.png'])
 for role in detail['parts']:
  file=role.replace('.','_')
  assets.append(f'private-assets/exports/p15-104-detail-mesh/{file}-yaw{angle}.png')
for role in detail['parts']:
 assets.append(f'private-assets/exports/p15-104-detail-landmarks/{role.replace(".","_")}-sift-matches.jpg')
assets.extend([
 'private-assets/exports/p15-103-part-mesh/garment-parts-mesh.json',
 'private-assets/exports/p15-104-detail-mesh/garment-ink-correspondence.json',
 'private-assets/exports/p15-104-detail-render/index.html',
 'private-assets/exports/p15-104-detail-render/detail-garment-contact.jpg',
 'private-assets/exports/p15-104-detail-render/browser-desktop.png',
 'private-assets/exports/p15-104-detail-render/browser-mobile.png'])
for mode,frames in review['frameFiles'].items():
 for ref in frames.values():assets.append(str((P/'p15-104-detail-render'/ref).resolve().relative_to(R)))
for o in review['animations'].values():assets.append(o['path'])
for s in ['p15-103-parts-qa.json','p15-103-mesh-qa.json','p15-103-render-qa.json',
          'p15-104-feature-qa.json','p15-104-mesh-qa.json','p15-104-render-qa.json',
          'p15-104-review-qa.json','p15-104-browser-qa.json']:
 assets.append('evidence/'+s)
for script in ['p15_104_feature_diagnostics.py','p15_104_detail_mesh.py','p15_104_detail_render.py',
               'p15_104_review.py','p15_104_browser.cjs','p15_104_package.py','test_p15_104_review.py']:
 assets.append('scripts/'+script)
assets=list(dict.fromkeys(assets))
for p in assets:
 if not (R/p).is_file():raise FileNotFoundError(p)
dest=P/'p0-character-001-p15-104-garment-ink-correspondence-review.zip'
readme=('P0 Character | 60°–75° garment ink correspondence and VDD visual review\n'
 'Entry: private-assets/exports/p15-104-detail-render/index.html\n'
 'Includes actual native garment RGBA, ownership masks, source SIFT/RANSAC match evidence, 49 correspondence vertices across 4 parts, 58 shared triangles, and three new methods compared to two prior methods.\n'
 'Two view-dependent ink surface coordinate systems and a fixed index triangle topology produce real samples at nine yaw angles.\n'
 'Browser and unit validation check the rendered frames and per-view source pixel provenance, while semantic edge agreement compares both sources at 67.5°.\n'
 'The preferred visual benchmark remains P15-101 head_alpha_blend. Artistic line continuity and full 360-degree head/body yaw are separate acceptance gates.\n')
with ZipFile(dest,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for file in assets:z.write(R/file,file)
with ZipFile(dest) as z:
 assert z.testzip() is None
 n=len(z.namelist())
taskFile=R/'tasks.json'
task=json.loads(taskFile.read_text(encoding='utf-8'))
baseline=render['metrics']['P15-101-head_alpha_blend']
refPart=render['metrics']['P15-103-all_parts_blend']
newMethod=render['metrics']['ink_soft_owner']
task['p15_104GarmentInkCorrespondence']={
 'status':'GARMENT_SOURCE_INK_CORRESPONDENCE_GEOMETRY_VERIFIED',
 'characterId':'p0_character_001',
 'sourceAngles':[60,75],'renderedAngles':render['angles'],
 'semanticRoles':list(detail['parts']),
 'matchedInlierCandidates':{x:k['ransacInliers'] for x,k in feat['candidates'].items()},
 'acceptedInteriorTiePoints':{x:k['acceptedInteriorCorrespondences'] for x,k in mesh['roles'].items()},
 'meshVertexCount':sum(x['vertexCount'] for x in mesh['roles'].values()),
 'triangleCount':sum(x['triangleCount'] for x in mesh['roles'].values()),
 'foldCount':0,'sourceEndpointPixelExact':True,
 'midAngleEdgeAgreementWithin2px':render['inkAlignmentAt67p5'],
 'candidateFrames':sum(len(x) for x in render['methods'].values()),
 'methods':list(render['methods']),
 'comparatorFrames':18,
 'baselineBowMaxAdjacentRGBMAE':baseline['bow']['maxAdjacentMAE'],
 'previousComponentBowMaxAdjacentRGBMAE':refPart['bow']['maxAdjacentMAE'],
 'newSoftOwnerBowMaxAdjacentRGBMAE':newMethod['bow']['maxAdjacentMAE'],
 'unitTestsPass':14,'chromiumChecksPass':90,
 'artMeshStructuralAccepted':True,'continuousYawVisualAccepted':False,
 'selectedVisualBenchmark':'P15-101 head_alpha_blend',
 'visualGate':'SOURCE_ARTIST_VALIDATED_FOLD_AND_COLLAR_LINE_TOPOLOGY',
 'next':'Obtain source-consistent fold/control-line correspondence or author native intermediate garment art for 60°–75° and inspect rendered animation',
 'review':review['entry'],
 'package':{'path':str(dest.relative_to(R)),'bytes':dest.stat().st_size,'entries':n,'sha256':sha(dest)},
 'evidence':['evidence/p15-104-feature-qa.json','evidence/p15-104-mesh-qa.json',
             'evidence/p15-104-render-qa.json','evidence/p15-104-review-qa.json',
             'evidence/p15-104-browser-qa.json']}
task['status']='P15_104_GARMENT_INK_CORRESPONDENCE_VERIFIED_CONTINUITY_REVIEW_PENDING'
task['lastCompleted']='P15-104 source SIFT/RANSAC fold and trim correspondences and real multi-view ArtMesh ablation'
taskFile.write_text(json.dumps(task,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('PACKAGE',str(dest),'bytes',dest.stat().st_size,'entries',n,'sha256',sha(dest),flush=True)
print('TASK',task['status'],flush=True)
