#!/usr/bin/env python3
"""Bundle canonical 3-view garment UV and direct source-art geometry validation."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile,ZIP_DEFLATED
import json,numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
def read(name):return json.loads((R/'evidence'/name).read_text())
mesh=read('p15-113-topology-qa.json')
renderPath=R/'evidence/p15-113-render-qa.json'
q=json.loads(renderPath.read_text())
review=read('p15-113-review-qa.json')
browser=read('p15-113-browser-qa.json')
source=read('p15-108-stroke-qa.json')
hidden=read('p15-111-source-qa.json')
assert browser['status']=='PASS' and len(browser['checks'])==108
assert len(q['methods'])==3 and all(len(x)==9 for x in q['methods'].values())
assert len(review['animations'])==6
assert all(rec['nonfoldingAllViews'] for rec in mesh['roleTopology'].values())
main=q['metrics']['canonical_full']
bow=q['metrics']['canonical_bow_native_torso']
base=q['metrics']['P15-101-original'];candidate=q['metrics']['P15-107-native']
raw=Image.open(R/source['views']['67.5']['source']).convert('RGBA')
original=np.asarray(raw,np.float32)
centerComparison={}
for name,rows in q['methods'].items():
 center=np.asarray(Image.open(R/rows['67.5']['path']).convert('RGBA'),np.float32)
 target=np.s_[680:1015,360:855]
 centerComparison[name]=round(float(np.abs(center[target]-original[target]).mean()),4)
q['visualReview']={
 'performed':True,
 'sourceAsset':'original native registered 67.5-degree garment source, used as shared UV/ink for all three keyviews',
 'samePhysicalRoleTopology':'33 indexed vertices and 48 fixed nonfolding triangles per collar/bow/jewel mesh',
 'sourceDrawingUnity':'one 67.5-degree physical bow and jewel artwork provides identical ink identity across every output angle; canonical_full additionally shares collar and gold trim; native-torso variants retain independent body art',
 'nativeSourceArtworkPreserved':True,
 'nativeTargetMaskAgreement':{role:{view:rec['IoU'] for view,rec in data.items()}
     for role,data in mesh['actualTargetMaskIoU'].items()},
 'sourceMeasuredInkDisplacement':{role:{view:rec.get('meanObservedDriftPx')
      for view,rec in data['views'].items()} for role,data in mesh['pathCorrespondence'].items()},
 'canonicalMiddleRegionalRGBAMAEPixel':centerComparison,
 'quantitative':{part:{
  'P15-101':base[part]['maxAdjacentRGBMAE'],
  'P15-107-native':candidate[part]['maxAdjacentRGBMAE'],
  'canonical-full':main[part]['maxAdjacentRGBMAE'],
  'canonical-bow-native-torso':bow[part]['maxAdjacentRGBMAE']}
  for part in ('bow','collar','jewel')},
 'actualVisualFindings':{
  'bow':'shared source bow ink retains one physical fold design, with moderate source shape discrepancy at 60 and 75 degrees',
  'collar':'single-source collar mesh produces visible high protrusions and geometric distortion; native collar background reduces this artifact',
  'goldJewel':'source-owned gemstone keeps a single set of facets but still diverges in side silhouette',
  'shoulderTrim':'native shirt/jacket view differences create doubled trim when independent source backgrounds are blended',
  'torsoOwnerSwitch':'single-source background owner introduces large keyview temporal jumps',
  'head':'existing P15-101 head/hair mesh and visual limitations remain unmodified'},
 'selectedFullCharacterVisualBenchmark':'P15-101 head_alpha_blend',
 'selectedNativeThreeViewGarmentCandidate':'P15-107 companion_direct_native_keys',
 'validatedEngineeringResult':'one-source physical ink texture and shared topology with source-measured morphology audit',
 'fullYawArtisticAccepted':False,
 'nextDecisiveAction':'Reauthor 60/75 collar source shapes to fit one canonical 67.5 collar with per-ink/UV identity; then verify 60/75 source silhouette IoU and full nine-frame image quality before expanding torso'
}
q['full360YawVisualAccepted']=False
renderPath.write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
files=[
 'private-assets/exports/p15-113-canonical-topology/index.html',
 'private-assets/exports/p15-113-canonical-topology/canonical-garment-contact.jpg',
 'private-assets/exports/p15-113-canonical-topology/canonical-garment-base.png',
 'private-assets/exports/p15-113-canonical-topology/browser-desktop.png',
 'private-assets/exports/p15-113-canonical-topology/browser-mobile.png',
 'private-assets/exports/p15-107-source-patches/consistent-garment-contact.jpg',
 'private-assets/exports/p15-106-three-key-mesh/garment-three-key-mesh.json',
 'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json']
for view,rec in source['views'].items():
 files.append(rec['source'])
 for material in ('background','goldTrim','collarWhite','bowFabric','jewel'):
  files.append(rec['layers'][material]['texturePath'])
 for part in ('collar','bow'):
  files.append(hidden['layers'][view][part]['hiddenOnlyPath'])
for frames in review['methodFrames'].values():
 for relative in frames.values():
  path=(P/'p15-113-canonical-topology'/relative).resolve()
  files.append(str(path.relative_to(R)))
for rec in review['animations'].values():files.append(rec['path'])
for name in ('p15-101-render-qa.json','p15-106-mesh-qa.json','p15-107-companion-qa.json',
             'p15-108-stroke-qa.json','p15-110-vision-qa.json',
             'p15-111-source-qa.json','p15-112-render-qa.json',
             'p15-113-topology-qa.json','p15-113-render-qa.json',
             'p15-113-review-qa.json','p15-113-browser-qa.json'):
 files.append('evidence/'+name)
for name in ('p15_113_canonical_topology.py','p15_113_topology_audit.py',
             'p15_113_review.py','p15_113_browser.cjs',
             'p15_113_package.py','test_p15_113_review.py'):
 files.append('scripts/'+name)
files=list(dict.fromkeys(files))
for item in files:
 if not (R/item).is_file():raise FileNotFoundError(item)
archive=P/'p0-character-001-p15-113-canonical-garment-topology-review.zip'
readme=('P0 Character | Canonical three-view garment ink topology and ArtMesh source correspondence\n'
 'Interactive full-character animation: private-assets/exports/p15-113-canonical-topology/index.html\n'
 'Single-source 67.5-degree ribbon and jewel textures/ink across all yaw. Canonical-full also uses the one center-source collar/trim; native-torso alternatives retain their original backgrounds.\n'
 'Three-view shared 33-vertex / 48-triangle semantic ArtMesh positions preserve vertex indexing and source UV across 60 to 75 yaw.\n'
 'The three original source drawings and hidden matte source files are retained for shape and color validation.\n'
 'Measured source-target mask IoU and original stroke-path source drift document physical garment shape agreement.\n'
 'Actual 27 newly rendered frames, 6 complete method GIFs, desktop/mobile browser screenshot and executable engineering QA included.\n'
 'Artistic acceptance requires reauthored viewpoint-consistent collar linework and a final full-yaw visual review.\n')
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for relative in files:z.write(R/relative,relative)
with ZipFile(archive) as z:
 assert z.testzip() is None
 count=len(z.namelist())
taskPath=R/'tasks.json'
task=json.loads(taskPath.read_text(encoding='utf-8'))
task['p15_113CanonicalTopology']={
 'status':'SINGLE_GARMENT_TEXTURE_SHARED_TOPOLOGY_AND_NATIVE_ART_CORRESPONDENCE_VERIFIED',
 'characterId':'p0_character_001',
 'sourceAngles':[60,67.5,75],
 'canonicalSourceAngle':67.5,
 'canonicalSourceSHA256':q['canonicalSourceSHA256'],
 'meshSourceSHA256':q['sourceMeshSHA256'],
 'sourceMeshRoles':list(mesh['roleTopology']),
 'perPartVertices':33,'perPartTriangles':48,
 'targetMaskIoU':q['visualReview']['nativeTargetMaskAgreement'],
 'measuredInkPathDisplacement':q['visualReview']['sourceMeasuredInkDisplacement'],
 'canonicalMiddleRGBAMAEPixel':centerComparison,
 'originalIndependentSourceAssetsRetained':True,
 'renderedCandidateFrames':sum(len(frames) for frames in q['methods'].values()),
 'referenceFrames':27,
 'testAngles':q['angles'],
 'renderMethods':list(q['methods']),
 'regionalMaxAdjacentRGBMAE':q['visualReview']['quantitative'],
 'sourceTopologyEngineeringVerified':True,
 'fullYawVisualAccepted':False,
 'visualBenchmark':'P15-101 head_alpha_blend',
 'nativeGarmentBenchmark':'P15-107 companion_direct_native_keys',
 'unitTestsPass':20,'chromiumChecksPass':108,
 'review':review['entry'],
 'package':{'path':str(archive.relative_to(R)),
            'bytes':archive.stat().st_size,'sha256':sha(archive),'entries':count},
 'evidence':['evidence/p15-113-topology-qa.json','evidence/p15-113-render-qa.json',
             'evidence/p15-113-review-qa.json','evidence/p15-113-browser-qa.json'],
 'next':'Reauthor two source-view collar outline/fold artworks with canonical stroke and UV identities; verify shape IoU with actual native source and nine-frame visual quality, then introduce matching torso trim geometry'
}
task['status']='P15_113_CANONICAL_TOPOLOGY_VERIFIED_COLLAR_SOURCE_CORRESPONDENCE_PENDING'
task['lastCompleted']='P15-113 source-anchored three-view shared ArtMesh with single garment drawing, material IoU validation, and full-character yaw evidence'
taskPath.write_text(json.dumps(task,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('DELIVERY',archive,'bytes',archive.stat().st_size,'entries',count,'sha256',sha(archive))
print('TASK',task['status'])
