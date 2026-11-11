#!/usr/bin/env python3
"""Source-derived local skin underpaint for hidden lash/eyebrow seam.
Never alters the source artwork. Preserves zero-pose pixel identity.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFilter,ImageChops
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
D=P/'p15-76-seam-source';D.mkdir(parents=True,exist_ok=True)
sources={
 'source':P/'p15-56-edge-matting/candidate-erode-2.png',
 'base':P/'p15-70-seam-repair/forehead-seam-repaired.png',
 'eye':P/'p15-65-eyelid-refinement/eye.near.refined-layer.png',
 'hair0':P/'p15-74-bangs-repair/hair.front.alpha-dedup.png',
 'clip':P/'p15-69-clip-separation/hair-clip-gold-independent.png'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
im={name:Image.open(file).convert('RGBA') for name,file in sources.items()}
src,base=im['source'],im['base']
# A narrow local repair based on the true hidden-face skin, not solid color.
# This covers the diagonal grey remnant that P15-63/70 left behind.
poly=[(535,460),(547,442),(565,424),(578,421),(563,454),(543,477)]
guard=Image.new('L',src.size,0)
ImageDraw.Draw(guard).polygon(poly,fill=255)
guard=guard.filter(ImageFilter.GaussianBlur(3))
guard.save(D/'hidden-skin-local-guard.png')
# Source pixels sampled 25px below the artifact, feathered into the hidden
# forehead. Preserve all skin texture and alpha from the known base image.
sample=Image.new('RGBA',src.size,(0,0,0,0))
sample.paste(base,(0,-25))
sample.save(D/'source-skin-clone-sampling.png')
clean=Image.composite(sample,base,guard)
clean.save(D/'hidden-skin-clean-candidate.png')
# The edit is pose dependent to avoid any modification of the approved 0px.
frames=[]
hole_count={}
old18=Image.open(P/'p15-75-eyebrow-seam/eye-shift-18.png').convert('RGBA')
for dx in (0,9,18):
 mask=guard.point(lambda a:round(a*dx/18))
 staged=Image.composite(sample,base,mask)
 staged.save(D/f'hidden-skin-{dx:02d}.png')
 eye=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
 hair=Image.open(P/f'p15-75-eyebrow-seam/hair.front.moving-{dx:02d}.png').convert('RGBA')
 moved=Image.new('RGBA',src.size);moved.alpha_composite(eye,(dx,0))
 out=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(staged,moved),hair),im['clip'])
 out.save(D/f'eye-shift-{dx:02d}.png')
 out.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'eye-shift-{dx:02d}-face.png')
 out.crop((505,405,660,485)).resize((930,480),Image.Resampling.LANCZOS).save(D/f'eye-shift-{dx:02d}-detail.png')
 roi=(510,425,685,530)
 a=src.getchannel('A').crop(roi).getdata();b=out.getchannel('A').crop(roi).getdata()
 hole_count[str(dx)]=sum(x>128 and y<32 for x,y in zip(a,b))
 frames.append({'dx':dx,'frameSHA256':sha(D/f'eye-shift-{dx:02d}.png'),
  'underpaintSHA256':sha(D/f'hidden-skin-{dx:02d}.png')})
out0=Image.open(D/'eye-shift-00.png').convert('RGBA')
assert ImageChops.difference(src,out0).getbbox() is None
assert hole_count=={'0':0,'9':0,'18':0}
diff=ImageChops.difference(old18,Image.open(D/'eye-shift-18.png').convert('RGBA'))
delta=sum(v>0 for v in diff.convert('L').getdata())
# All base changes are within the feathered mask, including at 9px.
mask_area=sum(v>0 for v in guard.getdata())
for dx in (0,9,18):
 stage=Image.open(D/f'hidden-skin-{dx:02d}.png').convert('RGBA')
 m=guard.tobytes();a=base.tobytes();b=stage.tobytes()
 assert all(a[4*i:4*i+4]==b[4*i:4*i+4] for i,v in enumerate(m) if v==0)
for label,image in [('before',old18),('after',Image.open(D/'eye-shift-18.png').convert('RGBA'))]:
 image.crop((505,405,660,485)).resize((930,480),Image.Resampling.LANCZOS).save(D/f'{label}-detail.png')
report={
 'schema':'KOMA-P15-76-SOURCE_DERIVED_UNDERPAINT_V1','characterId':'p0_character_001',
 'sourceHashes':{name:sha(p) for name,p in sources.items()},
 'guardSHA256':sha(D/'hidden-skin-local-guard.png'),
 'candidateUnderpaintSHA256':sha(D/'hidden-skin-clean-candidate.png'),
 'guardBBox':list(guard.getbbox()),'guardNonzeroPixels':mask_area,
 'paintSource':'P15-70 authentic face underpaint shifted 25px to sample unblemished adjacent skin',
 'sourceSampleDisplacementPx':[0,25],
 'localRepairPolygon':poly,'featherPx':3,
 'method':'SOURCE_PIXEL_CLONE_WITH_POSE_WEIGHTED_FEATHER_NOT_NEW_AI_PAINTING',
 'sourceUnchanged':True,'zeroPosePixelExact':True,'motionOffsets':[0,9,18],
 'frameHashes':frames,'holeCounts':hole_count,
 'changedFullFramePixels18':delta,
 'visualAssessment':'Source-derived skin clone removes much of the thin grey diagonal behind the moving upper eyelid at 18px. Residual brow texture and some inner hair/eyelash discontinuities remain. This is local underpaint restoration, not independently painted brow/lash/front-hair semantic RGBA.',
 'fullSemanticHairLayerAccepted':False,'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'visualGate':'LOCAL_HIDDEN_SKIN_SEAM_IMPROVED_SEMANTIC_BROW_HAIR_FAIL',
 'next':'P15-77 obtain truly isolated eyebrow/lash/front-bang edge artwork; inspect 0/9/18 and do not expand feather masks as replacement for original layers.'
}
(R/'evidence/p15-76-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'maskBBox':report['guardBBox'],'maskNonzeroPixels':mask_area,'18pxChanged':delta,'holes':hole_count,'zeroExact':True}))
