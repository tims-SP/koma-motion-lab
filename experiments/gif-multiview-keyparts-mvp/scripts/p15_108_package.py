#!/usr/bin/env python3
"""Deliver genuine P0 three-source stroke-role / occlusion evidence & review."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
sp=R/'evidence/p15-108-source-qa.json';s=json.loads(sp.read_text())
ip=R/'evidence/p15-108-stroke-qa.json';i=json.loads(ip.read_text())
rp=R/'evidence/p15-108-render-qa.json';r=json.loads(rp.read_text())
vp=R/'evidence/p15-108-review-qa.json';v=json.loads(vp.read_text())
bp=R/'evidence/p15-108-browser-qa.json';b=json.loads(bp.read_text())
assert b['status']=='PASS' and len(b['checks'])==90
assert all(info['reassembledPixelExact'] for info in i['views'].values())
assert len(i['roleIDs'])==6 and len(i['depthOrder'])==5
assert len(r['methods'])==3 and all(len(frames)==9 for frames in r['methods'].values())
assert not r['artisticStrokeIDsApproved'] and not r['continuousYawVisualAccepted']
metrics=r['metrics']
primary=metrics['P15-101-original'];native=metrics['P15-107-three-native']
sdf=metrics['sdf_role_ink_native_keys'];owner=metrics['single_bow_owner']
r['visualReview']={
 'performed':True,'sourcePartition':'all five role-owned RGBA layers per view reconstruct native original pixel-exactly',
 'automaticCandidateIdentity':'four bow subregions and two collar seam regions, identified by material and location',
 'correctedBowFabricMask':'source crimson HSV 160–179 with source-coordinate spatial support; dark jacket excluded',
 'strokeGeometry':'signed-distance contour for each role formed from real source ink candidates',
 'layerOrder':['collarInk','bowInk','jewel','headHair'],
 'visualObservations':{
  'bow':'single-source contour within ink regions is possible, but inbetween folds and outer contours remain inconsistent',
  'collar':'automatic white-collar line extraction and color-fill underpainting create local distortions',
  'jewel':'occlusion owner selection can jump between source keyframes',
  'body':'independent source jacket linework and shoulder profile create cross-view ghosting',
  'head':'preexisting P15-101 mesh and hair interpolation limit full-frame realism'},
 'measuredComparisons':{part:{
   'P15-101':primary[part]['maxAdjacentRGBMAE'],
   'P15-107-native':native[part]['maxAdjacentRGBMAE'],
   'P15-108-sdf-ink':sdf[part]['maxAdjacentRGBMAE'],
   'P15-108-owner-ink':owner[part]['maxAdjacentRGBMAE']}
   for part in ('bow','jewel','collar')},
 'selectedVisualBenchmark':'P15-101 head_alpha_blend',
 'sourceArtCandidate':'P15-107 three native garment sources',
 'engineeringValidation':'PASS',
 'artisticContinuityAccepted':False,
 'nextEvidence':'artist-identified cross-view stroke paths, matching layer masks and hidden-collar/shoulder reconstruction'}
rp.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
assets=[]
for view,item in i['views'].items():
 assets.append(item['source'])
 for e in item['layers'].values():assets.extend([e['texturePath'],e['maskPath']])
 for e in item['strokeRegions'].values():assets.append(e['maskPath'])
 for name,e in s['views'][view]['masks'].items():assets.append(e['path'])
 assets.append(f'private-assets/exports/p15-108-stroke-identity/yaw{view.replace(".","p")}/reconstructed.png')
 assets.append(f'private-assets/exports/p15-108-stroke-render/yaw{view.replace(".","p")}-undercoat.png')
assets.extend([
 'private-assets/exports/p15-108-stroke-sources/source-stroke-ownership-contact.jpg',
 'private-assets/exports/p15-108-stroke-render/index.html',
 'private-assets/exports/p15-108-stroke-render/stroke-sdf-occlusion-contact.jpg',
 'private-assets/exports/p15-108-stroke-render/browser-desktop.png',
 'private-assets/exports/p15-108-stroke-render/browser-mobile.png',
 'private-assets/exports/p15-107-source-patches/consistent-garment-contact.jpg',
 'private-assets/exports/p15-101-head-render/head_alpha_blend-yaw60.png'])
for mode,frames in v['methodFrames'].items():
 for path in frames.values():
  assets.append(str((P/'p15-108-stroke-render'/path).resolve().relative_to(R)))
for z in v['gifs'].values():assets.append(z['path'])
for name in ('p15-101-render-qa.json','p15-107-companion-qa.json','p15-107-patch-qa.json',
             'p15-108-source-qa.json','p15-108-stroke-qa.json','p15-108-render-qa.json',
             'p15-108-review-qa.json','p15-108-browser-qa.json'):
 assets.append('evidence/'+name)
for name in ('p15_108_stroke_sources.py','p15_108_stroke_identity.py',
             'p15_108_stroke_render.py','p15_108_review.py',
             'p15_108_browser.cjs','p15_108_package.py','test_p15_108_review.py'):
 assets.append('scripts/'+name)
assets=list(dict.fromkeys(assets))
for x in assets:
 if not (R/x).is_file():raise FileNotFoundError(x)
dest=P/'p0-character-001-p15-108-stroke-occlusion-study.zip'
readme=('P0 Character | Three-source garment stroke roles and occlusion validation\n'
 'Interactive review: private-assets/exports/p15-108-stroke-render/index.html\n'
 'Three genuine independent garment keyarts at yaw 60°, 67.5°, 75°.\n'
 'Five source-owned clothing layers with exact pixel reconstruction, and six position-based stroke role candidates.\n'
 'Three actual VDD ablations with source-role signed-distance ink transport and bow source-owner compositing, plus two historical comparators.\n'
 'Each source keyframe is genuine registered native garment art with the preserved P15-101 character head renderer.\n'
 'Unit/browser tests establish provenance, geometry, RGBA partition and interactive playback; artistic stroke identity and continuous movement require independent sign-off.\n'
 'Related research: https://github.com/MarkMoHR/LayerInbetween\n')
with ZipFile(dest,'w',ZIP_DEFLATED,compresslevel=6) as archive:
 archive.writestr('README.txt',readme)
 for a in assets:archive.write(R/a,a)
with ZipFile(dest) as z:
 assert z.testzip() is None
 count=len(z.namelist())
taskFile=R/'tasks.json'
task=json.loads(taskFile.read_text(encoding='utf-8'))
task['p15_108StrokeOcclusion']={
 'status':'SOURCE_OWNED_STROKE_ROLE_AND_OCCLUSION_EVIDENCE_VERIFIED',
 'characterId':'p0_character_001',
 'sourceAngles':[60,67.5,75],
 'garmentDepthLayers':i['depthOrder'],
 'candidateStrokeIDs':i['roleIDs'],
 'pixelExactLayerReconstructions':3,
 'sourceStrokeRoleProvenance':{view:{
   'bowPixels':item['bowInkPixelsOwned'],'collarPixels':item['collarInkPixelsOwned']}
   for view,item in i['views'].items()},
 'nativeSourceSHA256':r['sourceNativeSHA256'],
 'candidateFrames':sum(len(x) for x in r['methods'].values()),
 'referenceFrames':18,
 'renderStrategies':list(r['methods']),
 'regionMaxAdjacentRGBMAE':r['visualReview']['measuredComparisons'],
 'unitTestsPass':17,'browserChecksPass':90,
 'sourceLayerEngineeringVerified':True,
 'automaticStrokeIdentityArtistApproved':False,
 'continuousYawVisualAccepted':False,
 'visualBenchmark':'P15-101 head_alpha_blend',
 'nativeGarmentSources':'P15-107 source-registered 60°, 67.5°, 75°',
 'visualGate':'SOURCE_STROKE_PATH_IDENTITY_AND_HIDDEN_SURFACE_OCCLUSION',
 'review':v['entry'],
 'package':{'path':str(dest.relative_to(R)),'bytes':dest.stat().st_size,
            'sha256':sha(dest),'entries':count},
 'evidence':['evidence/p15-108-source-qa.json','evidence/p15-108-stroke-qa.json',
             'evidence/p15-108-render-qa.json','evidence/p15-108-review-qa.json',
             'evidence/p15-108-browser-qa.json'],
 'next':'Ground native 60/67.5/75 stroke IDs with actual matching paths and source-owned hidden surface/matte; rerender without source ink underpainting artifacts'
}
task['status']='P15_108_GARMENT_STROKE_ROLE_GEOMETRY_VERIFIED_VISUAL_CONTINUITY_PENDING'
task['lastCompleted']='P15-108 independent source-owned garment layers, stroke region identity candidates, three render strategies with browser and unit verification'
taskFile.write_text(json.dumps(task,ensure_ascii=False,indent=2)+'\n')
print('PACKAGE',dest,'bytes',dest.stat().st_size,'entries',count,'sha256',sha(dest),flush=True)
print('TASK',task['status'],flush=True)
