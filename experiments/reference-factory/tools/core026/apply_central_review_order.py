#!/usr/bin/env python3
"""Codex-authored fixed work order; actual --apply executor must be recorded."""
import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORDER = ROOT / 'evidence/core026-M1/central-review-pending-order.json'
CONFIG = ROOT / 'config/core026-landmark-review.json'
REGRESSIONS = ROOT / 'run_core026_landmark_review_regressions.py'
MUTABLE = {'state','xy','confidence','review_method','image_feature_evidence','eligible_for_fitting'}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Apply exact published decisions and run both checks')
    parser.add_argument('--executor', choices=['mcode','codex-fallback'])
    args = parser.parse_args()
    require(not args.apply or args.executor is not None,'--apply requires explicit --executor attribution')
    original = CONFIG.read_bytes()
    order = json.loads(ORDER.read_bytes())
    require(order['status']=='PENDING_MCODE_APPLICATION','Order is not pending')
    require(hashlib.sha256(original).hexdigest()==order['input_review_config_sha256'],'Review config drift; refusing')
    data = json.loads(original)
    require(len(order['decisions'])==19,'Need 19 ordered decisions')
    require([r['id'] for r in data['records']]==[r['id'] for r in order['decisions']],'Decision identity/order drift')
    for record, decision in zip(data['records'],order['decisions']):
        require([f['raw_yaw'] for f in decision['frames']]==[-.25,0,.25],'Wrong decision yaw grid')
        for current, reviewed in zip(record['frames'][3:6],decision['frames']):
            require(current['review_method']=='UNREVIEWED','Refusing to overwrite a reviewed cell')
            require(set(current)==set(reviewed),'Frame fields differ')
            require({k:v for k,v in current.items() if k not in MUTABLE}==
                    {k:v for k,v in reviewed.items() if k not in MUTABLE},'Immutable provenance/candidate changed')
        record['frames'][3:6]=copy.deepcopy(decision['frames'])
    spec=importlib.util.spec_from_file_location('review_preparer',ROOT/'prepare_core026_landmark_review.py')
    validator=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    counts=validator.verify(data,validator.skeleton())
    require(counts['reviewed']==57 and counts['fit_eligible']==9,'Unexpected review decision counts')
    old_regressions=REGRESSIONS.read_bytes()
    old="    data = json.loads(CONFIG.read_bytes())\n"
    new=("    baseline = OUT / 'unreviewed-baseline.json'\n"
         "    baseline.unlink(missing_ok=True)\n"
         "    prepared = command('--prepare', baseline)\n"
         "    assert prepared.returncode == 0, prepared.stderr\n"
         "    data = json.loads(baseline.read_bytes())\n")
    text=old_regressions.decode()
    require(text.count(old)==1,'Regression fixture drift; refusing')
    updated=text.replace(old,new).encode()
    if args.apply:
        try:
            CONFIG.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
            REGRESSIONS.write_bytes(updated)
            for command in [['prepare_core026_landmark_review.py','--verify'],['run_core026_landmark_review_regressions.py']]:
                result=subprocess.run([sys.executable,*command],cwd=ROOT)
                print('ACTUAL_COMMAND_EXIT',json.dumps({'command':['python',*command],'exit_code':result.returncode}),flush=True)
                require(result.returncode==0,'Command failed; rolling back both controlled files')
        except BaseException:
            CONFIG.write_bytes(original)
            REGRESSIONS.write_bytes(old_regressions)
            raise
    print('CORE026_CENTRAL_ORDER',json.dumps({'status':'APPLIED_AND_CHECKED' if args.apply else 'DRY_RUN_ONLY',
          **counts,'remaining_unreviewed':114,'source_decisions':'Codex actual image review',
          'executor':args.executor if args.apply else 'not executed',
          'overall_M1':'NOT_ACCEPTED','runtime_depth_and_occlusion':'NOT_IMPLEMENTED'}),flush=True)

if __name__=='__main__':
    try:
        main()
    except (ValueError,KeyError,TypeError,OSError) as error:
        print('CORE026_CENTRAL_ORDER_FAIL:',error,file=sys.stderr)
        sys.exit(11)
