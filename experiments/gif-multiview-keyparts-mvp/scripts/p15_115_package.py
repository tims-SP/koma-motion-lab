#!/usr/bin/env python3
"""Deliver P0 native bow, jewel and lapel source ownership with visual comparisons."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile,ZIP_DEFLATED
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda path:sha256(Path(path).read_bytes()).hexdigest()
def get(name):return json.loads((R/'evidence'/name).read_text())
source=get('p15-115-source-qa.json')
renderFile=R/'evidence/p15-115-render-qa.json';render=json.loads(renderFile.read_text())
localFile=R/'evidence/p15-115-local-qa.json';local=json.loads(localFile.read_text())
review=get('p15-115-review-qa.json')
browser=get('p15-115-browser-qa.json')
p108=get('p15-108-stroke-qa.json')
p111=get('p15-111-source-qa.json')
p114=get('p15-114-source-qa.json')
assert browser['status']=='PASS' and len(browser['checks'])==162 and not browser['errors']
assert len(source['registered'])==4
assert len(render['methods'])==3 and len(local['methods'])==3
assert all(len(x)==9 for x in render['methods'].values())
assert all(len(x)==9 for x in local['methods'].values())
assert source['registered']['goldTrimRight']['75']['sourceOwner']=='nativeTarget'
assert source['registered']['bowFabric']['60']['sourceToNativeMaskIoU']>.87
assert source['registered']['bowFabric']['75']['sourceToNativeMaskIoU']>.79
assert source['registered']['jewel']['75']['sourceToNativeMaskIoU']>.92
assert len(review['methodFrames'])==9
baseline=local['metrics']['P15-101-original']
native=local['metrics']['P15-107-native']
rfull=render['metrics']['registered_full']
rmatte=render['metrics']['target_matte']
ink=local['metrics']['ink_core']
inner=local['metrics']['inner_fabric']
left=local['metrics']['ink_core_gold']
findings={
 'sourceArtwork':'actual native P0 registered art at 60, 67.5, 75 degrees',
 'singleSourceRoles':['bowFabric','jewel','goldTrimLeft'],
 'partialSourceOwner':'goldTrimRight retains 75-degree native artwork after visible-contour coverage loss',
 'sourceMaterialCorrespondenceIoU':{role:{view:round(item['sourceToNativeMaskIoU'],5)
  for view,item in rows.items()} for role,rows in source['registered'].items()},
 'completeRecomposition':'complete source-layer rebuild under-exposes the source-owned right side jacket and causes white fabric gaps',
 'localRepair':'bounded source-ink patch preserves complete original body/sleeve and avoids broad background replacement',
 'frameContinuity':{roi:{
   'P15-101':baseline[roi]['maxAdjacentRGBMAE'],
   'P15-107-native':native[roi]['maxAdjacentRGBMAE'],
   'P15-115-full':rfull[roi]['maxAdjacentRGBMAE'],
   'P15-115-matte':rmatte[roi]['maxAdjacentRGBMAE'],
   'P15-115-inkCore':ink[roi]['maxAdjacentRGBMAE'],
   'P15-115-innerFabric':inner[roi]['maxAdjacentRGBMAE'],
   'P15-115-inkCoreGold':left[roi]['maxAdjacentRGBMAE']}
   for roi in ('bow','collar','goldTrim','jewel')},
 'visualFindings':{
  'sourceBow':'native 67.5-degree ribbon folds transfer to alternate yaw in observed native material region',
  'sourceJewel':'shared 67.5-degree gold center retains a single facet source, with original per-view background underneath',
  'shoulderTrim':'left lapel registered source geometry is partly stable; right 75-degree trim visibility changes ownership',
  'garmentBackground':'full recomposition exposes unsupported pixel regions at right jacket and white shirt',
  'boundedPatch':'partial source-ink overlay avoids the broader transparent gaps but retains original side silhouettes and some doubled ink',
  'head':'existing head/hair VDD remains P15-101'},
 'selectedOverallVisualBenchmark':'P15-101 head_alpha_blend',
 'selectedNativeGarmentCandidate':'P15-107 companion_direct_native_keys',
 'sourceGeometryEngineeringQA':'PASS',
 'continuousYawArtistApproved':False,
 'nextDecisiveWork':'draw physically consistent right lapel/shoulder and bow underlays per view with canonical ArtMesh; verify head/torso motion and animation on a 0-180-degree interval before extending 360-degree target'}
render['visualReview']=findings
local['visualReview']=findings
render['fullYawVisualApproved']=False;local['fullVisualAccepted']=False
renderFile.write_text(json.dumps(render,ensure_ascii=False,indent=2)+'\n')
localFile.write_text(json.dumps(local,ensure_ascii=False,indent=2)+'\n')
files=[
 'private-assets/exports/p15-115-review/index.html',
 'private-assets/exports/p15-115-review/browser-desktop.png',
 'private-assets/exports/p15-115-review/browser-mobile.png',
 'private-assets/exports/p15-115-component-art/component-registration-contact.jpg',
 'private-assets/exports/p15-115-component-render/component-yaw-contact.jpg',
 'private-assets/exports/p15-115-local-patch/localized-garment-contact.jpg',
 'private-assets/exports/p15-114-collar-art/collar-registration-contact.jpg',
 'private-assets/exports/p15-107-source-patches/consistent-garment-contact.jpg']
for role,views in source['registered'].items():
 for v,record in views.items():
  files.extend([record['source'],record['registeredPath'],record['targetMask']])
for view,record in p108['views'].items():
 files.append(record['source'])
 for role in ('background','goldTrim','collarWhite','bowFabric','jewel'):
  files.append(record['layers'][role]['texturePath'])
 for role in ('bow','collar'):
  files.append(p111['layers'][view][role]['hiddenOnlyPath'])
for view,record in p114['views'].items():
 files.append(record['canonicalCollarPath'])
for method,frames in review['methodFrames'].items():
 for relative in frames.values():
  files.append(str((P/'p15-115-review'/relative).resolve().relative_to(R)))
for rec in review['animations'].values():files.append(rec['path'])
for name in ('p15-101-render-qa.json','p15-107-companion-qa.json','p15-108-stroke-qa.json',
 'p15-111-source-qa.json','p15-114-source-qa.json','p15-114-render-qa.json',
 'p15-115-source-qa.json','p15-115-render-qa.json','p15-115-local-qa.json',
 'p15-115-review-qa.json','p15-115-browser-qa.json'):
 files.append('evidence/'+name)
for name in ('p15_115_component_registration.py','p15_115_component_render.py',
 'p15_115_local_patch.py','p15_115_review.py','p15_115_browser.cjs',
 'p15_115_package.py','test_p15_115_review.py'):
 files.append('scripts/'+name)
files=list(dict.fromkeys(files))
for relative in files:
 if not (R/relative).is_file():raise FileNotFoundError(relative)
archive=P/'p0-character-001-p15-115-garment-source-owner-review.zip'
readme=('P0 Character | Source-owned 60–75° ribbon, jewel, shoulder trim art registration\n'
 'Open: private-assets/exports/p15-115-review/index.html\n'
 'Single genuine 67.5° bow and jewel material and shared left lapel ink registered to three native source views.\n'
 'Native 75° right lapel retains physical source art where the trim becomes partially hidden.\n'
 'Source-owned component images, original drawings, actual nine-angle rendered full-character frames and loops, RGB timing comparisons, browser screenshots and test evidence included.\n'
 'Localized source-owned patches preserve torso backgrounds. Full composition experiments and native P15-101/107/114 reference frames allow direct visual inspection.\n'
 'Engineering checks establish source provenance and mask geometry. Complete artistic acceptance requires corresponding hidden torso and material surfaces.\n')
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for f in files:z.write(R/f,f)
with ZipFile(archive) as z:
 assert z.testzip() is None
 count=len(z.namelist())
taskFile=R/'tasks.json';tasks=json.loads(taskFile.read_text(encoding='utf-8'))
tasks['p15_115GarmentSourceOwnership']={
 'status':'SOURCE_OWNED_BOW_JEWEL_SHOULDER_COMPONENT_REGISTRATION_VERIFIED',
 'characterId':'p0_character_001',
 'sourceAngles':[60,67.5,75],
 'canonicalSourceView':67.5,
 'registeredRoles':source['roles'],
 'sourceOwnerByAngle':{role:{view:z['sourceOwner'] for view,z in rows.items()} for role,rows in source['registered'].items()},
 'sourceToNativeMaterialMaskIoU':findings['sourceMaterialCorrespondenceIoU'],
 'nativeArtworkSHA256':source['sourceArtSHA256'],
 'candidateCompleteRenderedFrames':sum(len(x) for x in render['methods'].values()),
 'candidateLocalRenderedFrames':sum(len(x) for x in local['methods'].values()),
 'referenceRenderedFrames':27,
 'fullCharacterVisualContinuity':findings['frameContinuity'],
 'selectedVisualBenchmark':'P15-101 head_alpha_blend',
 'selectedNativeGarmentBenchmark':'P15-107 companion_direct_native_keys',
 'sourceGeometryVerified':True,
 'localSourceArtPreservesFullBodyOutsidePatch':True,
 'fullYawVisualAccepted':False,
 'unitTestsPass':22,'previousRegressionTestsPass':19,
 'browserChecksPass':162,
 'review':review['entry'],
 'package':{'path':str(archive.relative_to(R)),'sha256':sha(archive),
            'bytes':archive.stat().st_size,'entries':count},
 'evidence':['evidence/p15-115-source-qa.json','evidence/p15-115-render-qa.json',
   'evidence/p15-115-local-qa.json','evidence/p15-115-review-qa.json','evidence/p15-115-browser-qa.json'],
 'next':'Resolve actual right torso/trim visibility ownership and bow side silhouette correspondence at source-art level before replacing P15-107 frame composition. Retain existing P15-101/107 visual baselines.'
}
tasks['status']='P15_115_COMPONENT_SOURCE_REGISTRATION_VERIFIED_FULL_VISUAL_TURN_PENDING'
tasks['lastCompleted']='P15-115 bow and gold source-art registration, local garment compositing and full-character browser comparisons'
taskFile.write_text(json.dumps(tasks,indent=2,ensure_ascii=False)+'\n')
print('PACKAGE',archive,'bytes',archive.stat().st_size,'entries',count,'sha256',sha(archive),flush=True)
print('TASK',tasks['status'],flush=True)
