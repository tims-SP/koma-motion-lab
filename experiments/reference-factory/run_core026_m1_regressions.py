#!/usr/bin/env python3
"""Codex supervisor tests for finite reference admission, not visual ground truth."""
import copy
import json
import subprocess
import sys
from pathlib import Path
from prepare_core026_landmark_review import skeleton,verify
from verify_core026_m1 import evaluate

ROOT=Path(__file__).resolve().parent

def main():
    original=json.loads((ROOT/'config/core026-landmark-review.json').read_bytes());base=skeleton()
    verify(original,base)
    assert evaluate(original)['status']=='PASS_REFERENCE_LIMITED'
    cases=[]
    def trial(name,mutate):
        altered=copy.deepcopy(original);mutate(altered)
        # Each fixture remains structurally legal: it must fail the aggregate gate.
        verify(altered,base)
        result=evaluate(altered)
        assert result['status']=='BLOCKED_REFERENCE_FOR_DEPTH_FIT',(name,result)
        cases.append({'name':name,'status':result['status'],'blockers':result['blockers']})
    def no_feature(d,index):
        for r in d['records']:
            if r['id']=='nose_tip':r['frames'][index]['eligible_for_fitting']=False
    trial('negative_nose_not_fit_eligible',lambda d:no_feature(d,3))
    trial('positive_nose_not_fit_eligible',lambda d:no_feature(d,5))
    trial('default_nose_not_fit_eligible',lambda d:no_feature(d,4))
    def no_lower(d):
        for r in d['records']:
            if r['id'] in ('chin','face_edgeL','face_edgeR') and r['frames'][3]['state']=='BOUNDARY_PROXY_ONLY':
                r['frames'][3]['confidence']='LOW'
    trial('negative_contours_not_credible',no_lower)
    def not_reviewed(d):
        d['records'][1]['frames'][0]=copy.deepcopy(base['records'][1]['frames'][0])
    trial('one_unknown_cell_unreviewed',not_reviewed)
    def missing_eye(d):
        for r in d['records']:
            if r['id']=='pupilL':
                r['frames'][5].update(state='UNKNOWN',xy=None,confidence='UNKNOWN',eligible_for_fitting=False)
    trial('positive_eye_missing',missing_eye)
    altered=copy.deepcopy(original);no_feature(altered,4)
    fixture=ROOT/'out/core026/m1-blocked-default-fixture.json';fixture.write_text(json.dumps(altered)+'\n')
    blocked_report=ROOT/'out/core026/m1-blocked-default-report.json'
    result=subprocess.run([sys.executable,str(ROOT/'verify_core026_m1.py'),'--review',str(fixture),
                           '--report',str(blocked_report)],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==12,(result.returncode,result.stdout,result.stderr)
    assert json.loads(blocked_report.read_bytes())['status']=='BLOCKED_REFERENCE_FOR_DEPTH_FIT'
    report={'schema':'core026-m1-gate-regressions/1','status':'PASS','cases':cases,
            'actual_cli_blocked_exit_code':result.returncode,
            'fixtures_structurally_valid':True,'baseline_usable_raw_yaws':evaluate(original)['usable_raw_yaws'],
            'scope':'AGGREGATE_REFERENCE_GATES_ONLY; visual decisions remain Codex observations'}
    out=ROOT/'out/core026/m1-gate-regressions.json';out.write_text(json.dumps(report,indent=2)+'\n')
    print('CORE026_M1_REGRESSIONS',json.dumps({'status':'PASS','legal_but_blocked_cases':len(cases)}))

if __name__=='__main__':main()
