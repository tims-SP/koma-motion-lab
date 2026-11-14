#!/usr/bin/env python3
"""P15-174 source-aligned AI crown patch, strictly limited to 112.5-degree root.

A Flux.2 Klein edit is used only as a 14x14 RGB texture donor around the
single ahoge attachment. The rest of the model's edited image is discarded.
Original source alpha and all pixels outside the 14x14 repair remain exact.
"""
import hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS,P
ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/'private-assets/exports/p15-174-ai-root-patch'
OUT=ASSET
E=ROOT/'evidence/p15-174-ai-root-patch-qa.json'
ANGLE=112.5; ANCHOR=(258,77); CROP_ORIGIN=(110,0); SCALE=2
def apply():
    source=keyframes()[ANGLE]
    edited=np.array(Image.open(ASSET/'flux-kontextual-edit.png').convert('RGB'))
    edited=cv2.resize(edited,(560,320),interpolation=cv2.INTER_AREA)
    cx=int((ANCHOR[0]-CROP_ORIGIN[0])*SCALE);cy=int((ANCHOR[1]-CROP_ORIGIN[1])*SCALE)
    patch=cv2.resize(edited[cy-14:cy+14,cx-14:cx+14],(14,14),interpolation=cv2.INTER_AREA).astype(np.float32)
    x,y=ANCHOR
    original=source[y-7:y+7,x-7:x+7,:3].astype(np.float32)
    context=source[y-14:y+14,x-14:x+14,:3].astype(np.float32)
    ring=np.ones((28,28),bool);ring[7:21,7:21]=False
    samples=context[ring]
    mu0=samples.mean(0);sd0=samples.std(0)+1
    mu1=patch.reshape(-1,3).mean(0);sd1=patch.reshape(-1,3).std(0)+1
    patch=np.clip((patch-mu1)*(sd0/sd1)+mu0,0,255)
    yy,xx=np.indices((14,14));dist=np.sqrt((xx-6.5)**2+(yy-6.5)**2)
    weight=np.clip((7.5-dist)/2,0,1).astype(np.float32)
    result=source.copy()
    result[y-7:y+7,x-7:x+7,:3]=np.uint8(np.clip(original*(1-weight[...,None])+patch*weight[...,None],0,255))
    result[...,3]=source[...,3]
    changed=np.any(result!=source,axis=2)
    return source,result,{'sourceSha256':hashlib.sha256(source.tobytes()).hexdigest(),
      'editedModelSha256':hashlib.sha256((ASSET/'flux-kontextual-edit.png').read_bytes()).hexdigest(),
      'candidateSha256':hashlib.sha256(result.tobytes()).hexdigest(),
      'anchor':list(ANCHOR),'patchSize':[14,14],'changedPixels':int(changed.sum()),
      'bbox':[int(x-7),int(y-7),int(x+6),int(y+6)],
      'outsidePatchPixelExact':bool(np.array_equal(result[~cv2.dilate(changed.astype('uint8'),np.ones((1,1),np.uint8)).astype(bool)],source[~changed])),
      'sourceAlphaExact':bool(np.array_equal(result[...,3],source[...,3]))}
def run(save=True):
    source,result,diag=apply()
    q={'schema':'KOMA_P15_174_AI_ROOT_PATCH_V1','characterId':'p0_character_001',
      'angle':ANGLE,'method':'Flux.2 Klein 4B visual edit as a source-color-matched 14x14 patch donor',
      'modelOutputScope':'Only 14x14 patch around root is sampled; all other generated pixels discarded',
      'diagnostics':diag,'nativeSourceUnchanged':True,'artistApproval':False,
      'intermediateYawAccepted':False,'canonicalRendererUpdated':False}
    q['gate']={'sourceAlphaExact':diag['sourceAlphaExact'],
      'outsidePatchExact':diag['outsidePatchPixelExact'],
      'editBounded':diag['changedPixels']<=196,
      'candidateRendered':True,'rootAttachmentVisuallyAccepted':False,'passes':False}
    if save:
      OUT.mkdir(exist_ok=True,parents=True)
      Image.fromarray(result,'RGBA').save(OUT/'local-composite.png')
      bg0=Image.new('RGBA',(source.shape[1],source.shape[0]),(45,57,75,255));bg0.alpha_composite(Image.fromarray(source,'RGBA'))
      bg1=Image.new('RGBA',(result.shape[1],result.shape[0]),(45,57,75,255));bg1.alpha_composite(Image.fromarray(result,'RGBA'))
      crop=(238,58,278,98)
      a=bg0.crop(crop).resize((400,400),Image.Resampling.NEAREST)
      b=bg1.crop(crop).resize((400,400),Image.Resampling.NEAREST)
      board=Image.new('RGB',(800,430),(35,42,54));board.paste(a,(0,30));board.paste(b,(400,30))
      d=ImageDraw.Draw(board);d.text((8,8),'source 112.5',fill='white');d.text((408,8),'AI-assisted local patch',fill='white')
      board.save(OUT/'root-patch-closeup.jpg',quality=96)
      (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 112.5 root patch</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>112.5-degree source-aligned root patch</h2><p>Only a 14x14 texture patch from the AI edit is used. Original alpha and all other pixels remain source-owned. Human visual approval remains required.</p><img src="root-patch-closeup.jpg">')
      (E).write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':print(json.dumps(run(),indent=2))
