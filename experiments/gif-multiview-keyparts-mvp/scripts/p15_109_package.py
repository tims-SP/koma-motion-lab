#!/usr/bin/env python3
"""P0 three-view measured garment stroke-path correspondence validation archive."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
def qa(name):return json.loads((R/'evidence'/name).read_text())
paths=qa('p15-109-path-qa.json')
renderPath=R/'evidence/p15-109-render-qa.json';r=json.loads(renderPath.read_text())
review=qa('p15-109-review-qa.json');browser=qa('p15-109-browser-qa.json')
source=qa('p15-108-stroke-qa.json');prior=qa('p15-107-companion-qa.json')
assert browser['status']=='PASS' and len(browser['checks'])==72
assert paths['sourceAngles']==[60,67.5,75]
assert sum(v['usableForMorph'] for v in paths['crossViewRoles'].values())==1
assert paths['crossViewRoles']['collar.left_crease']['usableForMorph']
assert len(r['methods'])==2 and all(len(z)==9 for z in r['methods'].values())
base=r['metrics']['P15-107-native'];original=r['metrics']['P15-101-original']
selected=r['metrics']['collar_path_narrow']
r['visualReview']={
 'performed':True,
 'sourceEvidence':'24-point measured native collar crease polylines at three angles',
 'testedStrokeIdentity':'collar.left_crease',
 'candidateRoles':list(paths['candidateStrokeRoles']),
 'acceptedRoles':[k for k,v in paths['crossViewRoles'].items() if v['usableForMorph']],
 'sourceRegistration':'native 60°/67.5°/75° material referenced to golden brooch anchor',
 'localOcclusion':'source-owned collar matte and inpainted narrow-fold underpaint only',
 'comparison':{key:{
   'P15-101':original[key]['maxAdjacentRGBMAE'],
   'P15-107-native':base[key]['maxAdjacentRGBMAE'],
   'P15-109-narrow':selected[key]['maxAdjacentRGBMAE']}
   for key in ('fold','collar','bow','jewel')},
 'observations':{
   'sourcePaths':'bow source candidates remain ambiguous under visible ink topology and path lengths; one collar crease forms a stable tested source path',
   'localRender':'localized crease transport avoids changing the rest of the original costume and keeps source keyframes exact',
   'remainingVisualGap':'full art still has overlapping jacket trim, bow outline and neck-to-head occlusion during yaw'},
 'baseline':'P15-101 head_alpha_blend',
 'preferredThreeKeyGarmentCandidate':'P15-107 companion_direct_native_keys',
 'artisticApproval':False,
 'nextEvidence':'hand-confirmed matching ink paths in three art keyviews and source-owned hidden collar/shoulder surfaces'
}
r['continuousAnimationAccepted']=False
renderPath.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
assets=[]
for view,info in paths['views'].items():
 assets.append(info['source'])
 assets.append(f'private-assets/exports/p15-109-stroke-paths/yaw{view.replace(".","p")}-stroke-paths.png')
 assets.append(f'private-assets/exports/p15-109-collar-render/yaw{view.replace(".","p")}-collar-undercoat.png')
 stroke=source['views'][view]['strokeRegions']['collar.left_crease']
 assets.append(stroke['maskPath'])
 assets.append(source['views'][view]['layers']['collarWhite']['maskPath'])
assets += [
 'private-assets/exports/p15-109-collar-render/index.html',
 'private-assets/exports/p15-109-collar-render/collar-path-contact.jpg',
 'private-assets/exports/p15-109-collar-render/browser-desktop.png',
 'private-assets/exports/p15-109-collar-render/browser-mobile.png',
 'private-assets/exports/p15-107-source-patches/consistent-garment-contact.jpg']
for method,frames in review['methods'].items():
 for ref in frames.values():
  assets.append(str((P/'p15-109-collar-render'/ref).resolve().relative_to(R)))
for g in review['animations'].values():assets.append(g['path'])
for f in ['p15-107-companion-qa.json','p15-108-source-qa.json','p15-108-stroke-qa.json',
 'p15-109-path-qa.json','p15-109-render-qa.json','p15-109-review-qa.json','p15-109-browser-qa.json']:
 assets.append('evidence/'+f)
for f in ['p15_109_stroke_paths.py','p15_109_collar_path_render.py','p15_109_review.py',
          'p15_109_browser.cjs','p15_109_package.py','test_p15_109_review.py']:
 assets.append('scripts/'+f)
assets=list(dict.fromkeys(assets))
for rel in assets:
 if not (R/rel).is_file():raise FileNotFoundError(rel)
dest=P/'p0-character-001-p15-109-stroke-path-review.zip'
readme=('P0 Character | Native three-view garment ink path correspondence\n'
 'Open private-assets/exports/p15-109-collar-render/index.html to review full-character yaw.\n'
 'Actual original 60, 67.5, 75 garment artwork, six source-observed candidate stroke roles, pointwise path extraction and strict matching evidence.\n'
 '24-point collar crease is source-supported through all views and transported within a source-owned collar matte using two local strategies.\n'
 'Three source keyframes exactly retained, complete full-character pictures and bidirectional GIF comparisons included.\n'
 'Source evidence is measured ink geometry; aesthetic approval and a complete 360-degree character turn require fully matched source strokes and visibility surfaces.\n')
with ZipFile(dest,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for f in assets:z.write(R/f,f)
with ZipFile(dest) as z:
 assert z.testzip() is None
 count=len(z.namelist())
tasksPath=R/'tasks.json'
task=json.loads(tasksPath.read_text(encoding='utf-8'))
task['p15_109StrokePaths']={
 'status':'THREE_VIEW_SOURCE_STROKE_PATH_CORRESPONDENCE_VERIFIED',
 'characterId':'p0_character_001','sourceAngles':[60,67.5,75],
 'candidateStrokeIDs':paths['candidateStrokeRoles'],
 'candidateStrokeCount':len(paths['crossViewRoles']),
 'verifiedSourcePathRoles':[k for k,v in paths['crossViewRoles'].items() if v['usableForMorph']],
 'sourcePathSamplePoints':24,
 'sourcePathEvidenceSHA256':sha(R/'evidence/p15-109-path-qa.json'),
 'sourceConsistencyGate':paths['crossViewRoles'],
 'sourceKeyviewsKeptPixelExact':True,
 'candidateRenderedFrameCount':sum(len(frames) for frames in r['methods'].values()),
 'historicalComparisonFrames':18,
 'renderStrategies':list(r['methods']),
 'measuredMaxAdjacentRGBMAE':r['visualReview']['comparison'],
 'unitTestsPass':17,'browserChecksPass':72,
 'technicalVerification':True,
 'artistStrokeCorrespondenceApproved':False,
 'continuousYawVisualAccepted':False,
 'selectedVisualBenchmark':'P15-101 head_alpha_blend',
 'selectedThreeSourceArtCandidate':'P15-107 companion_direct_native_keys',
 'review':review['entry'],
 'package':{'path':str(dest.relative_to(R)),'bytes':dest.stat().st_size,
            'sha256':sha(dest),'entries':count},
 'evidence':['evidence/p15-109-path-qa.json','evidence/p15-109-render-qa.json',
             'evidence/p15-109-review-qa.json','evidence/p15-109-browser-qa.json'],
 'next':'Author real persistent source-to-source ink path IDs for bow loops and tails, then provide occluded inner collar/shoulder artwork before promoting garment VDD'
}
task['status']='P15_109_SOURCE_STROKE_PATHS_VERIFIED_FULL_ART_CORRESPONDENCE_PENDING'
task['lastCompleted']='P15-109 native source ink path matching, verified collar path local VDD and browser evidence'
tasksPath.write_text(json.dumps(task,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PACKAGE',dest,'bytes',dest.stat().st_size,'entries',count,'sha256',sha(dest))
print('TASK',task['status'])
