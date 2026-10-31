#!/usr/bin/env python3
"""Codex local-fallback source/alpha observer and schedule proposal CLI."""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
CONTRACT_SHA='9f6d4190b597053027403575fa7b37d05bedf878e03d12c83efa46ae01fe9b6d'
INX_SHA='dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f'
HAIR=[44,46,48,50,52,54,56]

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_bytes())
def same(a,b):return json.dumps(a,sort_keys=True,allow_nan=False)==json.dumps(b,sort_keys=True,allow_nan=False)

def inside(path):
    path=path.resolve();require(path.is_relative_to(ROOT),'Path outside factory');return path

def source_observations(rows,contract):
    require([r['psd_order'] for r in rows]==list(range(1,63)),'Expected source order1..62')
    receivers={r['psd_order']:r['design']['receiver_order'] for r in rows}
    def surface(n):
        seen=set()
        while receivers[n] is not None:
            require(n not in seen,'Receiver cycle');seen.add(n);n=receivers[n]
        return n
    roots={n:surface(n) for n in receivers}
    w,h=contract['canvas'];raw={};groups={n:np.zeros((h,w),dtype=np.uint8) for n in sorted(set(roots.values()))}
    for layer,row in zip(contract['layers'],rows):
        n=layer['order'];require(n==row['psd_order'],'Source identity/order changed')
        path=inside(ROOT/layer['raw_source_texture']['file'])
        require(sha(path)==row['texture_sha256']==layer['raw_source_texture']['sha256'],'Frozen source PNG SHA differs')
        with Image.open(path) as im:a=np.array(im.convert('RGBA'))[...,3].copy()
        x0,y0,x1,y1=layer['bounds'];require(a.shape==(y1-y0,x1-x0),'Raw alpha/bounds differ')
        full=np.zeros((h,w),dtype=np.uint8);full[y0:y1,x0:x1]=a;raw[n]=full
        np.maximum(groups[roots[n]],full,out=groups[roots[n]])
    pairs=[];surfaces=sorted(groups)
    for i,left in enumerate(surfaces):
        for right in surfaces[i+1:]:
            a,b=groups[left],groups[right];overlap=int(np.count_nonzero((a>0)&(b>0)))
            if not overlap:continue
            opaque=int(np.count_nonzero((a>=253)&(b>=253)))
            pairs.append({'surface_a':left,'surface_b':right,'alpha_gt0_overlap_pixels':overlap,
                          'both_max_source_alpha_ge253_pixels':opaque,'partial_support_overlap_pixels':overlap-opaque})
    opaque_hair=np.maximum.reduce([raw[n] for n in HAIR])>=253
    late=[{'psd_order':n,'alpha_gt0_pixels':int(np.count_nonzero(raw[n]>0)),
           'overlap_hair_alpha_ge253_pixels':int(np.count_nonzero((raw[n]>0)&opaque_hair))} for n in [58,59,60,61]]
    require([r['overlap_hair_alpha_ge253_pixels'] for r in late]==[28,15,2156,1954],'Pinned late-paint observation changed')
    previous={n:np.zeros((h,w),dtype=np.uint8) for n in surfaces};backdrops=[]
    for row in rows:
        n=row['psd_order'];root=roots[n]
        if 'MULTIPLY' in row['observed']['source_blend_mode']:
            candidates=[]
            for other in surfaces:
                if other==root:continue
                count=int(np.count_nonzero((raw[n]>0)&(previous[other]>0)))
                if count:candidates.append({'earlier_surface_order':other,'alpha_support_overlap_pixels':count})
            backdrops.append({'psd_order':n,'ultimate_surface_order':root,'earlier_other_surface_candidates':candidates,
                              'runtime_dependency_status':'UNRESOLVED_RUNTIME_VALIDATION'})
        np.maximum(previous[root],raw[n],out=previous[root])
    return {'kind':'RAW_SOURCE_ALPHA_SUPPORT_ONLY_NOT_VISIBILITY_OR_PHYSICAL_OCCLUSION',
            'group_alpha_definition':'maximum of raw member alpha; not composited opacity',
            'cross_surface_pairs':pairs,'late_paint_over_hair':late,'multiply_backdrop_candidates':backdrops}

def build():
    from core026_compositor_schedule import build_schedule
    contract_path=ROOT/'config/core025-layer-contract.json';facts_path=ROOT/'config/core026-constraints.json'
    require(sha(contract_path)==CONTRACT_SHA and sha(ROOT/'out/source/Aka.inx')==INX_SHA,'Frozen inputs changed')
    facts=read(facts_path);require(facts['schema']=='core026-constraints/2','Need constraints v2')
    m1=read(ROOT/'out/core026/m1-acceptance.json')
    require(m1['status']=='PASS_REFERENCE_LIMITED','M1 limited reference gate not passed')
    review_path=ROOT/'config/core026-landmark-review.json'
    require(m1['inputs']['constraints_sha256']==sha(facts_path) and
            m1['inputs']['review_sha256']==sha(review_path),'Stale M1 controlled inputs')
    contract=read(contract_path);observations=source_observations(facts['records'],contract)
    before=copy.deepcopy([facts['records'],contract['clean_shadow_alpha_clip'],observations])
    result=build_schedule(facts['records'],contract['clean_shadow_alpha_clip'],observations)
    require(same(before,[facts['records'],contract['clean_shadow_alpha_clip'],observations]),'Algorithm mutated inputs')
    result['inputs']={'source_inx_sha256':INX_SHA,'layer_contract_sha256':CONTRACT_SHA,
                      'constraints_sha256':sha(facts_path),'review_sha256':sha(review_path),
                      'schedule_algorithm_sha256':sha(ROOT/'core026_compositor_schedule.py'),
                      'group_program_sha256':sha(ROOT/'core026_compositor_groups.py'),
                      'source_observer_program_sha256':sha(Path(__file__))}
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--build',action='store_true');mode.add_argument('--verify',action='store_true')
    ap.add_argument('--output',type=Path,default=ROOT/'config/core026-compositor-contract.json');args=ap.parse_args()
    path=inside(args.output);expected=build()
    if args.build:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n')
    else:require(same(read(path),expected),'Committed compositor contract differs from current source/schedule proposal')
    print('CORE026_COMPOSITOR_CONTRACT',json.dumps({'status':'BUILT' if args.build else 'VERIFIED',
        'schedule_entries':len(expected['painter_schedule']),'surfaces':len(expected['surface_groups']),
        'proposed_passes':len(expected['proposed_passes']),'scope':'SOURCE_SCHEDULE_AND_PROPOSAL_ONLY',
        'runtime_receiver_compositor':'NOT_IMPLEMENTED','physical_depth':'UNKNOWN'}))

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,TypeError,KeyError) as error:
        print('CORE026_COMPOSITOR_CONTRACT_FAIL:',error,file=sys.stderr);sys.exit(11)
