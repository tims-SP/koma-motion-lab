#!/usr/bin/env python3
"""Supervisor audit of default source-UV coordinates, not a rig or 3D recovery.

Independently disambiguates duplicated paintings using original INX transforms
and a single translation estimated from raster-unique correspondences.
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


def digest(b):
    return hashlib.sha256(b).hexdigest()


def main():
    source = ROOT / 'out/source/Aka.inx'
    raw = source.read_bytes()
    assert digest(raw) == 'dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f'
    length = struct.unpack('>I', raw[8:12])[0]
    model = json.loads(raw[12:12 + length])
    nodes, chains = {}, {}

    def visit(node, chain):
        nodes[node['uuid']] = node
        chains[node['uuid']] = chain + [node]
        for child in node.get('children', []):
            visit(child, chain + [node])

    visit(model['nodes'], [])
    pos = 12 + length
    assert raw[pos:pos + 8] == b'TEX_SECT'
    pos += 8
    count = struct.unpack('>I', raw[pos:pos + 4])[0]
    pos += 4
    sizes = []
    for _ in range(count):
        size = struct.unpack('>I', raw[pos:pos + 4])[0]
        pos += 5
        with Image.open(io.BytesIO(raw[pos:pos + size])) as im:
            sizes.append(im.size)
        pos += size
    contract_path = ROOT / 'config/core025-layer-contract.json'
    contract = json.loads(contract_path.read_text())
    pixel_path = OUT / 'supervisor-source-qa.json'
    pixels = json.loads(pixel_path.read_text())
    assert pixels['status'] == 'SOURCE_PIXEL_CHECK_PASS'
    assert len(pixels['entries']) == 62
    rows, translation_samples = [], []
    for pixel in pixels['entries']:
        order = pixel['psd_order']
        layer = contract['layers'][order - 1]
        assert layer['order'] == order
        assert digest((ROOT / layer['raw_source_texture']['file']).read_bytes()) == layer['raw_source_texture']['sha256']
        source_bbox = np.array(pixel['source_alpha_bbox'][:2], dtype=float)
        candidates = []
        for evidence in pixel['pixel_candidates']:
            uuid = evidence['inx_uuid']
            node = nodes[uuid]
            tid = evidence['texture_id']
            assert node['textures'][0] == tid
            mesh = node['mesh']
            assert mesh.get('origin') in (None, [0, 0])
            uv = np.array(mesh['uvs'], dtype=float).reshape(-1, 2)
            vertices = np.array(mesh['verts'], dtype=float).reshape(-1, 2)
            assert uv.shape == vertices.shape
            source_xy = uv * np.array(sizes[tid]) + np.array(layer['bounds'][:2]) + source_bbox - np.array(evidence['native_alpha_bbox'][:2])
            world_xy = vertices.copy()
            for ancestor in reversed(chains[uuid]):
                assert not ancestor.get('lockToRoot', False)
                transform = ancestor['transform']
                assert transform['rot'][:2] == [0, 0], 'Unsupported X/Y rotation'
                world_xy *= transform['scale']
                angle = transform['rot'][2]
                c, s = np.cos(angle), np.sin(angle)
                world_xy = world_xy @ np.array([[c, s], [-s, c]])
                world_xy += np.array(transform['trans'][:2])
            delta = world_xy - source_xy
            offset = np.median(delta, axis=0)
            candidates.append({'inx_uuid': uuid, 'inx_name': node['name'], 'texture_id': tid,
                               'texture_size': list(sizes[tid]), 'median_world_minus_source': offset.tolist(),
                               'within_layer_residual_max_px': float(np.linalg.norm(delta - offset, axis=1).max()),
                               'source_xy': source_xy.tolist(), 'default_world_xy': world_xy.tolist(),
                               'original_uv': uv.tolist(), 'indices': mesh['indices'],
                               'original_mesh_sha256': digest(json.dumps(mesh, sort_keys=True, separators=(',', ':')).encode()),
                               'ancestors_leaf_to_root': [{'uuid': a['uuid'], 'transform': a['transform']} for a in reversed(chains[uuid])]})
            if len(pixel['pixel_candidates']) == 1:
                translation_samples.extend(delta.tolist())
        rows.append({'psd_order': order, 'psd_name': layer['name'], 'candidates': candidates})
    translation = np.median(np.array(translation_samples), axis=0)
    unique_residuals = np.linalg.norm(np.array(translation_samples) - translation, axis=1)
    assert unique_residuals.max() <= 5, 'Global default coordinate mismatch'
    for row in rows:
        ranked = sorted(row['candidates'], key=lambda c: np.linalg.norm(np.array(c['median_world_minus_source']) - translation))
        for candidate in ranked:
            candidate['distance_from_global_translation_px'] = float(np.linalg.norm(np.array(candidate['median_world_minus_source']) - translation))
        if len(ranked) > 1:
            assert ranked[0]['distance_from_global_translation_px'] < 2
            assert ranked[1]['distance_from_global_translation_px'] > 20
        selected = ranked[0]
        row['selected_uuid'] = selected['inx_uuid']
        row['selection'] = 'UNIQUE_RASTER' if len(ranked) == 1 else 'RASTER_AND_DEFAULT_SPACE_DISAMBIGUATION'
        row['status'] = 'VERIFIED_DEFAULT_SOURCE_SPACE'
        row['candidates'] = ranked
        row['source_xy'] = selected['source_xy']
        row['default_world_xy'] = selected['default_world_xy']
    assert len(rows) == 62 and len({r['selected_uuid'] for r in rows}) == 62
    result = {'schema': 'core026-supervisor-default-source-space/1', 'status': 'PASS_DEFAULT_SOURCE_COORDINATES',
              'source_inx_sha256': digest(raw), 'contract_sha256': digest(contract_path.read_bytes()),
              'pixel_audit_sha256': digest(pixel_path.read_bytes()), 'source_node_count': len(nodes),
              'global_world_minus_source_translation': translation.tolist(),
              'raster_unique_median_residual_source_px': float(np.median(unique_residuals)),
              'raster_unique_max_residual_source_px': float(unique_residuals.max()),
              'convention': 'native TGA UV*full texture size + PSD layer bounds + source alpha offset - native alpha offset; original source parent scale/Rz/translation; one global translation only',
              'guards': {'unique_max_source_px': 5, 'duplicate_best_source_px_lt': 2, 'duplicate_second_source_px_gt': 20},
              'claims': {'original_uv_changed': False, 'GPU_registration': 'NOT_TESTED',
                         'HeadYaw_motion': 'NOT_TESTED', 'depth_3d': 'NOT_RECOVERED', 'overall_M1': 'NOT_ACCEPTED_BY_THIS_CHECK'},
              'entries': rows}
    (OUT / 'default-registration.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'entries'}, ensure_ascii=False))
    print('Duplicate selections', [(r['psd_order'], r['selected_uuid']) for r in rows if len(r['candidates']) > 1])


if __name__ == '__main__':
    main()
