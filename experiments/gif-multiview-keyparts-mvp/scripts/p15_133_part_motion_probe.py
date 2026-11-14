#!/usr/bin/env python3
"""Animate visible source-part candidates against the P15-129 whole-view benchmark."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from p15_133_semantic_layer_source import ROLES
from p15_129_ahoge_ownership import keyframes,ANGLES
from p15_128_keyart_registration import jumps
from flow_render import get_flow,morph
P=ROOT/'private-assets';OUT=P/'exports/p15-133-part-motion';E=ROOT/'evidence/p15-133-part-motion-qa.json'

def read(view,role):
    return np.asarray(Image.open(P/'exports/p15-133-semantic-source'/f'yaw{view:g}'.replace('.','p')/(role+'.png')).convert('RGBA')).copy()
def layer_mid(a,b,t,grid):
    f=get_flow(a,b,'dis')
    return morph(a,b,*f,t,grid)
def compose_parts(layers,shape):
    pic=Image.new('RGBA',(shape[1],shape[0]),(0,0,0,0))
    for role in ('uniform.visible','collar.visible','skin.visible','bow.visible','hair.visible'):
        pic.alpha_composite(Image.fromarray(layers[role],'RGBA'))
    return np.asarray(pic).copy()
def compare(save=True):
    native=keyframes();h,w=native[90.].shape[:2]
    ys,xs=np.indices((h,w),dtype=np.float32);grid=np.stack((xs,ys),axis=-1)
    layers={v:{r:read(v,r) for r in ROLES} for v in (90.,112.5,135.)}
    frames=[]
    for angle in ANGLES:
        if angle in native:frames.append(native[angle].copy());continue
        a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
        t=(angle-a)/(b-a)
        warped={r:layer_mid(layers[a][r],layers[b][r],t,grid) for r in ROLES}
        frames.append(compose_parts(warped,(h,w)))
    baseline=[np.asarray(Image.open(P/'exports/p15-129-ahoge-owner/nearest_key_owner'/(f'yaw{a:06.2f}'.replace('.','p')+'.png')).convert('RGBA')).copy() for a in ANGLES]
    baseline_jump=jumps(baseline);candidate_jump=jumps(frames)
    exact=all(np.array_equal(frames[ANGLES.index(a)],native[a]) for a in native)
    qa={'schema':'KOMA_P15_133_SEMANTIC_MOTION_PROBE_V1','characterId':'p0_character_001','yawSamples':list(ANGLES),
        'parts':list(ROLES),'candidateAlgorithm':'per-part DIS morph of disjoint source-visible color/region masks, composited in an approximate painter order',
        'baselineMaxAdjacentCompositeRGBMAE':max(baseline_jump),'candidateMaxAdjacentCompositeRGBMAE':max(candidate_jump),
        'baselineAdjacentCompositeRGBMAE':baseline_jump,'candidateAdjacentCompositeRGBMAE':candidate_jump,
        'nativeKeyframePixelExact':exact,'semanticArtMeshVerified':False,'hiddenUnderpaintVerified':False,
        'artistVisualAccepted':False,'visualAcceptance':False,
        'review':'private-assets/exports/p15-133-part-motion/index.html',
        'next':'Replace automated appearance masks with source-painted semantic parts and underpaint, then use physical visibility and anchor constraints for 90–135 VDD.'}
    if save:
        OUT.mkdir(exist_ok=True,parents=True)
        contact=Image.new('RGB',(320*5,355*2),(36,42,53));draw=ImageDraw.Draw(contact)
        for row,(name,sequence) in enumerate((('source-owned',baseline),('semantic-part-morph',frames))):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(angle,arr) in enumerate(zip(ANGLES,sequence)):
                Image.fromarray(arr,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(arr,'RGBA'))
                contact.paste(tile.convert('RGB').resize((315,315),Image.Resampling.LANCZOS),(320*col,355*row+29))
                draw.text((320*col+7,355*row+7),f'{name} / {angle:g}',fill='white')
        contact.save(OUT/'comparison.jpg',quality=93)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 semantic visible-part motion</title><style>body{background:#202733;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>P0 90–135° source-owned vs independent visible-part deformation</h2><p>Actual 5-frame rendering with provisional appearance-based semantic masks; original keyframes preserved. Hidden geometry and hand-painted parts pending.</p><img src="comparison.jpg">')
        E.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'baseline':max(baseline_jump),'candidate':max(candidate_jump),'nativeKeyframePixelExact':exact}))
    return qa
if __name__=='__main__':compare()
