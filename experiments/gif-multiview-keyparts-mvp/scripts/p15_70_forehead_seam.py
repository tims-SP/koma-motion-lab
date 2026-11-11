#!/usr/bin/env python3
"""Repair forehead seam above the eye without reintroducing the static original iris."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
import hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-70-seam-repair';D.mkdir(parents=True,exist_ok=True)
src=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
previous=R/'private-assets/exports/p15-69-clip-separation/clip-and-eye-free-underpaint.png'
reference=R/'private-assets/exports/p15-55-registration/underlay--28.png'
hairfile=R/'private-assets/exports/p15-69-clip-separation/hair-front-no-gold-candidate.png'
eyefile=R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'
clipfile=R/'private-assets/exports/p15-69-clip-separation/hair-clip-gold-independent.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=Image.open(previous).convert('RGBA')
ref=Image.open(reference).convert('RGBA')
hair=Image.open(hairfile).convert('RGBA')
eye=Image.open(eyefile).convert('RGBA')
clip=Image.open(clipfile).convert('RGBA')
# Ref v P15-69 differs drastically at near-eye; preserve all base pixels below
# the eyebrow/eyelid boundary, and feather the upper forehead texture only.
mask=Image.new('L',base.size,0)
ImageDraw.Draw(mask).rectangle((480,255,676,392),fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(7))
mp=mask.load()
for y in range(384,430):
    weight=max(0,min(1,(397-y)/13))
    for x in range(450,705):
        mp[x,y]=round(mp[x,y]*weight)
mask.save(D/'forehead-repair-mask.png')
repaired=Image.composite(ref,base,mask)
repaired.save(D/'forehead-seam-repaired.png')
oldframe=Image.open(R/'private-assets/exports/p15-69-clip-separation/eye-shift-18-clip-once.png').convert('RGBA')
frames=[]
for dx in (0,9,18):
    moving=Image.new('RGBA',base.size)
    moving.alpha_composite(eye,(dx,0))
    out=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(repaired,moving),hair),clip)
    file=f'eye-shift-{dx:02d}-seam-repaired.png'
    out.save(D/file)
    out.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'eye-shift-{dx:02d}-face.png')
    frames.append({'dx':dx,'file':file,'sha256':sha(D/file)})
for label,img in [('before',oldframe),('after',Image.open(D/'eye-shift-18-seam-repaired.png').convert('RGBA'))]:
    img.crop((450,300,720,540)).resize((810,720),Image.Resampling.LANCZOS).save(D/f'{label}-forehead.png')
    img.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'{label}-face.png')
diff=ImageChops.difference(base,repaired)
changed_pixels=sum(n>0 for n in diff.convert('L').getdata())
# Hard check outside generated mask alpha is pixel-identical.
aa=base.tobytes();bb=repaired.tobytes();mm=mask.tobytes()
outside=sum(aa[4*i:4*i+4]!=bb[4*i:4*i+4] for i,m in enumerate(mm) if m==0)
# Check original source preserved; this is not a formal asset update.
roi=(510,425,685,530)
original_a=Image.open(src).convert('RGBA').getchannel('A').crop(roi)
hole_by_frame={}
for f in frames:
    newa=Image.open(D/f['file']).convert('RGBA').getchannel('A').crop(roi)
    hole_by_frame[str(f['dx'])]=sum(a>128 and b<32 for a,b in zip(original_a.getdata(),newa.getdata()))
assert outside==0 and changed_pixels>100 and all(n==0 for n in hole_by_frame.values())
qa={'schema':'KOMA-P15-70-FOREHEAD-SEAM-REPAIR-V1','characterId':'p0_character_001',
 'sourceSHA256':sha(src),'oldBaseSHA256':sha(previous),'referenceSHA256':sha(reference),
 'hairSHA256':sha(hairfile),'eyeSHA256':sha(eyefile),'clipSHA256':sha(clipfile),
 'newBaseSHA256':sha(D/'forehead-seam-repaired.png'),'repairMaskSHA256':sha(D/'forehead-repair-mask.png'),
 'method':'FEATHERED_REFERENCE_RESTORE_FOREHEAD_ONLY_WITH_EYE_REGION_EXCLUDED',
 'referenceSource':'P15-55 known hair and skin underlay; not a generated independent face',
 'changedRGBApixels':changed_pixels,'outsideMaskChangedPixels':outside,'frames':frames,
 'transparentHolesByOffset':hole_by_frame,
 'visualGate':'FOREHEAD_PATCH_IMPROVED_FULL_FRONT_HAIR_UNAPPROVED',
 'visualAssessment':'Pink triangular forehead fill from P15-68 reduced by constrained P15-55 reference restoration. The horizontal grey-purple stripe and lash/hair boundary remain because they are embedded in the nonsemantic P15-67 hair candidate.',
 'fullFrontHairSemanticApproved':False,'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'next':'P15-71 fix front-bang source semantics and eyebrow-lash contamination; do not rerun LaMa or pursue further mask-only forehead fixes.'}
(R/'evidence/p15-70-seam-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'changedPixels':changed_pixels,'outsideMask':outside,'holes':hole_by_frame,'newBaseSHA256':qa['newBaseSHA256']}))
