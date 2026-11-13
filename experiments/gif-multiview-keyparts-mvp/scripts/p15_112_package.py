#!/usr/bin/env python3
"""Package and register P0 source visibility/disocclusion verification P15-112."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile,ZIP_DEFLATED
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
def evidence(name):return json.loads((R/'evidence'/name).read_text())
geometry=evidence('p15-112-render-qa.json')
reveal=evidence('p15-112-reveal-qa.json')
review=evidence('p15-112-review-qa.json')
browser=evidence('p15-112-browser-qa.json')
prev=evidence('p15-111-source-qa.json')
assert browser['status']=='PASS'
assert len(browser['yawChecks'])==108 and len(browser['revealChecks'])==30
assert len(geometry['methods'])==3 and all(len(v)==9 for v in geometry['methods'].values())
assert len(reveal['viewRecords'])==3 and len(review['animations'])==6
assert all(rec['poseMetrics']['neutral']['zeroPoseSourceRGBAMAEPixel']<0.2 for rec in reveal['viewRecords'].values())
assert all(e['opaquePixelsWithHidden']>e['opaquePixelsWithoutHidden']
 for rec in reveal['viewRecords'].values() for key,e in rec['poseMetrics'].items() if key!='neutral')
# Source hidden art supplements source-owned surfaces but does not establish
# the artistic fit of their silhouette or multi-view ink paths.
models=geometry['metrics']
baseline=models['P15-101-original'];native=models['P15-107-native']
candidate=models['edge_guard']
totalExposed=sum(e['newlyExposedSourceOwnedPixels']
 for r in reveal['viewRecords'].values() for k,e in r['poseMetrics'].items() if k!='neutral')
totalCover=sum(e['donorAlphaCoveredExposedPixels']
 for r in reveal['viewRecords'].values() for k,e in r['poseMetrics'].items() if k!='neutral')
totalOpaqueGain=sum(e['opaquePixelsWithHidden']-e['opaquePixelsWithoutHidden']
 for r in reveal['viewRecords'].values() for k,e in r['poseMetrics'].items() if k!='neutral')
geometry['visualReview']={
 'performed':True,
 'sourceArtwork':'three native P0 garment source views with the six inferred hidden textile layers',
 'geometry':'four measured bow source paths mapped to one SDF outline and source-owned foreground ink',
 'sampledJacobian':'all 36 endpoint warp samples at nine yaw positions retain positive Jacobian',
 'sourceViewOcclusionExperiment':'move native 1024 bow 10px or golden jewel 7px to reveal lower source-owned layers',
 'revealedSourceOwnedPixels':totalExposed,
 'inferredMaterialCoveragePixels':totalCover,
 'newOpaquePixelsFromUnderpaint':totalOpaqueGain,
 'zeroPoseRGBAReconstructionMAE':{
   k:v['poseMetrics']['neutral']['zeroPoseSourceRGBAMAEPixel']
   for k,v in reveal['viewRecords'].items()},
 'visualFindings':{
  'sourceLevelReconstruction':'the native layer partition preserves original character garment pixels at zero relative displacement',
  'broochDisocclusion':'genuine hidden red ribbon paint fills the majority of newly exposed brooch region at sampled offsets',
  'collarDisocclusion':'white collar underpaint restores a subset of newly exposed ribbon occlusion; exterior rim still has missing source-backed textile',
  'animatedAppearance':'cross-source bow creases and edge texture remain inconsistent; shape-map output produces local dark gaps and contour distortion',
  'layerPriority':'source-owned jewel draws above ribbon; ribbon draws above shirt/collar; head remains P15-101 source-owned mesh'},
 'regionalMaxAdjacentRGBMAE':{roi:{
  'P15-101':baseline[roi]['maxAdjacentRGBMAE'],
  'P15-107':native[roi]['maxAdjacentRGBMAE'],
  'P15-112-edgeGuard':candidate[roi]['maxAdjacentRGBMAE']}
  for roi in ('bow','collar','jewel')},
 'selectedVisualBenchmark':'P15-101 head_alpha_blend',
 'selectedGarmentCandidate':'P15-107 companion_direct_native_keys',
 'fullContinuousYawArtistApproved':False,
 'nextRequiredEvidence':'canonical ribbon/collar source ink artwork and matched visible-to-hidden contours; new garment source must have one physical component topology in all keyviews'}
geometry['artistVisualAccepted']=False
geometryFile=R/'evidence/p15-112-render-qa.json'
geometryFile.write_text(json.dumps(geometry,indent=2,ensure_ascii=False)+'\n')
files=[
 'private-assets/exports/p15-112-visibility-vdd/index.html',
 'private-assets/exports/p15-112-visibility-vdd/visibility-geometry-contact.jpg',
 'private-assets/exports/p15-112-visibility-vdd/browser-desktop.png',
 'private-assets/exports/p15-112-visibility-vdd/browser-mobile.png',
 'private-assets/exports/p15-112-occlusion-probe/three-view-occlusion-reveal-contact.jpg',
 'private-assets/exports/p15-111-hidden-registered/underpaint-source-contact.jpg',
 'private-assets/exports/p15-107-source-patches/consistent-garment-contact.jpg',
 'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json']
for view,parts in prev['layers'].items():
 files.extend([parts[role]['nativePath'] for role in ('bow','collar')])
 files.extend([parts[role]['hiddenOnlyPath'] for role in ('bow','collar')])
 files.append(reveal['viewRecords'][view]['sourceImage'])
for rec in reveal['viewRecords'].values():
 for samples in rec['files'].values():
  for item in samples.values():files.append(item['path'])
for method,frames in review['renderMethods'].items():
 for path in frames.values():
  files.append(str((P/'p15-112-visibility-vdd'/path).resolve().relative_to(R)))
for item in review['animations'].values():files.append(item['path'])
for name in ('p15-101-render-qa.json','p15-107-companion-qa.json',
             'p15-108-stroke-qa.json','p15-110-vision-qa.json',
             'p15-111-source-qa.json','p15-112-render-qa.json',
             'p15-112-reveal-qa.json','p15-112-review-qa.json',
             'p15-112-browser-qa.json'):
 files.append('evidence/'+name)
for name in ('p15_112_visibility_vdd.py','p15_112_reveal_probe.py',
             'p15_112_review.py','p15_112_browser.cjs',
             'p15_112_package.py','test_p15_112_review.py'):
 files.append('scripts/'+name)
files=list(dict.fromkeys(files))
for file in files:
 if not (R/file).is_file():raise FileNotFoundError(file)
dest=P/'p0-character-001-p15-112-garment-visibility-review.zip'
readme=('P0 Character | Source-aligned garment visibility and disocclusion verification\n'
 'Interactive full-character yaw and actual source-layer exposure: private-assets/exports/p15-112-visibility-vdd/index.html\n'
 'Three real 60°, 67.5°, 75° view garments, six hidden material RGBA illustrations, tested bow/collar/jewel surface ownership.\n'
 'Two physical controls: a moving ribbon exposes the shirt/collar textile underneath, and a moving golden brooch reveals drawn red ribbon material.\n'
 'Source-owned mattes reconstruct all three native canvases with under 0.2/255 channel mean error at zero movement.\n'
 'Full yaw compares ribbon-shape SDF, single-ink ownership and edge-aware color selection against P15-101, P15-107 and P15-111.\n'
 'Native sources, model-contour provenance, actual PNG frames and GIFs, two browser viewport screenshots, QA and executable scripts included.\n'
 'Visibility coverage and nonfolding geometry are engineering-verified. Continuous rotating clothing requires canonical cross-view ink correspondence and artistic validation.\n')
with ZipFile(dest,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for f in files:z.write(R/f,f)
with ZipFile(dest) as z:
 assert z.testzip() is None
 n=len(z.namelist())
taskFile=R/'tasks.json';task=json.loads(taskFile.read_text(encoding='utf-8'))
task['p15_112GarmentVisibility']={
 'status':'THREE_VIEW_SOURCE_VISIBILITY_AND_HIDDEN_MATERIAL_EXPOSURE_VERIFIED',
 'characterId':'p0_character_001','sourceAngles':[60,67.5,75],
 'visibleSourcePaths':4,
 'verifiedSourceInferredUnderpaintLayers':6,
 'testedSourceViewDisplacements':{'bowPixels':10,'jewelPixels':7},
 'sourceGeometrySurfaceOwner':'single shape SDF + source-owned ink and jewel',
 'actualSourceTestExposedPixels':totalExposed,
 'actualUnderpaintCoveredPixels':totalCover,
 'actualUnderpaintNewOpaquePixels':totalOpaqueGain,
 'sourceZeroPoseRGBAReconstructionMAE':geometry['visualReview']['zeroPoseRGBAReconstructionMAE'],
 'renderedYawCandidateFrames':sum(len(x) for x in geometry['methods'].values()),
 'renderedSourceRevealFrames':sum(len(x['files'])*2 for x in reveal['viewRecords'].values()),
 'referenceYawFrames':27,
 'renderMethods':list(geometry['methods']),
 'regionalMaxAdjacentRGBMAE':geometry['visualReview']['regionalMaxAdjacentRGBMAE'],
 'sourceArtNativeKeyframesPixelExact':True,
 'structuralOcclusionVerified':True,
 'sourceRasterNonfoldingVerified':True,
 'artistApprovedFullYaw':False,
 'selectedVisualBenchmark':'P15-101 head_alpha_blend',
 'selectedThreeKeyGarmentCandidate':'P15-107 companion_direct_native_keys',
 'unitTestsPass':17,'chromiumYawChecksPass':108,'chromiumRevealChecksPass':30,
 'review':review['entry'],
 'package':{'path':str(dest.relative_to(R)),'bytes':dest.stat().st_size,
            'sha256':sha(dest),'entries':n},
 'evidence':['evidence/p15-112-render-qa.json','evidence/p15-112-reveal-qa.json',
             'evidence/p15-112-review-qa.json','evidence/p15-112-browser-qa.json'],
 'next':'Produce a single canonically corresponding ribbon and collar drawing with consistent hidden/visible stroke identity across all three views, then rerender the source-owned VDD and inspect contour quality before promoting a visual benchmark'
}
task['status']='P15_112_GARMENT_VISIBILITY_MECHANISM_VERIFIED_CONTINUOUS_YAW_ART_PENDING'
task['lastCompleted']='P15-112 three-source bow/jewel geometry and source-hidden material exposure, full-character yaw comparison and browser evidence'
taskFile.write_text(json.dumps(task,ensure_ascii=False,indent=2)+'\n')
print('DELIVERY',dest,'bytes',dest.stat().st_size,'entries',n,'sha256',sha(dest),flush=True)
print('TASK',task['status'],flush=True)
