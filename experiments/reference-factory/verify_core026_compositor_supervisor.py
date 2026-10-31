#!/usr/bin/env python3
"""Codex independent pixels/input/local-state acceptance of real M2B0 browser captures."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out/core026/runtime-supervisor'
LIMITS={'rgb_global_mae':.10,'rgb_foreground_union_mae':.50,'rgb_max':4,'rgb_over16_pixels':0,
        'alpha_global_mae':.50,'alpha_max':4}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_bytes())
def need(ok,message):
    if not ok:raise ValueError(message)
def pixels(path,mode='RGB'):
    with Image.open(path) as im:
        need(im.size==(1630,1630),'Capture is not1630square')
        return np.asarray(im.convert(mode)).copy()

def compare(actual,reference,foreground):
    d=np.abs(actual.astype(np.int16)-reference.astype(np.int16))
    return {'global_mae':float(d.mean()),'foreground_union_mae':float(d[foreground].mean()),
            'max_channel_error':int(d.max()),'over16_pixels':int(np.count_nonzero(d.max(axis=2)>16))},d

def validate(report):
    manifest=read(OUT/'manifest.json');old=read(ROOT/'out/core025/render/manifest.json')
    asm=read(ROOT/'out/core025/assembly/assembly.json');contract=read(ROOT/'config/core025-layer-contract.json')
    need(old['inputs']['assembly_sha256']==sha(ROOT/'out/core025/assembly/assembly.json'),'Old assembly reference drift')
    need(manifest['schema']=='core026-supervisor-captures/1','Wrong independent capture schema')
    need(not manifest['blocked_paths'] and not manifest['page_errors'],'Candidate used forbidden inputs or browser errors')
    need(manifest['supervisor_capture_sha256']==sha(ROOT/'capture_core026_supervisor.mjs'),'Stale independent capture program')
    for file,digest in manifest['inputs'].items():need(sha(ROOT/file)==digest,'Stale capture input: '+file)
    expected_raw={'/'+l['raw_source_texture']['file'] for l in contract['layers']}
    need(set(manifest['requested_raw_pngs'])==expected_raw,'Candidate did not request exactly62 original source PNGs')
    for l in contract['layers']:
        need(sha(ROOT/l['raw_source_texture']['file'])==l['raw_source_texture']['sha256'],'Original PNG hash changed')
    meta=manifest['metadata']
    need(meta['source_count']==62 and meta['receiver_count']==19 and meta['logical_pass_count']==25,'Runtime source/receiver/pass accounting differs')
    expected_inputs=[{'order':l['order'],'file':l['raw_source_texture']['file'],'sha256':l['raw_source_texture']['sha256']} for l in contract['layers']]
    need(meta['source_color_inputs']==expected_inputs,'Runtime source color input metadata differs')
    need(meta['depth_tested'] is False,'This partial gate does not validate spatial depth testing')
    captures={c['id']:c for c in manifest['captures']}
    expected_ids={v+'_'+b for v in ('source','clean') for b in ('white','black','alpha','part_id')}
    expected_ids|={'source_pupilL_shift8','source_pupilL_reset','negative_hard_eye_white','source_mask_policy_reset'}
    need(len(captures)==12 and set(captures)==expected_ids,'Independent12-capture plan differs')
    for c in captures.values():need(sha(OUT/c['file'])==c['sha256'],'Capture hash changed')
    world=np.eye(4);world[2,3]=5
    projection=np.eye(4);projection[2,2]=-2/(20-.1);projection[2,3]=-(20+.1)/(20-.1)
    for c in captures.values():
        pose=c['pose'];need(pose['artwork_draw_count']==62,'Not all62 source paint operations were GPU drawn')
        need(np.allclose(np.asarray(pose['camera_matrix']).reshape(4,4,order='F'),world,rtol=0,atol=1e-12),'Fixed camera changed')
        need(np.allclose(np.asarray(pose['projection_matrix']).reshape(4,4,order='F'),projection,rtol=0,atol=1e-12),'Fixed orthographic projection changed')
    metrics={};alpha_metrics={};review_images=[]
    report['metrics']=metrics;report['alpha_metrics']=alpha_metrics
    for version in ('source','clean'):
        cpu_path=ROOT/asm['comparisons'][version]['cpu_composite']['file']
        need(sha(cpu_path)==asm['comparisons'][version]['cpu_composite']['sha256'],'Old CPU image reference drift')
        cpu=pixels(cpu_path,'RGBA');reference_alpha=cpu[...,3]
        a=pixels(OUT/captures[version+'_alpha']['file'])
        need(np.array_equal(a[...,0],a[...,1]) and np.array_equal(a[...,0],a[...,2]),'Alpha diagnostic is not grayscale')
        actual_alpha=a[...,0];alpha_diff=np.abs(actual_alpha.astype(np.int16)-reference_alpha.astype(np.int16))
        alpha_metrics[version]={'global_mae':float(alpha_diff.mean()),'max_abs':int(alpha_diff.max()),
                                'reference_support_pixels':int(np.count_nonzero(reference_alpha)),
                                'actual_support_pixels':int(np.count_nonzero(actual_alpha))}
        if not (alpha_metrics[version]['global_mae']<=LIMITS['alpha_global_mae'] and
                alpha_metrics[version]['max_abs']<=LIMITS['alpha_max']):
            report['failures'].append(f'{version}: alpha fidelity failed: {alpha_metrics[version]}')
        foreground=(reference_alpha>0)|(actual_alpha>0)
        need(bool(foreground.any()),'Empty foreground')
        for background,value in [('white',255),('black',0)]:
            c=captures[version+'_'+background]
            need(c['repeat_sha256']==c['sha256'],version+'/'+background+': repeated render differs')
            actual=pixels(OUT/c['file'])
            baseline=next(x for x in old['captures'] if x['params']['version']==version and x['params']['yaw_deg']==0 and
                          x['params']['pass']=='beauty' and x['params']['background']==background and x['repeat_sha256'] is not None)
            baseline_path=ROOT/'out/core025/render'/baseline['file']
            need(sha(baseline_path)==baseline['sha256'],'Old baseline image drift')
            gpu_reference=pixels(baseline_path)
            alpha=reference_alpha[...,None].astype(np.float64)/255
            cpu_reference=np.rint(cpu[...,:3]*alpha+value*(1-alpha)).astype(np.uint8)
            entry={}
            for label,reference in [('old_browser',gpu_reference),('old_cpu',cpu_reference)]:
                metric,diff=compare(actual,reference,foreground);entry[label]=metric
                Image.fromarray(np.minimum(diff.astype(np.int32)*16,255).astype(np.uint8)).save(OUT/(version+'_'+background+'_'+label+'_difference_x16.png'))
                if not (metric['global_mae']<=LIMITS['rgb_global_mae'] and
                        metric['foreground_union_mae']<=LIMITS['rgb_foreground_union_mae'] and
                        metric['max_channel_error']<=LIMITS['rgb_max'] and metric['over16_pixels']==0):
                    report['failures'].append(f'{version}/{background}/{label}: default RGB fidelity failed: {metric}')
            metrics[version+'_'+background]=entry
            if background=='white':review_images.extend([(version+' old browser',gpu_reference),(version+' candidate',actual)])
        identity=pixels(OUT/captures[version+'_part_id']['file'])
        need(np.unique(identity.reshape(-1,3),axis=0).shape[0]>2,'Part ID diagnostic is blank or constant')
    base=captures['source_white'];shift=captures['source_pupilL_shift8'];reset=captures['source_pupilL_reset']
    need(shift['sha256']!=base['sha256'] and reset['sha256']==base['sha256'],'Local UV changed nothing or failed to reset')
    delta=np.any(pixels(OUT/shift['file'])!=pixels(OUT/base['file']),axis=2)
    eye=contract['layers'][26]
    with Image.open(ROOT/eye['raw_source_texture']['file']) as im:
        mask=Image.new('L',(1630,1630));mask.paste(im.convert('RGBA').getchannel('A'),tuple(eye['bounds'][:2]))
    # One source-pixel filter support margin, fixed before examining candidate output.
    white_allowed=np.asarray(mask.filter(ImageFilter.MaxFilter(3)))>0
    outside_white=int(np.count_nonzero(delta&~white_allowed))
    paint=mask.copy()
    for n in [28,29]:
        layer=contract['layers'][n-1]
        with Image.open(ROOT/layer['raw_source_texture']['file']) as im:
            part=Image.new('L',(1630,1630));part.paste(im.convert('RGBA').getchannel('A'),tuple(layer['bounds'][:2]))
        paint=ImageChops.lighter(paint,part)
    allowed=np.asarray(paint.filter(ImageFilter.MaxFilter(3)))>0
    outside=int(np.count_nonzero(delta&~allowed))
    need(outside==0,'Local pupil control altered pixels outside source-painted eye support')
    negative=pixels(OUT/captures['negative_hard_eye_white']['file'])
    source_cpu=pixels(ROOT/asm['comparisons']['source']['cpu_composite']['file'],'RGBA')
    aa=source_cpu[...,3:4].astype(float)/255
    source_reference=np.rint(source_cpu[...,:3]*aa+255*(1-aa)).astype(np.uint8)
    negative_metric,_=compare(negative,source_reference,source_cpu[...,3]>0)
    need(negative_metric['max_channel_error']>LIMITS['rgb_max'] and negative_metric['over16_pixels']>0,
         'Known wrong hard eye-white mask was not rejected by original RGB limits')
    need(captures['source_mask_policy_reset']['sha256']==base['sha256'],'Mask policy did not reset exactly')
    sheet=Image.new('RGB',(1040,1100),'#222222');draw=ImageDraw.Draw(sheet)
    for i,(label,array) in enumerate(review_images):
        im=Image.fromarray(array);im.thumbnail((520,520));x,y=(i%2)*520,(i//2)*550
        sheet.paste(im,(x,y));draw.text((x+8,y+525),label,fill='white')
    sheet.save(OUT/'review-sheet.png')
    passed=not report['failures']
    report.update(status='PASS_DEFAULT_ART_ONLY' if passed else 'FAIL_DEFAULT_COMPOSITOR',
        numeric_gate='PASS_DEFAULT_ART_ONLY' if passed else 'FAIL',default_art_gate='PASS' if passed else 'FAIL',
        full_runtime_gate='BLOCKED_NATIVE_CLIP_PARITY_AND_DEPTH_TESTING',metrics=metrics,alpha_metrics=alpha_metrics,
        capture_count=12,original_pngs_checked=62,all_capture_hashes_valid=True,
        local_uv={'order':28,'offset_source_pixels':[8,0],'changed_pixels':int(delta.sum()),
                  'changes_outside_source_painted_eye_support_plus1px':outside,
                  'changes_outside_eye_white_only_plus1px':outside_white,
                  'eye_white_only_assumption':'BLOCKED_SOURCE_ART_ALREADY_OVERSHOOTS_RAW_WHITE_MASK',
                  'reset_restores_sha256':True},
        hard_eye_white_negative={'status':'REJECTED_BY_UNCHANGED_RGB_LIMITS','metric':negative_metric},
        capture_inputs=manifest['inputs'],metadata=manifest['metadata'],
        limitations={'visual_gate':'PENDING_CODEX_IMAGE_REVIEW','physical_depth':'NOT_RECOVERED',
                     'native_clip_parity':'BLOCKED_RAW_EYE_WHITE_MASK_FAILS_SOURCE_ART',
                     'source_paint_mask':'PROVISIONAL_ARTIST_DOMAIN_NOT_ANATOMICAL_OR_NATIVE_GPU_MASK',
                     'M3_permission':'BLOCKED_PENDING_COMPLETE_M2B',
                     'dynamic_occlusion':'NOT_IMPLEMENTED','natural_3d_turn':'NOT_ACCEPTED'})

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'schema':'core026-default-compositor-supervisor/2','author_executor':'Codex independent supervisor',
            'status':'FAIL_DEFAULT_COMPOSITOR','numeric_gate':'FAIL','limits':LIMITS,'failures':[],
            'validator_sha256':sha(Path(__file__))}
    try:
        for script in ['verify_core026_supervisor.py','verify_core026_compositor_contract.py']:
            result=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,capture_output=True,text=True)
            need(result.returncode==0,'Protected/source prerequisite failed: '+script)
        validate(report)
    except Exception as error:report['failures'].append(str(error))
    (OUT/'supervisor-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('CORE026_DEFAULT_SUPERVISOR',json.dumps({k:v for k,v in report.items() if k not in ('metadata','capture_inputs')}))
    return 0 if report.get('default_art_gate')=='PASS' and not report['failures'] else 11

if __name__=='__main__':sys.exit(main())
