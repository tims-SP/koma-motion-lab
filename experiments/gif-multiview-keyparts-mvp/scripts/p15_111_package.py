#!/usr/bin/env python3
"""P15-111 preserve native hidden garment art and auditable layer-composition QA."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda path:sha256(Path(path).read_bytes()).hexdigest()
srcP=R/'evidence/p15-111-source-qa.json';src=json.loads(srcP.read_text())
renderP=R/'evidence/p15-111-render-qa.json';render=json.loads(renderP.read_text())
review=json.loads((R/'evidence/p15-111-review-qa.json').read_text())
browser=json.loads((R/'evidence/p15-111-browser-qa.json').read_text())
meta=json.loads((R/'private-assets/p15-111-hidden-art/generation-summary.json').read_text())
assert meta['successfulImagegenCalls']==6
assert src['nativeImageCount']==6 and src['sourceViewsRegistered']==3
assert browser['status']=='PASS' and len(browser['checks'])==90
assert len(render['methods'])==3 and all(len(x)==9 for x in render['methods'].values())
assert len(review['methodFrames'])==5
ref=render['metrics']['P15-101-original']
prior=render['metrics']['P15-107-three-native']
layer=render['metrics']['layered_full']
jewel=render['metrics']['layered_jewel_owner']
render['visualReview']={
 'performed':True,
 'artProduction':'6 individually generated model-native transparent RGBAs',
 'sourceIdentity':'original p0_character_001 three-view character garments',
 'materialContent':'extended white collar under red bow; continuous red ribbon under central golden brooch',
 'registration':'source color/material centroids and physical source-occluder masks',
 'sourceNativeOutputPreservation':'original native 1254x1254 RGBA bytes SHA256 verified',
 'occlusionStructuralQA':'front bow and jewel source-owned masks gate each inferred hidden material image',
 'nativeViewKeyframeFidelity':'P15-107 source-owned full-character keyframes preserved',
 'visualFindings':{
  'underpaint':'generated transparent assets contain coherent collar folds and crimson material behind occluders',
  'uncoveredTexels':'registered images provide measured hidden-zone coverage per view, with remaining gaps at white collar boundaries',
  'artifactStatus':'independent imagegen source silhouettes need matched deformation and visibility; blended collar seams and jacket lines remain doubled',
  'goldJewel':'separate jewel ownership provides isolated foreground control but source-art shape differences cause temporal jumps',
  'head':'existing P15-101 multi-view head/hair ArtMesh remains unchanged'},
 'regionalComparison':{area:{
  'P15-101':ref[area]['maxAdjacentRGBMAE'],
  'P15-107-native':prior[area]['maxAdjacentRGBMAE'],
  'P15-111-layered':layer[area]['maxAdjacentRGBMAE'],
  'P15-111-jewelOwner':jewel[area]['maxAdjacentRGBMAE']}
  for area in ('bow','jewel','collar')},
 'artisticAcceptance':False,
 'selectedVisualBenchmark':'P15-101 head_alpha_blend',
 'sourceCostumeCandidate':'P15-107 companion_direct_native_keys',
 'nextCriticalEvidence':'source-consistent 2D deformation and disocclusion owner transitions, validated at actual bow/collar edges'}
render['visualApproved']=False
renderP.write_text(json.dumps(render,ensure_ascii=False,indent=2)+'\n')
files=[
 'private-assets/p15-111-hidden-art/generation-summary.json',
 'private-assets/p15-111-hidden-art/generation-brief.txt',
 'private-assets/p15-111-hidden-art/garment-three-reference.jpg',
 'private-assets/p15-111-hidden-art/bow-stroke-guide.jpg',
 'private-assets/exports/p15-111-hidden-registered/underpaint-source-contact.jpg',
 'private-assets/exports/p15-111-layered-render/hidden-material-layer-contact.jpg',
 'private-assets/exports/p15-111-layered-render/index.html',
 'private-assets/exports/p15-111-layered-render/browser-desktop.png',
 'private-assets/exports/p15-111-layered-render/browser-mobile.png']
for view in ('60','67.5','75'):
 srcRec=src['layers'][view]
 for item in srcRec.values():
  files.extend([item['nativePath'],item['registeredPath'],item['hiddenOnlyPath']])
 v=view.replace('.','p')
 files.append(f'private-assets/exports/p15-111-hidden-registered/yaw{v}-source-reveal.png')
 files.append(f'private-assets/p15-111-hidden-art/yaw{v}-reference.png')
for frames in review['methodFrames'].values():
 for rel in frames.values():
  files.append(str((P/'p15-111-layered-render'/rel).resolve().relative_to(R)))
for gif in review['animations'].values():files.append(gif['path'])
for name in ('p15-101-render-qa.json','p15-107-companion-qa.json','p15-108-stroke-qa.json',
             'p15-110-vision-qa.json','p15-111-source-qa.json','p15-111-render-qa.json',
             'p15-111-review-qa.json','p15-111-browser-qa.json'):
 files.append('evidence/'+name)
for script in ('p15_111_register_hidden.py','p15_111_layered_render.py',
               'p15_111_review.py','p15_111_browser.cjs','p15_111_package.py',
               'test_p15_111_review.py'):
 files.append('scripts/'+script)
files=list(dict.fromkeys(files))
for f in files:
 if not (R/f).is_file():raise FileNotFoundError(f)
archive=P/'p0-character-001-p15-111-garment-hidden-surface-review.zip'
readme=('P0 Character | Three-view garment hidden-surface original artwork and layered VDD\n'
 'Review: private-assets/exports/p15-111-layered-render/index.html\n'
 'Six individually generated native transparent PNGs: white-collar underpainting and bow-under-brooch crimson folds at 60°, 67.5°, 75°.\n'
 'Contains byte-preserved native 1254x1254 images, registered 1024 sources, source-owned hidden-only art layers, original RGBAs, source SHA256, visibility masks and occlusion-reveal contact.\n'
 'Actual full-character yaw 60–75° render strategies, source reference baselines, GIFs, desktop/mobile Chromium evidence, unit scripts and diagnostic measurements are included.\n'
 'The continuation of occluded textile is artistically inferred. A later artistic and source-shape correspondence review will determine motion acceptance.\n')
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.txt',readme)
 for path in files:z.write(R/path,path)
with ZipFile(archive) as z:
 assert z.testzip() is None
 count=len(z.namelist())
taskPath=R/'tasks.json'
data=json.loads(taskPath.read_text(encoding='utf-8'))
data['p15_111GarmentHiddenArt']={
 'status':'THREE_VIEW_GARMENT_HIDDEN_MATERIAL_ART_AND_LAYER_COMPOSITOR_VERIFIED',
 'characterId':'p0_character_001',
 'sourceAngles':[60,67.5,75],
 'nativeImageGenerator':'Codex builtin image_gen.imagegen',
 'generatedNativeTransparentRGBA':6,
 'nativeDimensions':[1254,1254],
 'registeredDimensions':[1024,1024],
 'nativeSourceSHA256':{view:{role:rec['nativeSHA256'] for role,rec in parts.items()}
                       for view,parts in src['layers'].items()},
 'sourceClothingUnderpaintByView':{view:{role:rec['hiddenOnlyPath'] for role,rec in parts.items()}
                                  for view,parts in src['layers'].items()},
 'actualHiddenCoverageByView':{view:{role:rec['hiddenCoverageFraction'] for role,rec in parts.items()}
                                for view,parts in src['layers'].items()},
 'sourceOwnedLayerOrder':render['drawingOrder'],
 'originalThreeKeyframeFidelity':True,
 'renderedCandidateFrames':sum(len(frames) for frames in render['methods'].values()),
 'referenceFrames':18,
 'regionalMaxAdjacentRGBMAE':render['visualReview']['regionalComparison'],
 'visualBenchmark':'P15-101 head_alpha_blend',
 'sourceCostumeCandidate':'P15-107 companion_direct_native_keys',
 'structuralMaterialValidation':True,
 'artistApprovedHiddenArt':False,
 'continuousYawVisualAccepted':False,
 'unitTestsPass':18,
 'browserChecksPass':90,
 'visualGate':'SOURCE_CONSISTENT_DISOCCLUSION_WITH_ARTISTICALLY_MATCHED_BOW_AND_COLLAR',
 'review':review['entry'],
 'package':{'path':str(archive.relative_to(R)),'bytes':archive.stat().st_size,
            'entries':count,'sha256':sha(archive)},
 'evidence':['evidence/p15-111-source-qa.json','evidence/p15-111-render-qa.json',
             'evidence/p15-111-review-qa.json','evidence/p15-111-browser-qa.json'],
 'next':'Validate part-specific source artwork silhouette/ink correspondence and disocclusion transitions with the six hidden-surface art layers; retain original source yaw keyframes and visually compare every intermediate frame'
}
data['status']='P15_111_HIDDEN_GARMENT_MATERIAL_LAYERED_RENDER_VERIFIED_VISUAL_ART_PENDING'
data['lastCompleted']='P15-111 native 3-view 2-component underpaint sources, occlusion-masked RGBA registration, and full-character layered VDD verification'
taskPath.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('DELIVERY',archive,'bytes',archive.stat().st_size,'entries',count,'sha256',sha(archive),flush=True)
print('TASK',data['status'],flush=True)
