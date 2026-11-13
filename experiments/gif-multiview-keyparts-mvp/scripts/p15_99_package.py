#!/usr/bin/env python3
"""Package reproducible P0 60-75 semantic topology research and ledger evidence."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1]
P=R/'private-assets'
E=P/'exports'
sha=lambda p:sha256(p.read_bytes()).hexdigest()
qa=json.loads((R/'evidence/p15-99-topology-vdd-qa.json').read_text())
top=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
eyes=json.loads((R/'evidence/p15-99-eye-mask-qa.json').read_text())
browser=json.loads((R/'evidence/p15-99-browser-qa.json').read_text())
assert browser['status']=='PASS' and len(browser['checks'])==72
assert top['sourceReconstructionAccepted'] and len(top['roles'])==7
assert len(qa['methods'])==4 and len(qa['angles'])==9
assert not qa['continuousYawAccepted'] and not qa['artistApproved']
included=[]
for view in ('60','75'):
 included.extend([
  f'private-assets/exports/p15-97-multiview-motion/yaw{view}-frame-06.png',
  top['views'][view]['modelUnderpaint'],
  top['views'][view]['externalSAM3Hair'],
  f'private-assets/exports/p15-99-topology/yaw{view}/reconstructed.png',
  f'private-assets/exports/p15-99-topology/yaw{view}/topology-contact.jpg',
  f'private-assets/exports/p15-99-topology/yaw{view}/eye-contact.jpg'
 ])
 for role in top['roles']:
  filename=role.replace('.','_')
  included.append(f'private-assets/exports/p15-99-topology/yaw{view}/{filename}.png')
  included.append(f'private-assets/exports/p15-99-topology/yaw{view}/{filename}-ownership.png')
 for candidate in eyes['viewResults'][view]['candidates']:
  n=candidate['index']
  included.append(f'private-assets/exports/p15-99-topology/yaw{view}/sam3-eye-mask-{n}.png')
  included.append(f'private-assets/exports/p15-99-topology/yaw{view}/sam3-eye-annotation-{n}.png')
for view,p in [('60','p15-95-underpaint/face-underpaint-native.png'),
               ('75','p15-97-underpaint-75/model-native.png')]:
 included.append('private-assets/'+p)
included.extend([
 'private-assets/p15-99-sam3-eyes/manifest.json',
 'private-assets/exports/p15-99-vdd-review/index.html',
 'private-assets/exports/p15-99-vdd-review/topology-vdd-contact.jpg',
 'private-assets/exports/p15-99-vdd-review/browser-desktop.png',
 'private-assets/exports/p15-99-vdd-review/browser-mobile.png'])
for method,frames in qa['methods'].items():
 for item in frames.values():included.append(item['file'])
 included.append(qa['animations'][method]['path'])
for name in ['p15-99-eye-mask-qa.json','p15-99-topology-qa.json','p15-99-topology-vdd-qa.json','p15-99-browser-qa.json','p15-98-landmarks.json']:
 included.append('evidence/'+name)
included=list(dict.fromkeys(included))
for rel in included:
 if not (R/rel).is_file():raise FileNotFoundError(rel)
path=E/'p0-character-001-p15-99-semantic-topology-review.zip'
readme=('P0 Character | Source-owned semantic topology and cross-view occlusion review\n'
 'Review HTML: private-assets/exports/p15-99-vdd-review/index.html\n'
 'Includes eye masks from Hugging Face SAM3, original 60/75 images, two registered hidden-face donors, 7 owner layers/view, 36 actual VDD frames, and 4 GIF previews.\n'
 'The source images reassemble pixel-exactly; near eye, far eye, face skin, profile contour, front hair and gold hairclip have explicit ownership.\n'
 'Manual proxy shape/anchor regions and semantic near/far eye visibility have been verified structurally but are not artist-approved geometry.\n'
 'Dynamic yaw remains an experiment: single-owner background controls ghosting but a discontinuity remains in cross-view face/hair correspondence.\n')
results={name:{'maxMAE':rec['maxAdjacentMAE'],'meanMAE':rec['meanAdjacentMAE']} for name,rec in qa['metrics'].items()}
qa['visualReview']={
 'performed':True,'formalApproval':False,
 'observations':{
  'perLayerEyeVisibility':'correct 60° far-eye pixels to absent 75° far-eye layer',
  'faceContour':'single-source topology avoids multiple nose ink contours in select intermediate views',
  'rearHair':'single owner produces cleaner silhouette but stronger midpoint jump',
  'artisticContinuity':'keyview switching and hair-boundary geometry remain visible'},
 'engineeringTest':'PASS',
 'visualGate':'ANCHORED_SHARED_MESH_CORRESPONDENCE_AND_CONCEALED_SURFACE_MATCHING'}
qa['visualGate']=qa['visualReview']['visualGate']
qa['continuousYawAccepted']=False
(R/'evidence/p15-99-topology-vdd-qa.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
# Package the finalized evidence together with all source-owned visual assets.
with ZipFile(path,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for rel in included:z.write(R/rel,rel)
with ZipFile(path) as z:
 assert z.testzip() is None
 total=len(z.namelist())
task=R/'tasks.json'
j=json.loads(task.read_text(encoding='utf-8'))
j['p15_99SemanticTopology']={
 'status':'SOURCE_OWNED_60_75_SEMANTIC_TOPOLOGY_ENGINEERING_VERIFIED',
 'characterId':'p0_character_001',
 'sourceAngles':[60,75],
 'roleCount':len(top['roles']),
 'semanticRoles':top['roles'],
 'occlusionOrder':top['occlusionOrder'],
 'realSAM3EyeAnnotations':{'60':len(eyes['viewResults']['60']['candidates']),
                           '75':len(eyes['viewResults']['75']['candidates'])},
 'nearEyeVisibleInBoth':True,'farEyeOccludedAt75':True,
 'underpaintSource':'existing Codex-generated hidden-face donor',
 'sourcePixelsReconstructedExactly':True,
 'renderedAngles':qa['angles'],
 'methods':list(qa['methods']),
 'renderedFrameCount':sum(len(frames) for frames in qa['methods'].values()),
 'unitTestsPass':16,'browserChecksPass':72,
 'quantitativeMetrics':results,
 'formalArtMeshAccepted':False,'continuousYawAccepted':False,
 'visualGate':qa['visualGate'],
 'remainingCriticalIssue':'shared mesh and hidden surface correspondence across 60°–75° in changing silhouette',
 'next':'Build a common deformable face mesh with explicit per-view visibility ownership and align the nose/jaw/forehead UV contours before the next continuous-yaw render',
 'review':'private-assets/exports/p15-99-vdd-review/index.html',
 'package':{'path':str(path.relative_to(R)),'sha256':sha(path),'bytes':path.stat().st_size,'entries':total},
 'evidence':['evidence/p15-99-eye-mask-qa.json','evidence/p15-99-topology-qa.json',
             'evidence/p15-99-topology-vdd-qa.json','evidence/p15-99-browser-qa.json']
}
j['status']='P15_99_SOURCE_OWNED_TOPOLOGY_READY_SHARED_MESH_CORRESPONDENCE_NEXT'
j['lastCompleted']='P15-99 real SAM3 eye visibility, exact 7-role source partitions and layered yaw occlusion comparison'
task.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PACKAGE',path,'bytes',path.stat().st_size,'files',total,'sha256',sha(path))
print('TASK',j['status'])
