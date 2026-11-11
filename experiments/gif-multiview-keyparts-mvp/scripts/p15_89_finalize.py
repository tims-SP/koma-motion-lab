#!/usr/bin/env python3
"""Post-inference P15-89 evidence: enforce model output as masked-only trial.
Never treat composite pixel guard as visual acceptance."""
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter
import hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-89-masked-local-art';E=R/'evidence'
qa=json.loads((E/'p15-89-masked-inference-qa.json').read_text())
sd=json.loads((E/'p15-89-sd-masked-qa.json').read_text())
src=Image.open(D/'full-source-1024.png').convert('RGB')
mask=Image.open(D/'local-mask-1024.png').convert('L')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'schema':'KOMA-P15-89-SPATIAL_MASK_ADMISSION_V1',
 'qwenStatus':qa['status'],'sdStatus':sd['status'],
 'qwenMaskInputAccepted':qa['maskPassedAsTrueModelArgument'],
 'sdMaskInputAccepted':sd['maskPassedAsTrueModelArgument'],
 'maskSHA256':sha(D/'local-mask-1024.png'),'sourceSHA256':sha(D/'full-source-1024.png'),
 'maskBBox':list(mask.getbbox()),'maskActivePixels':sum(v>0 for v in mask.getdata()),
 'sourceZeroPoseReferenceSHA256':sha(R/'private-assets/exports/p15-86-semantic-ownership/frame-reassigned-00.png'),
 'newModelOutputAvailable':False,'formalArtMeshAccepted':False,
 'formalKeyframeAccepted':False,'candidateAccepted':False,
 'visualGate':'BLOCKED_NO_MODEL_OUTPUT','newDynamicRenderAccepted':False}
choices=[]
if qa.get('modelOutputCreated'):choices.append(('qwen',D/'returned-model-1024.png'))
if sd.get('modelOutputCreated'):choices.append(('sd',D/'sd-model-returned.png'))
for kind,p in choices:
 raw=Image.open(p).convert('RGB').resize(src.size,Image.Resampling.LANCZOS)
 raw.save(D/f'{kind}-model-aligned-canvas.png')
 candidate=Image.composite(raw,src,mask)
 path=D/f'{kind}-strict-mask-preview.png'
 candidate.save(path)
 a=list(src.getdata());b=list(candidate.getdata());m=list(mask.getdata())
 diff=sum(x!=y for x,y in zip(a,b));outside=sum(x!=y and w==0 for x,y,w in zip(a,b,m))
 assert outside==0
 result['newModelOutputAvailable']=True
 result.setdefault('modelCandidates',{})[kind]={'outputSHA256':sha(p),'trialSHA256':sha(path),
  'changedPixels':diff,'outsideMaskChangedPixels':outside}
 result['visualGate']='MODEL_RETURNED_PENDING_SEAM_AND_0_9_18_REVIEW'
# Even if inference succeeds the model is not automatically admitted: must assess
# color geometry and actual animation, rather than rely on an unchanged outside mask.
(E/'p15-89-final-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
