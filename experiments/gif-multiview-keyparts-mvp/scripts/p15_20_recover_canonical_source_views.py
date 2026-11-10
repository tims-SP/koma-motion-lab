#!/usr/bin/env python3
"""Recover canonical P0 0/45/90 ArtMesh layers from original P1/P2 manifests.

Copies source layers byte-for-byte. Does not invent, paint, mirror or re-label parts.
"""
import json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
PRIVATE=ROOT/'private-assets'
OUT=PRIVATE/'p15-20-canonical-source-views'
ANGLES=[('yaw000',0,PRIVATE/'p1-front/parts.json'),
        ('yaw045',45,PRIVATE/'p2-views/parts.json'),
        ('yaw090',90,PRIVATE/'p2-views/parts.json')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 views=[];roles=None
 for view,angle,manifest_path in ANGLES:
  manifest=json.loads(manifest_path.read_text())
  if manifest.get('characterId')!='p0_character_001':raise ValueError('identity mismatch')
  entries=[x for x in manifest['parts'] if x['yawDeg']==angle]
  if len(entries)!=13:raise ValueError(f'{view}: expected 13 parts, got {len(entries)}')
  current={x['semanticId'] for x in entries}
  if roles is None:roles=current
  if current!=roles:raise ValueError(f'{view}: semantic slots mismatch')
  dest=OUT/view;dest.mkdir(parents=True,exist_ok=True)
  rows=[]
  for e in sorted(entries,key=lambda x:x['depthOrder']):
   src=PRIVATE/e['path']
   if not src.is_file():raise FileNotFoundError(src)
   with Image.open(src) as im:
    if im.size!=(1024,1024) or im.mode!='RGBA':raise ValueError(f'bad source {src}: {im.size} {im.mode}')
   h=sha(src)
   expected=e.get('sha256') or e.get('frameSha256')
   if expected and expected!=h:raise ValueError(f'manifest hash mismatch {src}: {expected} != {h}')
   target=dest/(e['semanticId']+'.png')
   shutil.copy2(src,target)
   if sha(target)!=h:raise ValueError('copy changed source bytes')
   with Image.open(target) as im:
    alpha=im.getchannel('A')
    bbox=alpha.getbbox()
    pix=sum(1 for a in alpha.getdata() if a>16)
   rows.append({'semanticId':e['semanticId'],'depthOrder':e['depthOrder'],
    'visibility':e.get('visibility'),'anatomicalSide':e.get('anatomicalSide'),
    'sourcePath':e['path'],'path':str(target.relative_to(PRIVATE)),
    'sha256':h,'sourceManifestRecordedSHA256':expected,'alphaPixelsGt16':pix,'alphaBBox':list(bbox) if bbox else None,
    'sourceRole':e.get('sourceRole'),'sourceYaw':angle})
  views.append({'view':view,'yaw':angle,'sourceManifest':str(manifest_path.relative_to(PRIVATE)),
   'sourceManifestSHA256':sha(manifest_path),'parts':rows})
 # Contact sheet, one column per view and one row per semantic component
from PIL import Image as PILImage
def contact(views):
 roles=[x['semanticId'] for x in views[0]['parts']]
 tile=250;label=190;head=38
 canvas=PILImage.new('RGBA',(label+3*tile,head+len(roles)*tile),(38,44,54,255))
 d=ImageDraw.Draw(canvas)
 for i,v in enumerate(views):
  d.text((label+i*tile+8,10),f"{v['yaw']} deg",fill=(245,245,245,255))
  for j,role in enumerate(roles):
   d.text((8,head+j*tile+8),role,fill=(245,245,245,255))
   p=PRIVATE/next(x['path'] for x in v['parts'] if x['semanticId']==role)
   im=PILImage.open(p).convert('RGBA');im.thumbnail((tile-12,tile-12))
   bg=PILImage.new('RGBA',(tile-12,tile-12),(65,72,84,255))
   bg.alpha_composite(im,((tile-12-im.width)//2,(tile-12-im.height)//2))
   canvas.alpha_composite(bg,(label+i*tile+6,head+j*tile+6))
 out=OUT/'canonical-0-45-90-contact.png';canvas.convert('RGB').save(out,quality=92);return out
if __name__=='__main__':
 import hashlib
 # function sha visible in main's scope
 views=[]
 roles=None
 for view,angle,manifest_path in ANGLES:
  manifest=json.loads(manifest_path.read_text())
  if manifest.get('characterId')!='p0_character_001':raise ValueError('identity mismatch')
  entries=[x for x in manifest['parts'] if x['yawDeg']==angle]
  if len(entries)!=13:raise ValueError(f'{view}: expected 13 parts, got {len(entries)}')
  current={x['semanticId'] for x in entries}
  if roles is None:roles=current
  if current!=roles:raise ValueError(f'{view}: semantic slots mismatch')
  dest=OUT/view;dest.mkdir(parents=True,exist_ok=True);rows=[]
  for e in sorted(entries,key=lambda x:x['depthOrder']):
   src=PRIVATE/e['path']
   if not src.is_file():raise FileNotFoundError(src)
   with Image.open(src) as im:
    if im.size!=(1024,1024) or im.mode!='RGBA':raise ValueError(f'bad source {src}: {im.size} {im.mode}')
    alpha=im.getchannel('A');bbox=alpha.getbbox();pix=sum(1 for a in alpha.getdata() if a>16)
   h=sha(src)
   expected=e.get('sha256') or e.get('frameSha256')
   if expected and expected!=h:raise ValueError(f'manifest hash mismatch {src}: {expected} != {h}')
   target=dest/(e['semanticId']+'.png');shutil.copy2(src,target)
   if sha(target)!=h:raise ValueError('copy changed source bytes')
   rows.append({'semanticId':e['semanticId'],'depthOrder':e['depthOrder'],'visibility':e.get('visibility'),
    'anatomicalSide':e.get('anatomicalSide'),'sourcePath':e['path'],'path':str(target.relative_to(PRIVATE)),
    'sha256':h,'sourceManifestRecordedSHA256':expected,'alphaPixelsGt16':pix,'alphaBBox':list(bbox) if bbox else None,
    'sourceRole':e.get('sourceRole'),'sourceYaw':angle})
  views.append({'view':view,'yaw':angle,'sourceManifest':str(manifest_path.relative_to(PRIVATE)),
   'sourceManifestSHA256':sha(manifest_path),'parts':rows})
 contact(views)
 qa={'schema':'KOMA-P15-20-CANONICAL-SOURCE-VIEW-RECOVERY-V1','characterId':'p0_character_001',
  'sourceType':'BYTE_EXACT_RECOVERY_FROM_APPROVED_P1_P2_ARTMESH_MANIFESTS',
  'newPaintingCreated':False,'mirroringOrGeometricTransformation':False,
  'semanticSlots':sorted(roles),'views':views,'viewCount':3,'partCount':39,
  'artisticAcceptance':False,'hiddenUnderpaintAcceptance':False,
  'known':{'yaw000':'P1 front original semantic layers','yaw045':'P2 45-degree original semantic layers',
           'yaw090':'P2 side original semantic layers'},
  'note':'These are recovered source parts, not newly painted intermediate views. Hidden slots with zero alpha are intentional when source manifest says hidden.'}
 (OUT/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'views':3,'parts':39,'frontHairSidePixels':next(x['alphaPixelsGt16'] for x in views[0]['parts'] if x['semanticId']=='hair.side'),
 'frontAhogePixels':next(x['alphaPixelsGt16'] for x in views[0]['parts'] if x['semanticId']=='hair.ahoge'),
 'frontClipPixels':next(x['alphaPixelsGt16'] for x in views[0]['parts'] if x['semanticId']=='hair.clip.cross_gold'),
 'yaw90FarEyePixels':next(x['alphaPixelsGt16'] for x in views[2]['parts'] if x['semanticId']=='eye.far'),
 'yaw90ClipPixels':next(x['alphaPixelsGt16'] for x in views[2]['parts'] if x['semanticId']=='hair.clip.cross_gold')},ensure_ascii=False))
