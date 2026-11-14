#!/usr/bin/env python3
from pathlib import Path
import json,zipfile,hashlib
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-89-masked-local-art'
q=json.loads((R/'evidence/p15-89-final-qa.json').read_text())
browser=json.loads((R/'evidence/p15-89-browser-qa.json').read_text())
a=json.loads((R/'evidence/p15-89-masked-inference-qa.json').read_text())
b=json.loads((R/'evidence/p15-89-sd-masked-qa.json').read_text())
assert browser['status']=='PASS' and len(browser['checks'])==2
assert not q['formalArtMeshAccepted'] and not q['candidateAccepted']
assert q['maskActivePixels']==2259
qbytes=(D/'local-mask-1024.png').read_bytes()
assert hashlib.sha256(qbytes).hexdigest()==q['maskSHA256']
task=R/'tasks.json';d=json.loads(task.read_text())
d.setdefault('implementation',{})['p15_89SpatialMaskModelTrial']={
 'status':'EXPLICIT_MASK_INPUT_SUBMITTED_NO_FORMAL_ART_ADMISSION',
 'characterId':'p0_character_001',
 'sourceSHA256':q['sourceSHA256'],'maskSHA256':q['maskSHA256'],
 'maskBBox':q['maskBBox'],'maskActivePixels':q['maskActivePixels'],
 'qwenBackend':'hugging-apps/Qwen-Image-2.1-ControlNet-Union-Demo',
 'qwenEventId':a.get('eventId'),'qwenStatus':a['status'],
 'sdBackend':'pg56714/Inpaint-Anything /get_fill_img_with_sd',
 'sdEventId':b.get('eventId'),'sdStatus':b['status'],
 'actualExplicitMaskInput':True,
 'modelOutputAvailable':q['newModelOutputAvailable'],
 'visualGate':q['visualGate'],
 'candidateAccepted':False,'formalArtMeshAccepted':False,'formalKeyframeAccepted':False,
 'unitTestsPass':18,'browserChecksPass':2,'browserImagesLoaded':sum(x['imagesLoaded'] for x in browser['checks']),
 'evidence':['evidence/p15-89-masked-inference-qa.json','evidence/p15-89-sd-masked-qa.json','evidence/p15-89-final-qa.json','evidence/p15-89-browser-qa.json'],
 'review':'private-assets/exports/p15-89-masked-local-art/index.html',
 'plan':'docs/plans/2026-11-11-p15-89-masked-spatial-inference.md',
 'next':'P15-90 obtain a usable actual masked model output or artist authored true hidden contour, then render exact 0/9/18px and inspect appearance'
}
task.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=R/'private-assets/exports/p15-89-spatial-mask-review.zip'
files=[f for f in D.iterdir() if f.is_file() and f.suffix in ('.png','.html')]
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(f,f.name)
 for f in ('evidence/p15-89-masked-inference-qa.json','evidence/p15-89-sd-masked-qa.json','evidence/p15-89-final-qa.json','evidence/p15-89-browser-qa.json','docs/plans/2026-11-11-p15-89-masked-spatial-inference.md'):
  z.write(R/f,'qa/'+Path(f).name)
print(json.dumps({'bytes':p.stat().st_size,'files':len(zipfile.ZipFile(p).namelist()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},ensure_ascii=False))
