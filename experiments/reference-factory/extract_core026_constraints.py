#!/usr/bin/env python3
"""Source occlusion facts and unvalidated receiver proposals.

Codex local fallback: mcode execution was blocked by automatic approval review.
No network access, source edits, physical-depth estimates or renderer changes.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
INX_SHA = 'dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f'
CONTRACT_SHA = '9f6d4190b597053027403575fa7b37d05bedf878e03d12c83efa46ae01fe9b6d'
SURFACES = {1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13, 44, 46, 48, 50, 52, 54, 56, 62}
FACE_PAINT = {21, 22, 23, 24, 25, 26, 27, 30, 31, 32, 33, 34, 35, 36, 37,
              40, 41, 42, 43, 58, 59, 60, 61}
RECEIVERS = {6: 5, 12: 11, **{n: 13 for n in range(14, 21)},
             **{n: 13 for n in FACE_PAINT}, 28: 27, 29: 27, 38: 37, 39: 37,
             45: 44, 47: 46, 49: 48, 51: 50, 53: 52, 55: 54, 57: 56}
CASTERS = dict(zip(range(14, 21), (44, 46, 50, 48, 54, 52, 56)))
HAIR = {44, 46, 48, 50, 52, 54, 56}
LATE = {58, 59, 60, 61}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside_root(path):
    path = path.resolve()
    require(path.is_relative_to(ROOT), f'Path outside project: {path.name}')
    return path


def build():
    inx = ROOT / 'out/source/Aka.inx'
    contract_path = ROOT / 'config/core025-layer-contract.json'
    registration_path = ROOT / 'out/core026/default-registration.json'
    require(sha(inx) == INX_SHA, 'Frozen INX SHA mismatch')
    require(sha(contract_path) == CONTRACT_SHA, 'Frozen layer-contract SHA mismatch')
    raw = inx.read_bytes()
    require(len(raw) >= 12, 'Truncated INX header')
    length = struct.unpack('>I', raw[8:12])[0]
    require(0 < length <= len(raw) - 12, 'Invalid INX JSON length')
    model = json.loads(raw[12:12 + length])
    contract = json.loads(contract_path.read_text())
    registration = json.loads(registration_path.read_text())
    require(registration['status'] == 'PASS_DEFAULT_SOURCE_COORDINATES', 'Registration not verified')
    require(registration['source_inx_sha256'] == INX_SHA and
            registration['contract_sha256'] == CONTRACT_SHA, 'Registration input hashes differ')
    require([r['psd_order'] for r in registration['entries']] == list(range(1, 63)),
            'Registration must contain ordered identities 1..62')
    require([r['order'] for r in contract['layers']] == list(range(1, 63)),
            'Contract must contain ordered identities 1..62')
    by_order = {r['psd_order']: r['selected_uuid'] for r in registration['entries']}
    by_uuid = {uuid: order for order, uuid in by_order.items()}
    require(len(by_uuid) == 62, 'Registration UUIDs are not unique')
    nodes, chains = {}, {}

    def visit(node, chain):
        uuid = node['uuid']
        require(uuid not in nodes, f'Duplicate source node UUID: {uuid}')
        nodes[uuid], chains[uuid] = node, chain
        for child in node.get('children', []):
            visit(child, chain + [uuid])

    visit(model['nodes'], [])
    require(all(uuid in nodes for uuid in by_uuid), 'Mapped node missing in original INX')
    identity_rows = []
    for row in registration['entries']:
        uuid = row['selected_uuid']
        candidates = [c for c in row['candidates'] if c['inx_uuid'] == uuid]
        require(len(candidates) == 1, 'Selected registration candidate is not unique')
        mesh_sha = hashlib.sha256(json.dumps(nodes[uuid]['mesh'], sort_keys=True,
                                  separators=(',', ':')).encode()).hexdigest()
        require(candidates[0]['original_mesh_sha256'] == mesh_sha, 'Original registration mesh changed')
        identity_rows.append([row['psd_order'], uuid, mesh_sha])
    identity_sha = hashlib.sha256(json.dumps(identity_rows, separators=(',', ':')).encode()).hexdigest()
    parameters = [p for p in model['param'] if p['name'] == 'Head:: Yaw-Pitch']
    require(len(parameters) == 1 and len(parameters[0]['bindings']) == 114, 'Unexpected yaw/pitch bindings')
    bindings = parameters[0]['bindings']
    width, height = contract['canvas']
    alpha, records = {}, []
    require(SURFACES | RECEIVERS.keys() == set(range(1, 63)) and not SURFACES & RECEIVERS.keys(),
            'Proposal map does not cover all 62 layers exactly once')
    for layer in contract['layers']:
        order = layer['order']; uuid = by_order[order]; node = nodes[uuid]
        texture = inside_root(ROOT / layer['raw_source_texture']['file'])
        texture_sha = sha(texture)
        require(texture_sha == layer['raw_source_texture']['sha256'], f'Layer {order}: texture SHA mismatch')
        x0, y0, x1, y1 = layer['bounds']
        require(0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height, f'Layer {order}: invalid bounds')
        with Image.open(texture) as image:
            require(image.size == (x1 - x0, y1 - y0), f'Layer {order}: texture/bounds mismatch')
            if order in HAIR | LATE:
                canvas = np.zeros((height, width), dtype=np.uint8)
                canvas[y0:y1, x0:x1] = np.asarray(image.convert('RGBA'))[..., 3]
                alpha[order] = canvas
        chain = chains[uuid]
        observed = {
            'psd_order': order, 'psd_name': layer['name'], 'native_uuid': uuid,
            'native_name': node['name'], 'ancestor_uuids': chain,
            'ancestor_names': [nodes[parent]['name'] for parent in chain],
            'nearest_mapped_ancestor_order': next((by_uuid[p] for p in reversed(chain) if p in by_uuid), None),
            'native_blend_mode': node.get('blend_mode'), 'source_blend_mode': layer['source_blend_mode'],
            'native_zsort': node.get('zsort'), 'zsort_meaning': 'DEFAULT_PAINT_ORDER_NOT_PHYSICAL_DEPTH',
            'head_yaw_binding_names': [b['param_name'] for b in bindings if b['node'] == uuid],
            'physical_depth': 'UNKNOWN', 'status': 'SOURCE_OBSERVED'}
        role = ('INDEPENDENT_SURFACE' if order in SURFACES else 'LOCAL_EYE_CANVAS' if order in {27, 37}
                else 'RECEIVER_SHADOW' if order in {6, 12} | CASTERS.keys()
                else 'HIGHLIGHT' if order in {45, 47, 49, 51, 53, 55, 57} else 'ATTACHED_PAINT')
        design = {'status': 'DESIGN_PROPOSAL_NOT_RENDER_VALIDATED', 'receiver_order': RECEIVERS.get(order),
                  'shadow_caster_order': CASTERS.get(order), 'role': role, 'late_paint': order in LATE,
                  'physical_depth': 'UNKNOWN', 'local_before_behind': 'UNKNOWN', 'local_mask': 'UNKNOWN',
                  'pose_scope': 'DEFAULT_ONLY',
                  'reason': 'Explicit work-order proposal; physical depth, dynamic masks and attachment roots are unvalidated.'}
        if order in LATE:
            design['reason'] += ' Retain late face painting over hair; face attachment does not put this paint under hair.'
        records.append({'psd_order': order, 'texture_sha256': texture_sha, 'observed': observed, 'design': design})
    hair = np.maximum.reduce([alpha[order] for order in sorted(HAIR)])
    late = [{'psd_order': order, 'alpha_gt0_pixels': int((alpha[order] > 0).sum()),
             'overlap_hair_alpha_ge253_pixels': int(((alpha[order] > 0) & (hair >= 253)).sum()),
             'status': 'SOURCE_OBSERVED_DEFAULT_ONLY'} for order in sorted(LATE)]
    multiply = [r['order'] for r in contract['layers'] if 'MULTIPLY' in r['source_blend_mode']]
    clips = contract['clean_shadow_alpha_clip']
    require(len(multiply) == 11 and len(clips) == 9, 'Unexpected multiply/default-clip count')
    return {'schema': 'core026-constraints/2', 'scope': 'DEFAULT_SOURCE_AND_UNVALIDATED_DESIGN',
            'inputs': {'inx_sha256': INX_SHA, 'contract_sha256': CONTRACT_SHA,
                       'registration_identity_sha256': identity_sha,
                       'registration_program_sha256': sha(ROOT / 'verify_core026_registration.py')},
            'records': records, 'multiply_orders': multiply, 'default_shadow_clips': clips,
            'late_face_paint_over_hair': late,
            'claims': {'overall_M1': 'NOT_ACCEPTED', 'runtime_receiver_compositor': 'NOT_IMPLEMENTED',
                       'physical_yaw_degrees': 'UNKNOWN', 'moving_occlusion': 'NOT_TESTED'}}


def first_difference(expected, actual, path='$'):
    if type(expected) is not type(actual):
        return f'{path}: type differs'
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            return f'{path}: keys differ'
        for key in expected:
            difference = first_difference(expected[key], actual[key], f'{path}.{key}')
            if difference:
                return difference
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            return f'{path}: length differs'
        for index, (left, right) in enumerate(zip(expected, actual)):
            difference = first_difference(left, right, f'{path}[{index}]')
            if difference:
                return difference
    elif expected != actual:
        return f'{path}: value differs'
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--build', action='store_true')
    mode.add_argument('--verify', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'config/core026-constraints.json')
    args = parser.parse_args()
    output = inside_root(args.output)
    expected = build()
    if args.build:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + '\n')
    else:
        difference = first_difference(expected, json.loads(output.read_text()))
        require(difference is None, f'Constraint verification failed: {difference}')
    print('CORE026_CONSTRAINTS', json.dumps({'status': 'BUILT' if args.build else 'VERIFIED',
          'records': len(expected['records']), 'multiply': len(expected['multiply_orders']),
          'default_clips': len(expected['default_shadow_clips']),
          'late_overlaps': [r['overlap_hair_alpha_ge253_pixels'] for r in expected['late_face_paint_over_hair']],
          'overall_M1': 'NOT_ACCEPTED', 'runtime_receiver_compositor': 'NOT_IMPLEMENTED'}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'CORE026_CONSTRAINTS_FAIL: {error}', file=sys.stderr)
        sys.exit(11)
