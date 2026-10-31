#!/usr/bin/env python3
"""Offline restore from an authenticated native job log; no network access."""
import argparse,base64,hashlib,io,json,re,zipfile
from pathlib import Path
from PIL import Image
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--job-log',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parent/'out/core026/reference')
    a=ap.parse_args()
    lines=[re.sub(r'^\d{4}-\d\d-\d\dT\S+\s','',l.lstrip('\ufeff')) for l in a.job_log.read_text(encoding='utf-8-sig').splitlines()]
    i=lines.index('CORE026_REVIEW_BUNDLE_BEGIN');j=lines.index('CORE026_REVIEW_BUNDLE_END',i+1)
    b=base64.b64decode(''.join(lines[i+1:j]),validate=True)
    expected=next(l.split()[1] for l in lines if l.startswith('CORE026_BUNDLE_SHA256 '))
    assert len(b)<=2*1024*1024 and sha(b)==expected
    z=zipfile.ZipFile(io.BytesIO(b));m=json.loads(z.read('reference-manifest.json'))
    assert m['status']=='PASS' and len(m['poses'])==9
    assert m['source']['sha256']=='dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f'
    assert m['capture']['ffmpeg_draw_mouse'] is False
    assert m['capture']['camera_scale']==.4 and m['capture']['camera_position']==[82,1773]
    assert m['roi']['head']==[34,114,686,766]
    assert [p['raw_yaw'] for p in m['poses']]==[v/4 for v in range(-4,5)]
    console=[l for l in lines if l.startswith('CORE026_MANIFEST_JSON ')]
    if console: assert json.loads(console[-1].split(' ',1)[1])==m
    allowed={'reference-manifest.json','patch-report.json'}|{'frames/'+Path(p['full_png']).name for p in m['poses']}
    assert len(z.namelist())==len(set(z.namelist()))==11 and set(z.namelist())==allowed
    files={}
    for item in z.infolist():
        p=Path(item.filename)
        assert not p.is_absolute() and '..' not in p.parts and item.file_size<3000000
        files[item.filename]=z.read(item)
    assert sum(map(len,files.values()))<30000000
    assert sha(files['patch-report.json'])==m['patch_report']['sha256']
    for p in m['poses']:
        name='frames/'+Path(p['full_png']).name
        assert sha(files[name])==p['full_sha256']
        with Image.open(io.BytesIO(files[name])) as im:
            assert im.mode=='RGB' and im.size==(720,880)
            head=im.crop((34,114,686,766));buffer=io.BytesIO();head.save(buffer,format='PNG')
        assert sha(buffer.getvalue())==p['head_sha256'],'Crop encoding differs; use pinned dependencies'
        files['frames/'+Path(p['head_png']).name]=buffer.getvalue()
    for name,data in files.items():
        p=a.out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    result={'status':'RESTORED_AND_HASH_VERIFIED','bundle_sha256':expected,'full_pngs':9,'crop_pngs':9,'natural_3d_turn':'NOT_EVALUATED'}
    (a.out/'restore-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    print('CORE026_RESTORE_QA',json.dumps(result))
if __name__=='__main__': main()
