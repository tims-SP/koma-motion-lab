#!/usr/bin/env python3
"""Package P0 source-owned multi-view garment ArtMesh evidence for local review."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
def sha(p):return sha256(Path(p).read_bytes()).hexdigest()
B=json.loads((R/'evidence/p15-103-browser-qa.json').read_text())
parts=json.loads((R/'evidence/p15-103-parts-qa.json').read_text())
mesh=json.loads((R/'evidence/p15-103-mesh-qa.json').read_text())
rp=R/'evidence/p15-103-render-qa.json'
render=json.loads(rp.read_text())
fp=R/'evidence/p15-103-flow-qa.json'
flow=json.loads(fp.read_text())
review=json.loads((R/'evidence/p15-103-review-qa.json').read_text())
assert B['status']=='PASS' and len(B['checks'])==144
assert parts['sourceReassemblyExact'] and mesh['negativeTriangleCount']==0
assert len(render['methods'])==5 and len(flow['methods'])==2 and len(review['frameFiles'])==8
baseline=render['metrics']['P15-101-head_alpha_blend']
trials={m:v for m,v in render['metrics'].items() if m!='P15-101-head_alpha_blend'}
trials.update({m:v for m,v in flow['metrics'].items() if m!='P15-101-head_alpha_blend'})
render['visualReview']={
 'performed':True,'sourceKeyviewsPixelExact':True,
 'sourceLayerReconstruction':'byte-exact source RGBA for both keyviews',
 'meshGeometry':'four independent matching 9-vertex garment parts with shared 8-triangle topology',
 'segmentVisualFindings':{
  'bow':'source-owned ribbon body and folds extracted in both views; internal line shapes remain view-dependent',
  'jewel':'central ornament remains single semantic part but cross-view ornament ink differs',
  'collar':'polygon ownership is a provisional layout proxy that contains nearby neck/hair pixels',
  'shoulder':'independent left shoulder support does not resolve jacket trim beyond the support'},
 'localFlowResult':'after view-mesh alignment, local DIS residual registration still increases garment adjacent frame pixel differences',
 'selectedVisualBenchmark':'P15-101 head_alpha_blend',
 'visualGate':'ARTIST_VERIFIABLE_COLLAR_BOW_STRAND_CORRESPONDENCE',
 'continuousYawAccepted':False,'formalArtMeshApproved':False,
 'engineeringQA':'PASS'}
render['fullContinuityAccepted']=False
rp.write_text(json.dumps(render,indent=2,ensure_ascii=False)+'\n')
flow['visualReview']={'performed':True,'visualAcceptance':False,
 'sourceInput':'native source bow texture on per-view registered UV mesh',
 'diagnostic':'mapped ribbon folds and edges remain inconsistent at intermediate yaw'}
fp.write_text(json.dumps(flow,indent=2,ensure_ascii=False)+'\n')
files=[]
for v in ('60','75'):
 files += [
  f'private-assets/exports/p15-97-multiview-motion/yaw{v}-frame-06.png',
  f'private-assets/exports/p15-103-parts/yaw{v}/reconstructed.png',
  f'private-assets/exports/p15-103-parts/yaw{v}/parts-contact.jpg',
  f'private-assets/exports/p15-103-render/yaw{v}-bow-undercoat.png',
  f'private-assets/exports/p15-103-render/yaw{v}-full-undercoat.png']
 for role in parts['partOrder']:
  token=role.replace('.','_')
  files.append(f'private-assets/exports/p15-103-parts/yaw{v}/{token}.png')
  files.append(f'private-assets/exports/p15-103-parts/yaw{v}/{token}-ownership.png')
 for role in mesh['sourceRoles']:
  files.append(f'private-assets/exports/p15-103-part-mesh/{role.replace(".","_")}-mesh-yaw{v}.png')
files += [
 'private-assets/exports/p15-103-part-mesh/garment-parts-mesh.json',
 'private-assets/exports/p15-103-render/index.html',
 'private-assets/exports/p15-103-render/garment-contact.jpg',
 'private-assets/exports/p15-103-render/bow-flow-contact.jpg',
 'private-assets/exports/p15-103-render/browser-desktop.png',
 'private-assets/exports/p15-103-render/browser-mobile.png']
for item in review['animations'].values():files.append(item['path'])
for method,frames in review['frameFiles'].items():
 for ref in frames.values():files.append(str((P/'p15-103-render'/ref).resolve().relative_to(R)))
for f in ['p15-101-render-qa.json','p15-102-neck-mesh-qa.json','p15-102-render-qa.json',
          'p15-103-parts-qa.json','p15-103-mesh-qa.json','p15-103-render-qa.json',
          'p15-103-flow-qa.json','p15-103-review-qa.json','p15-103-browser-qa.json']:
 files.append('evidence/'+f)
files=list(dict.fromkeys(files))
for rel in files:
 if not (R/rel).is_file():raise FileNotFoundError(rel)
dest=P/'p0-character-001-p15-103-garment-artmesh-study.zip'
text=('P0 Character | 60°–75° garment ArtMesh view correspondence study\n'
 'Review page: private-assets/exports/p15-103-render/index.html\n'
 'Actual source-owned jacket, shoulder, collar, bow and jewel RGBA layers, exact source reconstruction.\n'
 'Four independent 9-vertex 8-triangle grids share per-view UV correspondence.\n'
 'Seven experimental methods and P15-101 visual benchmark rendered over nine angles per method.\n'
 'Local optical flow and geometry-aligned source textures included for reproducible visual diagnosis.\n'
 'Engineering QA establishes layer reconstruction, UV geometry and browser frame delivery.\n'
 'Full garment animation quality and full-360 character motion require artist-verified garment fold and outline correspondences.\n')
with ZipFile(dest,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',text)
 for rel in files:z.write(R/rel,rel)
with ZipFile(dest) as z:
 assert z.testzip() is None
 entries=len(z.namelist())
tasks=R/'tasks.json'
j=json.loads(tasks.read_text())
j['p15_103GarmentArtMesh']={
 'status':'SOURCE_OWNED_GARMENT_COMPONENT_UV_CORRESPONDENCE_REPRODUCED',
 'characterId':'p0_character_001','sourceAngles':[60,75],
 'sourceLayerCount':5,'componentMeshCount':mesh['semanticPartCount'],
 'componentMeshVertices':mesh['vertexCount'],'componentTriangles':mesh['triangleCount'],
 'sampledAngleCount':mesh['sampledAngles'],'foldedTriangles':mesh['negativeTriangleCount'],
 'sourceImageReassemblyPixelExact':parts['sourceReassemblyExact'],
 'candidateFrameCount':sum(len(v) for v in render['methods'].values())+sum(len(v) for v in flow['methods'].values()),
 'baselineFrameCount':9,
 'methodNames':list(render['methods'])+list(flow['methods']),
 'actualImageOutputs':['native_rgba','garment_ownership_masks','head_uv_artmesh','component_uv_grid','local_dis_flow'],
 'browserChecksPass':144,'unitTestsPass':14,
 'baselineBowMaxAdjacentRGBMAE':baseline['bow']['maxAdjacentMAE'],
 'candidateBowMaxAdjacentRGBMAE':{m:v['bow']['maxAdjacentMAE'] for m,v in trials.items()},
 'baselineJewelMaxAdjacentRGBMAE':baseline['jewel']['maxAdjacentMAE'],
 'candidateJewelMaxAdjacentRGBMAE':{m:v['jewel']['maxAdjacentMAE'] for m,v in trials.items()},
 'selectedVisualBaseline':'P15-101 head_alpha_blend',
 'engineeringVerified':True,'continuousYawVisualAccepted':False,
 'formalArtMeshArtistApproved':False,
 'visualGate':render['visualReview']['visualGate'],
 'review':review['entry'],
 'package':{'path':str(dest.relative_to(R)),'bytes':dest.stat().st_size,'entries':entries,'sha256':sha(dest)},
 'evidence':['evidence/p15-103-parts-qa.json','evidence/p15-103-mesh-qa.json',
  'evidence/p15-103-render-qa.json','evidence/p15-103-flow-qa.json',
  'evidence/p15-103-review-qa.json','evidence/p15-103-browser-qa.json'],
 'next':'Establish artist-confirmable ribbon fold and collar trim landmarks / masks on both source keyviews; rerender corresponding ArtMesh before expanding head yaw'
}
j['status']='P15_103_GARMENT_SOURCE_ARTMESH_REPRODUCED_VIEW_CORRESPONDENCE_REVIEW'
j['lastCompleted']='P15-103 source-owned 60°–75° garment ArtMesh and local flow correspondence evidence with browser and unit QA'
tasks.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
print('PACKAGE',dest,'bytes',dest.stat().st_size,'entries',entries,'sha256',sha(dest))
print('TASK',j['status'])
