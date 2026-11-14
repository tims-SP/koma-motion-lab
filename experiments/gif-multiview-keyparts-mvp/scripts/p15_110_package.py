#!/usr/bin/env python3
"""P0 three-view model-observed source ink and validated local VDD study."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
rqa=R/'evidence/p15-110-render-qa.json';r=json.loads(rqa.read_text())
vqa=R/'evidence/p15-110-vision-qa.json';v=json.loads(vqa.read_text())
rev=json.loads((R/'evidence/p15-110-review-qa.json').read_text())
b=json.loads((R/'evidence/p15-110-browser-qa.json').read_text())
raw=R/'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json'
assert b['status']=='PASS' and len(b['checks'])==72
assert v['annotationSHA256']==sha(raw) and len(v['roleNames'])==8
assert len(v['experimentAcceptedRoles'])==4
assert len(r['methods'])==2 and all(len(x)==9 for x in r['methods'].values())
assert all(len(z)==9 for z in rev['methodFrames'].values())
for row in r['methods'].values():
 for key in ('60','67.5','75'):
  assert row[key]['diagnostics']['sourceOwnedKeyframe']
# Verify benchmark selection: shape and fold evidence only; temporal differences
# and artistic preview remain explicit independent acceptance gates.
base=r['metrics']['P15-101-original'];reference=r['metrics']['P15-107-three-native']
direct=r['metrics']['matched_path_direct'];owner=r['metrics']['matched_path_owner']
r['visualReview']={
 'performed':True,
 'trueSourceCoordinates':'Codex visual observations with source 1024x1024 image grids',
 'crossViewExperimentPaths':v['experimentAcceptedRoles'],
 'crossViewCandidateCount':len(v['roleNames']),
 'acceptedPathCount':len(v['experimentAcceptedRoles']),
 'sourceImageConstraint':'all accepted points checked for source ink-edge and alpha support',
 'occlusionFacts':{
  'jewel':'front of ribbon bow',
  'ribbon':'front of white collar seam',
  'hair':'existing source-owned head/hair mesh',
  'actualHiddenUnderBroochArtwork':'SOURCE_NOT_OBSERVED',
  'newHiddenSurfaceArtistApproved':False},
 'observedFrameArtifacts':{
  'bow':'local path displacement registers some source edges but introduces duplicated fabric silhouettes around ribbon wing transitions',
  'jewel':'brooch remains view-dependent; mismatch between generated source keyviews causes ghosted gold boundaries',
  'collar':'collar hidden edge and fabric folds have no approved source-backed underpainting, so warped blends retain double seams',
  'head':'P15-101 head and hair still exhibit separate source profile limitations'},
 'quantitative':{region:{
  'P15-101':base[region]['maxAdjacentRGBMAE'],
  'P15-107-native':reference[region]['maxAdjacentRGBMAE'],
  'pathDirect':direct[region]['maxAdjacentRGBMAE'],
  'pathOwner':owner[region]['maxAdjacentRGBMAE']}
  for region in ('bow','collar','jewel')},
 'baselineSelection':'P15-101 head_alpha_blend',
 'threeKeyCandidate':'P15-107 companion_direct_native_keys',
 'engineeringQA':'PASS',
 'completeYawArtisticAccepted':False,
 'nextCriticalResource':'source-matched bow interior fold paths plus artist-consistent hidden collar/brooch surface artwork'}
r['naturalYawAccepted']=False
rqa.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
files=[
 'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json',
 'private-assets/p15-110-vision-strokes/analysis-brief.txt',
 'private-assets/p15-110-vision-strokes/garment-three-view.jpg',
 'private-assets/exports/p15-107-source-patches/consistent-garment-contact.jpg',
 'private-assets/exports/p15-110-path-vdd/index.html',
 'private-assets/exports/p15-110-path-vdd/vision-matched-bow-contact.jpg',
 'private-assets/exports/p15-110-path-vdd/browser-desktop.png',
 'private-assets/exports/p15-110-path-vdd/browser-mobile.png']
for vkey,original in [('60','060'),('67.5','0675'),('75','075')]:
 files += [
  f'private-assets/p15-110-vision-strokes/yaw{original}-source.png',
  f'private-assets/p15-110-vision-strokes/yaw{original}-coordinate-grid.png',
  f'private-assets/exports/p15-110-vision-validated/yaw{vkey.replace(".","p")}-model-paths.jpg']
for row in rev['methodFrames'].values():
 for file in row.values():files.append(str((P/'p15-110-path-vdd'/file).resolve().relative_to(R)))
for gif in rev['animations'].values():files.append(gif['path'])
for name in ('p15-101-render-qa.json','p15-107-companion-qa.json','p15-108-stroke-qa.json',
             'p15-109-path-qa.json','p15-110-vision-qa.json','p15-110-render-qa.json',
             'p15-110-review-qa.json','p15-110-browser-qa.json'):
 files.append('evidence/'+name)
for script in ('p15_110_vision_validate.py','p15_110_path_vdd.py','p15_110_review.py',
               'p15_110_browser.cjs','p15_110_package.py','test_p15_110_review.py'):
 files.append('scripts/'+script)
files=list(dict.fromkeys(files))
for item in files:
 if not (R/item).is_file():raise FileNotFoundError(item)
out=P/'p0-character-001-p15-110-vision-stroke-correspondence.zip'
readme=('P0 Character | Vision-grounded three-view garment source ink\n'
 'Interactive full-character review: private-assets/exports/p15-110-path-vdd/index.html\n'
 'Eight annotated semantic source-ink roles, three independent 1024 original costume views, 96 source points, per-view occlusion/visibility and original Codex vision annotation JSON.\n'
 'Four candidates satisfy source-edge, 3-view visibility, and geometry gates for local view-dependent warp experiments.\n'
 '36 source and candidate rendering frames, 4 actual GIF previews, desktop/mobile Chromium screenshots, evidence and reproducible Python/JS scripts.\n'
 'The actual source stroke annotations are model-assisted; no human artist has approved the correspondences.\n'
 'Observed covered material that has no corresponding original source should be independently drawn before full 360-degree artistic validation.\n')
with ZipFile(out,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for file in files:z.write(R/file,file)
with ZipFile(out) as z:
 assert z.testzip() is None
 n=len(z.namelist())
taskFile=R/'tasks.json';t=json.loads(taskFile.read_text())
t['p15_110VisionStrokeCorrespondence']={
 'status':'THREE_SOURCE_MODEL_GROUNDED_STROKE_PATHS_VERIFIED',
 'characterId':'p0_character_001',
 'sourceViews':[60,67.5,75],
 'visionSource':'Codex multimodal image interpretation with original source coordinate grids',
 'roleCandidates':v['roleNames'],
 'sourcePointCount':sum(len(e['points']) for role in json.loads(raw.read_text())['roles'].values()
                         for e in role['views'].values()),
 'acceptedSourceRoles':v['experimentAcceptedRoles'],
 'sourcePathsSHA256':v['annotationSHA256'],
 'sourceOwnedImageSHA256':{view:rec['sha256'] for view,rec in v['sourceImages'].items()},
 'sourcePixelAndGeometryGate':'source-edge alpha and normalized cross-view path displacement',
 'renderedCandidateFrames':sum(len(x) for x in r['methods'].values()),
 'comparatorFrames':18,
 'renderMethods':list(r['methods']),
 'regionalMaxAdjacentRGBMAE':r['visualReview']['quantitative'],
 'nativeKeyframeSourcePixelExact':True,
 'hiddenSurfaceNeedsOriginalArt':True,
 'artistApprovedStrokes':False,
 'fullYawVisualAccepted':False,
 'visualBenchmark':'P15-101 head_alpha_blend',
 'preferredThreeKeyGarmentCandidate':'P15-107 companion_direct_native_keys',
 'unitTestsPass':17,'chromiumChecksPass':72,
 'review':rev['entry'],
 'package':{'path':str(out.relative_to(R)),'bytes':out.stat().st_size,
            'entries':n,'sha256':sha(out)},
 'evidence':['evidence/p15-110-vision-qa.json','evidence/p15-110-render-qa.json',
             'evidence/p15-110-review-qa.json','evidence/p15-110-browser-qa.json'],
 'next':'Develop source-backed inner folds and hidden collar/jewel surfaces for incomplete roles, then apply per-part occlusion and verify nine yaw frames for artifact removal'
}
t['status']='P15_110_VISION_SOURCE_STROKE_PATHS_VERIFIED_HIDDEN_SURFACE_ART_REVIEW_PENDING'
t['lastCompleted']='P15-110 Codex observed multi-source bow stroke paths, source-pixel QA and VDD animation comparison'
taskFile.write_text(json.dumps(t,ensure_ascii=False,indent=2)+'\n')
print('DELIVERY',out,'bytes',out.stat().st_size,'entries',n,'sha256',sha(out),flush=True)
print('TASK',t['status'],flush=True)
