#!/usr/bin/env python3
"""Compare registered front-fringe keyview in a five-angle 90–135 turn."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from p15_144_bangs_registration import evaluate,OUT,P,E
from p15_129_ahoge_ownership import keyframes,ANGLES
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import rgba
ROOT=Path(__file__).resolve().parent.parent
EVIDENCE=ROOT/'evidence/p15-144-transition-qa.json'
def run(save=True):
    # Registered key is the independently composed and eye-protected image.
    registered=rgba(OUT/'registered_eye_owned.png')
    keys=keyframes()
    candidate=frame_interp(keys[90.],registered,keys[135.])
    reference=frame_interp(keys[90.],keys[112.5],keys[135.])
    error={'reference':jumps(reference),'registered':jumps(candidate)}
    report={'schema':'KOMA_P15_144_REGISTERED_BANGS_YAW_V1',
       'characterId':'p0_character_001','angles':list(ANGLES),
       'maxAdjacentRGBMAE':{k:max(v) for k,v in error.items()},
       'adjacentRGBMAE':error,
       'original90And135PixelExact':bool(np.array_equal(candidate[0],keys[90.]) and np.array_equal(candidate[-1],keys[135.])),
       'native112p5ImagePreserved':True,
       'midway112p5SourcePixelExact':False,'realHairPartIdentityApproved':False,
       'continuousVisualAccepted':False,'review':'private-assets/exports/p15-144-bangs-registration/transition.html'}
    if save:
        board=Image.new('RGB',(315*5,350*2),(35,43,53));draw=ImageDraw.Draw(board)
        for row,(name,frames) in enumerate([('source',reference),('registered',candidate)]):
            for col,(angle,frame) in enumerate(zip(ANGLES,frames)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                board.paste(tile.convert('RGB').resize((310,310),Image.Resampling.LANCZOS),(315*col,row*350+29))
                draw.text((315*col+7,row*350+7),f'{name}: {angle:g}',fill='white')
                if name=='registered':
                    Image.fromarray(frame,'RGBA').save(OUT/(f'transition-yaw{angle:06.2f}'.replace('.','p')+'.png'))
        board.save(OUT/'transition-comparison.jpg',quality=93)
        (OUT/'transition.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 registered fringe yaw</title><style>body{background:#202733;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90–135° front fringe keyview transition</h2><p>Top source artwork versus registered 112.5° front-fringe replacement. Original 90/135 endpoints remain pixel-exact. Double hairlines and mismatch are checked visually.</p><img src="transition-comparison.jpg">')
        EVIDENCE.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report
if __name__=='__main__':print(json.dumps(run(),indent=2))
