#!/usr/bin/env python3
"""Cross-check P0 45-degree image provenance and record the limits of relative camera control."""
import hashlib,json,zipfile
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
A=R/'private-assets'
D=A/'exports/p15-58-provenance-pose'
D.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
P0=A/'p2-views/whole/yaw045.png'
refs={
 'original_recovered_P2': P0,
 'P15_37_identity':A/'exports/p15-37-temporal-art-review/p0-45-identity.png',
 'P15_38_original':A/'exports/p15-38-original-p0-arc-review/p0-yaw45-original.png',
 'P15_42_reference':A/'exports/p15-42-65-keyart-review/source-45.png',
 'P15_43_reference':A/'exports/p15-43-camera-pose-review/p0-45.png',
}
expected='78a08d5f010a8f449efda915a710a2de8958c3b1a32375df491d806fca251e40'
actual={name:sha(p) for name,p in refs.items()}
assert all(v==expected for v in actual.values())
archive=A/'exports/p0-character-001-multiview-source-review-v4.zip'
arch_name='private-assets/p2-views/whole/yaw045.png'
with zipfile.ZipFile(archive) as z: arch_hash=hashlib.sha256(z.read(arch_name)).hexdigest()
assert arch_hash==expected
recovery=json.loads((R/'evidence/2026-11-05-recovered-p0-review.json').read_text())
assert recovery['rgbaLayers']['pixelParity']['45']['sourceSha256']==expected
hero_record=recovery['sourceIdentity']['approvedHeroSha256']
hero_record_validated=recovery['sourceIdentity']['approvedHeroBytesValidated']
assert not hero_record_validated
report51=json.loads((R/'evidence/p15-51-camera-angle-qa.json').read_text())
report56=json.loads((R/'evidence/p15-56-alpha-matte-qa.json').read_text())
assert report51['source']['sha256']==expected
candidate=A/'exports/p15-56-edge-matting/candidate-erode-2.png'
assert sha(candidate)==report56['selectedCandidateSHA256']
P90=A/'p2-views/whole/yaw090.png'
assets=[('canonical45.png',P0),('historical90.png',P90),('relative-plus20-candidate.png',candidate)]
for name,source in assets:
 img=Image.open(source).convert('RGBA')
 assert img.size==(1024,1024)
 img.save(D/name)
 for suffix,rect in [('face',(440,310,800,740)),('clip',(670,240,820,410))]:
  if name!='historical90.png' or suffix=='face':
   img.crop(rect).resize(((rect[2]-rect[0])*2,(rect[3]-rect[1])*2),Image.Resampling.LANCZOS).save(D/(name.removesuffix('.png')+'-'+suffix+'.png'))
features=[
 {'feature':'short_lavender_bob','source45':'visible','candidate':'visible','assessment':'consistent color and haircut class'},
 {'feature':'single_ahoge','source45':'visible','candidate':'visible','assessment':'single curled strand retained; curve differs'},
 {'feature':'purple_pink_eyes','source45':'both visible','candidate':'near eye dominant and far eye strongly foreshortened','assessment':'plausible yaw progression; no calibrated 3D landmark geometry'},
 {'feature':'nose_bridge_and_chin','source45':'three-quarter','candidate':'nose shifts to right and chin narrows','assessment':'plausible side-turn; manual visual only'},
 {'feature':'gold_cross_hairclip','source45':'right side of image','candidate':'right side of image, independent alpha-refined piece','assessment':'X preserved; mounted position and perspective not independently artist-approved'},
 {'feature':'navy_uniform_red_bow','source45':'visible','candidate':'visible','assessment':'outfit palette and bow preserved'},
]
qa={
 'schema':'KOMA-P15-58-PROVENANCE-POSE-V1',
 'characterId':'p0_character_001',
 'canonical45':{'sha256':expected,'verifiedIdenticalCopies':actual,
   'verifiedArchiveEntry':{'zip':str(archive.relative_to(R)),'entry':arch_name,'sha256':arch_hash},
   'recoveryPixelParityClaimMatches':True,'sourceImageBytesIdentical':True,
   'approvedHeroSHA256OnRecord':hero_record,'approvedHeroBytesValidated':hero_record_validated,
   'heroTo45ProvenanceLevel':'NOT_PROVEN; canonical45 downstream identity established, original approved Hero file unverified'},
 'candidate':{'source45SHA256':report51['source']['sha256'],
   'cameraCommandRelativeDegrees':report51['positive20']['rotate_deg'],
   'cameraCommandAxis':'left','randomSeed':report51['positive20']['seed'],
   'rawModelOutputSHA256':report51['positive20']['sha256'],
   'selectedP1556SHA256':sha(candidate),
   'absoluteYawDegrees':None,'absoluteYawVerified':False,
   'yawReason':'A relative natural-language/LoRA camera rotation command does not provide an externally calibrated 3D rotation angle. The original image yaw is nominal 45deg, not independently camera calibrated.'},
 'historic90':{'sha256':sha(P90),'role':'historical reference only; not camera calibration'},
 'features':features,
 'visualIdentityStatus':'PLAUSIBLE_CONTINUITY_NOT_APPROVED',
 'poseStatus':'RIGHT_FACING_STRONGER_PROFILE_NOT_CALIBRATED_65',
 'formalArtMeshModified':False,'formalKeyframeAccepted':False,
 'next':'Use an independently calibrated 3D or keypoint-to-camera representation for absolute yaw; the provenance chain to approved Hero bytes remains unresolved.'
}
(R/'evidence/p15-58-provenance-pose-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'copies':len(actual),'canonical_sha':expected,'archive_matches':arch_hash==expected,
 'hero_bytes_verified':hero_record_validated,'candidate':qa['candidate']['selectedP1556SHA256'],'yaw_verified':False}))
