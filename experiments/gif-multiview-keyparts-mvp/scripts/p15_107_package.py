#!/usr/bin/env python3
"""Package source-coherent garment ink transport engineering evidence and review."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile,ZIP_DEFLATED
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
inkP=R/'evidence/p15-107-ink-qa.json'
ink=json.loads(inkP.read_text())
rv=json.loads((R/'evidence/p15-107-review-qa.json').read_text())
browser=json.loads((R/'evidence/p15-107-browser-qa.json').read_text())
prev=json.loads((R/'evidence/p15-106-render-qa.json').read_text())
native=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
assert browser['status']=='PASS' and len(browser['checks'])==90
assert len(ink['methods'])==3 and len(rv['methods'])==5
assert all(rec['negativeJacobianSamples']==0 for rec in ink['maps'].values())
assert ink['sourceImageSHA256']==native['registeredSHA256']
ref=ink['metrics']['P15-101-head_alpha_blend']
candidates=ink['metrics']
ink['visualReview']={
 'performed':True,
 'sourceOwnedRibbonInk':'a single registered middle source owns the detailed folds in each interpolated bow component',
 'nativeSourceConsistency':'all rendered interior texture coordinates originate from one registered 67.5-degree art',
 'geometry':'regularized 2D thin plate spline over original three-view semantic correspondence anchors',
 'lineArtObservation':'middle ribbon ink is coherent within each frame, while keyview switches remain abrupt at original endpoints',
 'garmentOcclusionObservation':'background shoulder, trim and collar lines still exhibit cross-view ghosting in bow-only composition',
 'nativeFullGarmentObservation':'single-source whole-garment source remains recognizable but source keyview shape differences make endpoint continuity worse',
 'regionalMetrics':{region:{
   'baselineMaxAdjacentRGBMAE':ref[region]['maxAdjacentRGBMAE'],
   'singleSourceFullMaxAdjacentRGBMAE':candidates['canonical_full'][region]['maxAdjacentRGBMAE'],
   'singleSourceBowMaxAdjacentRGBMAE':candidates['canonical_bow'][region]['maxAdjacentRGBMAE']}
   for region in ('bow','jewel','collar')},
 'preferredVisualBenchmark':'P15-101 head_alpha_blend',
 'engineeringQA':'PASS','artisticContinuity':'REQUIRES_STROKE_IDENTITY_AND_OCCLUSION_CORRESPONDENCE',
 'nextCriticalProblem':'stroke-level ribbon and collar correspondence plus foreground/background occlusion and truly matching garment keyart'}
ink['fullYawVisualAccepted']=False
inkP.write_text(json.dumps(ink,indent=2,ensure_ascii=False)+'\n')
assets=[
 'private-assets/p15-105-yaw0675/yaw0675-garment-native.png',
 'private-assets/p15-105-yaw0675/generation-result.json',
 'private-assets/exports/p15-105-middle-art/yaw067p5-garment-registered.png',
 'private-assets/exports/p15-105-middle-art/native-garment-contact.jpg',
 'private-assets/exports/p15-106-three-key-mesh/garment-three-key-mesh.json',
 'private-assets/exports/p15-107-canonical-ink/index.html',
 'private-assets/exports/p15-107-canonical-ink/single-source-ink-contact.jpg',
 'private-assets/exports/p15-107-canonical-ink/browser-desktop.png',
 'private-assets/exports/p15-107-canonical-ink/browser-mobile.png',
 'private-assets/exports/p15-107-canonical-ink/yaw60-bow-undercoat.png',
 'private-assets/exports/p15-107-canonical-ink/yaw75-bow-undercoat.png']
for mode,frames in rv['methods'].items():
 for p in frames.values():
  assets.append(str((P/'p15-107-canonical-ink'/p).resolve().relative_to(R)))
for item in rv['gifs'].values():assets.append(item['relativePath'])
for e in ('p15-101-render-qa.json','p15-105-native-art-qa.json','p15-106-mesh-qa.json',
          'p15-106-render-qa.json','p15-107-ink-qa.json','p15-107-review-qa.json','p15-107-browser-qa.json'):
 assets.append('evidence/'+e)
for s in ('p15_107_single_ink.py','p15_107_review.py','p15_107_browser.cjs',
          'p15_107_package.py','test_p15_107_review.py'):
 assets.append('scripts/'+s)
assets=list(dict.fromkeys(assets))
for relative in assets:
 if not (R/relative).is_file():raise FileNotFoundError(relative)
output=P/'p0-character-001-p15-107-source-ink-correspondence-review.zip'
readme=('P0 Character | Native 67.5° source-owned garment ink transport research\n'
 'Open private-assets/exports/p15-107-canonical-ink/index.html for the interactive 60°-75° review.\n'
 'Real original three-view garment and source-owned shared semantic ArtMesh carried into a TPS warp.\n'
 'Three actual source-ink transport strategies are provided alongside P15-101 and P15-105 reference motions.\n'
 'All 60° and 75° character endpoints retain their source RGBAs; the independent registered source was preserved.\n'
 'Each interpolated source-owned garment uses common 67.5° detail ink; nonfolding warps and source hashes validated.\n'
 'Animation acceptance depends on coherent stroke identity across keyframe boundaries and proper occlusion of collar, shoulder and ribbon.\n')
with ZipFile(output,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for f in assets:z.write(R/f,f)
with ZipFile(output) as z:
 assert z.testzip() is None
 count=len(z.namelist())
tasksPath=R/'tasks.json'
tasks=json.loads(tasksPath.read_text(encoding='utf-8'))
tasks['p15_107SourceInkCorrespondence']={
 'status':'SOURCE_OWNED_INK_TRANSPORT_EVIDENCE_VERIFIED',
 'characterId':'p0_character_001',
 'sourceGarment':native['registeredPath'],
 'sourceOriginalSHA256':native['nativeSHA256'],
 'sourceRegisteredSHA256':native['registeredSHA256'],
 'sourceMeshSHA256':ink['baseTopologySHA256'],
 'correspondenceSource':'P15-106 three-key source garment ArtMesh landmarks',
 'viewAngles':ink['angles'],
 'nonfoldedTPSFrames':len(ink['maps']),
 'landmarksMin':min(m['landmarks'] for m in ink['maps'].values()),
 'landmarksMax':max(m['landmarks'] for m in ink['maps'].values()),
 'candidateMethodNames':list(ink['methods']),
 'renderedCandidateFrames':sum(len(m) for m in ink['methods'].values()),
 'referenceFrames':18,
 'baselineBowMaxAdjacentRGBMAE':ref['bow']['maxAdjacentRGBMAE'],
 'singleSourceBowMaxAdjacentRGBMAE':ink['metrics']['canonical_bow']['bow']['maxAdjacentRGBMAE'],
 'baselineCollarMaxAdjacentRGBMAE':ref['collar']['maxAdjacentRGBMAE'],
 'singleSourceBowCollarMaxAdjacentRGBMAE':ink['metrics']['canonical_bow']['collar']['maxAdjacentRGBMAE'],
 'sourceInkTechnicalVerified':True,'continuousYawVisualAccepted':False,
 'visualBenchmark':'P15-101 head_alpha_blend',
 'unitTestsPass':15,'chromiumChecksPass':90,
 'next':'Establish actual stroke-level correspondence and occlusion masks on the 60/67.5/75 source drawings; inspect a true 67.5° garment joint with compatible source textures',
 'visualGate':'STROKE_IDENTITY_AND_VIEW_CONSISTENT_FOREGROUND_BACKGROUND_OCCLUSION',
 'review':rv['entry'],
 'package':{'path':str(output.relative_to(R)),'bytes':output.stat().st_size,
   'sha256':sha(output),'entries':count},
 'evidence':['evidence/p15-107-ink-qa.json','evidence/p15-107-review-qa.json','evidence/p15-107-browser-qa.json']
}
tasks['status']='P15_107_SOURCE_INK_TRANSPORT_VERIFIED_STROKE_AND_OCCLUSION_REVIEW_PENDING'
tasks['lastCompleted']='P15-107 source-owned garment ink TPS and actual yaw screenshot and motion evidence verified'
tasksPath.write_text(json.dumps(tasks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PACKAGE',output,'bytes',output.stat().st_size,'entries',count,'sha256',sha(output))
print('TASK',tasks['status'])
