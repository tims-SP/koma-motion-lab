#!/usr/bin/env python3
"""Independent source/contract check; does not accept M1 overall or a compositor."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / 'config/core025-layer-contract.json').is_file())
SHA_INX = 'dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f'
SHA_CONTRACT = '9f6d4190b597053027403575fa7b37d05bedf878e03d12c83efa46ae01fe9b6d'
SURFACES = {1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13, 44, 46, 48, 50, 52, 54, 56, 62}
FACE_PAINT = {21, 22, 23, 24, 25, 26, 27, 30, 31, 32, 33, 34, 35, 36, 37,
              40, 41, 42, 43, 58, 59, 60, 61}
RECEIVERS = {6: 5, 12: 11, **{i: 13 for i in range(14, 21)},
             **{i: 13 for i in FACE_PAINT}, 28: 27, 29: 27, 38: 37, 39: 37,
             45: 44, 47: 46, 49: 48, 51: 50, 53: 52, 55: 54, 57: 56}
CASTERS = dict(zip(range(14, 21), [44, 46, 50, 48, 54, 52, 56]))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equal_json(left, right):
    # A representation check independent of the producer's recursive comparator.
    options = {'sort_keys': True, 'allow_nan': False, 'separators': (',', ':')}
    return json.dumps(left, **options) == json.dumps(right, **options)


def verify(path):
    c = json.loads((ROOT / 'config/core025-layer-contract.json').read_text())
    reg_path = ROOT / 'out/core026/default-registration.json'
    facts = json.loads((ROOT / 'out/core026/supervisor-constraints.json').read_text())
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError('Constraints must be a JSON object')
    problems = []

    def require(ok, message):
        if not ok:
            problems.append(message)

    require(sha(ROOT / 'out/source/Aka.inx') == SHA_INX, 'Frozen INX hash changed')
    require(sha(ROOT / 'config/core025-layer-contract.json') == SHA_CONTRACT,
            'Frozen contract hash changed')
    require(facts['status'] == 'SOURCE_OBSERVATIONS_VERIFIED', 'Independent facts not verified')
    require(data.get('schema') == 'core026-constraints/1', 'Wrong schema')
    require(data.get('scope') == 'DEFAULT_SOURCE_AND_UNVALIDATED_DESIGN', 'Wrong scope')
    require(equal_json(data.get('inputs'), {'inx_sha256': SHA_INX,
            'contract_sha256': SHA_CONTRACT, 'registration_sha256': sha(reg_path)}),
            'Missing/wrong input provenance SHA')
    rows = data.get('records', [])
    require(isinstance(rows, list) and len(rows) == 62, 'Need exactly 62 records')
    if not isinstance(rows, list):
        rows = []
    require(equal_json([r.get('psd_order') for r in rows if isinstance(r, dict)], list(range(1, 63))),
            'Record identity/order/uniqueness mismatch')
    require(SURFACES | RECEIVERS.keys() == set(range(1, 63)) and not SURFACES & RECEIVERS.keys(),
            'Supervisor work-order coverage is incomplete')
    by_order = {r['psd_order']: r for r in facts['records']}
    observed_uuids = []
    for row in rows:
        if not isinstance(row, dict) or row.get('psd_order') not in by_order:
            require(False, 'Malformed record'); continue
        order = row['psd_order']; expected = by_order[order]
        observed = row.get('observed', {})
        design = row.get('design', {})
        if not isinstance(observed, dict) or not isinstance(design, dict):
            require(False, f'{order}: malformed observed/design'); continue
        for key, value in expected.items():
            require(equal_json(observed.get(key), value), f'{order}.observed.{key}: differs from native facts')
        observed_uuids.append(observed.get('native_uuid'))
        layer = c['layers'][order - 1]
        texture = ROOT / layer['raw_source_texture']['file']
        require(row.get('texture_sha256') == layer['raw_source_texture']['sha256'] == sha(texture),
                f'{order}: raw source texture hash mismatch')
        require(design.get('status') == 'DESIGN_PROPOSAL_NOT_RENDER_VALIDATED',
                f'{order}: design was promoted to observed/accepted')
        require(design.get('physical_depth') == 'UNKNOWN', f'{order}: invented physical depth')
        require(design.get('local_before_behind') == 'UNKNOWN', f'{order}: unvalidated physical ordering')
        require(design.get('local_mask') == 'UNKNOWN', f'{order}: unvalidated runtime mask')
        require(design.get('pose_scope') == 'DEFAULT_ONLY', f'{order}: scope exceeds default source evidence')
        require('receiver_order' in design and equal_json(design['receiver_order'], RECEIVERS.get(order)),
                f'{order}: wrong receiver')
        require('shadow_caster_order' in design and equal_json(design['shadow_caster_order'], CASTERS.get(order)),
                f'{order}: wrong caster')
        require(design.get('late_paint') is (order in {58, 59, 60, 61}), f'{order}: wrong late-paint flag')
        require(isinstance(design.get('role'), str) and bool(design['role']), f'{order}: role missing')
        if order in {27, 37}:
            require(design.get('role') == 'LOCAL_EYE_CANVAS', f'{order}: eye canvas role missing')
    require(len(observed_uuids) == len(set(observed_uuids)) == 62, 'Native UUIDs not unique')
    require(equal_json(data.get('multiply_orders'), facts['multiply_orders']), 'Multiply list mismatch')
    require(equal_json(data.get('default_shadow_clips'), facts['default_shadow_clips']), 'Default clip list mismatch')
    late = data.get('late_face_paint_over_hair', [])
    require(isinstance(late, list) and len(late) == 4, 'Need all four late-face observations')
    if isinstance(late, list) and len(late) == 4:
        for actual, expected in zip(late, facts['late_face_paint_over_hair']):
            if not isinstance(actual, dict):
                require(False, 'Malformed late-paint observation'); continue
            for key in ['psd_order', 'alpha_gt0_pixels', 'overlap_hair_alpha_ge253_pixels']:
                require(equal_json(actual.get(key), expected[key]), f'Late-paint observation {key} mismatch')
    claims = data.get('claims', {})
    if not isinstance(claims, dict):
        require(False, 'Claims must be an object'); claims = {}
    for key, expected in {'overall_M1': 'NOT_ACCEPTED', 'runtime_receiver_compositor': 'NOT_IMPLEMENTED',
                          'physical_yaw_degrees': 'UNKNOWN'}.items():
        require(claims.get(key) == expected, f'Claim {key} overstates acceptance')
    return {'schema': 'core026-m1c1-supervisor/1',
            'status': 'PASS_SOURCE_FACTS_AND_DESIGN_CONTRACT' if not problems else 'FAIL',
            'constraints_sha256': sha(path), 'records': len(rows), 'source_facts_checked': len(observed_uuids),
            'multiply_count': len(facts['multiply_orders']), 'default_clip_count': len(facts['default_shadow_clips']),
            'late_overlap_counts': [r['overlap_hair_alpha_ge253_pixels'] for r in facts['late_face_paint_over_hair']],
            'problems': problems, 'overall_M1': 'NOT_ACCEPTED_BY_THIS_CHECK',
            'runtime_compositor': 'NOT_IMPLEMENTED', 'natural_3d_turn': 'NOT_EVALUATED'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--constraints', type=Path, default=ROOT / 'config/core026-constraints.json')
    ap.add_argument('--report', type=Path, default=ROOT / 'out/core026/m1c1-supervisor.json')
    args = ap.parse_args()
    for script in ['verify_core026_registration.py', 'verify_core026_constraints.py']:
        result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(f'Independent prerequisite {script} failed: {result.stderr[-1000:]}')
    result = verify(args.constraints)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('CORE026_M1C1_SUPERVISOR', json.dumps(result, ensure_ascii=False))
    return 0 if not result['problems'] else 11


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f'CORE026_M1C1_SUPERVISOR_FAIL: {exc}', file=sys.stderr)
        sys.exit(11)
