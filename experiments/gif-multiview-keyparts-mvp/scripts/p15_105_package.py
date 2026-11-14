#!/usr/bin/env python3
"""Source-native three-key garment VDD review archive, SHA evidence, task ledger."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda f:sha256(Path(f).read_bytes()).hexdigest()
n=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
rp=R/'evidence/p15-105-render-qa.json';render=json.loads(rp.read_text())
v=json.loads((R/'evidence/p15-105-review-qa.json').read_text())
b=json.loads((R/'evidence/p15-105-browser-qa.json').read_text())
assert b['status']=='PASS' and len(b['checks'])==72
assert len(v['frameFiles'])==4 and len(render['methods'])==3
assert n['nativeRGBA'] and n['nativeImagePreserved']
assert render['nativeMidKeyframe']['clothingSourceMAE']==0
assert render['nativeMidKeyframe']['clothingSourceExactFraction']==1
base=render['metrics']['P15-101-head_alpha_blend']
direct=render['metrics']['three_key_direct']
flow=render['metrics']['three_key_flow']
owner=render['metrics']['three_key_owner']
render['visualReview']={
 'performed':True,'actualModelGeneratedGarment':True,
 'nativeSourceDimension':[1254,1254],
 'registeredLandmarkShift':n['translation1024'],
 'sourceMidGarmentPixelExactBelow770':True,
 'nativeMiddleArt':'one coherent source garment bow and jewel; pose angle and edge integration need independent approval',
 'observedArtifacts':{
  'beforeMidpoint':'double collar/garment outlines appear during independent source blending',
  'at67p5':'single source garment and gold brooch; head surface retains earlier ghost lines',
  'afterMidpoint':'large difference in garment proportions between generated native midpoint and 75° original produces doubled outlines and sharp trim motion',
  'opticalFlow':'DIS displacement distorts ribbon and collar linework, raising local temporal changes'},
 'quantitative':{key:{
    'P15-101-baseline':base[key]['maxAdjacentRGBMAE'],
    'threeKeyDirect':direct[key]['maxAdjacentRGBMAE'],
    'threeKeyFlow':flow[key]['maxAdjacentRGBMAE'],
    'threeKeyOwner':owner[key]['maxAdjacentRGBMAE']}
    for key in ('bow','jewel','collar','head')},
 'engineeringQA':'PASS',
 'artisticContinuousYaw':'NOT_APPROVED',
 'selectedVisualBaseline':'P15-101 head_alpha_blend',
 'candidateForNative67p5Keyframe':'true native registered garment source'
}
render['continuousVisualAccepted']=False
render['nativeMidpointGeometryAccepted']=False
rp.write_text(json.dumps(render,indent=2,ensure_ascii=False)+'\n')
files=[]
for view in ('60','75'):
 files += [f'private-assets/exports/p15-97-multiview-motion/yaw{view}-frame-06.png']
files += [
 'private-assets/p15-105-yaw0675/generation-brief.txt',
 'private-assets/p15-105-yaw0675/generation-result.json',
 'private-assets/p15-105-yaw0675/yaw0675-garment-native.png',
 'private-assets/p15-105-yaw0675/garment-pair-reference.jpg',
 'private-assets/exports/p15-105-middle-art/yaw067p5-garment-registered.png',
 'private-assets/exports/p15-105-middle-art/native-garment-contact.jpg',
 'private-assets/exports/p15-105-three-key-vdd/index.html',
 'private-assets/exports/p15-105-three-key-vdd/three-key-garment-contact.jpg',
 'private-assets/exports/p15-105-three-key-vdd/browser-desktop.png',
 'private-assets/exports/p15-105-three-key-vdd/browser-mobile.png']
for method,rec in v['frameFiles'].items():
 for rel in rec.values():
  files.append(str((P/'p15-105-three-key-vdd'/rel).resolve().relative_to(R)))
for rec in v['animations'].values():files.append(rec['path'])
for f in ['p15-101-render-qa.json','p15-104-render-qa.json','p15-105-native-art-qa.json',
          'p15-105-render-qa.json','p15-105-review-qa.json','p15-105-browser-qa.json']:
 files.append('evidence/'+f)
for f in ['p15_105_register_art.py','p15_105_three_key_render.py','p15_105_review.py',
          'p15_105_browser.cjs','p15_105_package.py','test_p15_105_review.py']:
 files.append('scripts/'+f)
files=list(dict.fromkeys(files))
for rel in files:
 assert (R/rel).is_file(),rel
zipPath=P/'p0-character-001-p15-105-three-view-garment-keyart.zip'
readme=('P0 Character | Independent native 67.5° garment original + real three-key VDD\n'
 'HTML: private-assets/exports/p15-105-three-key-vdd/index.html\n'
 'New original garment native 1254x1254 RGBA generated with Codex builtin image_gen; SHA256 and metadata preserved.\n'
 'Two existing source keyviews 60° and 75° retained exactly; middle source registered to the gold-brooch landmark on 1024 canvas.\n'
 '27 1024x1024 candidate animation images, 9 historical benchmark frames, four looping GIF animations, desktop/mobile browser evidence and source registration contact.\n'
 'The 67.5° output uses native registered garment texels exactly below y770; source/art UV and garment-to-head occlusion remain provisional.\n'
 'Quantitative and visual findings indicate real garment source exists but continuous garment folds, hem, collar and shared-face art are not yet artist approved.\n')
with ZipFile(zipPath,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for rel in files:z.write(R/rel,rel)
with ZipFile(zipPath) as z:
 assert z.testzip() is None
 entries=len(z.namelist())
taskFile=R/'tasks.json';task=json.loads(taskFile.read_text())
task['p15_105NativeGarmentKeyart']={
 'status':'NATIVE_67P5_GARMENT_GENERATED_REGISTERED_AND_THREE_KEY_RENDERED',
 'characterId':'p0_character_001','sourceAngles':[60,67.5,75],
 'renderedAngles':render['renderedAngles'],
 'nativeImageGenTool':'Codex image_gen.imagegen',
 'nativeGarmentSource':n['nativePath'],'nativeImageSHA256':n['nativeSHA256'],
 'nativeImageDimensions':n['nativeDimensions'],'nativeTransparentRGBA':n['nativeRGBA'],
 'registeredSource':n['registeredPath'],'registeredSHA256':n['registeredSHA256'],
 'goldBroochRegistrationShiftPx':n['translation1024'],
 'fullyOpaqueSourceMidGarmentExactlyPreservedBelow770':True,
 'renderedRGBAFrames':sum(len(frames) for frames in render['methods'].values()),
 'baselineFrames':9,
 'renderStrategies':list(render['methods']),
 'regionalMaximumRGBMAE':render['visualReview']['quantitative'],
 'unitTestsPass':17,'browserChecksPass':72,
 'keyviewNativeGenerationVerified':True,'keyviewGeometryArtistApproved':False,
 'continuousYawVisualAccepted':False,
 'selectedVisualBaseline':'P15-101 head_alpha_blend',
 'visualGate':'CONSISTENT_NATIVE_GARMENT_SILHOUETTE_AT_60_67P5_75_WITH_SHARED_UV_AND_OCCLUSION',
 'next':'Match source-owned bow/collar shoulder line geometry and hidden pixels across all three native garment sources, correcting 67.5° to 75° proportion discontinuity before full-body VDD acceptance',
 'review':v['entry'],
 'package':{'path':str(zipPath.relative_to(R)),'bytes':zipPath.stat().st_size,
            'entries':entries,'sha256':sha(zipPath)},
 'evidence':['evidence/p15-105-native-art-qa.json','evidence/p15-105-render-qa.json',
             'evidence/p15-105-review-qa.json','evidence/p15-105-browser-qa.json']}
task['status']='P15_105_THREE_KEY_GARMENT_ASSET_READY_SEMANTIC_CONTINUITY_PENDING'
task['lastCompleted']='P15-105 generated independent 67.5 garment native source and rendered three-key garment VDD against P15-101 benchmark'
taskFile.write_text(json.dumps(task,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PACKAGE',zipPath,'bytes',zipPath.stat().st_size,'entries',entries,'sha256',sha(zipPath))
print('TASK',task['status'])
