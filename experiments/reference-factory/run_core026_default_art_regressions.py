#!/usr/bin/env python3
"""Reject one forged foreground pixel even when average error remains tiny."""
import copy
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image
import verify_core026_compositor_supervisor as supervisor

ROOT=Path(__file__).resolve().parent
ACTUAL=ROOT/'out/core026/runtime-supervisor'
OUT=ROOT/'out/core026/default-art-regressions'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((ACTUAL/'supervisor-qa.json').read_bytes())
    assert baseline['default_art_gate']=='PASS' and baseline['full_runtime_gate'].startswith('BLOCKED_')
    assert baseline['limitations']['M3_permission']=='BLOCKED_PENDING_COMPLETE_M2B'
    assert baseline['hard_eye_white_negative']['metric']['max_channel_error']>4
    manifest=json.loads((ACTUAL/'manifest.json').read_bytes());original={c['file']:sha(ACTUAL/c['file']) for c in manifest['captures']}
    fixture=OUT/'forged_foreground_pixel';fixture.mkdir(exist_ok=True)
    changed={'source_white','source_pupilL_shift8','source_pupilL_reset','source_mask_policy_reset'}
    for c in manifest['captures']:
        p=fixture/c['file'];shutil.copy2(ACTUAL/c['file'],p)
        if c['id'] in changed:
            with Image.open(p) as im:altered=im.convert('RGB')
            altered.putpixel((812,1072),(0,0,0));altered.save(p)
            c['sha256']=sha(p)
            if c['repeat_sha256'] is not None:c['repeat_sha256']=c['sha256']
    (fixture/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    old=supervisor.OUT;supervisor.OUT=fixture
    report={'failures':[]}
    try:supervisor.validate(report)
    finally:supervisor.OUT=old
    assert report['default_art_gate']=='FAIL' and any('default RGB fidelity failed' in f for f in report['failures'])
    assert report['metrics']['source_white']['old_browser']['global_mae']<=.10
    assert report['metrics']['source_white']['old_browser']['max_channel_error']>4
    assert all(sha(ACTUAL/p)==digest for p,digest in original.items())
    result={'schema':'core026-default-art-regressions/1','status':'PASS',
        'known_hard_eye_white_mask_rejected_by_unchanged_rgb_limits':True,
        'one_forged_foreground_pixel_rejected_despite_small_global_mae':True,
        'forged_capture_hashes_and_repeats_updated_so_test_reaches_real_pixels':True,
        'original_actual_captures_unchanged':True,'default_art_pass_does_not_admit_M3':True,
        'scope':'DEFAULT_ART_ONLY; full runtime/native clip/depth remain blocked'}
    (OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print('CORE026_DEFAULT_ART_REGRESSIONS',json.dumps(result))

if __name__=='__main__':main()
