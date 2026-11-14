#!/usr/bin/env python3
"""P15-184 alpha-aware texture blend and 13-yaw temporal sweep."""
import json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
import p15_181_curve_correspondence as curve
from p15_182_free_tip_root_tangent import root_extension
from p15_183_valid_strand_texture import donor_texture
from p15_129_ahoge_ownership import keyframes,KEYS,top_components
from p15_128_keyart_registration import jumps
from p15_134_underpaint_probe import P,compose
from flow_render import get_flow,morph
from p15_153_source_topology import extract

ROOT=Path(__file__).resolve().parents[1]
OUT=P/'exports/p15-184-alpha-aware-temporal-sweep'
E=ROOT/'evidence/p15-184-alpha-aware-temporal-sweep-qa.json'
ANGLES=tuple(float(x) for x in np.linspace(90,135,13))
MODES=('valid_mix_65','valid_mix_70','valid_mix_75','valid_mix_80')
H=W=443

def build_sequence(keys):
    h,w=keys[90.].shape[:2];yy,xx=np.indices((h,w),dtype=np.float32);grid=np.stack((xx,yy),axis=-1)
    flows={}
    for a,b in ((90.,112.5),(112.5,135.)):
        flows[a,b]=get_flow(keys[a],keys[b],'dis')
    frames=[];crowns=[]
    from p15_134_underpaint_probe import P
    tags={90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}
    crown_keys={}
    for a in KEYS:
        crown_keys[a]=np.asarray(Image.open(P/f'exports/p15-178-ai-rootless-crown/local/{tags[a]}/crown-motion-underpaint.png').convert('RGBA')).copy()
    for angle in ANGLES:
        if angle in KEYS:
            frames.append(keys[angle].copy());crowns.append(crown_keys[angle].copy());continue
        a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
        t=(angle-a)/(b-a)
        frames.append(morph(keys[a],keys[b],*flows[a,b],t,grid))
        crowns.append(morph(crown_keys[a],crown_keys[b],*get_flow(crown_keys[a],crown_keys[b],'dis'),t,grid))
    return frames,crowns

def donor_for_mix(source,curve_data,ratio):
    valid=donor_texture(source,curve_data,'nearest_valid').astype(np.float32)
    native=source[...,:3].astype(np.float32)
    return np.uint8(np.clip(np.rint(native*(1-ratio)+valid*ratio),0,255))

def local_metrics(frames):
    # Broad crop diagnostic; includes the moving crown and is intentionally
    # kept separate from the isolated strand-only temporal score.
    # Focus on the upper-hair/ahoge ROI, not unrelated face/background pixels.
    composites=[]
    for frame in frames:
        alpha=frame[...,3:4].astype(np.float32)/255
        bg=np.array([49,61,78],np.float32)
        composites.append(frame[...,:3].astype(np.float32)*alpha+(1-alpha)*bg)
    errors=[];global_errors=[]
    for a,b in zip(composites,composites[1:]):
        errors.append(round(float(np.mean(np.abs(a[:130,110:380]-b[:130,110:380]))),4))
        global_errors.append(round(float(np.mean(np.abs(a-b))),4))
    return errors,global_errors


def evaluate(save=True):
    src=keyframes()
    source_curves={a:curve.source_curve(src[a]) for a in KEYS}
    source_frames,crown_frames=build_sequence(src)
    sequences={};strand_sequences={};details={};metrics={}
    for mode in MODES:
        ratio=float(mode.split('_')[-1])/100
        curves={}
        for a in KEYS:
            curves[a]=source_curves[a].copy()
            curves[a]['texture']=donor_for_mix(src[a],source_curves[a],ratio)
        output=[];reports={}
        for i,angle in enumerate(ANGLES):
            if angle in KEYS:
                output.append(src[angle].copy())
                continue
            left,right=(90.,112.5) if angle<112.5 else (112.5,135.)
            t=(angle-left)/(right-left)
            target=curve.interp_curve(curves[left],curves[right],t)
            core,core_info=curve.render_curve(target,curves[left],curves[right],t)
            target,root_info=root_extension(target,crown_frames[i],8)
            strand,strand_info=curve.render_curve(target,curves[left],curves[right],t)
            frame=compose(crown_frames[i],strand)
            frame[125:]=source_frames[i][125:]
            output.append(frame)
            gray=cv2.cvtColor(strand[:120,:,:3],cv2.COLOR_RGB2GRAY)
            edge=(strand[:120,:,3]>64)&(strand[:120,:,3]<245)
            dark=edge&(gray<85)
            reports[f'{angle:g}']={
              **root_info,**strand_info,
              'darkEdgePixels':int(dark.sum()),'edgePixels':int(edge.sum()),
              'darkEdgeRatio':round(float(dark.sum()/max(1,edge.sum())),5),
              'topComponents':top_components(frame),
              'deepBodyExact':bool(np.array_equal(frame[125:],source_frames[i][125:])),
              'coreArea':core_info['loopPixels']}
        sequences[mode]=output;details[mode]=reports
        local,global_e=local_metrics(output)
        baseline_local,baseline_global=local_metrics(source_frames)
        metrics[mode]={
          'maxAdjacentLocalRGBMAE':max(local),'adjacentLocalRGBMAE':local,
          'maxAdjacentGlobalRGBMAE':max(global_e),'adjacentGlobalRGBMAE':global_e,
          'maxAdjacentDISLocalRGBMAE':max(baseline_local),
          'maxAdjacentDISGlobalRGBMAE':max(baseline_global),
          'totalDarkEdgePixels':sum(x['darkEdgePixels'] for x in reports.values()),
          'meanDarkEdgeRatio':round(float(np.mean([x['darkEdgeRatio'] for x in reports.values()])),5),
          'allNativeKeysExact':all(np.array_equal(output[ANGLES.index(a)],src[a]) for a in KEYS),
          'allDeepBodyExact':all(x['deepBodyExact'] for x in reports.values()),
          'singleConnectedStrand':all(x['topComponents']==1 for x in reports.values()),
          'freeTipPreserved':all(x['freeTipPreserved'] for x in reports.values())}
    # Choose minimum local temporal error among edge-clean variants.
    eligible=[m for m in MODES if metrics[m]['totalDarkEdgePixels']<=25]
    selected=min(MODES,key=lambda m:(metrics[m]['totalDarkEdgePixels'],metrics[m]['maxAdjacentLocalRGBMAE']))
    q={'schema':'KOMA_P15_184_ALPHA_AWARE_TEMPORAL_SWEEP_V1',
       'characterId':'p0_character_001','renderAngles':list(ANGLES),
       'sourceAngles':list(KEYS),'textureMixVariants':list(MODES),
       'metrics':metrics,'intermediateDetails':details,
       'selectedDiagnosticMethod':selected,
       'selectionRule':'Minimize total dark antialias edge pixels; use local ROI RGB MAE as tie-breaker. The 5-view <=25-pixel threshold is not reused because this sweep has twice as many generated intermediate views.',
       'productionRendererUpdated':False,'visualAccepted':False,
       'review':'private-assets/exports/p15-184-alpha-aware-temporal-sweep/index.html'}
    m=metrics[selected]
    q['gate']={
      'allNativeKeysExact':m['allNativeKeysExact'],
      'allDeepBodyExact':m['allDeepBodyExact'],
      'singleConnectedStrand':m['singleConnectedStrand'],
      'freeTipPreserved':m['freeTipPreserved'],
      'darkEdgePixelsAtMost25':m['totalDarkEdgePixels']<=25,
      'localTemporalBeatsDIS':m['maxAdjacentLocalRGBMAE']<=m['maxAdjacentDISLocalRGBMAE'],
      'globalTemporalBeatsDIS':m['maxAdjacentGlobalRGBMAE']<=m['maxAdjacentDISGlobalRGBMAE'],
      'temporalBeatsP15182':m['maxAdjacentLocalRGBMAE']<12.2739,
      'visualAccepted':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(210*len(ANGLES),190*(len(MODES)+1)),(35,42,54));d=ImageDraw.Draw(board)
        for row,(name,frames) in enumerate([('whole_frame_DIS',source_frames),*sequences.items()]):
            folder=OUT/name;folder.mkdir(exist_ok=True)
            for col,(a,frame) in enumerate(zip(ANGLES,frames)):
                Image.fromarray(frame,'RGBA').save(folder/(f'yaw{a:06.2f}'.replace('.','p')+'.png'))
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                crop=tile.crop((110,0,380,130)).resize((204,156),Image.Resampling.LANCZOS)
                board.paste(crop.convert('RGB'),(col*210,row*190+27))
                d.text((col*210+4,row*190+5),f'{name} {a:g}',fill='white')
        board.save(OUT/'13-yaw-comparison.jpg',quality=95)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P15-184 13-yaw alpha-aware temporal sweep</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>13-yaw alpha-aware texture and temporal comparison</h2><p>Thirteen views from 90° through 135° compare 65/70/75/80 percent source-valid donor mixes. Native source keys remain exact. Top-head ROI and global temporal errors are recorded separately.</p><img src="13-yaw-comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
 q=evaluate();print(json.dumps({'selected':q['selectedDiagnosticMethod'],'gate':q['gate'],'metrics':q['metrics']},indent=2))
