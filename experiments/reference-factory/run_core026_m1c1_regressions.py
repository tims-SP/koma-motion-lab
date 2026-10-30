#!/usr/bin/env python3
"""Exercise both verifiers against real candidate data and isolated corruptions."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / 'config/core026-constraints.json'
OUT = ROOT / 'out/core026/m1c1-regressions'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(script, *args):
    result = subprocess.run([sys.executable, str(ROOT / script), *map(str, args)],
                            cwd=ROOT, capture_output=True, text=True)
    return {'exit_code': result.returncode, 'output_tail': (result.stdout + result.stderr)[-2000:]}


def replace(document, path, value):
    parent = document
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value


def swap_uuids(document):
    left, right = document['records'][0]['observed'], document['records'][1]['observed']
    left['native_uuid'], right['native_uuid'] = right['native_uuid'], left['native_uuid']


def remove_late_flag(document):
    del document['records'][59]['design']['late_paint']


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    baseline_sha = sha(CONFIG)
    data = json.loads(CONFIG.read_text())
    positive = {
        'producer': invoke('extract_core026_constraints.py', '--verify'),
        'supervisor': invoke('verify_core026_m1c1_supervisor.py')}
    problems = [f'Positive {key} failed' for key, result in positive.items() if result['exit_code'] != 0]
    mutations = [
        ('swap-valid-native-uuids', swap_uuids),
        ('shadow-attached-to-caster', lambda j: replace(j, ['records', 13, 'design', 'receiver_order'], 44)),
        ('missing-late-brow-paint', remove_late_flag),
        ('invent-normal-instead-of-clip', lambda j: replace(j, ['records', 27, 'observed', 'native_blend_mode'], 'Normal')),
        ('wrong-source-texture-hash', lambda j: replace(j, ['records', 12, 'texture_sha256'], '0' * 64)),
        ('float-receiver-id', lambda j: replace(j, ['records', 5, 'design', 'receiver_order'], 5.0)),
        ('invent-overlap-count', lambda j: replace(j, ['late_face_paint_over_hair', 2, 'overlap_hair_alpha_ge253_pixels'], 0)),
        ('claim-compositor-implemented', lambda j: replace(j, ['claims', 'runtime_receiver_compositor'], 'IMPLEMENTED')),
        ('wrong-input-inx-hash', lambda j: replace(j, ['inputs', 'inx_sha256'], '0' * 64))]
    cases = []
    for name, mutate in mutations:
        candidate = copy.deepcopy(data); mutate(candidate)
        path = OUT / f'{name}.json'
        path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n')
        before = sha(path)
        results = {
            'producer': invoke('extract_core026_constraints.py', '--verify', '--output', path),
            'supervisor': invoke('verify_core026_m1c1_supervisor.py', '--constraints', path,
                                 '--report', OUT / f'{name}-report.json')}
        unchanged = sha(path) == before
        passed = unchanged and all(r['exit_code'] == 11 for r in results.values())
        if not passed:
            problems.append(f'Corruption was not rejected cleanly: {name}')
        cases.append({'name': name, 'status': 'REJECTED_AS_EXPECTED' if passed else 'FAIL',
                      'verify_did_not_modify_candidate': unchanged, **results})
    rebuilt = OUT / 'rebuilt.json'
    reconstruction = invoke('extract_core026_constraints.py', '--build', '--output', rebuilt)
    repeat_equal = reconstruction['exit_code'] == 0 and rebuilt.read_bytes() == CONFIG.read_bytes()
    if not repeat_equal:
        problems.append('Repeated build differs from committed candidate')
    restored = {
        'producer': invoke('extract_core026_constraints.py', '--verify'),
        'supervisor': invoke('verify_core026_m1c1_supervisor.py')}
    if sha(CONFIG) != baseline_sha or any(r['exit_code'] != 0 for r in restored.values()):
        problems.append('Original candidate changed or failed after corruption checks')
    report = {'schema': 'core026-m1c1-corruption-regressions/1',
              'status': 'PASS' if not problems else 'FAIL', 'baseline_sha256': baseline_sha,
              'positive': positive, 'cases': cases, 'repeated_build_identical': repeat_equal,
              'original_candidate_unchanged': sha(CONFIG) == baseline_sha, 'restored': restored,
              'problems': problems, 'overall_M1': 'NOT_ACCEPTED_BY_THIS_CHECK'}
    (ROOT / 'out/core026/m1c1-regressions.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('CORE026_M1C1_REGRESSIONS', json.dumps({'status': report['status'], 'negative_cases': len(cases),
          'all_rejected_by_both': all(c['status'] == 'REJECTED_AS_EXPECTED' for c in cases),
          'repeated_build_identical': repeat_equal, 'original_candidate_unchanged': report['original_candidate_unchanged'],
          'problems': problems}))
    return 0 if not problems else 11


if __name__ == '__main__':
    sys.exit(main())
