#!/usr/bin/env python3
"""Extract actual GIF frames in source coordinates for semantic visual QA."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parents[1]

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def checks_image(image):
    alpha = image.getchannel('A')
    hist = alpha.histogram()
    occupied = sum(hist[1:])
    corners = [alpha.getpixel(pos) for pos in ((0,0), (image.width-1,0),
                 (0,image.height-1), (image.width-1,image.height-1))]
    return {'bbox': list(alpha.getbbox()) if alpha.getbbox() else None,
            'partialAlphaPixels': sum(hist[1:255]), 'visiblePixels': occupied,
            'cornersAlphaZero': all(x == 0 for x in corners)}

def key_name(group, index, contract):
    if group == 'whole':
        yaw = contract['wholeAngles'][index]
        return f'yaw{yaw:03d}.png', yaw, 'head.whole'
    config = next(x for x in contract['groups'] if x['name'] == group)
    ids = config['ids']
    yaw = contract['keyAngles'][index // len(ids)]
    sid = ids[index % len(ids)]
    return f'yaw{yaw:03d}/{sid}.png', yaw, sid

def sheet(entries, destination):
    if not entries:
        return
    thumb = 256
    cols = min(5, len(entries))
    rows = math.ceil(len(entries) / cols)
    cellw, cellh = 280, 308
    board = Image.new('RGB', (cols * cellw, rows * cellh), (29,39,51))
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default()
    for i, entry in enumerate(entries):
        im = Image.open(entry['absolutePath']).convert('RGBA')
        im.thumbnail((thumb,thumb), Image.Resampling.LANCZOS)
        tx, ty = (i%cols)*cellw, (i//cols)*cellh
        ox, oy = tx+12,ty+12
        for yy in range(0,256,16):
            for xx in range(0,256,16):
                if (xx//16+yy//16)%2 == 0:
                    draw.rectangle((ox+xx,oy+yy,ox+xx+15,oy+yy+15),fill=(74,80,94))
                else:
                    draw.rectangle((ox+xx,oy+yy,ox+xx+15,oy+yy+15),fill=(111,120,134))
        src = Image.new('RGBA', (256,256))
        src.alpha_composite(im, ((256-im.width)//2,(256-im.height)//2))
        board.paste(src,(ox,oy),src)
        draw.text((tx+12,ty+273),entry['label'][:38],fill=(233,237,244),font=font)
    destination.parent.mkdir(parents=True,exist_ok=True)
    board.save(destination)

def extract(root, contract_path, output):
    root = Path(root).resolve()
    contract = json.loads(Path(contract_path).read_text(encoding='utf8'))
    diagnostics = root / 'extracted'
    groups = [{'name':'whole',**contract['wholeGif']}] + contract['groups']
    found = []
    records = []
    errors = []
    all_canvas_1024 = True
    for group in groups:
        name, source = group['name'], root / group['path']
        if not source.is_file():
            errors.append(f'missing {name}: {source}')
            continue
        digest = sha(source)
        found.append({'name':name,'path':group['path'],'sha256':digest})
        try:
            with Image.open(source) as im:
                if im.format != 'GIF':
                    raise ValueError('GIF format required')
                if getattr(im,'n_frames',1) != group['frames']:
                    errors.append(f'{name} frame count mismatch {im.n_frames}/{group["frames"]}')
                if im.size != (1024,1024):
                    all_canvas_1024 = False
                    errors.append(f'{name} global canvas {im.size} requires 1024x1024')
                local_entries = []
                for index in range(min(im.n_frames,group['frames'])):
                    im.seek(index)
                    rgba = im.convert('RGBA')
                    dispose = getattr(im,'disposal_method',None)
                    rel,yaw,sid = key_name(name,index,contract)
                    dest = diagnostics / name / rel
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    rgba.save(dest)
                    stats = checks_image(rgba)
                    entry = {'sourceGroup':name,'sourceGIF':group['path'],
                             'sourceGIFSHA256':digest,'frameIndex':index,'yawDeg':yaw,
                             'semanticId':sid,'size':list(rgba.size), 'disposal':dispose,
                             'png':str(dest.relative_to(root)), 'pngSHA256':sha(dest),
                             **stats,'role':'gif_decoder_reference_only'}
                    records.append(entry)
                    local_entries.append({'absolutePath':str(dest),
                                          'label':f'{index:02d}  {yaw}deg  {sid}'})
                    if dispose != 2:
                        errors.append(f'{name} frame {index} disposal {dispose} requires 2')
                    if not stats['cornersAlphaZero']:
                        errors.append(f'{name} frame {index} opaque corner')
                sheet(local_entries,diagnostics/'contacts'/f'{name}.png')
        except (ValueError, OSError, IndexError) as error:
            errors.append(f'{name} decode: {error}')
    result = {'schema':'KOMA-GIF-38FRAME-EXTRACTION-QA-V1',
              'characterId':contract['characterId'],
              'role':'reference_frames_not_production_RGBA',
              'sourceGIFs':found,'expectedFrames':38,'extractedFrames':len(records),
              'canvasRegistered':all_canvas_1024 and len(found)==4,
              'sourceChecks':errors,'records':records,
              'status':'READY_FOR_SEMANTIC_VISUAL_REVIEW' if len(records)==38 and not errors
                       else 'SOURCE_FRAME_AUDIT_REQUIRED'}
    output = Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--contract',default=str(HERE/'contract.json'))
    parser.add_argument('--output',required=True)
    args = parser.parse_args()
    report = extract(args.root,args.contract,args.output)
    print(json.dumps({k:report[k] for k in ('status','expectedFrames','extractedFrames','canvasRegistered','sourceChecks')},ensure_ascii=False))
    return 0 if report['status']=='READY_FOR_SEMANTIC_VISUAL_REVIEW' else 2

if __name__=='__main__':
    raise SystemExit(main())
