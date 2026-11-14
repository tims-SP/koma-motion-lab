#!/usr/bin/env python3
"""Register independent ahoge against original loop ink while retaining native reference.

Uses a conservative image-space mask limited to pixels ABOVE the crown.
The crown/loop attachment remains an unresolved painter-authored boundary.
"""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_148_native_ahoge_review import actual_source,OUT,P
from p15_134_underpaint_probe import SOURCE,rgba,compose,background_rgb
from p15_129_ahoge_ownership import keyframes,ANGLES
from p15_128_keyart_registration import frame_interp,jumps
ROOT=Path(__file__).resolve().parent.parent
E=ROOT/'evidence/p15-148-ahoge-registration-qa.json'

def shift(image,scale,dx,dy):
    mid=221.5
    mat=np.float32([[scale,0,mid*(1-scale)+dx],[0,scale,mid*(1-scale)+dy]])
    return cv2.warpAffine(image,mat,(443,443),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)

def loop_target(source):
    y,x=np.indices((443,443))
    # Above the crown at this yaw the loop is a distinct alpha component.
    return (source[...,3]>96)&(y<54)&(x>245)&(x<337)
def register(source,part):
    desired=loop_target(source)
    tests=[]
    y,x=np.indices((443,443))
    feature=(y<55)&(x>220)&(x<360)
    for scale in (.80,.90,1.,1.10,1.20):
      for dx in range(-28,49,4):
       for dy in range(-18,23,4):
        image=shift(part,scale,dx,dy)
        current=(image[...,3]>128)&feature
        inter=int((current&desired).sum())
        union=int((current|desired).sum())
        score=inter/max(1,union)
        tests.append((score,scale,dx,dy,inter,union))
    best=max(tests)
    score,scale,dx,dy,inter,union=best
    return shift(part,scale,dx,dy),{'iouAboveCrown':round(score,5),'scale':scale,'shiftXY':[dx,dy],
       'intersectionPixels':inter,'unionPixels':union}

def replace_loop(source,registered,erase_y=56):
    y,x=np.indices((443,443))
    # Only the free-standing old loop above crown can be independently erased.
    # Keep all source crown/root/face pixels at y>=56 untouched.
    old=(source[...,3]>32)&(y<erase_y)&(x>245)&(x<337)
    keep=source.copy();keep[old]=0
    new=registered.copy();new[y>=erase_y]=0
    new[(x<230)|(x>350)]=0
    return compose(keep,new),old,int((new[...,3]>128).sum())

def evaluate(save=True):
    source=rgba(SOURCE)
    part,_=actual_source()
    registered,fit=register(source,part)
    candidate,old,new_count=replace_loop(source,registered)
    direct=compose(source,part)
    key=keyframes()
    variants={'canonical':source,'direct_overlay':direct,'registered_overlay':compose(source,registered),
              'loop_replacement':candidate}
    scores={}
    for name,image in variants.items():
        frames=frame_interp(key[90.],image,key[135.])
        scores[name]={'maxAdjacentRGBMAE':max(jumps(frames)),'adjacentRGBMAE':jumps(frames),
           'sourceEndpoint90And135PixelExact':np.array_equal(frames[0],key[90.]) and np.array_equal(frames[-1],key[135.]),
           'sourceDifferenceMAE':round(float(np.abs(background_rgb(image)-background_rgb(source)).mean()),4)}
    original_lower=bool(np.array_equal(source[56:],candidate[56:]))
    q={'schema':'KOMA_P15_148_AHOGE_SPATIAL_REGISTRATION_V1','characterId':'p0_character_001',
       'sourceYaw':112.5,'nativeGeneratedSourceUnchanged':True,'fit':fit,'freeStandingSourcePixelsErased':int(old.sum()),
       'replacementOpaquePixelsAboveCrown':new_count,'sourcePixelsBelowCrownUnmodified':original_lower,
       'methods':scores,'sourceArtAndIdentityVerified':False,'hiddenRootPaintVerified':False,
       'visualAccepted':False,'review':'private-assets/exports/p15-148-native-ahoge/registration.html',
       'next':'Draw fully matching complete root and visible loop contour plus crown hidden underpaint; validate physically registered three-yaw isolated hair layers before VDD.'}
    if save:
        Image.fromarray(registered,'RGBA').save(OUT/'registered-ahoge.png')
        Image.fromarray(candidate,'RGBA').save(OUT/'loop-replacement.png')
        board=Image.new('RGB',(345*4,390),(35,42,54));d=ImageDraw.Draw(board)
        for col,(name,im) in enumerate(variants.items()):
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
            board.paste(tile.convert('RGB').resize((338,338),Image.Resampling.LANCZOS),(345*col,33))
            d.text((345*col+7,8),name,fill='white')
        board.save(OUT/'registration-comparison.jpg',quality=94)
        images=[('canonical',frame_interp(key[90.],source,key[135.])),
                ('loop_replacement',frame_interp(key[90.],candidate,key[135.]))]
        yaw=Image.new('RGB',(305*5,345*2),(35,42,54));draw=ImageDraw.Draw(yaw)
        for row,(name,frames) in enumerate(images):
            for i,(angle,im) in enumerate(zip(ANGLES,frames)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
                yaw.paste(tile.convert('RGB').resize((300,300),Image.Resampling.LANCZOS),(305*i,345*row+30))
                draw.text((305*i+7,345*row+7),f'{name} {angle:g}',fill='white')
        yaw.save(OUT/'registration-yaw.jpg',quality=93)
        (OUT/'registration.html').write_text('<!doctype html><meta charset="utf-8"><title>112.5 ahoge registration</title><style>body{font:16px system-ui;background:#202833;color:#eee}img{max-width:100%}</style><h2>Independent ahoge fitted to the canonical free loop</h2><p>Above-crown pixel registration and loop replacement diagnostic; root underpainting/strand identity await approval.</p><img src="registration-comparison.jpg"><h2>Yaw rendering</h2><img src="registration-yaw.jpg">')
        E.write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n')
    return q
if __name__=='__main__':
    q=evaluate();print(json.dumps({'fit':q['fit'],'sourceLowerExact':q['sourcePixelsBelowCrownUnmodified'],'methods':q['methods']},indent=2))
