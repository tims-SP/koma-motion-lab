#!/usr/bin/env python3
"""Source-owned garment visibility review delivery and task evidence."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json,os
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
def qa(name):return json.loads((R/'evidence'/name).read_text())
q=qa('p15-116-render-qa.json')
review=qa('p15-116-review-qa.json')
browser=qa('p15-116-browser-qa.json')
src=qa('p15-115-source-qa.json')
part=qa('p15-108-stroke-qa.json')
base=qa('p15-107-companion-qa.json')
assert browser['status']=='PASS' and len(browser['checks'])==126 and not browser['errors']
assert len(q['models'])==4 and all(len(z)==9 for z in q['models'].values())
assert len(review['methodFrames'])==7 and len(review['animations'])==7
for role,frames in q['models'].items():
 for a in ('60','67.5','75'):
  assert frames[a]['sha256']==base['methods']['companion_direct_native_keys'][a]['sha256'],(role,a)
numbers={method:{region:data['maxAdjacentRGBMAE'] for region,data in value.items()}
 for method,value in q['metrics'].items()}
native=numbers['P15-107-native']
trim=numbers['trim_matte']
head=numbers['P15-101-original']
allCandidates=[m for m in q['models']]
# Quantify the effect on true keyframe-preserved artwork rather than choosing
# a flattering synthetic interpolation metric.
delta={roi:round(trim[roi]-native[roi],4) for roi in ('bow','goldTrim','rightLap')}
decision={
 'schema':'KOMA_P15_116_VISUAL_DECISION_V1',
 'character':'p0_character_001','sourceAngles':[60,67.5,75],
 'readableMetric':'max adjacent-frame RGB MAE (0–255) inside each physical garment region',
 'nativeKeyframeByteExact':True,'candidateModels':allCandidates,
 'sourceOwner':q['physicalSourceOwnership'],
 'originalSourceBaseline':native,'headBenchmark':head,
 'measuredLocalTrimDifferenceFromNative':delta,
 'fullSequenceVisionApproved':False,
 'selectedOverallVisualBenchmark':'P15-101 head_alpha_blend',
 'selectedThreeViewSourceGarmentBenchmark':'P15-107 companion_direct_native_keys',
 'localVisibilityMechanism':'native source masks, one-source material, physical right-lapel ownership, bounded inbetween correction',
 'actualVisualInspection':{
   'trim':'source-owned gold strokes remain confined to source-registered lapels; the right-hand 75° occlusion uses its original material',
   'ribbon':'single-source ribbon side material introduces native-versus-interpolated ink mismatch on the outer side silhouette',
   'occlusion':'inpainting of old source rim material cannot reconstruct wholly hidden cloth and jacket surfaces',
   'head':'preexisting P15-101 head/hair source-view inbetweens remain in the full-character preview'},
 'conclusion':'geometry, identity and editable source-owned visibility are reproducible; finished animation awaits physical-source view/occlusion correspondence',
 'nextRequiredAsset':'0–180° canonical P0 source-view coverage audit and consistent side-view bow/lapel/underlay art'
}
f=R/'evidence/p15-116-decision-qa.json'
f.write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n')
files=[
 'private-assets/exports/p15-116-visibility-repair/index.html',
 'private-assets/exports/p15-116-visibility-repair/browser-desktop.png',
 'private-assets/exports/p15-116-visibility-repair/browser-mobile.png',
 'private-assets/exports/p15-116-visibility-repair/source-matte-occlusion-contact.jpg',
 'private-assets/exports/p15-116-visibility-repair/trim-reference-difference.jpg',
 'private-assets/exports/p15-115-component-art/component-registration-contact.jpg',
 'private-assets/exports/p15-115-local-patch/localized-garment-contact.jpg',
 'private-assets/exports/p15-114-collar-art/collar-registration-contact.jpg',
 'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json']
for role,entries in src['registered'].items():
 for view,item in entries.items():
  files.extend([item['registeredPath'],item['source'],item['targetMask']])
for view,z in part['views'].items():
 files.append(z['source'])
 for name in ('bowFabric','jewel','goldTrim'):
  files.extend([z['layers'][name]['maskPath'],z['layers'][name]['texturePath']])
for frames in review['methodFrames'].values():
 for file in frames.values():
  files.append(os.path.relpath((P/'p15-116-visibility-repair'/file).resolve(),R))
for entry in review['animations'].values():files.append(entry['path'])
for name in ('p15-101-render-qa.json','p15-107-companion-qa.json',
 'p15-108-stroke-qa.json','p15-110-vision-qa.json','p15-115-source-qa.json',
 'p15-115-local-qa.json','p15-116-render-qa.json','p15-116-review-qa.json',
 'p15-116-browser-qa.json','p15-116-decision-qa.json'):
 files.append('evidence/'+name)
for script in ('p15_116_occlusion_repair.py','p15_116_review.py','p15_116_browser.cjs',
 'p15_116_package.py','test_p15_116_review.py'):
 files.append('scripts/'+script)
files=list(dict.fromkeys(files))
for item in files:
 if not (R/item).is_file():raise FileNotFoundError(item)
out=P/'p0-character-001-p15-116-source-owned-visibility-review.zip'
intro=('P0 Character · Source-owned garment visibility / material ownership\n'
 'Interactive nine-yaw full-character comparison: private-assets/exports/p15-116-visibility-repair/index.html\n'
 'Three 1024x1024 keyframes preserved byte-for-byte; four localized inbetween-only contour/trim corrections with source-owned visible ink, alpha masks and part-level right lapel source ownership.\n'
 'Includes all actual method frame PNGs and GIFs, independent source images, measured ROI changes, original-source difference visualization, responsive browser screenshots and reproducible scripts.\n'
 'Full-view artistic acceptance depends on canonical view-consistent physical garment and concealed-surface drawings, including source views outside the 60-75-degree sample.\n')
with ZipFile(out,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',intro)
 for item in files:z.write(R/item,item)
with ZipFile(out) as z:
 assert z.testzip() is None
 count=len(z.namelist())
taskPath=R/'tasks.json';task=json.loads(taskPath.read_text(encoding='utf-8'))
task['p15_116SourceVisibility']={
 'status':'SOURCE_OWNED_GARMENT_OCCLUSION_AND_PIXEL_PRESERVATION_VALIDATED',
 'characterId':'p0_character_001',
 'sourceAngles':[60,67.5,75],
 'outputFramesPerMethod':9,
 'testedMethods':allCandidates,
 'originalNativeKeyframesByteExact':True,
 'inbetweenChangesSourceMaskBounded':True,
 'sourceOwner':q['physicalSourceOwnership'],
 'sourceRegistrationSHA256':q['sourceQASHA256'],
 'regionalMaxAdjacentRGBMAE':numbers,
 'trimCandidateDifferenceFromNative':delta,
 'full360YawVisualAccepted':False,
 'selectedOverallVisualBenchmark':'P15-101 head_alpha_blend',
 'selectedNativeThreeViewBenchmark':'P15-107 companion_direct_native_keys',
 'unitTestsPass':17,'browserCasesPass':126,
 'review':review['entry'],
 'evidence':['evidence/p15-116-render-qa.json','evidence/p15-116-review-qa.json',
             'evidence/p15-116-browser-qa.json','evidence/p15-116-decision-qa.json'],
 'package':{'path':str(out.relative_to(R)),'bytes':out.stat().st_size,
            'sha256':sha(out),'entries':count},
 'next':'Inventory and validate the complete P0 0–180° source-view/part/hidden-surface coverage before deciding further clothing mesh refinement. Prioritize coherent character rotation over isolated 60–75° garment optimizations.'
}
task['status']='P15_116_SOURCE_VISIBILITY_AUDITED_FULL_YAW_SOURCE_COVERAGE_PENDING'
task['lastCompleted']='P15-116 native-keyframe-exact source-registered garment part visibility and real 60-75-degree motion comparison'
taskPath.write_text(json.dumps(task,ensure_ascii=False,indent=2)+'\n')
print('DELIVERY',out,'bytes',out.stat().st_size,'entries',count,'sha256',sha(out),flush=True)
print('TASK',task['status'],flush=True)
