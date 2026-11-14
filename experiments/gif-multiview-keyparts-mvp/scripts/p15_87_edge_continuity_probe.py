#!/usr/bin/env python3
"""P15-87: Evaluate real same-view hidden-edge pixel candidates. Failure-gate
prevents papering over broken hair geometry with repeat mask feathering.
No overwrite of approved source layers or ArtMesh."""
from PIL import Image,ImageDraw,ImageFilter,ImageChops
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-87-hair-face-seam';D.mkdir(exist_ok=True)
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
srcp=P/'p15-56-edge-matting/candidate-erode-2.png'
underp=P/'p15-86-semantic-ownership/hidden-face.reassigned.png'
donorp=P/'p15-70-seam-repair/forehead-seam-repaired.png'
hairp=P/'p15-86-semantic-ownership/bangs.without-source-eyelash.png'
clipp=P/'p15-82-rest-underpaint/part.source-clip.png'
src=Image.open(srcp).convert('RGBA');under=Image.open(underp).convert('RGBA')
donor=Image.open(donorp).convert('RGBA');hair=Image.open(hairp).convert('RGBA')
clip=Image.open(clipp).convert('RGBA')
shapes={
 'canonical-left':[(514,438),(531,435),(536,440),(536,464),(526,467),(512,458)],
 'wide-left':[(507,434),(534,429),(538,440),(538,469),(524,471),(506,456)],
 'edge-taper':[(514,438),(528,434),(532,439),(537,450),(533,458),(532,464),(513,465)],
}
maskbbox=(498,417,565,487)
crop=(500,420,565,485)
roi=(510,405,690,535)
ref_alpha=src.getchannel('A').crop(roi)
oldframe={d:Image.open(P/f'p15-86-semantic-ownership/frame-reassigned-{d:02d}.png').convert('RGBA') for d in (9,18)}
def comp(layers):
 o=Image.new('RGBA',src.size)
 for layer in layers:o=Image.alpha_composite(o,layer)
 return o
# Loss measure at two deterministic structural locations:
# dangling eyebrow/dark patch on hair side; actual contour at hair/skin boundary.
def dark_count(img, box,limit=175):
 return sum(r<limit and g<limit-20 and b<limit-10 and a>128 for r,g,b,a in img.crop(box).getdata())
def side_edge_jump(im):
 p=im.load()
 # consecutive horizontal RGB delta across x534-541, near exposed vertical line
 scores=[]
 for y in range(438,465):
  for x in range(532,542):
   a=p[x,y];b=p[x+1,y]
   scores.append(sum(abs(a[k]-b[k]) for k in range(3)))
 return sum(scores),max(scores)
q={'schema':'KOMA-P15-87-REAL_SAME_VIEW_OCCLUSION_EDGE_PROBE_V1',
 'baselineGit':'fc8269f83b880cfce55a19c3e5115c0da6e9236b',
 'inputSHA256':{'source':sha(srcp),'underpaint':sha(underp),'donor':sha(donorp),'hair':sha(hairp),'clip':sha(clipp)},
 'sourcePose':'same-view P15-56','proposals':{},'candidateAccepted':False,'formalArtMeshAccepted':False,'formalKeyframeAccepted':False}
q['baseline']={}
for dx in (9,18):
 a=oldframe[dx]
 q['baseline'][str(dx)]={'sha256':sha(P/f'p15-86-semantic-ownership/frame-reassigned-{dx:02d}.png'),
 'darkDangling':dark_count(a,(526,438,536,462)),
 'edgeJump':list(side_edge_jump(a))}
for name,poly in shapes.items():
 for radius in (0.7,1.7):
  key=f'{name}-blur{str(radius).replace(".","")}'
  mask=Image.new('L',src.size,0);ImageDraw.Draw(mask).polygon(poly,fill=255)
  mask=mask.filter(ImageFilter.GaussianBlur(radius))
  mp=D/f'{key}-mask.png';mask.save(mp)
  newunder=Image.composite(donor,under,mask)
  up=D/f'{key}-underpaint.png';newunder.save(up)
  modified=sum(x!=y for x,y in zip(under.getdata(),newunder.getdata()))
  boundary=mask.getbbox()
  if boundary and not (boundary[0]>=maskbbox[0] and boundary[1]>=maskbbox[1] and boundary[2]<=maskbbox[2] and boundary[3]<=maskbbox[3]):
   raise RuntimeError('changed outside containment ROI')
  row={'radiusPx':radius,'polygon':poly,'maskSHA256':sha(mp),'underpaintSHA256':sha(up),'maskBBox':list(boundary),
       'changedUnderpaintPixels':modified,'frames':{}}
  for dx in (9,18):
   eye=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
   move=Image.new('RGBA',src.size);move.alpha_composite(eye,(dx,0))
   frame=comp([newunder,move,hair,clip])
   f=D/f'{key}-{dx:02d}.png';frame.save(f)
   frame.crop(crop).resize((650,650),Image.Resampling.NEAREST).save(D/f'{key}-{dx:02d}-detail.png')
   a=frame.tobytes();b=oldframe[dx].tobytes()
   delta=sum(a[4*i:4*i+4]!=b[4*i:4*i+4] and (a[4*i+3]>0 or b[4*i+3]>0) for i in range(src.width*src.height))
   holes=sum(x>128 and y<32 for x,y in zip(ref_alpha.getdata(),frame.getchannel('A').crop(roi).getdata()))
   row['frames'][str(dx)]={'sha256':sha(f),'visibleChanged':delta,'faceHoles':holes,
    'darkDangling':dark_count(frame,(526,438,536,462)),'edgeJump':list(side_edge_jump(frame))}
  q['proposals'][key]=row
# Rest is recomposed P15-86, never copied from the unpartitioned original input.
rest=Image.new('RGBA',src.size)
for name in ('face','eye','bangs','clip'):
 rest=Image.alpha_composite(rest,Image.open(P/f'p15-86-semantic-ownership/part-{name}.png').convert('RGBA'))
rest.save(D/'frame-00-from-source-layers.png')
s=src.tobytes();r=rest.tobytes()
visible_rest=sum(s[4*i:4*i+4]!=r[4*i:4*i+4] and s[4*i+3]>0 for i in range(src.width*src.height))
alpha_rest=sum(s[4*i+3]!=r[4*i+3] for i in range(src.width*src.height))
assert visible_rest==alpha_rest==0
assert all(v['faceHoles']==0 for row in q['proposals'].values() for v in row['frames'].values())
q['restSHA256']=sha(D/'frame-00-from-source-layers.png')
q['restVisiblePixelDiff']=visible_rest;q['restAlphaPixelDiff']=alpha_rest
q['visualGate']='FAIL_SAME_VIEW_DONOR_EDGE_CANNOT_REPLACE_TRUE_HIDDEN_HAIR_ART'
q['visualAssessment']='All six same-view donor edge variants retain a detached dark hair/skin stalk or produce conspicuous straight edge/flat patch. Numerical mask, alpha-hole, zero-pose checks pass but do not establish hair-strand geometry continuity. The genuine concealed hair/skin edge has not been drawn or reconstructed.'
q['next']='P15-88 create actual transparent concealed side-fringe/skin contour source rather than further copy/feather variants; only promote after 0/9/18 manual/art image inspection.'
(R/'evidence/p15-87-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'sixVariants':len(q['proposals']),'baseline':q['baseline'],'summary':{k:{dx:f['darkDangling'] for dx,f in v['frames'].items()} for k,v in q['proposals'].items()},'rest':visible_rest},ensure_ascii=False))
