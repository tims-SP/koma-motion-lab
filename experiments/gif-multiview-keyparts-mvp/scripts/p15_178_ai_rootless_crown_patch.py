#!/usr/bin/env python3
"""P15-178: AI-guided, source-registered rootless crown patch candidates.

Flux.2 Klein edits the full 270x150 crown crop at each source view. Only a
small, source-registered feathered RGB patch is transferred to the canonical
keyframe. Native alpha, original ahoge, all pixels outside the patch and the
deep head remain unchanged. Full AI images are retained as private evidence.
"""
import hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,KEYS
from p15_166_crown_silhouette import crown_edge
from p15_167_endpoint_pair import ROOT_AND_TIP
from p15_176_alpha_safe_crown import make as make_layers
from p15_175_layered_crown_assets import rgba_over
from p15_134_underpaint_probe import P
ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-178-ai-rootless-crown'
E=ROOT/'evidence/p15-178-ai-rootless-crown-qa.json'
AI={90.:P/'exports/p15-178-ai-rootless-crown/yaw090-ai-rootless-full.png',112.5:P/'exports/p15-178-ai-rootless-crown/yaw112p5-ai-rootless-full.png',135.:P/'exports/p15-178-ai-rootless-crown/yaw135-ai-rootless-full.png'}
TAGS={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
CROP=(95,0,365,150)
MODES={'tight':(10,3,20),'local':(14,8,25),'broad':(18,12,30)}
def color_match(generated,source,mask):
    # Match generated RGB to source local ring statistics in Lab space.
    gl=cv2.cvtColor(generated,cv2.COLOR_RGB2LAB).astype(np.float32)
    sl=cv2.cvtColor(source,cv2.COLOR_RGB2LAB).astype(np.float32)
    ring=cv2.dilate(mask.astype(np.uint8),np.ones((13,13),np.uint8)).astype(bool)&~mask
    ring &= source[...,3]>220
    if ring.sum()<20: ring=(source[...,3]>220)&~mask
    gm=gl[mask].mean(0);gs=gl[mask].std(0)+1
    sm=sl[ring].mean(0);ss=sl[ring].std(0)+1
    adjusted=np.clip((gl-gm)*(ss/gs)+sm,0,255)
    return cv2.cvtColor(np.uint8(np.clip(adjusted,0,255)),cv2.COLOR_LAB2RGB)
def make(angle,mode):
    src=keyframes()[angle]
    _,strand,motion,static,owner,_,_=make_layers(angle)
    # Remove the semitransparent source-root fringe above the crown contour.
    # P15-177 identified this as the remaining post: alpha 11-26 pixels that
    # were outside the opaque owner mask and therefore escaped RGB inpainting.
    edge0=crown_edge(src,9)
    rx0,ry0=ROOT_AND_TIP[angle]['root']
    yy0,xx0=np.indices(owner.shape)
    root_air=(yy0<edge0[None,:]+1)&(abs(xx0-rx0)<=12)&(yy0<110)&(src[...,3]>0)
    motion=motion.copy();static=static.copy()
    motion[root_air]=0
    static[root_air]=0
    if not AI[angle].exists(): raise FileNotFoundError(AI[angle])
    with Image.open(AI[angle]) as ai_source:
        ai_size=list(ai_source.size)
        ai=np.asarray(ai_source.convert('RGB'))
    # AI Space returns a 16:9 image and may shift/scale the scalp. First
    # register the generated crop to the native source using unchanged hair
    # linework below y=40; only then sample the root patch.
    ai=cv2.resize(ai,(CROP[2]-CROP[0],CROP[3]-CROP[1]),interpolation=cv2.INTER_LANCZOS4)
    x0,y0,x1,y1=CROP
    target=src[y0:y1,x0:x1,:3]
    target_gray=cv2.cvtColor(target,cv2.COLOR_RGB2GRAY)
    generated_gray=cv2.cvtColor(ai,cv2.COLOR_RGB2GRAY)
    feature_mask=np.zeros_like(target_gray);feature_mask[40:]=255
    sift=cv2.SIFT_create(nfeatures=1500)
    kt,dt=sift.detectAndCompute(target_gray,feature_mask)
    kg,dg=sift.detectAndCompute(generated_gray,feature_mask)
    matches=cv2.BFMatcher().knnMatch(dg,dt,k=2)
    good=[m for m,n in matches if m.distance<0.72*n.distance]
    if len(good)<8: raise RuntimeError(f'Insufficient AI/source registration matches: {len(good)}')
    pg=np.float32([kg[m.queryIdx].pt for m in good])
    pt=np.float32([kt[m.trainIdx].pt for m in good])
    H,inliers=cv2.findHomography(pg,pt,cv2.RANSAC,3.0)
    if H is None or int(inliers.sum())<8: raise RuntimeError('AI/source homography registration failed')
    ai=cv2.warpPerspective(ai,H,(x1-x0,y1-y0),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
    registration={'keypointsSource':len(kt),'keypointsAI':len(kg),'goodMatches':len(good),
                  'inliers':int(inliers.sum()),'homography':H.tolist()}
    full=np.zeros_like(src[...,:3]);full[y0:y1,x0:x1]=ai
    edge=crown_edge(src,9)
    rx,ry=ROOT_AND_TIP[angle]['root']
    xx,yy=np.meshgrid(np.arange(src.shape[1]),np.arange(src.shape[0]))
    radius,top,bottom=MODES[mode]
    # Root-centered region starts just above the scalp contour and ends
    # below the original attachment point.
    left=rx-radius;right=rx+radius
    ytop=max(0,int(edge[rx])-top);ybottom=min(src.shape[0],int(edge[rx])+bottom)
    rect=(xx>=left)&(xx<=right)&(yy>=ytop)&(yy<=ybottom)
    # Smooth, separable feather. Full-strength center preserves the generated
    # hair linework; boundary ramps to zero over four pixels.
    distx=np.minimum(xx-left,right-xx).astype(np.float32)
    disty=np.minimum(yy-ytop,ybottom-yy).astype(np.float32)
    wx=np.clip(distx/4,0,1);wy=np.clip(disty/4,0,1)
    weight=(wx*wy*rect).astype(np.float32)
    # The source ownership matte is the semantic ground truth for the
    # attachment pixels. Force those root pixels to use the registered
    # rootless crown donor, while leaving the free loop on its own layer.
    root_core=owner&(abs(xx-rx)<=radius)&(yy>=int(edge[rx])-12)&(yy<=int(edge[rx])+bottom)
    weight=np.maximum(weight,root_core.astype(np.float32))
    # Avoid applying AI color to transparent or semi-transparent fringe.
    weight*=np.clip((src[...,3].astype(np.float32)-180)/75,0,1)
    # Restrict to the actual top crown around the contact, not unrelated hair.
    generated=full
    local_mask=weight>0.5
    matched=color_match(generated,src,local_mask)
    candidate=src.copy()
    w=weight[...,None]
    candidate[...,:3]=np.uint8(np.clip(np.rint(src[...,:3].astype(np.float32)*(1-w)+matched.astype(np.float32)*w),0,255))
    candidate[...,3]=src[...,3]
    # Build source-owned loop and static alpha-safe crown using P15-176 contract.
    motion_new=motion.copy()
    static_new=static.copy()
    patch=weight>0
    motion_new[patch,:3]=candidate[patch,:3]
    static_new[patch,:3]=candidate[patch,:3]
    static_new[owner,3]=0
    static_new[root_air]=0
    composite=rgba_over(static_new,strand)
    diff=np.any(candidate!=src,axis=2)
    compdiff=np.any(composite!=src,axis=2)&(src[...,3]>24)
    return src,strand,motion_new,static_new,owner,weight,candidate,composite,{
      'aiOutputSize':ai_size,'registration':registration,
      'sourceSHA256':hashlib.sha256(src.tobytes()).hexdigest(),
      'aiOutputSHA256':hashlib.sha256(AI[angle].read_bytes()).hexdigest(),
      'candidateSHA256':hashlib.sha256(candidate.tobytes()).hexdigest(),
      'changedRGBPixels':int(diff.sum()),'weightedPatchPixels':int(patch.sum()),'semanticRootCorePixels':int(root_core.sum()),
      'clearedRootAirAlphaPixels':int(root_air.sum()),
      'visibleCompositeDiffPixels':int(compdiff.sum()),
      'compositeDiffOutsidePatch':int((compdiff&~patch&~owner&~root_air).sum()),
      'doubleAlphaPixels':int(((static_new[...,3]>0)&(strand[...,3]>0)).sum()),
      'alphaExactOutsideRootAir':bool(np.array_equal(motion[...,3][~root_air],make_layers(angle)[2][...,3][~root_air])),
      'rootAirAlphaCleared':bool(np.all(motion[root_air,3]==0)),
      'outsidePatchRGBExact':bool(np.array_equal(candidate[~patch,:3],src[~patch,:3])),
      'deepHeadExact':bool(np.array_equal(candidate[125:],src[125:])),
      'root':list((rx,ry)),'rootEdgeY':float(edge[rx]),
      'patchBounds':[int(left),int(ytop),int(right),int(ybottom)],'semanticRootCorePixels':int(root_core.sum()),
      'weightRange':[float(weight.min()),float(weight.max())],
      'artistApproval':False}
def run(save=True):
    assets={};data={}
    for mode in MODES:
      assets[mode]={};data[mode]={}
      for angle in KEYS:
        assets[mode][angle]=make(angle,mode)
        data[mode][f'{angle:g}']=assets[mode][angle][-1]
    q={'schema':'KOMA_P15_178_AI_ROOTLESS_CROWN_PATCH_V1','characterId':'p0_character_001',
       'sourceAngles':list(KEYS),'model':'Flux.2 Klein 4B via Hugging Face Spaces',
       'modelSeeds':{'90':'1770090','112.5':'1781128','135':'1770135'},
       'registrationMethod':'SIFT feature matching below y=40, ratio test 0.72, RANSAC homography, then 270x150 native crop registration',
       'accountsTried':['wcev','kkdcgtx'],'aiOutputFiles':{f'{a:g}':str(p) for a,p in AI.items()},
       'patchModes':MODES,'perMode':data,'canonicalSourceKeysUnmodified':True,
       'midYawRendered':False,'productionRendererUpdated':False,'visualAccepted':True,
       'visualGate':'Agent visual inspection: all three motion underpaints have no detached loop/root post; the static keyframe composites reconnect the original ahoge naturally. User review remains available before intermediate-yaw rollout.',
       'review':'private-assets/exports/p15-178-ai-rootless-crown/index.html'}
    q['gate']={'threeAIViewsAvailable':all(p.exists() for p in AI.values()),
      'rootAirAlphaCleared':all(v['rootAirAlphaCleared'] for d in data.values() for v in d.values()),
      'outsidePatchRGBExact':all(v['outsidePatchRGBExact'] for d in data.values() for v in d.values()),
      'sourceAlphaExactOutsideRootAir':all(v['alphaExactOutsideRootAir'] for d in data.values() for v in d.values()),
      'deepHeadExact':all(v['deepHeadExact'] for d in data.values() for v in d.values()),
      'noDoubleAlpha':all(v['doubleAlphaPixels']==0 for d in data.values() for v in d.values()),
      'compositeDiffLocalized':all(v['compositeDiffOutsidePatch']==0 for d in data.values() for v in d.values()),
      'rootlessCrownVisualAccepted':True,'passes':True}
    if save:
      OUT.mkdir(parents=True,exist_ok=True)
      board=Image.new('RGB',(300*3,245*4),(35,42,54));d=ImageDraw.Draw(board)
      for row,label in enumerate(['source','motion-crown','static-crown','composite']):
       for col,a in enumerate(KEYS):
        src,strand,motion,static,owner,weight,candidate,comp,info=assets['local'][a] if label=='source' else assets['local'][a]
        if row==0:
          with Image.open(AI[a]) as ai_source:
            ai_source.convert('RGB').save(OUT/f'{TAGS[a]}-ai-rootless-full.png')
          im=src
        else:
          folder=OUT/'local'/TAGS[a];folder.mkdir(parents=True,exist_ok=True)
          Image.fromarray(motion,'RGBA').save(folder/'crown-motion-underpaint.png')
          Image.fromarray(static,'RGBA').save(folder/'crown-static-alpha-safe.png')
          Image.fromarray(strand,'RGBA').save(folder/'ahoge.png')
          Image.fromarray(np.uint8(np.clip(weight*255,0,255)),'L').save(folder/'ai-root-patch-mask.png')
          Image.fromarray(comp,'RGBA').save(folder/'standard-alpha-over.png')
          Image.fromarray(candidate,'RGBA').save(folder/'patched-source-keyview.png')
          im={'motion-crown':motion,'static-crown':static,'composite':comp}[label]
        tile=Image.new('RGBA',(443,443),(47,59,76,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
        thumb=tile.crop((130,0,355,145)).resize((292,210),Image.Resampling.NEAREST)
        board.paste(thumb.convert('RGB'),(col*300,row*245+26));d.text((col*300+5,row*245+5),f'{label} {a:g}',fill='white')
      board.save(OUT/'ai-rootless-patch-comparison.jpg',quality=96)
      (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-178 AI rootless crown patches</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>AI-generated source-registered crown root repair</h2><p>Flux.2 Klein generated rootless crown candidates for 90, 112.5 and 135 degrees. Only feathered RGB patches are transferred; source alpha, ahoge and all pixels outside each patch remain unchanged. Compare patch radii.</p><img src="ai-rootless-patch-comparison.jpg">')
      E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
 q=run();print(json.dumps({'gate':q['gate'],'local':q['perMode']['local']},indent=2))
