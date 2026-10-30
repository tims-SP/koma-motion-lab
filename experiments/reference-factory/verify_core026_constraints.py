#!/usr/bin/env python3
"""Read-only native hierarchy/default stacking observations, not a compositor or 3D depth."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out/core026'
def main():
    raw=(ROOT/'out/source/Aka.inx').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f'
    model=json.loads(raw[12:12+struct.unpack('>I',raw[8:12])[0]])
    c=json.loads((ROOT/'config/core025-layer-contract.json').read_text())
    reg=json.loads((OUT/'default-registration.json').read_text())
    assert reg['status']=='PASS_DEFAULT_SOURCE_COORDINATES' and len(reg['entries'])==62
    by_order={r['psd_order']:r['selected_uuid'] for r in reg['entries']};by_uuid={u:o for o,u in by_order.items()}
    assert len(by_uuid)==62;nodes={};chains={}
    def visit(node,chain):
        nodes[node['uuid']]=node;chains[node['uuid']]=chain
        for child in node.get('children',[]):visit(child,chain+[node['uuid']])
    visit(model['nodes'],[])
    head=next(p for p in model['param'] if p['name']=='Head:: Yaw-Pitch');assert len(head['bindings'])==114
    records=[]
    for l in c['layers']:
        o=l['order'];u=by_order[o];n=nodes[u]
        records.append({'psd_order':o,'psd_name':l['name'],'native_uuid':u,'native_name':n['name'],
            'ancestor_uuids':chains[u],'ancestor_names':[nodes[a]['name'] for a in chains[u]],
            'nearest_mapped_ancestor_order':next((by_uuid[a] for a in reversed(chains[u]) if a in by_uuid),None),
            'native_blend_mode':n.get('blend_mode'),'source_blend_mode':l['source_blend_mode'],
            'native_zsort':n.get('zsort'),'zsort_meaning':'DEFAULT_PAINT_ORDER_NOT_PHYSICAL_DEPTH',
            'head_yaw_binding_names':[b['param_name'] for b in head['bindings'] if b['node']==u],
            'physical_depth':'UNKNOWN','status':'SOURCE_OBSERVED'})
    def alpha(order):
        l=c['layers'][order-1];p=ROOT/l['raw_source_texture']['file']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==l['raw_source_texture']['sha256']
        a=np.array(Image.open(p).convert('RGBA'))[...,3];out=np.zeros((1630,1630),np.uint8)
        x,y,x1,y1=l['bounds'];out[y:y1,x:x1]=a;return out
    hair=np.maximum.reduce([alpha(o) for o in [44,46,48,50,52,54,56]]);late=[]
    for o in [58,59,60,61]:
        a=alpha(o);late.append({'psd_order':o,'alpha_gt0_pixels':int((a>0).sum()),
            'overlap_hair_alpha_ge253_pixels':int(((a>0)&(hair>=253)).sum()),
            'status':'SOURCE_OBSERVED_DEFAULT_ONLY',
            'implication':'Face attachment does not justify moving paint under hair; grouping requires explicit zero-pose comparison.'})
    counts=[r['overlap_hair_alpha_ge253_pixels'] for r in late];assert counts==[28,15,2156,1954]
    mul=[l['order'] for l in c['layers'] if 'MULTIPLY' in l['source_blend_mode']]
    assert len(mul)==11 and len(c['clean_shadow_alpha_clip'])==9
    result={'schema':'core026-supervisor-source-occlusion-observations/1','status':'SOURCE_OBSERVATIONS_VERIFIED',
        'scope':'DEFAULT_SOURCE_ONLY','records':records,'multiply_orders':mul,'default_shadow_clips':c['clean_shadow_alpha_clip'],
        'late_face_paint_over_hair':late,'claims':{'runtime_receiver_compositor':'NOT_IMPLEMENTED',
        'moving_occlusion':'NOT_TESTED','three_dimensional_depth':'UNKNOWN','overall_M1':'NOT_ACCEPTED_BY_THIS_CHECK'}}
    (OUT/'supervisor-constraints.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('CORE026_SOURCE_CONSTRAINT_COUNTS',json.dumps({'records':62,'multiply':11,'clips':9,'late_overlaps':counts}))
if __name__=='__main__':main()
