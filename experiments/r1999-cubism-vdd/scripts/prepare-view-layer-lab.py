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
 # Make the app discoverable from the existing Cubism HTML review panel.
 pth=demo/"index.html"
 content=pth.read_text()
 marker='<aside id="r1999-panel"'
 if content.count(marker)!=1:raise ValueError("Review panel missing")
 content=content.replace(marker,'<a href="./view-layer-lab.html" style="position:fixed;top:5px;right:10px;z-index:100;color:white;background:#315c79;border-radius:6px;padding:6px 10px;text-decoration:none;font:12px system-ui">视角分层工作台</a>\n  '+marker)
 pth.write_text(content)
 print("VIEW_LAYER_HTML_PREPARED",public)
if __name__=="__main__":main()
