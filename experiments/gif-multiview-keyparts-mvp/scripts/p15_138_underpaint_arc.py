#!/usr/bin/env python3
"""Evaluate independently painted rear scalp underpaint in static and yaw transitions."""
import json,hashlib,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from p15_134_underpaint_probe import P,SOURCE,rgba,transform,compose,move,background_rgb
from p15_135_closed_hair_mask import closed_mask,split
from p15_121_rear_arc_render import load
from flow_render import get_flow,morph
SRC=P/'p15-138-rear-scalp/underpaint-native.png'
META=P/'p15-138-rear-scalp/generation-result.json'
OUT=P/'exports/p15-138-rear-scalp';E=ROOT/'evidence/p15-138-rear-scalp-qa.json'
ANGLES=(90.,101.25,112.5,123.75,135.)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def validation():
    d=json.loads(META.read_text())
    assert d.get('tool_name')=='image_gen.imagegen'
    assert d.get('source_path') and d.get('output_path')
    hash_val=d.get('sha256') or d.get('SHA256')
    assert hash_val==sha(SRC),(hash_val,sha(SRC))
    im=Image.open(SRC);assert im.mode=='RGBA' and im.size==(1254,1254)
    return d

def composite_with_painted(source,under,dx):
    mask,_=closed_mask(source);hair,rest=split(source,mask)
    return compose(compose(under,rest),move(hair,dx,0))

def holes(source,x):
    return (source[...,3]>160)&(x[...,3]<64)
def regions(x):
    positions={'eye':(175,295,265,365),'rear_scalp':(52,305,85,245),'neck':(285,370,140,320),'ear':(180,325,195,280)}
    d={'all':int(x.sum())}
    for name,(a,b,c,e) in positions.items():d[name]=int(x[a:b,c:e].sum())
    return d

def register(candidate,source):
    # Local size / registration sweep. Optimize only jacket below hair (avoid overfitting hidden anatomy).
    roi=np.s_[335:435,80:375]
    a=source[roi][...,3]>128
    proposals=[]
    for scale in (.94,.97,1.00,1.03):
      for dx in (-4,4,12,20):
       for dy in (4,12,20):
        shifted=transform(candidate,scale,dx,dy)
        b=shifted[roi][...,3]>128
        iou=(a&b).sum()/max(1,(a|b).sum())
        proposals.append((float(iou),scale,dx,dy))
    score,scale,dx,dy=max(proposals)
    return transform(candidate,scale,dx,dy),{'jacketAlphaIoU':round(score,5),'scale':scale,'translationXY':[dx,dy]}

def merge_rear(old,new,feather=12):
    yy,xx=np.indices(old.shape[:2],dtype=np.float32)
    # New independently painted material owns rear scalp; old anatomical art
    # still owns near eye, ear, lower nape, collar and jacket.
    left=np.clip((275-xx)/feather,0,1)
    upper=np.clip((313-yy)/feather,0,1)
    blend=cv2.GaussianBlur((left*upper).astype(np.float32),(0,0),2)
    blend=np.clip(blend,0,1)[...,None]
    oldf=old.astype(np.float32)/255
    newf=new.astype(np.float32)/255
    al=oldf[...,3:4]*(1-blend)+newf[...,3:4]*blend
    rgb=(oldf[...,:3]*oldf[...,3:4]*(1-blend)+newf[...,:3]*newf[...,3:4]*blend)/np.maximum(al,1e-6)
    result=np.uint8(np.round(np.clip(np.concatenate([rgb,al],axis=-1)*255,0,255)))
    result[result[...,3]==0]=0
    return result

def run(save=True):
    meta=validation()
    source=rgba(SOURCE)
    raw=np.asarray(Image.open(SRC).convert('RGBA').resize((443,443),Image.Resampling.LANCZOS))
    new_under,registration=register(raw,source)
    old_under=rgba(P/'exports/p15-137-occlusion-regions/eye_08-underpaint.png')
    hybrid=merge_rear(old_under,new_under)
    view={'p15_137':old_under,'new_painted':new_under,'hybrid_rear':hybrid}
    cases={};frames={}
    roi=np.s_[125:350,125:390]
    for name,under in view.items():
        frames[name]={i:composite_with_painted(source,under,i) for i in (0,12,24)}
        cases[name]={str(i):{'alphaHoles':regions(holes(source,img)),
                 'rgbMAE':round(float(np.abs(background_rgb(img)[roi]-background_rgb(source)[roi]).mean()),4)}
                 for i,img in frames[name].items()}
    # A second, specifically yaw-related check: insert the newly painted material behind
    # the original mid-keyframe, keeping 90/135 source pixels verbatim.
    keys=load();before={90.:keys[90],112.5:frames['p15_137'][0],135.:keys[135]}
    after={90.:keys[90],112.5:frames['new_painted'][0],135.:keys[135]}
    hybrid_yaw={90.:keys[90],112.5:frames['hybrid_rear'][0],135.:keys[135]}
    y,x=np.indices((443,443),dtype=np.float32);grid=np.stack((x,y),axis=-1)
    transition={}
    for name,inputs in [('p15_137',before),('new_painted',after),('hybrid_rear',hybrid_yaw)]:
        pairs={(90.,112.5):get_flow(inputs[90.],inputs[112.5],'dis'),
               (112.5,135.):get_flow(inputs[112.5],inputs[135.],'dis')}
        rendered=[]
        for angle in ANGLES:
            if angle in inputs:arr=inputs[angle].copy()
            else:
                a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
                arr=morph(inputs[a],inputs[b],*pairs[a,b],(angle-a)/(b-a),grid)
            rendered.append(arr)
        err=[round(float(np.abs(background_rgb(a)-background_rgb(b)).mean()),4)
             for a,b in zip(rendered,rendered[1:])]
        transition[name]={'maxAdjacentCompositeRGBMAE':max(err),'adjacentCompositeRGBMAE':err,
         'nativeSource90And135PixelExact':np.array_equal(rendered[0],keys[90]) and np.array_equal(rendered[-1],keys[135])}
        frames[name+'_yaw']=rendered
    qa={'schema':'KOMA_P15_138_NATIVE_REAR_SCALP_ARC_V1','characterId':'p0_character_001',
     'nativeImageSHA256':sha(SRC),'nativeRGBA':True,'sourcePaintingPreserved':True,
     'registration':registration,'staticStress':cases,'transition':transition,'yawAngles':list(ANGLES),
     'newModelUnderpaint':'private-assets/p15-138-rear-scalp/underpaint-native.png',
     'physicalHairTopologyVerified':False,'facialIdentityApproved':False,
     'rearScalpArtistApproved':False,'continuousVisualAccepted':False,
     'review':'private-assets/exports/p15-138-rear-scalp/index.html',
     'next':'Check new scalp source for visible identity/ink differences, then correct source-owned hair and face/neck geometry before production admission.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        Image.fromarray(new_under,'RGBA').save(OUT/'registered-underpaint.png')
        board=Image.new('RGB',(350*4,395*3),(35,41,51));d=ImageDraw.Draw(board)
        for j,name in enumerate(('p15_137','new_painted','hybrid_rear')):
            for i,(label,im) in enumerate([('underpaint',view[name])]+[(str(dx)+'px',frames[name][dx]) for dx in (0,12,24)]):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
                board.paste(tile.convert('RGB').resize((344,344),Image.Resampling.LANCZOS),(350*i,j*395+31))
                d.text((350*i+8,j*395+7),f'{name} / {label}',fill='white')
        board.save(OUT/'stress-comparison.jpg',quality=93)
        yaw=Image.new('RGB',(310*5,349*3),(35,41,51));drawer=ImageDraw.Draw(yaw)
        for row,name in enumerate(('p15_137','new_painted','hybrid_rear')):
            for i,(angle,im) in enumerate(zip(ANGLES,frames[name+'_yaw'])):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
                yaw.paste(tile.convert('RGB').resize((305,305),Image.Resampling.LANCZOS),(310*i,row*349+28))
                drawer.text((310*i+5,row*349+5),f'{name} / {angle:g}',fill='white')
                Image.fromarray(im,'RGBA').save(OUT/(f'{name}-yaw{angle:06.2f}'.replace('.','p')+'.png'))
        yaw.save(OUT/'yaw-comparison.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 rear scalp source study</title><style>body{background:#202832;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>112.5° newly painted rear-scalp underpaint</h2><p>Independent source painting registered for 0/12/24px hair reveal and a 90–135° DIS transition. Native key views are preserved. Inferred physical anatomy remains subject to visual QA.</p><img src="stress-comparison.jpg"><h2>90–135° transition</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    return qa
if __name__=='__main__':
    q=run()
    print(json.dumps({'registration':q['registration'],'staticStress':q['staticStress'],'transition':q['transition']},indent=2))
