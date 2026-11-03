#!/usr/bin/env python3
"""Bundle the HTML semantic-view editor into a private official Cubism demo."""
from pathlib import Path
import argparse,shutil

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--samples",type=Path,required=True)
 p.add_argument("--html",type=Path,required=True)
 p.add_argument("--javascript",type=Path,required=True)
 p.add_argument("--native-front",type=Path,help="Private PNG Part layer directory with front-layer-manifest.json")
 p.add_argument("--geometry-reference",type=Path,help="Private 3D-rendered geometry reference (8 orthographic PNG views)")
 args=p.parse_args()
 demo=args.samples.resolve()/"Samples/TypeScript/Demo"
 public=demo/"public";public.mkdir(parents=True,exist_ok=True)
 for source,name in [(args.html,"view-layer-lab.html"),(args.javascript,"view-layer-lab.js")]:
  if not source.is_file():raise FileNotFoundError(source)
  shutil.copy2(source,public/name)
 if args.native_front:
  directory=args.native_front.resolve()
  if not (directory/'front-layer-manifest.json').is_file():raise FileNotFoundError(directory/'front-layer-manifest.json')
  shutil.copytree(directory,public/'private-view-assets',dirs_exist_ok=True)
 if args.geometry_reference:
  import json
  source=args.geometry_reference.resolve()
  qa_path=source/'turnaround-qa.json'
  if not qa_path.is_file():raise FileNotFoundError(qa_path)
  qa=json.loads(qa_path.read_text())
  if qa.get('status')!='PASS_3D_REFERENCE_RENDER' or qa.get('independent2DArtworkCount')!=0:
   raise ValueError('Structural reference source QA failed')
  destination=public/'private-geometry-view'
  destination.mkdir(parents=True,exist_ok=True)
  for entry in qa['renderedImages']:
   name=entry['filename']
   if not name.endswith('.png') or '/' in name or '\\' in name:raise ValueError('Unsafe reference file name')
   shutil.copy2(source/name,destination/name)
  shutil.copy2(qa_path,destination/'turnaround-qa.json')
 # Make the app discoverable from the existing Cubism HTML review panel.
 pth=demo/"index.html"
 content=pth.read_text()
 marker='<aside id="r1999-panel"'
 if content.count(marker)!=1:raise ValueError("Review panel missing")
 if 'href="./view-layer-lab.html"' not in content:
  content=content.replace(marker,'<a href="./view-layer-lab.html" style="position:fixed;top:5px;right:10px;z-index:100;color:white;background:#315c79;border-radius:6px;padding:6px 10px;text-decoration:none;font:12px system-ui">视角分层工作台</a>\n  '+marker)
 pth.write_text(content)
 print("VIEW_LAYER_HTML_PREPARED",public)
if __name__=="__main__":main()
