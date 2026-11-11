#!/usr/bin/env python3
"""Independent verification of GroundingDINO/SAM result geometry and face contamination."""
from pathlib import Path
from PIL import Image
import hashlib,json,shutil
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-72-semantic-hair';D.mkdir(parents=True,exist_ok=True)
source=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
inputpath=R/'private-assets/exports/p15-71-sam-semantic/input-512.png'
model_files=[D/'grounded-sam-output.png',D/'grounded-sam-fringe.png']
source_im=Image.open(source).convert('RGBA')
p70=R/'private-assets/exports/p15-70-seam-repair'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Compare source and outputs in consistent crop coordinates (350,125)-(862,637).
crop=(350,125,862,637)
source_im.crop(crop).save(D/'reference-same-view.png')
face_points={
 'near_eye':(230,345),
 'cheek_skin':(245,410),
 'lower_cheek':(240,465),
 'forehead_skin':(245,310),
 'hair_interior':(150,160),
 'outside_character':(500,490)
}
results=[]
for name,path in zip(['pink_anime_bangs_hair','front_hair_fringe_bangs'],model_files):
 im=Image.open(path).convert('RGB')
 assert im.size==(512,512)
 p={k:list(im.getpixel(xy)) for k,xy in face_points.items()}
 is_image=lambda rgb:max(rgb)>22
 result={'prompt':name,'path':path.name,'sha256':sha(path),'size':[512,512],
         'samplePixelRGB':p,'nearEyeIncluded':is_image(p['near_eye']),
         'cheekIncluded':is_image(p['cheek_skin']),
         'lowerCheekIncluded':is_image(p['lower_cheek']),
         'hairInteriorIncluded':is_image(p['hair_interior'])}
 assert result['hairInteriorIncluded'] and result['cheekIncluded'] and result['nearEyeIncluded']
 results.append(result)
for dx in (0,9,18):
 shutil.copy2(p70/f'eye-shift-{dx:02d}-seam-repaired.png',D/f'baseline-eye-{dx:02d}.png')
a=json.loads((R/'evidence/p15-72-semantic-provider-qa.json').read_text())
b=json.loads((R/'evidence/p15-72-semantic-provider-fringe-qa.json').read_text())
assert a['status']=='MODEL_RETURNED' and b['status']=='MODEL_RETURNED'
qa={'schema':'KOMA-P15-72-SEMANTIC-INFERENCE-QUALITY-V1',
 'characterId':'p0_character_001','sourceSHA256':sha(source),
 'inputSHA256':sha(inputpath),'provider':'Volkopat/SegmentAnythingxGroundingDINO',
 'providerModel':'GroundingDINO + SAM (CPU Space)','providerCalls':2,
 'providerResults':results,'modelProducedImage':True,'modelProducedUsableFrontHairAlpha':False,
 'faceContaminationConfirmed':True,
 'sourceHairMatteStillUnapproved':True,
 'baselineMovementOffsets':[0,9,18],
 'modelOutputsUsedToGenerateNewArtMesh':False,
 'originalP0Modified':False,'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'FAIL_MODEL_SEGMENTATION_INCLUDES_EYES_AND_CHEEK',
 'analysis':'Provider reports single detected object but outputs contain whole head/face rather than clean front-hair semantic mask. Both the near-eye and facial skin locations are nonblack in the result crop. No independent hair alpha layer or 0px exact-reconstruction proof exists.',
 'next':'P15-73 seek a genuinely supported hair-part segmentation/edit pipeline or commissioned same-view layered artwork; require full 0px identity reconstruction before dynamic eye offsets.'}
(R/'evidence/p15-72-semantic-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'modelCalls':2,'cheekIncluded':True,'nearEyeIncluded':True,'accepted':False,'files':len(list(D.glob('*.png')))}))
