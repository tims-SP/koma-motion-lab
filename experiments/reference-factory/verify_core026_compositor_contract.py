#!/usr/bin/env python3
"""Codex independent source schedule/alpha checks; imports no producer algorithm."""
import argparse
import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageChops

ROOT=Path(__file__).resolve().parent
SURFACES={1,2,3,4,5,7,8,9,10,11,13,44,46,48,50,52,54,56,62}
FACE_PAINT={21,22,23,24,25,26,27,30,31,32,33,34,35,36,37,40,41,42,43,58,59,60,61}
RECEIVERS={6:5,12:11,**{n:13 for n in range(14,21)},**{n:13 for n in FACE_PAINT},
           28:27,29:27,38:37,39:37,45:44,47:46,49:48,51:50,53:52,55:54,57:56}
CASTERS=dict(zip(range(14,21),(44,46,50,48,54,52,56)))
INX='dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f'
CONTRACT='9f6d4190b597053027403575fa7b37d05bedf878e03d12c83efa46ae01fe9b6d'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def equal(a,b):return json.dumps(a,sort_keys=True,allow_nan=False)==json.dumps(b,sort_keys=True,allow_nan=False)
def need(ok,message):
    if not ok:raise ValueError(message)

def root(n):
    while n in RECEIVERS:n=RECEIVERS[n]
    return n

def verify(path):
    c=read(ROOT/'config/core025-layer-contract.json');facts=read(ROOT/'out/core026/supervisor-constraints.json')
    reg=read(ROOT/'out/core026/default-registration.json');data=read(path)
    need(set(data)=={'schema','status','scope','painter_schedule','surface_groups','proposed_passes',
         'native_clip_orders','source_multiply_orders','default_shadow_clips','overlap_observations',
         'runtime_receiver_compositor','physical_depth','natural_3d_turn','unknown_attachment_roots',
         'per_layer_eye_uv_motion_required','global_head_bake_allowed','runtime_dependencies','inputs'},
         'Unexpected top-level fields/claims')
    need(sha(ROOT/'out/source/Aka.inx')==INX and sha(ROOT/'config/core025-layer-contract.json')==CONTRACT,'Frozen source changed')
    inputs={'source_inx_sha256':INX,'layer_contract_sha256':CONTRACT,
            'constraints_sha256':sha(ROOT/'config/core026-constraints.json'),
            'review_sha256':sha(ROOT/'config/core026-landmark-review.json'),
            'schedule_algorithm_sha256':sha(ROOT/'core026_compositor_schedule.py'),
            'group_program_sha256':sha(ROOT/'core026_compositor_groups.py'),
            'source_observer_program_sha256':sha(ROOT/'prepare_core026_compositor.py')}
    need(equal(data['inputs'],inputs),'Input provenance differs')
    m1=read(ROOT/'out/core026/m1-acceptance.json')
    need(m1['status']=='PASS_REFERENCE_LIMITED' and m1['inputs']['review_sha256']==inputs['review_sha256'] and
         m1['inputs']['constraints_sha256']==inputs['constraints_sha256'],'M1 prerequisite controlled inputs changed')
    for key,value in {'schema':'core026-compositor-contract/1','status':'PASS_SOURCE_SCHEDULE_AND_PROPOSAL',
        'scope':'DEFAULT_PAINTER_SCHEDULE_ONLY','runtime_receiver_compositor':'NOT_IMPLEMENTED',
        'physical_depth':'UNKNOWN','natural_3d_turn':'NOT_ACCEPTED','unknown_attachment_roots':True,
        'per_layer_eye_uv_motion_required':True,'global_head_bake_allowed':False}.items():
        need(equal(data.get(key),value),f'Invalid scope/claim {key}')
    need(equal(data.get('runtime_dependencies'),{'cross_surface_multiply':'UNRESOLVED_RUNTIME_VALIDATION',
        'cross_surface_transparency':'UNRESOLVED_RUNTIME_VALIDATION'}),'Runtime dependency claims promoted')
    expected=[];masks={};groups={n:Image.new('L',tuple(c['canvas'])) for n in SURFACES}
    by_order={r['psd_order']:r for r in facts['records']};native={r['psd_order']:r['selected_uuid'] for r in reg['entries']}
    for layer in c['layers']:
        n=layer['order'];f=by_order[n];p=(ROOT/layer['raw_source_texture']['file']).resolve()
        need(p.is_relative_to(ROOT) and sha(p)==layer['raw_source_texture']['sha256'],'Original PNG differs')
        with Image.open(p) as im:alpha=im.convert('RGBA').getchannel('A')
        full=Image.new('L',tuple(c['canvas']));full.paste(alpha,tuple(layer['bounds'][:2]));masks[n]=full
        groups[root(n)]=ImageChops.lighter(groups[root(n)],full)
        expected.append({'psd_order':n,'native_uuid':native[n],'texture_sha256':layer['raw_source_texture']['sha256'],
            'native_blend_mode':f['native_blend_mode'],'source_blend_mode':layer['source_blend_mode'],
            'receiver_order':RECEIVERS.get(n),'ultimate_surface_order':root(n),'shadow_caster_order':CASTERS.get(n),
            'is_native_clip_to_lower':f['native_blend_mode']=='ClipToLower',
            'is_source_multiply':'MULTIPLY' in layer['source_blend_mode'],'physical_depth':'UNKNOWN'})
    need(equal(data['painter_schedule'],expected),'Painter source identity/order/blend/receiver differs')
    need(equal(data['native_clip_orders'],[28,29,38,39]),'Wrong native ClipToLower list')
    multiplies=[r['psd_order'] for r in expected if r['is_source_multiply']]
    need(equal(data['source_multiply_orders'],multiplies) and len(multiplies)==11,'Multiply list differs')
    need(equal(data['default_shadow_clips'],c['clean_shadow_alpha_clip']),'Derived9 shadow clips changed or conflated')
    expected_groups=[]
    for surface in sorted(SURFACES):
        members=[r['psd_order'] for r in expected if r['ultimate_surface_order']==surface]
        runs=[list(map(lambda p:p[1],g)) for _,g in itertools.groupby(enumerate(members),lambda p:p[1]-p[0])]
        gaps=sorted(set(range(members[0],members[-1]+1))-set(members))
        segments=sum(1 for key,_ in itertools.groupby(expected,lambda r:(r['ultimate_surface_order'],r['is_source_multiply']))
                     if key[0]==surface)
        expected_groups.append({'surface_order':surface,'members':members,'span':[members[0],members[-1]],
                                'gaps':gaps,'contiguous_runs':runs,'requires_multiple_painter_passes':segments>1})
    need(equal(data['surface_groups'],expected_groups),'Surface groups/spans/gaps differ')
    passes=[]
    for key,segment in itertools.groupby(expected,lambda r:(r['ultimate_surface_order'],r['is_source_multiply'])):
        passes.append({'pass_index':len(passes)+1,'orders':[r['psd_order'] for r in segment],
                       'surface_order':key[0],'blend_policy':'MULTIPLY_SCENE_BACKDROP_REQUIRED' if key[1] else 'NORMAL_LOCAL'})
    need(equal(data['proposed_passes'],passes),'Passes merge late painting or lose scene-backdrop blend')
    # Recompute support independently with Pillow group maxima, not the producer observer.
    arrays={n:np.asarray(im) for n,im in groups.items()};raw={n:np.asarray(im) for n,im in masks.items()}
    pairs=[]
    for a,b in itertools.combinations(sorted(SURFACES),2):
        positive=(arrays[a]!=0)&(arrays[b]!=0);count=int(positive.sum())
        if not count:continue
        solid=int(((arrays[a]>=253)&(arrays[b]>=253)).sum())
        pairs.append({'surface_a':a,'surface_b':b,'alpha_gt0_overlap_pixels':count,
                      'both_max_source_alpha_ge253_pixels':solid,'partial_support_overlap_pixels':count-solid})
    hair=Image.new('L',tuple(c['canvas']))
    for n in [44,46,48,50,52,54,56]:hair=ImageChops.lighter(hair,masks[n])
    hair=np.asarray(hair)>=253
    late=[{'psd_order':n,'alpha_gt0_pixels':int((raw[n]>0).sum()),
           'overlap_hair_alpha_ge253_pixels':int(((raw[n]>0)&hair).sum())} for n in [58,59,60,61]]
    backdrops=[]
    for n in multiplies:
        prior={s:Image.new('L',tuple(c['canvas'])) for s in SURFACES}
        for earlier in range(1,n):prior[root(earlier)]=ImageChops.lighter(prior[root(earlier)],masks[earlier])
        hits=[]
        for s in sorted(SURFACES-{root(n)}):
            count=int(((raw[n]>0)&(np.asarray(prior[s])>0)).sum())
            if count:hits.append({'earlier_surface_order':s,'alpha_support_overlap_pixels':count})
        backdrops.append({'psd_order':n,'ultimate_surface_order':root(n),'earlier_other_surface_candidates':hits,
                          'runtime_dependency_status':'UNRESOLVED_RUNTIME_VALIDATION'})
    observed={'kind':'RAW_SOURCE_ALPHA_SUPPORT_ONLY_NOT_VISIBILITY_OR_PHYSICAL_OCCLUSION',
              'group_alpha_definition':'maximum of raw member alpha; not composited opacity',
              'cross_surface_pairs':pairs,'late_paint_over_hair':late,'multiply_backdrop_candidates':backdrops}
    need(equal(data['overlap_observations'],observed),'Source alpha support observations differ')
    return {'schema':'core026-m2a-independent/1','status':'PASS_SOURCE_SCHEDULE_AND_PROPOSAL',
            'contract_sha256':sha(path),'entries':62,'independent_surfaces':19,'attached_proposals':43,
            'proposed_passes':len(passes),'native_clip_count':4,'derived_shadow_clip_count':9,
            'multiply_count':11,'late_overlap_counts':[r['overlap_hair_alpha_ge253_pixels'] for r in late],
            'cross_surface_support_pairs':len(pairs),'runtime_receiver_compositor':'NOT_IMPLEMENTED',
            'physical_depth':'UNKNOWN','natural_3d_turn':'NOT_ACCEPTED'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--contract',type=Path,default=ROOT/'config/core026-compositor-contract.json')
    ap.add_argument('--report',type=Path,default=ROOT/'out/core026/m2a-supervisor.json');a=ap.parse_args()
    for script in ['verify_core026_m1c1_supervisor.py']:
        r=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,capture_output=True,text=True)
        need(r.returncode==0,'Independent source prerequisite failed')
    result=verify(a.contract);a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n');print('CORE026_M2A_SUPERVISOR',json.dumps(result))

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,TypeError) as error:
        print('CORE026_M2A_SUPERVISOR_FAIL:',error,file=sys.stderr);sys.exit(11)
