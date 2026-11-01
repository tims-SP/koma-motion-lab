#!/usr/bin/env python3
"""Fetch reproducible public P0 asset fixtures into a portable audit archive."""
from __future__ import annotations
import hashlib, json, os, pathlib, urllib.parse, urllib.request
ROOT=pathlib.Path("transfer")
ROOT.mkdir(exist_ok=True)
fixtures={
 "lmy414/ai-chan-sheets": [
 ("设定图/07_豆包Seed娘/便于查看/横版完整设定图_01_三视图_查看用.jpg","ai-chan/turnaround-preview.jpg"),
 ("设定图/07_豆包Seed娘/原图切片/横版完整设定图_01_三视图_原图.png","ai-chan/turnaround-native.png"),
 ("设定图/07_豆包Seed娘/制作清单.json","ai-chan/production-list.json"),
 ("设定图/07_豆包Seed娘/拼接布局与素材索引.json","ai-chan/assembly-index.json"),
 ("设定图/07_豆包Seed娘/提示词/A02_三视图_左侧.json","ai-chan/profile-prompt.json"),
 ("设定图/07_豆包Seed娘/提示词/A03_三视图_背面.json","ai-chan/back-prompt.json")],
 "Fenglin-Maple/AutoLive2d":[
 ("public/samples/u6/input.psd","autolive2d/u6-layers.psd"),
 ("public/samples/u6/input_depth.psd","autolive2d/u6-depth.psd"),
 ("public/samples/u6/source.png","autolive2d/u6-source.png"),
 ("public/samples/u6/attachments/expr_open_mouth.png","autolive2d/u6-open-mouth.png"),
 ("public/samples/u6/attachments/expr_shocked_eye_l.png","autolive2d/u6-eye-left.png"),
 ("public/samples/u6/attachments/expr_shocked_eye_r.png","autolive2d/u6-eye-right.png"),
 ("public/samples/u6/attachments.json","autolive2d/u6-attachments.json")],
 "Ariakage/live2d-agent-kit":[
 ("examples/pink-sakura/source/reference.png","pink-sakura/reference.png"),
 ("examples/pink-sakura/source/eyeless-face-v1.png","pink-sakura/eyeless-face.png"),
 ("examples/pink-sakura/source/face-parts-v1.png","pink-sakura/face-parts.png"),
 ("examples/pink-sakura/source/rear-hair-underpainting-v1.png","pink-sakura/rear-hair.png")]
}
def read(url):
 req=urllib.request.Request(url,headers={"User-Agent":"P0-asset-audit/1.0","Accept":"application/vnd.github+json"})
 with urllib.request.urlopen(req,timeout=90) as resp:return resp.read()
sources=[]
for repo,files in fixtures.items():
 owner,name=repo.split("/")
 info=json.loads(read(f"https://api.github.com/repos/{repo}"))
 branch=info["default_branch"]
 commit=json.loads(read(f"https://api.github.com/repos/{repo}/commits/{branch}"))["sha"]
 for src,dst in files:
  url=f"https://raw.githubusercontent.com/{repo}/{commit}/"+urllib.parse.quote(src)
  data=read(url)
  if len(data)<100:raise RuntimeError(f"Suspicious empty fixture: {src}")
  path=ROOT/"fixtures"/dst
  path.parent.mkdir(parents=True,exist_ok=True)
  path.write_bytes(data)
  sources.append({"repo":repo,"commit":commit,"path":src,"destination":"fixtures/"+dst,
    "bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"url":url})
  print(f"OK {dst}: {len(data):,} bytes",flush=True)
(ROOT/"p0-source-manifest.json").write_text(json.dumps(sources,ensure_ascii=False,indent=2)+"\n")
