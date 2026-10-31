#!/usr/bin/env python3
"""Independent source/correspondence check. Does not accept native captures or M1.

Written by the supervisor, independently of mcode's correspondence implementation.
Compare alpha-trimmed decoded pixels, accounting for INX premultiplied RGB.
No names, left/right assumptions, mirroring or resampling participate in matching.
"""
from pathlib import Path
import hashlib
import io
import json
import struct
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out/core026'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trimmed(im):
    a = np.array(im.convert('RGBA'))
    yy, xx = np.nonzero(a[..., 3])
    assert len(xx), 'Empty source texture'
    bb = [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1]
    return a[bb[1]:bb[3], bb[0]:bb[2]], bb


def main():
    frozen = json.loads((ROOT / 'evidence/core026-M1/supervisor-start-preflight.json').read_text())
    for s in frozen['sources']:
        assert sha(ROOT / 'out/source' / s['file']) == s['expected'], s['file']
    for s in frozen['protected_files']:
        p = ROOT.parents[1] / s['path']
        assert sha(p) == s['sha256'], s['path']
    b = (ROOT / 'out/source/Aka.inx').read_bytes()
    assert b[:8] == b'TRNSRTS\0'
    n = struct.unpack('>I', b[8:12])[0]
    model = json.loads(b[12:12 + n])
    p = next(p for p in model['param'] if p['name'] == 'Head:: Yaw-Pitch')
    assert p['min'] == [-1, -1] and p['max'] == [1, 1] and p['defaults'] == [0, 0]
    assert p['axis_points'] == [[i / 8 for i in range(9)], [0, .5, 1]]
    assert len(p['bindings']) == 114
    nodes = []

    def walk(node):
        if node.get('mesh'):
            nodes.append(node)
        for child in node.get('children', []):
            walk(child)

    walk(model['nodes'])
    pos = 12 + n
    assert b[pos:pos + 8] == b'TEX_SECT'
    pos += 8
    count = struct.unpack('>I', b[pos:pos + 4])[0]
    pos += 4
    textures = []
    for tid in range(count):
        length = struct.unpack('>I', b[pos:pos + 4])[0]
        pos += 5
        assert pos + length <= len(b)
        a, bb = trimmed(Image.open(io.BytesIO(b[pos:pos + length])))
        pos += length
        textures.append((a, bb))
    contract = json.loads((ROOT / 'config/core025-layer-contract.json').read_text())
    assembly = json.loads((ROOT / 'out/core025/assembly/assembly.json').read_text())
    assert [l['order'] for l in contract['layers']] == list(range(1, 63))
    assert [l['order'] for l in assembly['layers']] == list(range(1, 63))
    for layer in assembly['layers']:
        for role in ['raw_source_texture', 'source_texture', 'clean_texture']:
            rec = layer[role]
            assert sha(ROOT / rec['file']) == rec['sha256'], (layer['order'], role)
    entries = []
    for layer in contract['layers']:
        raw, bb = trimmed(Image.open(ROOT / layer['raw_source_texture']['file']))
        premul = np.rint(raw[..., :3].astype(float) * raw[..., 3:4] / 255)
        visible = raw[..., 3] > 0
        matches = []
        for tid, (native, native_bb) in enumerate(textures):
            if raw.shape != native.shape or not np.array_equal(raw[..., 3], native[..., 3]):
                continue
            delta = np.abs(premul - native[..., :3])[visible]
            if delta.max() > 1:
                continue
            for node in nodes:
                if node.get('textures') and node['textures'][0] == tid:
                    matches.append({'inx_uuid': node['uuid'], 'inx_name': node['name'],
                                    'texture_id': tid, 'native_alpha_bbox': native_bb,
                                    'alpha_max_error': 0, 'premul_rgb_max_error': int(delta.max()),
                                    'premul_rgb_mae': float(delta.mean())})
        assert matches, ('No independently supported pixel correspondence', layer['order'])
        entries.append({'psd_order': layer['order'], 'psd_name': layer['name'],
                        'source_alpha_bbox': bb, 'pixel_candidates': matches,
                        'spatial_registration': 'NOT_ACCEPTED_BY_PIXEL_CHECK'})
    mapping_path = ROOT / 'config/core026-part-correspondence.json'
    accepted = []
    unresolved = []
    if mapping_path.exists():
        mapping = json.loads(mapping_path.read_text())
        records = mapping.get('entries', mapping.get('layers', []))
        assert len(records) == 62
        assert sorted(e['psd_order'] for e in records) == list(range(1, 63))
        by_order = {e['psd_order']: e for e in entries}
        for rec in records:
            order = rec['psd_order']
            if rec['status'] != 'VERIFIED':
                unresolved.append(order)
                continue
            expected = by_order[order]['pixel_candidates']
            uuid = rec.get('inx_uuid')
            assert uuid in [e['inx_uuid'] for e in expected], ('Unsupported mapping', order, uuid)
            # A repeated raster is not enough to accept one spatial instance.
            assert len(expected) == 1, ('Spatial disambiguation requires separate review', order)
            accepted.append(order)
    result = {'schema': 'core026-supervisor-independent-source/1', 'status': 'SOURCE_PIXEL_CHECK_PASS',
              'overall_m1': 'NOT_EVALUATED', 'native_capture': 'NOT_EVALUATED',
              'protected_files_checked': len(frozen['protected_files']), 'layer_pngs_checked': 186,
              'source_layers': 62, 'native_textures': count,
              'method': 'Exact alpha after alpha>0 trim; rounded PSD RGB*alpha/255 vs INX RGB, max<=1. No mirror/resampling/names.',
              'unique_pixel_correspondences': sum(len(e['pixel_candidates']) == 1 for e in entries),
              'ambiguous_pixel_orders': [e['psd_order'] for e in entries if len(e['pixel_candidates']) != 1],
              'mcode_verified_independently_supported': accepted, 'mcode_unresolved': unresolved,
              'entries': entries}
    OUT.mkdir(exist_ok=True, parents=True)
    (OUT / 'supervisor-source-qa.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'entries'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
