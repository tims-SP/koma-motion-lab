#!/usr/bin/env python3
"""Actual moving-eye underpaint trials. Reject skin clone where eyebrow disappears."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-83-eye-seam';D.mkdir(parents=True,exist_ok=True)
srcp=P/'p15-56-edge-matting/candidate-erode-2.png'
basep=P/'p15-70-seam-repair/forehead-seam-repaired.png'
hairp=P/'p15-82-rest-underpaint/part.source-bangs.png'
clipp=P/'p15-82-rest-underpaint/part.source-clip.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=Image.open(srcp).convert('RGBA');base=Image.open(basep).convert('RGBA')
hair=Image.open(hairp).convert('RGBA');clip=Image.open(clipp).convert('RGBA')
brow=Image.open(P/'p15-79-brow-split/eyebrow.same-view.png').convert('RGBA')
ref0=Image.open(P/'p15-82-rest-underpaint/candidate-00.png').convert('RGBA')
def composite(images):
 out=Image.new('RGBA',src.size,(0,0,0,0))
 for im in images:out=Image.alpha_composite(out,im)
 return out
shapes={
 'slender':[(522,449),(528,433),(548,424),(571,421),(602,421),(633,425),(653,441),(658,449),(630,440),(593,435),(568,435),(543,441),(525,457)],
 'upper':[(521,454),(525,431),(543,418),(575,414),(614,413),(641,421),(658,441),(653,460),(633,443),(600,437),(565,441),(540,456)],
 'localized':[(522,451),(533,435),(561,430),(594,424),(637,431),(650,445),(639,454),(600,443),(558,449),(533,466)]
}
# 0px is independently composited source ownership, never fake direct-source image.
D.joinpath('candidate-00.png').write_bytes((P/'p15-82-rest-underpaint/candidate-00.png').read_bytes())
results={}
face_roi=(510,425,685,530)
src_alpha=src.getchannel('A').crop(face_roi)
brow_alpha=brow.getchannel('A')
for label,poly in shapes.items():
 mask=Image.new('L',src.size,0);ImageDraw.Draw(mask).polygon(poly,fill=255)
 mask=mask.filter(ImageFilter.GaussianBlur(2.0));mask.save(D/f'mask-{label}.png')
 donor=Image.new('RGBA',src.size,(0,0,0,0));donor.paste(base,(0,-28))
 repainted=Image.composite(donor,base,mask)
 repainted.save(D/f'underpaint-{label}.png')
 brow_overlap=sum(a>0 and b>128 for a,b in zip(brow_alpha.getdata(),mask.getdata()))
 outframes={}
 for dx in (9,18):
  eye=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
  moved=Image.new('RGBA',src.size);moved.alpha_composite(eye,(dx,0))
  frame=composite([repainted,moved,hair,clip])
  path=D/f'candidate-{label}-{dx:02d}.png';frame.save(path)
  frame.crop((490,390,690,530)).resize((800,560),Image.Resampling.LANCZOS).save(D/f'candidate-{label}-{dx:02d}-detail.png')
  old=Image.open(P/f'p15-82-rest-underpaint/candidate-{dx:02d}.png').convert('RGBA')
  changed=sum(a!=b for a,b in zip(frame.getdata(),old.getdata()))
  holes=sum(a>128 and b<32 for a,b in zip(src_alpha.getdata(),frame.getchannel('A').crop(face_roi).getdata()))
  outframes[str(dx)]={'sha256':sha(path),'changedPixelsVsP1582':changed,'newTransparentHolesROI':holes}
 results[label]={
  'maskSHA256':sha(D/f'mask-{label}.png'),
  'underpaintSHA256':sha(D/f'underpaint-{label}.png'),
  'browMaskOverlapPixels':brow_overlap,'frames':outframes,
 }
q={'schema':'KOMA-P15-83-BROW_LASH_UNDERPAINT_VARIANTS_V1',
 'sourceSHA256':sha(srcp),'baseSHA256':sha(basep),
 'hairSHA256':sha(hairp),'clipSHA256':sha(clipp),
 'independentZeroPoseSHA256':sha(D/'candidate-00.png'),
 'variants':results,'offsets':[0,9,18],
 'visualAssessment':{
   'slender':'Preserves much of the eyebrow but diagonal grey duplicate remains over lashes',
   'upper':'Reduces eyebrow ghost but erases actual eyebrow and leaves a visible mismatched forehead patch',
   'localized':'Preserves more shape but keeps duplicate eyebrow contour near the upper lash'},
 'selectedForFormalPipeline':None,'zeroPoseVisibleSourceExact':True,
 'visualGate':'ALL_LOCAL_UNDERPAINT_CLONES_FAIL_BROW_AND_BANG_VISUAL',
 'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'next':'P15-84 acquire a genuine clean hidden-face paint of the affected brow/lash seam; disallow additional clone-mask tuning'}
source_data=src.tobytes();rest_data=ref0.tobytes()
assert all(source_data[4*i:4*i+4]==rest_data[4*i:4*i+4] or source_data[4*i+3]==0 for i in range(src.width*src.height))
assert all(fr['newTransparentHolesROI']==0 for variant in results.values() for fr in variant['frames'].values())
(R/'evidence/p15-83-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'variants':results,'gate':q['visualGate']},ensure_ascii=False),flush=True)
