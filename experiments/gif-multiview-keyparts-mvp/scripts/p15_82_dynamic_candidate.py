#!/usr/bin/env python3
"""Select rendered dynamic candidate after real P15-82 layer comparisons.
0px must recompose independently owned source layers; 9/18 use true
P15-70 hidden underpaint + independently moving P15-74 eye matte.
"""
from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-82-rest-underpaint'
qa_path=R/'evidence/p15-82-source-decomposition-qa.json'
q=json.loads(qa_path.read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
srcbytes=source.tobytes()
clip=Image.open(D/'part.source-clip.png').convert('RGBA')
hair=Image.open(D/'part.source-bangs.png').convert('RGBA')
face=Image.open(D/'part.source-face.png').convert('RGBA')
eye=Image.open(D/'part.source-eye.png').convert('RGBA')
base=Image.open(P/'p15-70-seam-repair/forehead-seam-repaired.png').convert('RGBA')
def blend(images):
 out=Image.new('RGBA',source.size)
 for i in images:out=Image.alpha_composite(out,i)
 return out
frames={}
roi=(510,425,685,530)
refalpha=source.getchannel('A').crop(roi)
for dx in (0,9,18):
 if dx==0:
  out=blend([face,eye,hair,clip])
 else:
  native=Image.open(P/f'p15-74-bangs-repair/eye.matte-{dx:02d}.png').convert('RGBA')
  moved=Image.new('RGBA',source.size);moved.alpha_composite(native,(dx,0))
  out=blend([base,moved,hair,clip])
 outpath=D/f'candidate-{dx:02d}.png';out.save(outpath)
 out.crop((445,265,795,605)).resize((700,680),Image.Resampling.LANCZOS).save(D/f'candidate-{dx:02d}-face.png')
 out.crop((510,390,700,525)).resize((950,675),Image.Resampling.LANCZOS).save(D/f'candidate-{dx:02d}-detail.png')
 outalpha=out.getchannel('A').crop(roi)
 hole=sum(a>128 and b<32 for a,b in zip(refalpha.getdata(),outalpha.getdata()))
 if dx==0:
  a=out.tobytes();changed=sum(a[4*i:4*i+4]!=srcbytes[4*i:4*i+4] for i in range(1024*1024))
  visible_changed=sum(a[4*i:4*i+4]!=srcbytes[4*i:4*i+4] and srcbytes[4*i+3]>0 for i in range(1024*1024))
 else:
  prior=Image.open(P/f'p15-76-seam-source/eye-shift-{dx:02d}.png').convert('RGBA')
  a=out.tobytes();b=prior.tobytes()
  changed=sum(a[4*i:4*i+4]!=b[4*i:4*i+4] for i in range(1024*1024))
  visible_changed=None
 frames[str(dx)]={'sha256':sha(outpath),'faceHoles':hole,'pixelDiffVsSourceIfRestElseP1576':changed,'visiblePixelDiffVsSourceIfRest':visible_changed}
q['selectedDynamicCandidate']='P15-70 forehead underpaint + P15-74 independently moving eye + SAM3-027 source-owned bangs + source-owned clip'
q['selectedFrameQA']=frames
q['finalZeroPoseVisuallyExact']=frames['0']['visiblePixelDiffVsSourceIfRest']==0
q['finalZeroPoseRawRGBAExact']=frames['0']['pixelDiffVsSourceIfRestElseP1576']==0
q['sourceInvisibleRGBDifferences']=frames['0']['pixelDiffVsSourceIfRestElseP1576']
q['motionFaceHoles']=max(z['faceHoles'] for z in frames.values())
q['dynamicVisualAssessment']='Original eye move with clean P15-70 base reduces the large jagged white crescent seen when shifting rigid source-owned eye pixels. However eyebrow/eyelash thin ghost contours remain and the SAM3 mask is still a binary mask with coarse antialiasing; dynamic animation quality is not formally approved.'
q['dynamicVisualGate']='ZERO_POSE_VISIBLE_EXACT_DYNAMIC_EDGE_SEAMS_REMAIN'
q['formalArtMeshAccepted']=False
q['formalKeyframeAccepted']=False
assert q['finalZeroPoseVisuallyExact'] and not q['finalZeroPoseRawRGBAExact']
assert q['motionFaceHoles']==0
qa_path.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'selectedFrames':frames,'gate':q['dynamicVisualGate']},ensure_ascii=False),flush=True)
