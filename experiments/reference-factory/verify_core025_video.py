"""Supervisor-owned encoding, decode review and acceptance of CORE-025 video."""
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out/core025/turntable'
VIDEO = OUT / 'core025-head-yaw-15deg.mp4'
ROIS = {'eyes': [200, 340, 440, 445], 'ear_roots': [150, 135, 490, 310],
        'fringe_face': [155, 275, 500, 540], 'neck': [245, 500, 390, 610]}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(args, log):
    result = subprocess.run(args, capture_output=True, text=True)
    (OUT / log).write_text(result.stdout+result.stderr)
    require(result.returncode == 0, f'{args[0]} exit {result.returncode}: {result.stderr[-1200:]}')
    return result.stdout


def rgb(file):
    with Image.open(file) as im:
        require(im.size == (640, 640), f'image size: {file}')
        return np.array(im.convert('RGB'))


def validate(report):
    manifest = json.loads((OUT / 'video-manifest.json').read_text())
    inputs = {'assembly_sha256': 'out/core025/assembly/assembly.json',
              'config_sha256': 'config/core025-render.json', 'scene_sha256': 'core025.js',
              'anchor_manifest_sha256': 'out/core025/render/manifest.json',
              'video_capture_sha256': 'capture_core025_video.mjs'}
    for key, path in inputs.items():
        require(manifest['inputs'][key] == sha(ROOT / path), f'stale video input: {path}')
    require((manifest['fps'], manifest['width'], manifest['height'], manifest['frame_count']) == (24, 640, 640, 97), 'video contract')
    frames = manifest['frames']
    require(len(frames) == 97 and [f['index'] for f in frames] == list(range(97)), 'frame index continuity')
    require({p.name for p in (OUT / 'frames').glob('*.png')} == {f'{i:04d}.png' for i in range(97)}, 'frame file inventory')
    camera = np.asarray(frames[0]['pose']['camera_matrix'])
    projection = np.asarray(frames[0]['pose']['projection_matrix'])
    first = rgb(OUT / frames[0]['file'])
    hashes, margins, loops, changes = [], [], [], []
    for i, frame in enumerate(frames):
        file = OUT / frame['file']
        require(frame['sha256'] == sha(file), f'frame hash {i}')
        hashes.append(frame['sha256'])
        yaw = 15*math.sin(2*math.pi*i/96)
        if abs(yaw) < 1e-10:
            yaw = 0.
        require(abs(frame['yaw_deg']-yaw) < 1e-9, f'planned yaw {i}')
        params = frame['params']
        require(params['version'] == 'clean' and params['depth'] == 'curved' and params['background'] == 'white'
                and params['pass'] == 'beauty' and params['size'] == 640 and abs(params['yaw_deg']-yaw) < 1e-9, f'frame params {i}')
        pose = frame['pose']
        require(np.array_equal(camera, pose['camera_matrix']) and np.array_equal(projection, pose['projection_matrix']), 'camera changed')
        t = math.radians(yaw)
        c, s = math.cos(t), math.sin(t)
        expected = np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]])
        matrix = np.asarray(pose['group_matrix']).reshape(4, 4, order='F')
        require(np.isfinite(matrix).all() and np.abs(matrix-expected).max() <= 1e-6, f'head matrix {i}')
        image = rgb(file)
        foreground = (255-image.astype(int)).max(2) > 3
        ys, xs = np.nonzero(foreground)
        require(len(ys) > 0, f'empty frame {i}')
        margin = int(min(xs.min(), ys.min(), 639-xs.max(), 639-ys.max()))
        margins.append(margin)
        require(margin >= 2, f'cropped subject {i}')
        difference = float(np.abs(image.astype(int)-first.astype(int)).mean())
        if i in (0, 48, 96):
            loops.append(difference)
            require(difference <= .01, f'0-degree roundtrip {i}')
        if i in (24, 72):
            changes.append(difference)
            require(frame['sha256'] != frames[0]['sha256'], 'static extreme frame')
    require(len(set(hashes)) >= 35, 'insufficient changing frames')
    require(len(manifest['black_checks']) == 2, 'black-background checks missing')
    require({b['params']['yaw_deg'] for b in manifest['black_checks']} == {-15, 15}, 'black check angles')
    for check in manifest['black_checks']:
        require(check['sha256'] == sha(OUT / check['file']), 'black check hash')
        require(check['params']['background'] == 'black', 'black check background')
        rgb(OUT / check['file'])
    encode = ['ffmpeg', '-y', '-v', 'error', '-framerate', '24', '-i', str(OUT / 'frames/%04d.png'),
              '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-movflags', '+faststart', str(VIDEO)]
    run(encode, 'ffmpeg-encode.log')
    probe_args = ['ffprobe', '-v', 'error', '-count_frames', '-show_entries',
                  'stream=codec_name,width,height,r_frame_rate,nb_read_frames:format=duration', '-of', 'json', str(VIDEO)]
    probe = json.loads(run(probe_args, 'ffprobe.json'))
    stream = probe['streams'][0]
    require(stream['codec_name'] == 'h264' and (stream['width'], stream['height']) == (640, 640), 'encoded codec/size')
    require(Fraction(stream['r_frame_rate']) == 24 and int(stream['nb_read_frames']) == 97, 'encoded rate/count')
    require(abs(float(probe['format']['duration'])-97/24) <= 1/24, 'encoded duration')
    decoded = OUT / 'decoded-review'
    decoded.mkdir(exist_ok=True)
    for file in decoded.glob('*.png'):
        file.unlink()
    decode = ['ffmpeg', '-y', '-v', 'error', '-i', str(VIDEO), '-vf', r'select=not(mod(n\,8))',
              '-fps_mode', 'vfr', str(decoded / '%03d.png')]
    run(decode, 'ffmpeg-decode.log')
    files = sorted(decoded.glob('*.png'))
    require(len(files) == 13, 'decoded sample count')
    samples = []
    sheet = Image.new('RGB', (1600, 3*346), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for i, file in enumerate(files):
        index = i*8
        image = Image.fromarray(rgb(file))
        image.thumbnail((320, 320), Image.Resampling.LANCZOS)
        x, y = i % 5*320, i // 5*346
        sheet.paste(image, (x, y))
        draw.text((x+4, y+324), f'frame {index:03d} / {frames[index]["yaw_deg"]:+.2f} deg', fill='white')
        samples.append({'source_frame': index, 'yaw_deg': frames[index]['yaw_deg'],
                        'file': str(file.relative_to(OUT)), 'sha256': sha(file)})
    sheet.save(OUT / 'decoded-review-sheet.png')
    heights = [2*(box[3]-box[1])+30 for box in ROIS.values()]
    detail = Image.new('RGB', (2070, sum(heights)), (24, 24, 24))
    draw = ImageDraw.Draw(detail)
    y = 0
    for (name, box), height in zip(ROIS.items(), heights):
        for col, index in enumerate((0, 24, 72)):
            image = Image.open(files[index//8]).convert('RGB').crop(box)
            image = image.resize((image.width*2, image.height*2), Image.Resampling.NEAREST)
            x = col*690+(690-image.width)//2
            detail.paste(image, (x, y))
            draw.text((col*690+6, y+height-24), f'{name} / frame {index} / {frames[index]["yaw_deg"]:+.1f} deg', fill='white')
        y += height
    detail.save(OUT / 'detail-review-sheet.png')
    report.update(numeric_gate='PASS', frames=97, fps=24, unique_raw_images=len(set(hashes)),
                  min_subject_margin_px=min(margins), zero_roundtrip_mae=loops,
                  extreme_vs_zero_mae=changes, fixed_camera=True, ffprobe=probe,
                  video={'file': VIDEO.name, 'sha256': sha(VIDEO), 'bytes': VIDEO.stat().st_size},
                  decoded_samples=samples, rois=ROIS, inputs=manifest['inputs'],
                  validator_sha256=sha(__file__), bbox_method='RGB difference from white >3; coarse outline, not alpha truth')


def main():
    report = {'schema': 'koma-core025-video-supervisor-qa/1', 'numeric_gate': 'FAIL',
              'visual_gate': 'NOT_REVIEWED', 'production_gate': 'NOT_ACCEPTED', 'failures': []}
    try:
        require(len(sys.argv) == 1, 'usage: python verify_core025_video.py')
        validate(report)
    except Exception as error:
        report['failures'].append(f'{type(error).__name__}: {error}')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'video-qa.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    return 0 if report['numeric_gate'] == 'PASS' and not report['failures'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
