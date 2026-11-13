#!/usr/bin/env python3
"""Verify provenance of 135/180 view candidates and build an evidence-backed comparison."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'private-assets'
EXPORT = ASSETS / 'exports/p15-118-back-source-review'
EVIDENCE = ROOT / 'evidence/p15-118-back-source-review-qa.json'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def audit():
    old = json.loads((ASSETS/'recovered-review/manifest.json').read_text())
    rows = []
    for angle in (90,135,180):
        frame = next(x for x in old['frames'] if x['group']=='head_8' and x['yawDeg']==angle and x['part']=='whole')
        original = ASSETS/'recovered-review'/frame['path']
        extracted = ASSETS/f'extracted/whole/yaw{angle:03}.png'
        assert digest(original) == frame['sha256'], f'original GIF frame provenance: yaw{angle}'
        assert extracted.is_file()
        with Image.open(original) as source, Image.open(extracted) as comparison:
            source_rgba = source.convert('RGBA')
            candidate_rgba = comparison.convert('RGBA')
            assert source_rgba.size == candidate_rgba.size == (443,443)
            pixel_identical = source_rgba.tobytes() == candidate_rgba.tobytes()
            alpha = candidate_rgba.getchannel('A')
            bbox = alpha.getbbox()
            opaque = sum(v>16 for v in alpha.getdata())
        rows.append({'angle':angle,'source':str(original.relative_to(ASSETS)),
                     'sourceSHA256':digest(original),'extracted':str(extracted.relative_to(ASSETS)),
                     'extractedSHA256':digest(extracted),'pixelIdenticalToRecovered':pixel_identical,
                     'size':[443,443], 'alphaPixelsGt16':opaque, 'alphaBBox':list(bbox) if bbox else None,
                     'registeredToP0Canonical':False,'independentlyEditableLayers':False,
                     'sourceRole':'multi-view whole-frame drawing reference'})
    return {'schema':'KOMA_P15_118_BACK_SOURCE_REVIEW_V1','characterId':'p0_character_001',
            'candidates':rows,'provenance':'recovered-review/manifest.json head_8 frames',
            'identityReferenceApproved':False,'registrationVerified':False,
            'semanticLayerCoverage135180':0,'expectedSemanticLayersPerAngle':13,
            'visualAcceptance':False,
            'next':'Use these native 135/180 drawings as visual references; create true 13-slot source layers, occlusion underpaint, and registration proof before binding VDD.'}

def build():
    result = audit()
    EXPORT.mkdir(parents=True,exist_ok=True)
    width,height = 3*450, 515
    sheet = Image.new('RGB',(width,height),(39,44,53))
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(result['candidates']):
        with Image.open(ASSETS/row['extracted']) as img:
            frame = Image.new('RGBA',img.size,(65,73,85,255))
            frame.alpha_composite(img.convert('RGBA'))
            sheet.paste(frame.convert('RGB'),(i*450,48))
        draw.text((i*450+12,16),f"{row['angle']} deg | extracted source reference",fill=(244,244,244))
    sheet.save(EXPORT/'back-source-contact.jpg',quality=94)
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>P0 back-view source candidates</title><style>body{font:16px system-ui;background:#20252d;color:#eee;margin:30px}img{width:min(100%,1350px)}p{max-width:950px;line-height:1.5}</style><h1>P0 90/135/180° source reference</h1><p>Recovered whole-frame reference paintings, source provenance checked. 135° and 180° require semantic decomposition, occlusion underpaint and identity registration for animation.</p><img src="back-source-contact.jpg" alt="90 135 180 source-reference contact sheet"></html>'''
    (EXPORT/'index.html').write_text(html)
    result['contact']='private-assets/exports/p15-118-back-source-review/back-source-contact.jpg'
    result['entry']='private-assets/exports/p15-118-back-source-review/index.html'
    EVIDENCE.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'candidateAngles':[r['angle'] for r in result['candidates']], 'registered':result['registrationVerified'], 'layers135180':result['semanticLayerCoverage135180']}))

if __name__=='__main__': build()
