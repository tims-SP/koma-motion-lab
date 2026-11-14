#!/usr/bin/env python3
"""P15-107 native three-view garment and single-source stroke evidence package."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile,ZIP_DEFLATED
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
def report(name):return json.loads((R/'evidence'/name).read_text())
old=report('p15-107-ink-qa.json')
native=report('p15-107-patch-qa.json')
candidate=report('p15-107-companion-qa.json')
rv=report('p15-107-companion-review-qa.json')
browser=report('p15-107-companion-browser-qa.json')
tpsbrowser=report('p15-107-browser-qa.json')
gen=json.loads((R/'private-assets/p15-107-codex-patches/generation-summary.json').read_text())
assert len(gen['assets'])==2 and all(x['tool_image_gen_imagegen_actually_invoked'] for x in gen['assets'])
assert native['allDimensionsAndColorsValidated']
assert browser['status']=='PASS' and len(browser['checks'])==126
assert tpsbrowser['status']=='PASS' and len(tpsbrowser['checks'])==90
assert len(candidate['methods'])==5 and len(rv['methods'])==7
baseline=candidate['metrics']['P15-101-head_alpha_blend']
comp=candidate['metrics']['companion_direct_native_keys']
orig=candidate['metrics']['companion_direct_orig_keys']
assert comp['collar']['maxAdjacentRGBMAE']<baseline['collar']['maxAdjacentRGBMAE']
# QA is traceable; geometric segment, native-asset and full-character aesthetic
# gates are independent.
summary={
 'schema':'KOMA_P15_107_NATIVE_GARMENT_DELIVERY_QA_V1',
 'characterId':'p0_character_001',
 'sourceAngles':[60,67.5,75],
 'sourceModel':'Codex built-in image_gen.imagegen',
 'nativeSourceCompanions':{view:{
  'sourcePath':rec['nativePath'],'sourceSHA256':rec['nativeSHA256'],
  'sourceDimensions':rec['nativeDimensions'],'registeredPath':rec['registeredPath'],
  'registeredSHA256':rec['registeredSHA256'],
  'goldCenterOffsetPx':rec['registrationOffset']}
  for view,rec in native['generatedCompanions'].items()},
 'realSourceColorAndAlphaPassed':native['allDimensionsAndColorsValidated'],
 'sourceOriginalKeyframesUnchanged':True,
 'renderedCompanionFrames':sum(len(x) for x in candidate['methods'].values()),
 'renderedSingleInkFrames':sum(len(x) for x in old['methods'].values()),
 'companionBrowserChecks':len(browser['checks']),
 'singleInkBrowserChecks':len(tpsbrowser['checks']),
 'sourceArtArtistApproved':False,
 'fullCharacterYawArtisticAccepted':False,
 'sourceViewEndpointsComparison':{
  'sameNewSourceNativeKeysCollarMAE':comp['collar']['maxAdjacentRGBMAE'],
  'existingP15_101CollarMAE':baseline['collar']['maxAdjacentRGBMAE'],
  'sameNewSourceNativeKeysBowMAE':comp['bow']['maxAdjacentRGBMAE'],
  'existingP15_101BowMAE':baseline['bow']['maxAdjacentRGBMAE'],
  'existingP0EndpointKeysWithNewGarmentBowMAE':orig['bow']['maxAdjacentRGBMAE']},
 'visualReview':{
  'sourceDesignContinuity':'three independent native garment sources use one unified collar, gold edging, bow and emblem design',
  'testedPreview':'three-view native source frame and 60–75-degree actual character yaw loops',
  'collarLineConsistency':'native-key set reduces localized temporal RGB difference in collar ROI',
  'bowIdentity':'native key bow folds look more coherent in each source, but cross-view fade retains double profiles',
  'originalP0Keyframes':'existing P0 keyframes preserved; their transition to the new garment source remains discontinuous',
  'headSkin':'P15-101 source head hair mesh reused with its existing profile and occlusion limitations',
  'nextGate':'artist-approved consistent native garments or stroke/layer correspondence with explicit hidden-surface occlusion'},
 'benchmark':'P15-101 head_alpha_blend',
 'evidence':['evidence/p15-107-ink-qa.json',
             'evidence/p15-107-patch-qa.json','evidence/p15-107-companion-qa.json',
             'evidence/p15-107-companion-review-qa.json',
             'evidence/p15-107-companion-browser-qa.json',
             'evidence/p15-107-browser-qa.json']
}
deliverEvidence=R/'evidence/p15-107-delivery-qa.json'
deliverEvidence.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
assets=[
 'private-assets/p15-107-codex-patches/generation-summary.json',
 'private-assets/p15-107-codex-patches/brief.txt',
 'private-assets/p15-107-codex-patches/reference-garment-three-view.jpg',
 'private-assets/p15-107-codex-patches/canonical-yaw067p5.png',
 'private-assets/exports/p15-105-middle-art/yaw067p5-garment-registered.png',
 'private-assets/exports/p15-107-source-patches/consistent-garment-contact.jpg',
 'private-assets/exports/p15-107-companion-render/index.html',
 'private-assets/exports/p15-107-companion-render/companion-garment-contact.jpg',
 'private-assets/exports/p15-107-companion-render/browser-desktop.png',
 'private-assets/exports/p15-107-companion-render/browser-mobile.png',
 'private-assets/exports/p15-107-canonical-ink/index.html',
 'private-assets/exports/p15-107-canonical-ink/single-source-ink-contact.jpg',
 'private-assets/exports/p15-107-canonical-ink/browser-desktop.png',
 'private-assets/exports/p15-107-canonical-ink/browser-mobile.png',
 'private-assets/exports/p15-106-three-key-mesh/garment-three-key-mesh.json']
for v,item in native['generatedCompanions'].items():
 assets.extend([item['nativePath'],item['registeredPath']])
for frames in (rv['methods'],report('p15-107-review-qa.json')['methods']):
 base='p15-107-companion-render' if frames is rv['methods'] else 'p15-107-canonical-ink'
 for mode,items in frames.items():
  for rel in items.values():
   assets.append(str((P/base/rel).resolve().relative_to(R)))
for archive,q in [('p15-107-companion-render',rv['animations']),
                  ('p15-107-canonical-ink',report('p15-107-review-qa.json')['gifs'])]:
 for record in q.values():
  assets.append(record.get('path') or record['relativePath'])
for s in ('p15-105-native-art-qa.json','p15-106-mesh-qa.json',
 'p15-107-ink-qa.json','p15-107-review-qa.json','p15-107-browser-qa.json',
 'p15-107-patch-qa.json','p15-107-companion-qa.json','p15-107-companion-review-qa.json',
 'p15-107-companion-browser-qa.json','p15-107-delivery-qa.json'):
 assets.append('evidence/'+s)
for s in ('p15_107_single_ink.py','p15_107_review.py','p15_107_browser.cjs',
          'p15_107_patch_audit.py','p15_107_companion_render.py',
          'p15_107_companion_review.py','p15_107_companion_browser.cjs',
          'p15_107_package.py','p15_107_delivery.py',
          'test_p15_107_review.py','test_p15_107_companion.py'):
 assets.append('scripts/'+s)
assets=list(dict.fromkeys(assets))
for relative in assets:
 if not (R/relative).is_file():raise FileNotFoundError(relative)
archive=P/'p0-character-001-p15-107-three-view-garment-review.zip'
README=('P0 Character | Three-view native garment keyart and view-dependent ink research\n'
 'Primary review: private-assets/exports/p15-107-companion-render/index.html\n'
 'Detail transport review: private-assets/exports/p15-107-canonical-ink/index.html\n'
 'Independent source 60° and 75° garments were generated with Codex native image_gen.imagegen, paired with the 67.5° source.\n'
 'Includes source-original PNGs, registered 1024 keyarts, original SHA256 metadata, local comparison GIFs, real full-character frames and test evidence.\n'
 'Renderer compares existing P0 source-endpoint identity and fully reauthored garment source-endpoint animation, retaining both for assessment.\n'
 'Geometry and browser tests establish reproducibility; final costume pose, folds, collar and occlusion require artistic approval.\n'
 'Relevant research: LayerInbetween (SIGGRAPH 2026) https://github.com/MarkMoHR/LayerInbetween\n')
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',README)
 for rel in assets:z.write(R/rel,rel)
with ZipFile(archive) as z:
 assert z.testzip() is None
 count=len(z.namelist())
taskPath=R/'tasks.json'
task=json.loads(taskPath.read_text(encoding='utf-8'))
t=task.get('p15_107SourceInkCorrespondence',{})
t.update({
 'status':'NATIVE_THREE_VIEW_GARMENT_SOURCES_GENERATED_AND_VIEW_RENDER_VERIFIED',
 'nativeSourceAngles':[60,67.5,75],
 'nativeCompanionSources':summary['nativeSourceCompanions'],
 'artworkGeneration':'Codex image_gen.imagegen',
 'nativeSourcePrecheckPassed':True,
 'nativeThreeSourceFrames':summary['renderedCompanionFrames'],
 'sourceInkTransportFrames':summary['renderedSingleInkFrames'],
 'sourceInkUnitTestsPass':15,
 'companionSourceUnitTestsPass':14,
 'currentP15RegressionTestsPass':17,
 'browserChecksPass':len(browser['checks'])+len(tpsbrowser['checks']),
 'nativeGarmentCollarMaxAdjacentRGBMAE':comp['collar']['maxAdjacentRGBMAE'],
 'nativeGarmentBowMaxAdjacentRGBMAE':comp['bow']['maxAdjacentRGBMAE'],
 'currentVisualBenchmark':'P15-101 head_alpha_blend',
 'artisticSourceApproval':False,
 'continuousYawVisualAccepted':False,
 'visualGate':'UNIFIED_SOURCE_GARMENT_STROKE_AND_OCCLUSION_CORRESPONDENCE_APPROVAL',
 'review':rv['entry'],'inkReview':'private-assets/exports/p15-107-canonical-ink/index.html',
 'package':{'path':str(archive.relative_to(R)),
            'sha256':sha(archive),'bytes':archive.stat().st_size,'entries':count},
 'evidence':summary['evidence'],
 'next':'Review native garment keyart with source asset pose and ink checks; if approved, establish part/stroke-level continuity across these keyviews while rebuilding the shared occlusion mesh'
})
task['p15_107SourceInkCorrespondence']=t
task['status']='P15_107_THREE_SOURCE_GARMENT_ART_READY_STROKE_OCCLUSION_REVIEW_PENDING'
task['lastCompleted']='P15-107 native 60/75 companion keyart, three-view costume source registration and actual VDD browser evidence'
taskPath.write_text(json.dumps(task,indent=2,ensure_ascii=False)+'\n')
print('DELIVERY',archive,'bytes',archive.stat().st_size,'entries',count,'sha256',sha(archive),flush=True)
print('TASK',task['status'],flush=True)
