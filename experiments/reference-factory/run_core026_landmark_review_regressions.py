#!/usr/bin/env python3
"""Codex independent negative checks; synthetic visual edits are not reviews."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / 'prepare_core026_landmark_review.py'
CONFIG = ROOT / 'config/core026-landmark-review.json'
OUT = ROOT / 'out/core026/landmark-review-regressions'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def command(mode, path):
    result = subprocess.run([sys.executable, str(SCRIPT), mode, '--output', str(path)],
                            cwd=ROOT, capture_output=True, text=True)
    return result

def visual(frame):
    frame.update(state='VERIFIED_IMAGE_FIDUCIAL', confidence='HIGH',
                 review_method='VISUAL_NATIVE', image_feature_evidence='SYNTHETIC TEST ONLY; not an actual review',
                 eligible_for_fitting=True)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = digest(CONFIG)
    baseline = OUT / 'unreviewed-baseline.json'
    baseline.unlink(missing_ok=True)
    prepared = command('--prepare', baseline)
    assert prepared.returncode == 0, prepared.stderr
    data = json.loads(baseline.read_bytes())
    checks = []
    result = command('--verify', CONFIG)
    assert result.returncode == 0, result.stderr
    checks.append({'case': 'committed_table_verify', 'exit_code': result.returncode})

    def case(name, mutate, expected=11):
        altered = copy.deepcopy(data)
        mutate(altered)
        path = OUT / (name + '.json')
        path.write_text(json.dumps(altered, indent=2) + '\n')
        old = digest(path)
        run = command('--verify', path)
        assert run.returncode == expected, (name, run.returncode, run.stdout, run.stderr)
        assert digest(path) == old, name + ': verify wrote input'
        checks.append({'case': name, 'exit_code': run.returncode, 'input_unchanged': True})

    case('wrong_native_png_hash', lambda d: d['records'][0]['frames'][4].update(native_head_sha256='0'*64))
    case('proxy_promoted_to_fit', lambda d: visual(d['records'][2]['frames'][4]))
    def fake_unknown(d):
        f = d['records'][1]['frames'][4]
        f['xy'] = [320, 320]
        visual(f)
    case('hard_unknown_forged_point', fake_unknown)
    case('unreviewed_candidate_promoted', lambda d: d['records'][0]['frames'][4].update(eligible_for_fitting=True))
    case('missing_identity', lambda d: d['records'].pop())
    case('missing_pose', lambda d: d['records'][0]['frames'].pop())
    case('candidate_coordinate_changed', lambda d: d['records'][0]['frames'][4].update(candidate_xy=[320,320]))
    for name, xy in [('nan_coordinate', [float('nan'), 320]), ('bool_coordinate', [True,320]),
                     ('out_of_bounds_coordinate', [652,320])]:
        case(name, lambda d, xy=xy: d['records'][0]['frames'][4].update(xy=xy))
    case('source_alpha_changed', lambda d: d['records'][0].update(source_alpha=0))
    case('source_hash_changed', lambda d: d['inputs'].update(source_inx_sha256='0'*64))
    case('overall_m1_claim_promoted', lambda d: d['claims'].update(overall_M1='PASS'))
    case('visual_evidence_missing', lambda d: d['records'][0]['frames'][4].update(
        state='VERIFIED_IMAGE_FIDUCIAL',confidence='HIGH',review_method='VISUAL_NATIVE',eligible_for_fitting=True))
    case('synthetic_visual_edit_allowed', lambda d: visual(d['records'][0]['frames'][4]), 0)

    # Positive round trip occurs in isolated output, never over the committed table.
    prepared = OUT / 'fresh.json'
    prepared.unlink(missing_ok=True)
    result = command('--prepare', prepared)
    assert result.returncode == 0, result.stderr
    fresh_hash = digest(prepared)
    result = command('--prepare', prepared)
    assert result.returncode == 11 and digest(prepared) == fresh_hash, result.stderr
    checks.append({'case':'existing_review_not_overwritten','exit_code':result.returncode,'input_unchanged':True})
    fresh = json.loads(prepared.read_bytes())
    assert all(not f['eligible_for_fitting'] and f['review_method']=='UNREVIEWED'
               for r in fresh['records'] for f in r['frames'])
    assert digest(CONFIG) == before, 'Original config changed'
    report = {'status':'PASS', 'author':'Codex independent supervisor',
              'scope':'STRUCTURE_AND_REJECTION_ONLY', 'synthetic_positive_case_is_not_review_evidence':True,
              'checks':checks, 'original_config_sha256':before, 'original_config_unchanged':True,
              'overall_M1':'NOT_ACCEPTED', 'runtime_depth_and_occlusion':'NOT_IMPLEMENTED'}
    (OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('CORE026_LANDMARK_REVIEW_REGRESSIONS', json.dumps({'status':'PASS','checks':len(checks),
          'rejected_corruptions':14,'original_config_unchanged':True}))

if __name__ == '__main__':
    main()
