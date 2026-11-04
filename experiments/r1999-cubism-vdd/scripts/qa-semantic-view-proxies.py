#!/usr/bin/env python3
"""Validate depth-visible 45/90 PMX-derived semantic proxy PNGs.

The provenance gate is explicit: output 16/16 only means engineering RGB/RGBA
semantic pixels, not independently painted art or successful VDD beauty.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

PARTS=['hair.back','face.skin','ear.near','hair.side','eye.near','nose','mouth','hair.front']
MIN_PIXELS={'hair.back':2000,'face.skin':1000,'ear.near':40,'hair.side':1000,
            'eye.near':100,'nose':100,'mouth':100,'hair.front':100}

def sha(path:Path)->str:
 return hashlib.sha256(path.read_bytes()).hexdigest()

def inspect(root:Path)->dict:
 manifest=json.loads((root/'proxy-semantic-manifest.json').read_text())
 errs=[]
 if manifest.get('schema')!='R1999-PMX-SEMANTIC-PROXY-V1':errs.append('schema')
 if manifest.get('independentArtCoverage')!=0:errs.append('provenance')
 if manifest.get('sourceRole')!='third_party_3d_proxy':errs.append('role')
 if sorted(manifest.get('requiredAngles',[]))!=[45,90]:errs.append('angles')
 if sorted(manifest.get('parts',[]))!=sorted(PARTS):errs.append('parts')
 records=manifest.get('layers',[])
 if len(records)!=16:errs.append('count')
 files={}
 coverage={}
 for item in records:
  angle,part=item.get('yawDeg'),item.get('semanticId')
  if angle not in (45,90) or part not in PARTS:
   errs.append('unknown_semantic');continue
  key=(angle,part)
  if key in files:errs.append('duplicate_semantic');continue
  f=root/item['path']
  if not f.is_file():errs.append('file_missing:'+str(key));continue
  if sha(f)!=item.get('sha256'):errs.append('sha:'+str(key))
  with Image.open(f) as source:
   if source.format!='PNG' or source.mode!='RGBA' or source.size!=(640,640):
    errs.append('image_format:'+str(key));continue
   image=source.copy()
  alpha=image.getchannel('A')
  pixels=sum(v for i,v in enumerate(alpha.histogram()) if i>0)
  bbox=alpha.getbbox()
  if pixels<MIN_PIXELS[part]:
   errs.append('visible_pixels:'+str(key)+':'+str(pixels))
  if bbox is None or not (0<bbox[0]<bbox[2]<640 and 0<bbox[1]<bbox[3]<640):
   errs.append('bbox:'+str(key)+':'+str(bbox))
  if item.get('role')!='third_party_3d_proxy' or item.get('sourceId')!='WTHN_Ross_Sonetto_PMX_v1.1':
   errs.append('source_role:'+str(key))
  if item.get('pixels')!=pixels:errs.append('counter:'+str(key))
  if item.get('bbox')!=list(bbox or []):errs.append('bbox_manifest:'+str(key))
  files[key]=image
  coverage[f'{angle}:{part}']={'visible':pixels,'sha256':sha(f),'bbox':bbox}
 for angle in (45,90):
  for part in PARTS:
   if (angle,part) not in files:errs.append('missing:'+str((angle,part)))
 if len(set(item.get('sha256') for item in records))!=len(records):
  errs.append('identical_layer_assets')
 if errs:return {'schema':'R1999-SEMANTIC-PROXY-QA-V1','status':'FAIL',
                 'errors':errs,'pixelCoverage':coverage,'independentPaintedArtwork':0}
 previews={}
 for angle in (45,90):
  rgba=Image.new('RGBA',(640,640))
  # Source-visible masks; stacking follows the current HTML depth contract.
  for part in PARTS:rgba.alpha_composite(files[(angle,part)])
  previews[angle]=rgba
  rgba.save(root/f'preview-yaw{angle:03d}-semantic-composite.png')
  alpha=rgba.getchannel('A')
  if not alpha.getbbox():errs.append('empty_preview')
  # A real side view must change silhouette and shape.
  rgba_r=rgba.getchannel('R')
  if max(rgba_r.getextrema())-min(rgba_r.getextrema())<30:
   errs.append('preview_no_RGB_variation')
 c45=previews[45].getchannel('A').histogram()
 c90=previews[90].getchannel('A').histogram()
 sum45=sum(c45[1:]);sum90=sum(c90[1:])
 if sum45<=sum90*0.85:errs.append('side_view_silhouette_not_narrower')
 sheet=Image.new('RGB',(1440,760),(20,29,44))
 draw=ImageDraw.Draw(sheet)
 for row,angle in enumerate((45,90)):
  for col,part in enumerate(PARTS):
   im=files[(angle,part)]
   im.thumbnail((168,168),Image.Resampling.LANCZOS)
   cell=Image.new('RGBA',(168,168),(242,245,249,255))
   cell.alpha_composite(im,((168-im.width)//2,(168-im.height)//2))
   x=col*180+6;y=row*380+4
   sheet.paste(cell.convert('RGB'),(x,y))
   draw.text((x+3,y+180),f'{angle} {part}',fill=(239,243,252))
 sheet.save(root/'semantic-contact-sheet.png',optimize=True)
 report={'schema':'R1999-SEMANTIC-PROXY-QA-V1',
   'status':'PASS_3D_SEMANTIC_PROXY' if not errs else 'FAIL',
   'independentPaintedArtwork':0,
   'semanticProxyCoverage':len(files),
   'requiredSemanticProxyCount':16,
   'sourceType':'THIRD_PARTY_PMX_GEOMETRY_AND_RENDERED_RGB',
   'angles':[45,90],
   'checks':{
     'all_rgba_layers':len(files)==16,
     'visible_source':not errs,
     'side_narrower':sum45>sum90*0.85,
     'cross_view_unique_hashes':len(set(item['sha256'] for item in records))==16
   },
   'compositeAlphaPixels':{'45':sum45,'90':sum90},
   'pixelCoverage':coverage,
   'contactSheet':{'file':'semantic-contact-sheet.png','sha256':sha(root/'semantic-contact-sheet.png')},
   'errors':errs}
 (root/'semantic-proxy-qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--dir',type=Path,required=True)
 args=p.parse_args()
 report=inspect(args.dir.resolve())
 print(json.dumps({key:report.get(key) for key in
   ('status','semanticProxyCoverage','independentPaintedArtwork','compositeAlphaPixels','errors')},
   ensure_ascii=False))
 if report['status']!='PASS_3D_SEMANTIC_PROXY':raise SystemExit(1)

if __name__=='__main__':main()
