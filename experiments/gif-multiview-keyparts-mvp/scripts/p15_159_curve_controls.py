#!/usr/bin/env python3
"""Five-control image-space loop correspondence and crown-attachment diagnostics.

An independent upper-loop contour is tracked by apex/left/right/root-adjacent
control points. All source material remains byte-exact; this is not a claim
that generated geometry is a painted underlayer or a physical 3D curve.
"""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image,ImageDraw
from p15_158_loop_correspondence import anchors
from p15_153_source_topology import extract,ROOT
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose,background_rgb
OUT=P/'exports/p15-159-curve-controls'
E=ROOT/'evidence/p15-159-curve-controls-qa.json'
SIZE=443
CUT=54

def control_points(part,angle):
    ys,xs=np.where(part[:CUT,:,3]>96)
    assert len(xs)>500
    root,apex=anchors(angle)
    # Landmarks are source-raster control proposals; collect left/right arch
    # points at mid upper-hair height, plus a lower right root leg.
    middle=(ys>=int(max(10,(apex[1]+CUT)*.5))-5)&(ys<=int(max(10,(apex[1]+CUT)*.5))+5)
    xm=xs[middle];ym=ys[middle]
    if len(xm)<20:xm=xs;ym=ys
    li=np.argmin(xm);ri=np.argmax(xm)
    # Fifth control is the lowest source-connected point near the outer root.
    low=(ys>=CUT-8)
    if np.any(low):
        xl=xs[low];yl=ys[low];i=np.argmax(xl)
        lower=np.array([xl[i],yl[i]],np.float32)
    else:lower=root.copy()
    return np.stack([root,apex,np.array([xm[li],ym[li]],np.float32),
                     np.array([xm[ri],ym[ri]],np.float32),lower])

def inverse_deform(source,src_controls,dst_controls,radius=35):
    # Iterative inverse Gaussian radial displacement, smoothed throughout
    # material. Source-color samples remain source-owned.
    yy,xx=np.indices((SIZE,SIZE),np.float32)
    sample_x=xx.copy();sample_y=yy.copy()
    delta=dst_controls-src_controls
    for _ in range(3):
        wx=np.zeros_like(xx);wy=np.zeros_like(xx);denom=np.full_like(xx,1e-6)
        for pt,move in zip(src_controls,delta):
            dist=(sample_x-pt[0])**2+(sample_y-pt[1])**2
            weight=np.exp(-dist/(2*radius*radius)).astype(np.float32)
            wx+=weight*move[0];wy+=weight*move[1];denom+=weight
        sample_x=xx-wx/denom
        sample_y=yy-wy/denom
    return cv2.remap(source,sample_x,sample_y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)

def add_root_bridge(frame,part,target,mode='bridge'):
    # A local registration probe may connect the upper loop to an existing
    # crown pixel. The bridge is synthesized, so it is kept out of production.
    image=part.copy()
    alpha=image[...,3]>96
    yy,xx=np.indices(alpha.shape)
    below=alpha&(yy>=CUT-9)&(yy<CUT)
    if below.any():
        by,bx=np.where(below)
        # Nearest visible source endpoint to interpolated root control.
        idx=np.argmin((bx-target[0])**2+(by-target[1])**2)
        p0=(int(bx[idx]),int(by[idx]))
        # Only connect toward crown line y54, retaining source crown below.
        p1=(int(np.clip(target[0],0,442)),CUT)
        if mode=='bridge':
            color=image[p0[1],p0[0]].copy()
            if color[3]<96:color=np.array([210,139,165,255],np.uint8)
            cv2.line(image,p0,p1,[int(v) for v in color],thickness=2,lineType=cv2.LINE_AA)
    base=frame.copy();base[:CUT]=0
    # Existing lower crown is unmodified; upper loop owns visible region.
    return compose(base,image)

def evaluate(save=True):
    source=keyframes()
    loops={a:extract(source[a])[0]['loop_visible'] for a in KEYS}
    controls={a:control_points(loops[a],a) for a in KEYS}
    baseline=frame_interp(source[90.],source[112.5],source[135.])
    outputs={'reference':baseline}
    metadata={}
    for mode in ('controls_only','controls_bridge'):
        seq=[];middle={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                seq.append(source[angle].copy());continue
            left,right=(90.,112.5) if angle<112.5 else (112.5,135.)
            t=(angle-left)/(right-left)
            desired=(1-t)*controls[left]+t*controls[right]
            owner=left if t<=.5 else right
            warped=inverse_deform(loops[owner],controls[owner],desired)
            rendered=add_root_bridge(baseline[i],warped,desired[0],mode='bridge' if mode=='controls_bridge' else 'none')
            seq.append(rendered)
            middle[f'{angle:g}']={'owner':owner,
                'curveControls':desired.round(2).tolist(),
                'upperPartPixels':int((warped[:CUT,:,3]>96).sum())}
        outputs[mode]=seq
        metadata[mode]=middle
    results={}
    for mode,seq in outputs.items():
        results[mode]={
            'maxAdjacentRGBMAE':max(jumps(seq)),
            'adjacentRGBMAE':jumps(seq),
            'topConnectedComponents':[top_components(frame) for frame in seq],
            'sourceKeyframesPixelExact':all(np.array_equal(seq[ANGLES.index(a)],source[a]) for a in KEYS),
            'crownBelowCutPixelExact':all(np.array_equal(seq[ANGLES.index(a)][CUT:],baseline[ANGLES.index(a)][CUT:]) for a in (101.25,123.75)),
            'midview':metadata.get(mode,{})}
    q={'schema':'KOMA_P15_159_FIVE_CONTROL_CURVE_V1',
       'characterId':'p0_character_001','sourceAngles':list(KEYS),'sampleAngles':list(ANGLES),
       'viewControls':{f'{a:g}':controls[a].round(2).tolist() for a in KEYS},
       'controlDefinitions':['proposed_root','apex','left_mid_contour','right_mid_contour','lower_outer_leg'],
       'renderers':results,'sourceArtUnchanged':True,
       'realPhysicalStrandIdentityVerified':False,'hiddenScalpArtValidated':False,
       'artistCurveControlsApproved':False,'fullYawVisualAccepted':False,
       'review':'private-assets/exports/p15-159-curve-controls/index.html',
       'next':'Review 101.25/123.75 loop structure and artifact seams. Author matching 3-view root underpaint and true inner/outer contour points before selecting continuous yaw.'}
    q['acceptanceGate']={
       'passes':False,'candidateSelectedForProduction':False,
       'maxPermittedAdjacentRGBMAE':results['reference']['maxAdjacentRGBMAE'],
       'midviewSingleComponent':{
           name:all(results[name]['topConnectedComponents'][ANGLES.index(a)]==1
                    for a in (101.25,123.75))
           for name in ('controls_only','controls_bridge')},
       'crownPixelPreservation':{
           name:results[name]['crownBelowCutPixelExact']
           for name in ('controls_only','controls_bridge')},
       'reason':'Source root pixels cross the experimental upper-hair boundary; 101.25 and 123.75 show extra connected components, remaining crown strokes and owner-switch discontinuity.'
    }
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        rows=len(outputs)
        board=Image.new('RGB',(310*5,350*rows),(35,42,53))
        zoom=Image.new('RGB',(310*5,223*rows),(35,42,53))
        d=ImageDraw.Draw(board);dz=ImageDraw.Draw(zoom)
        for row,(name,seq) in enumerate(outputs.items()):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(angle,arr) in enumerate(zip(ANGLES,seq)):
                Image.fromarray(arr,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(arr,'RGBA'))
                board.paste(tile.convert('RGB').resize((304,304),Image.Resampling.LANCZOS),(310*col,row*350+28))
                d.text((310*col+6,row*350+5),f'{name} {angle:g}',fill='white')
                zoom.paste(tile.crop((135,0,360,112)).resize((304,184),Image.Resampling.NEAREST).convert('RGB'),(310*col,row*223+29))
                dz.text((310*col+6,row*223+5),f'{name} {angle:g}',fill='white')
        board.save(OUT/'yaw-comparison.jpg',quality=94)
        zoom.save(OUT/'loop-closeup.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 five-control loop study</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90–135° five-point loop deformation</h2><p>Native source reference, five-control deformation and local crown-root connection probe. All three source keys remain exact. Physical strand identity and hidden scalp paint require separate validation.</p><img src="loop-closeup.jpg"><h2>Full frames</h2><img src="yaw-comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'reference':q['renderers']['reference'],'controls_only':q['renderers']['controls_only'],'controls_bridge':q['renderers']['controls_bridge']},indent=2))
