#!/usr/bin/env python3
"""Register two native imagegen candidates, select a bracketed 112.5° view, and render a local keyview transition."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
import cv2
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from flow_render import get_flow,morph
from p15_121_rear_arc_render import load
P=ROOT/'private-assets';OUT=P/'exports/p15-127-yaw112p5-review';E=ROOT/'evidence/p15-127-keyview-transition-qa.json'
A=P/'p15-127-yaw112p5/yaw112p5-native.png'
B=P/'p15-127-yaw112p5/candidate-b/native.png'
SAMPLES=(90,101.25,112.5,123.75,135)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(path):return np.asarray(Image.open(path).convert('RGBA').resize((443,443),Image.Resampling.LANCZOS)).copy()
def face_skin_count(arr):
    r,g,b=[arr[...,i].astype(np.int16) for i in (0,1,2)]
    y,x=np.indices((443,443))
    skin=(r>g+15)&(g>b+4)&(r>125)&(g>90)&(x>250)&(y>145)&(y<340)&(arr[...,3]>64)
    return int(skin.sum())
def validate_native(path,meta):
    d=json.loads(meta.read_text())
    assert d['actual_image_tool_used'] and d['tool']=='image_gen.imagegen'
    assert sha(path)==d['sha256']
    with Image.open(path) as im:assert im.mode=='RGBA' and im.size==(1254,1254)
    return {'sha256':d['sha256'],'actualImageGeneration':True,'size':[1254,1254]}
def render(save=True):
    native={90:load()[90],112.5:key(B),135:load()[135]}
    candidate_a=key(A)
    info={'candidateA':validate_native(A,A.with_name('generation-result.json')),
          'candidateB':validate_native(B,B.with_name('generation-result.json'))}
    counts={name:face_skin_count(image) for name,image in [('90',native[90]),('A',candidate_a),('B',native[112.5]),('135',native[135])]}
    # Midpoint selection based on visible-face coverage bracket and visual source review,
    # not a claim that requested physical yaw has been measured.
    target=(counts['90']+counts['135'])/2
    assert counts['135']<counts['B']<counts['90']
    info['candidateA']['faceSkinPixels']=counts['A'];info['candidateB']['faceSkinPixels']=counts['B']
    flows={(90,112.5):get_flow(native[90],native[112.5],'dis'),
           (112.5,135):get_flow(native[112.5],native[135],'dis')}
    y,x=np.indices((443,443),dtype=np.float32);grid=np.stack([x,y],axis=-1)
    frames=[]
    for angle in SAMPLES:
        if angle in native:frame=native[angle].copy()
        else:
            a,b=(90,112.5) if angle<112.5 else (112.5,135)
            frame=morph(native[a],native[b],*flows[a,b],(angle-a)/(b-a),grid)
        frames.append(frame)
    def bg(arr):
        alpha=arr[...,3:4].astype(np.float32)/255
        return arr[...,:3]*alpha+(1-alpha)*np.array([49,61,78])
    adjacent=[round(float(np.abs(bg(a)-bg(b)).mean()),4) for a,b in zip(frames,frames[1:])]
    original=all(np.array_equal(native[k],frames[SAMPLES.index(k)]) for k in native)
    metrics={'maxAdjacentCompositeRGBMAE':max(adjacent),'adjacentCompositeRGBMAE':adjacent,
             'nativeSourceEndpointPixelExact':original,
             'faceSkinPixelCounts':counts,'expectedFaceSkinMidpoint':target,
             'candidateBWithinFaceVisibilityBracket':True}
    if save:
        OUT.mkdir(exist_ok=True,parents=True)
        Image.fromarray(native[112.5],'RGBA').save(OUT/'yaw112p5-selected-review.png')
        Image.fromarray(candidate_a,'RGBA').save(OUT/'yaw112p5-comparison-review.png')
        folder=OUT/'transition';folder.mkdir(exist_ok=True)
        for angle,frame in zip(SAMPLES,frames):
            Image.fromarray(frame,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
        board=Image.new('RGB',(350*5,395*2),(36,43,54));draw=ImageDraw.Draw(board)
        for i,angle in enumerate(SAMPLES):
            for j,arr in enumerate([frames[i],np.asarray(Image.open(P/'exports/p15-124-face-safe'/(f'yaw{angle:06.2f}'.replace('.','p')+'.png')).convert('RGBA'))]):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(arr,'RGBA'))
                board.paste(tile.convert('RGB').resize((345,345),Image.Resampling.LANCZOS),(i*350,j*395+31))
                draw.text((i*350+9,j*395+7),('independent key / ' if j==0 else 'prior / ')+f'{angle:g}',fill='white')
        board.save(OUT/'transition-comparison.jpg',quality=94)
        compare=Image.new('RGB',(350*4,395),(36,43,54));d=ImageDraw.Draw(compare)
        for i,(name,img) in enumerate([('90',native[90]),('candidate A',candidate_a),('candidate B',native[112.5]),('135',native[135])]):
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(img,'RGBA'))
            compare.paste(tile.convert('RGB').resize((345,345),Image.Resampling.LANCZOS),(i*350,31));d.text((i*350+9,7),name,fill='white')
        compare.save(OUT/'candidates-comparison.jpg',quality=94)
        previews=[]
        for frame in frames+frames[-2:0:-1]:
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
            previews.append(tile.convert('RGB'))
        previews[0].save(OUT/'transition-loop.gif',save_all=True,append_images=previews[1:],duration=160,loop=0,optimize=False)
        (OUT/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>P0 112.5° source-painting review</title><style>body{font:16px system-ui;background:#202833;color:#eee}img{max-width:100%}</style><h2>Independent model-rendered 112.5° source candidates</h2><p>Candidate B is selected for continuity evaluation based on face-visibility bracket and visual reference. Physical yaw, linework continuity and semantic ArtMesh remain unapproved.</p><img src="candidates-comparison.jpg"><h2>90°–135° local inbetween comparison</h2><img src="transition-comparison.jpg"><h2>Animated preview</h2><img src="transition-loop.gif">')
        result={'schema':'KOMA_P15_127_NATIVE_MIDVIEW_TRANSITION_V1','characterId':'p0_character_001',
                'targetYaw':112.5,'sourceAngles':[90,135],
                'nativeGenerationCandidates':info,'selectedCandidate':'B',
                'candidateSelection':'face coverage bracket plus visual continuity hypothesis',
                'renderMethod':'bidirectional DIS flow between independently generated 112.5° painting and existing 90°/135° source frames',
                'metrics':metrics,'artisticYawVerified':False,'semanticPartIdentityVerified':False,
                'hiddenUnderpaintVerified':False,'fullSequenceVisualAccepted':False,
                'review':'private-assets/exports/p15-127-yaw112p5-review/index.html',
                'next':'Inspect independent midview key in 90–135 sequence. Fix silhouette, line-art palette, bow and hair correspondence via source art before admitting it as production VDD source.'}
        E.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return metrics
if __name__=='__main__':print(json.dumps(render(),indent=2))
