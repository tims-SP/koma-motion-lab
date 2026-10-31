#!/usr/bin/env python3
"""Codex independent corruption/round-trip checks for the M2A proposal contract."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CONFIG=ROOT/'config/core026-compositor-contract.json'
OUT=ROOT/'out/core026/m2a-regressions'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(script,*args):
    r=subprocess.run([sys.executable,str(ROOT/script),*map(str,args)],cwd=ROOT,capture_output=True,text=True)
    return {'exit_code':r.returncode,'output_tail':(r.stdout+r.stderr)[-1600:]}

def main():
    OUT.mkdir(parents=True,exist_ok=True);original=CONFIG.read_bytes();data=json.loads(original)
    cases=[]
    def swap_uuid(d):
        a,b=d['painter_schedule'][:2];a['native_uuid'],b['native_uuid']=b['native_uuid'],a['native_uuid']
    def move_late(d):
        d['proposed_passes'].insert(0,d['proposed_passes'].pop(22))
    def merge_face(d):
        g=next(g for g in d['surface_groups'] if g['surface_order']==13)
        g.update(gaps=[],contiguous_runs=[g['members']],requires_multiple_painter_passes=False)
    mutations=[('missing_source_layer',lambda d:d['painter_schedule'].pop()),
        ('swapped_valid_source_uuids',swap_uuid),
        ('missing_multiply_brow',lambda d:d['source_multiply_orders'].remove(60)),
        ('late_paint_moved_before_hair',move_late),
        ('invented_physical_depth',lambda d:d['painter_schedule'][12].update(physical_depth=.25)),
        ('native_clip_conflated_with_derived',lambda d:d['native_clip_orders'].append(6)),
        ('wrong_late_alpha_overlap',lambda d:d['overlap_observations']['late_paint_over_hair'][2].update(overlap_hair_alpha_ge253_pixels=0)),
        ('face_gaps_baked_away',merge_face),
        ('whole_head_bake_allowed',lambda d:d.update(global_head_bake_allowed=True)),
        ('float_receiver_identity',lambda d:d['painter_schedule'][5].update(receiver_order=5.0)),
        ('extra_claim_field',lambda d:d.update(physical_depth_measured=True))]
    for name,mutate in mutations:
        candidate=copy.deepcopy(data);mutate(candidate);path=OUT/(name+'.json')
        path.write_text(json.dumps(candidate,indent=2)+'\n');before=sha(path)
        producer=command('prepare_core026_compositor.py','--verify','--output',path)
        supervisor=command('verify_core026_compositor_contract.py','--contract',path,'--report',OUT/(name+'-report.json'))
        assert producer['exit_code']==11 and supervisor['exit_code']==11,(name,producer,supervisor)
        assert sha(path)==before,'Verifier wrote candidate'
        cases.append({'name':name,'status':'REJECTED_BY_BOTH','producer':producer,'supervisor':supervisor,'candidate_unchanged':True})
    rebuilt=OUT/'rebuilt.json';build=command('prepare_core026_compositor.py','--build','--output',rebuilt)
    assert build['exit_code']==0 and rebuilt.read_bytes()==original,'Repeated build not byte-identical'
    assert CONFIG.read_bytes()==original,'Original controlled config changed'
    positive={'producer':command('prepare_core026_compositor.py','--verify'),
              'supervisor':command('verify_core026_compositor_contract.py')}
    assert all(v['exit_code']==0 for v in positive.values()),positive
    report={'schema':'core026-m2a-regressions/1','status':'PASS','cases':cases,'positive':positive,
            'repeated_build_byte_identical':True,'original_controlled_config_unchanged':True,
            'contract_sha256':sha(CONFIG),'scope':'SOURCE_SCHEDULE_AND_PROPOSAL_ONLY',
            'runtime_receiver_compositor':'NOT_IMPLEMENTED','physical_depth':'UNKNOWN'}
    (ROOT/'out/core026/m2a-regressions.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CORE026_M2A_REGRESSIONS',json.dumps({'status':'PASS','corruptions_rejected_by_both':len(cases),
          'repeated_build_byte_identical':True,'original_controlled_config_unchanged':True}))

if __name__=='__main__':main()
