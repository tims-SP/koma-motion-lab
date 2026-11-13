#!/usr/bin/env python3
"""P15-114 canonical three-view collar material and source-seam review archive."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
def qa(name):return json.loads((R/'evidence'/name).read_text())
source=qa('p15-114-source-qa.json')
renderFile=R/'evidence/p15-114-render-qa.json'
render=json.loads(renderFile.read_text())
review=qa('p15-114-review-qa.json')
browser=qa('p15-114-browser-qa.json')
previous=qa('p15-113-topology-qa.json')
assert browser['status']=='PASS' and len(browser['checks'])==90
assert all(source['views'][view]['mappedNativeTargetIoU']>.82 for view in ('60','75'))
assert len(render['methods'])==2 and all(len(frames)==9 for frames in render['methods'].values())
native=render['metrics']['P15-107-native']
baseline=render['metrics']['P15-101-original']
pure=render['metrics']['source_collar_continuous']
shape=render['metrics']['source_collar_silhouette']
render['visualReview']={
 'performed':True,
 'artSource':'one native 67.5-degree P0 white collar drawing projected to three source-view positions',
 'sourceRegistration':'source mask ECC affine alignment with 1024 RGBA texture and model-observed crease endpoints',
 'shapeAgreement':{v:{
  'nativeTargetIoU':item['mappedNativeTargetIoU'],
  'previousSharedMeshIoU':previous['actualTargetMaskIoU']['collar'][v]['IoU'],
  'leftCreaseMeanDriftPx':item['nativeObservedSeamDrift']['collar.left_inner_edge']['meanSourceLineDriftPx'],
  'rightCreaseMeanDriftPx':item['nativeObservedSeamDrift']['collar.right_inner_edge']['meanSourceLineDriftPx']}
  for v,item in source['views'].items()},
 'sourceColorAndStroke':'single canonical collar ink, shades and highlights across all 9 angles',
 'separateSilhouetteGate':'one variant clips the registered art to interpolated native-view collar ownership',
 'regionalMaxAdjacentRGBMAE':{part:{
   'P15-101':baseline[part]['maxAdjacentRGBMAE'],
   'P15-107-native':native[part]['maxAdjacentRGBMAE'],
   'P15-114-continuous':pure[part]['maxAdjacentRGBMAE'],
   'P15-114-silhouette':shape[part]['maxAdjacentRGBMAE']}
   for part in ('collar','bow','jewel')},
 'observedVisualFindings':{
  'collar':'affine registration matches collar silhouettes and native seam endpoints without the P15-113 protruding fabric artifact',
  'sourceArt':'all output collar folds use the same source-original inner crease identities and shading',
  'torso':'separately generated source-view jacket, gold trim and bow artwork still overlap during intermediate yaw',
  'underpaint':'existing six native hidden garment image sources remain in the correct depth order',
  'head':'preexisting P15-101 head and hair rendering continues unchanged'},
 'bestSourceRegistration':'P15-114 source_collar_continuous geometric correspondence',
 'selectedOverallVisualBenchmark':'P15-101 head_alpha_blend',
 'selectedThreeViewCostumeBenchmark':'P15-107 companion_direct_native_keys',
 'fullYawArtisticApproved':False,
 'nextDecisiveWork':'register jacket/gold trim and bow to one source geometry or develop source-owned per-part occlusion; validate actual 60–75 image motion before full 360° expansion'}
render['fullVisualApproved']=False
renderFile.write_text(json.dumps(render,indent=2,ensure_ascii=False)+'\n')
files=[
 'private-assets/exports/p15-114-collar-render/index.html',
 'private-assets/exports/p15-114-collar-render/single-source-collar-yaw-contact.jpg',
 'private-assets/exports/p15-114-collar-render/browser-desktop.png',
 'private-assets/exports/p15-114-collar-render/browser-mobile.png',
 'private-assets/exports/p15-114-collar-art/collar-registration-contact.jpg',
 'private-assets/exports/p15-113-canonical-topology/p15-114-source-collar-diagnostic.jpg',
 'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json']
for v,record in source['views'].items():
 files.extend([record['sourceTarget'],record['canonicalCollarPath'],
   record['nativeSilhouetteCollarPath'],record['targetCollarMaskPath']])
for mode,frames in review['methodFrames'].items():
 for relative in frames.values():
  files.append(str((P/'p15-114-collar-render'/relative).resolve().relative_to(R)))
for rec in review['animations'].values():files.append(rec['path'])
for filename in ('p15-108-stroke-qa.json','p15-110-vision-qa.json',
 'p15-111-source-qa.json','p15-113-topology-qa.json','p15-113-render-qa.json',
 'p15-114-source-qa.json','p15-114-render-qa.json','p15-114-review-qa.json',
 'p15-114-browser-qa.json'):
 files.append('evidence/'+filename)
for name in ('p15_114_collar_registration.py','p15_114_collar_render.py',
 'p15_114_review.py','p15_114_browser.cjs','p15_114_package.py',
 'test_p15_114_review.py'):
 files.append('scripts/'+name)
files=list(dict.fromkeys(files))
for name in files:
 if not (R/name).is_file():raise FileNotFoundError(name)
archive=P/'p0-character-001-p15-114-collar-source-correspondence.zip'
readme=('P0 Character | Source-owned three-view collar and seam correspondence\n'
 'Interactive review: private-assets/exports/p15-114-collar-render/index.html\n'
 'Original 67.5° source material and ink preserved; 60°/75° transparent collar art is view-aligned by native source mask geometry and two model-observed crease identities.\n'
 'Contains native-source and registered transparent 1024×1024 RGBA collars, original source masks, measured agreement and source-fold error, and all 9 animated yaw frames for two strategies.\n'
 'Source-original P0 assets, previous benchmark PNGs and GIFs, complete browser/unit validation and executable scripts are included.\n'
 'Single collar drawing geometry is technically verified; independent artwork for jacket/bow and full-turn aesthetic acceptance remain separate requirements.\n')
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for file in files:z.write(R/file,file)
with ZipFile(archive) as z:
 assert z.testzip() is None
 n=len(z.namelist())
taskFile=R/'tasks.json';task=json.loads(taskFile.read_text(encoding='utf-8'))
task['p15_114CollarSourceCorrespondence']={
 'status':'SOURCE_OWNED_THREE_VIEW_COLLAR_ART_AND_SEAM_GEOMETRY_VERIFIED',
 'characterId':'p0_character_001','sourceAngles':[60,67.5,75],
 'canonicalSourceAngle':67.5,
 'canonicalSourceSHA256':source['canonicalSourceSHA256'],
 'registeredNativeSourceCollarViews':{v:{'mappedMaskIoU':rec['mappedNativeTargetIoU'],
    'collarArtwork':rec['canonicalCollarPath'],
    'nativeMaskConstrainedArtwork':rec['nativeSilhouetteCollarPath'],
    'seamCorrespondence':rec['nativeObservedSeamDrift']}
    for v,rec in source['views'].items()},
 'meshShapeBenchmarkIoU':{v:previous['actualTargetMaskIoU']['collar'][v]['IoU'] for v in ('60','75')},
 'sourceOwnedInkSharedAcrossViews':True,
 'originalThreeIndependentNativeViewsRetained':True,
 'renderedCandidateFrames':sum(len(z) for z in render['methods'].values()),
 'referenceFrames':27,
 'regionalMaxAdjacentRGBMAE':render['visualReview']['regionalMaxAdjacentRGBMAE'],
 'engineeringGeometryVerified':True,'fullYawVisualAccepted':False,
 'unitTestsPass':19,'browserChecksPass':90,
 'selectedOverallVisualBenchmark':'P15-101 head_alpha_blend',
 'selectedNativeGarmentBenchmark':'P15-107 companion_direct_native_keys',
 'review':review['entry'],
 'package':{'path':str(archive.relative_to(R)),
            'sha256':sha(archive),'bytes':archive.stat().st_size,'entries':n},
 'evidence':['evidence/p15-114-source-qa.json','evidence/p15-114-render-qa.json',
             'evidence/p15-114-review-qa.json','evidence/p15-114-browser-qa.json'],
 'next':'Apply source-space registration and stable per-part visibility to jacket gold trim and bow, then compare full P0 yaw loop quality; prioritize artwork correspondence before further solver complexity'
}
task['status']='P15_114_COLLAR_SOURCE_CORRESPONDENCE_VERIFIED_FULL_ART_YAW_PENDING'
task['lastCompleted']='P15-114 matching original collar texture and folds in three source views, mask/line geometry validation, and 9-frame browser preview'
taskFile.write_text(json.dumps(task,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('PACKAGE',archive,'size',archive.stat().st_size,'entries',n,'sha256',sha(archive))
print('TASK',task['status'])
