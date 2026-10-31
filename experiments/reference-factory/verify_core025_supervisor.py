"""Independent supervisor acceptance of real CORE-025 browser captures.

This validator is authored by the supervisor, independently of mcode's scene.
It reads actual exported geometry and pixels, without importing scene code.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out/core025/render'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def signature(params):
    return tuple(params[k] for k in ('version', 'yaw_deg', 'depth', 'background', 'pass', 'size'))


def rgba(path):
    return np.asarray(Image.open(path).convert('RGBA'))


def background(image, value):
    a = image[..., 3:4].astype(float) / 255
    return np.rint(image[..., :3] * a + value * (1-a)).astype(np.uint8)


def validate(report):
    manifest = read(OUT / 'manifest.json')
    assembly = read(ROOT / 'out/core025/assembly/assembly.json')
    cfg = read(ROOT / 'config/core025-render.json')
    inputs = {'assembly_sha256': 'out/core025/assembly/assembly.json',
              'config_sha256': 'config/core025-render.json',
              'scene_sha256': 'core025.js', 'capture_sha256': 'capture_core025.mjs'}
    for key, file in inputs.items():
        require(manifest['inputs'][key] == sha(ROOT / file), f'stale input: {file}')
    require(manifest['geometry']['sha256'] == sha(OUT / manifest['geometry']['file']), 'geometry hash')
    captures = manifest['captures']
    expected = [(v, 0, 'curved', b, 'beauty', 1630) for v in ('source', 'clean') for b in ('white', 'black')]
    expected += [('clean', y, 'curved', 'black' if p == 'silhouette' else 'white', p, 1630)
                 for y in (-15, 0, 15) for p in ('beauty', 'silhouette', 'part_id', 'wireframe')]
    expected += [('clean', 15, 'flat', 'white', 'beauty', 1630)]
    require(Counter(signature(c['params']) for c in captures) == Counter(expected), '17-capture plan mismatch')
    require(len({c['id'] for c in captures}) == 17, 'duplicate capture IDs')
    camera = np.asarray(captures[0]['pose']['camera_matrix'])
    projection = np.asarray(captures[0]['pose']['projection_matrix'])
    for c in captures:
        require(c['sha256'] == sha(OUT / c['file']), f'PNG hash: {c["id"]}')
        require(Image.open(OUT / c['file']).size == (1630, 1630), f'PNG size: {c["id"]}')
        pose = c['pose']
        require(pose['geometry_count'] == 62 and pose['active_draw_mesh_count'] == 124, 'active mesh counts')
        require(np.array_equal(camera, pose['camera_matrix']), 'camera moved')
        require(np.array_equal(projection, pose['projection_matrix']), 'projection changed')
        angle = math.radians(c['params']['yaw_deg'])
        co, si = math.cos(angle), math.sin(angle)
        target = np.array([[co, 0, si, 0], [0, 1, 0, 0], [-si, 0, co, 0], [0, 0, 0, 1]])
        matrix = np.asarray(pose['group_matrix']).reshape(4, 4, order='F')
        require(np.isfinite(matrix).all() and np.max(np.abs(matrix-target)) <= 1e-6, 'head rotation mismatch')
    layers = read(OUT / manifest['geometry']['file'])['layers']
    require(len(layers) == 62 and {l['order'] for l in layers} == set(range(1, 63)), '62 geometry identities')
    source = {l['order']: l for l in assembly['layers']}
    uv_error, z_error, vertices = 0., 0., 0
    for layer in layers:
        order = layer['order']
        require(layer['name'] == source[order]['name'] and layer['bounds'] == source[order]['bounds'], 'layer correspondence')
        p = np.asarray(layer['positions']).reshape(-1, 3)
        uv = np.asarray(layer['uv']).reshape(-1, 2)
        indices = np.asarray(layer['indices'])
        require(len(p) == len(uv) and np.isfinite(p).all() and np.isfinite(uv).all(), 'nonfinite geometry')
        require(indices.size > 0 and indices.size % 3 == 0 and np.isfinite(indices).all(), 'triangle indices')
        require(np.all(indices == indices.astype(int)) and indices.min() >= 0 and indices.max() < len(p), 'index range')
        left, top, right, bottom = layer['bounds']
        sx, sy = 815 + p[:, 0]*815, 815-p[:, 1]*815
        require(np.allclose([sx.min(), sy.min(), sx.max(), sy.max()], layer['bounds'], atol=.001, rtol=0), 'source bounds')
        error = max(np.abs(sx-(left+uv[:, 0]*(right-left))).max(),
                    np.abs(sy-(top+(1-uv[:, 1])*(bottom-top))).max())
        uv_error = max(uv_error, float(error))
        d = cfg['depth']
        h = d['a1']*np.exp(-(p[:, 0]/d['sx1'])**2-((p[:, 1]+d['yoffset1'])/d['sy1'])**2)
        h += d['a2']*np.exp(-(p[:, 0]/d['sx2'])**2-((p[:, 1]+d['yoffset2'])/d['sy2'])**2)
        z_error = max(z_error, float(np.abs(p[:, 2]-h-order*d['layer_offset']).max()))
        vertices += len(p)
        if order == 13:
            centered = p-p.mean(0)
            _, _, vh = np.linalg.svd(centered, full_matrices=False)
            face = {'vertices': len(p), 'z_range': float(np.ptp(p[:, 2])),
                    'max_plane_residual': float(np.abs(centered @ vh[-1]).max())}
    require(uv_error <= .001 and z_error <= 1e-5, 'UV or surface formula gate')
    require(face['z_range'] > .02 and face['max_plane_residual'] > .005, 'face is planar')
    metrics = {}
    review = []
    for version in ('source', 'clean'):
        cpu = rgba(ROOT / assembly['comparisons'][version]['cpu_composite']['file'])
        fg = cpu[..., 3] > 0
        require(fg.any(), 'empty CPU foreground')
        for name, value in (('white', 255), ('black', 0)):
            matches = [c for c in captures if signature(c['params']) == (version, 0, 'curved', name, 'beauty', 1630)
                       and c['repeat_sha256'] is not None]
            require(len(matches) == 1, 'missing front repeat capture')
            c = matches[0]
            require(c['repeat_sha256'] == c['sha256'], 'repeat differs')
            gpu = np.asarray(Image.open(OUT / c['file']).convert('RGB'))
            ref = background(cpu, value)
            diff = np.abs(gpu.astype(np.int16)-ref.astype(np.int16))
            metric = {'mae_0_255': float(diff[fg].mean()), 'max_channel_error': int(diff[fg].max()),
                      'over16_fraction': float((diff[fg].max(1) > 16).mean()),
                      'outside_foreground_mae': float(diff[~fg].mean())}
            require(metric['mae_0_255'] <= 1 and metric['over16_fraction'] <= .001, f'front fidelity: {version}/{name}')
            metrics[f'{version}_{name}'] = metric
            if name == 'white':
                review += [(f'{version} CPU reference', Image.fromarray(ref)),
                           (f'{version} real GPU', Image.fromarray(gpu)),
                           (f'{version} abs difference x8', Image.fromarray(np.clip(diff*8, 0, 255).astype(np.uint8)))]
    def select(yaw, depth='curved', pass_name='beauty'):
        return next(c for c in captures if signature(c['params']) == ('clean', yaw, depth, 'white', pass_name, 1630))
    curved, flat = select(15), select(15, 'flat')
    require(curved['sha256'] != flat['sha256'], 'curved and flat images identical')
    delta = [np.linalg.norm(np.asarray(v['pixel_xy'])-flat['pose']['landmarks'][n]['pixel_xy'])*640/1630
             for n, v in curved['pose']['landmarks'].items()]
    require(np.isfinite(delta).all() and np.mean(delta) > .5, 'curved/flat projection ablation')
    for pass_name in ('beauty', 'wireframe'):
        review += [(f'clean {yaw:+d} deg / {pass_name}', Image.open(OUT / select(yaw, pass_name=pass_name)['file']).convert('RGB'))
                   for yaw in (-15, 0, 15)]
    sheet = Image.new('RGB', (1560, 4*548), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for i, (label, image) in enumerate(review):
        image.thumbnail((520, 520), Image.Resampling.LANCZOS)
        x, y = i % 3*520, i // 3*548
        sheet.paste(image, (x+(520-image.width)//2, y))
        draw.text((x+6, y+526), label, fill='white')
    sheet.save(OUT / 'supervisor-review-sheet.png')
    report.update(numeric_gate='PASS', geometry_count=62, total_vertices=vertices, face=face,
                  uv_max_source_px=uv_error, surface_max_world_error=z_error,
                  front_fidelity=metrics, curved_flat_mean_anchor_px_at640=float(np.mean(delta)),
                  capture_count=17, all_hashes_valid=True, fixed_camera=True,
                  inputs=manifest['inputs'], validator_sha256=sha(__file__))


def main():
    report = {'schema': 'koma-core025-supervisor-qa/1', 'numeric_gate': 'FAIL',
              'visual_gate': 'NOT_REVIEWED', 'production_gate': 'NOT_ACCEPTED', 'failures': []}
    try:
        require(len(sys.argv) == 1, 'usage: python verify_core025_supervisor.py')
        validate(report)
    except Exception as error:
        report['failures'].append(f'{type(error).__name__}: {error}')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'supervisor-qa.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    return 0 if report['numeric_gate'] == 'PASS' and not report['failures'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
