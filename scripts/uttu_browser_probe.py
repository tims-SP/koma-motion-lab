#!/usr/bin/env python3
"""One-pass browser smoke test of UTTU's public animation previews.

Produces *metadata only*. Does not save game textures, skeletons, motions,
screenshots, page text or browser HAR. One browser and one click per page.
"""
import asyncio
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse

from playwright.async_api import async_playwright

OUT=Path(os.getenv("OUT_DIR","out/uttu-browser"))
OUT.mkdir(parents=True,exist_ok=True)
PAGES=("https://uttu.merui.net/npcs/jailer/","https://uttu.merui.net/live2d-sandbox/")
FMT=re.compile(r'(?i)(\.model3\.json|\.moc3|\.physics3\.json|\.motion3\.json|\.skel|\.atlas(?:\.txt)?|\.riv)(?:[?#]|$)')
DOMAIN_RE=re.compile(r'(?i)(live2d|cubism|spine|\.atlas|\.model3|\.moc3|\.skel)')
EVENT_LIMIT=220
results=[]

async def run():
  async with async_playwright() as p:
    browser=await p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
    for url in PAGES:
      page=await browser.new_page(viewport={"width":1400,"height":850},device_scale_factor=1)
      rec={"url":url,"navigation":None,"request_counts":{},"asset_requests":[],"click":None,"errors":[]}
      events=[]
      def on_response(resp):
        if len(events)>=EVENT_LIMIT:return
        full=resp.url
        path=urlparse(full).path
        m=FMT.search(path)
        if m:
          events.append({"kind":"model_asset","format":m.group(1).lower(),"status":resp.status,"host":urlparse(full).hostname,"content_type":resp.headers.get("content-type","")})
        elif DOMAIN_RE.search(full) and ('.js' not in path or 'cubism' in path.lower() or 'spine' in path.lower()):
          events.append({"kind":"resource_hint","status":resp.status,"host":urlparse(full).hostname,"extension":path.split(".")[-1][:12]})
      page.on("response",on_response)
      try:
        resp=await page.goto(url,wait_until="domcontentloaded",timeout=25000)
        rec["navigation"]=resp.status if resp else None
        await page.wait_for_timeout(5000)
        rec["document_title"]=await page.title()
        if "jailer" in url:
          # This control is visible on the NPC profile in the UTTU archive.
          control=page.get_by_alt_text("L2D Viewer")
          if await control.count():
            try:
              await control.first.click(timeout=6000)
              rec["click"]="l2d-viewer image (success)"
            except Exception as e:rec["click"]="l2d-viewer image (not clickable): "+str(e)[:100]
          else:
            rec["click"]="L2D Viewer alt selector absent"
        else:
          # Open a single listed character without guessing hidden endpoint paths.
          for selector in (".character-card",".l2d-card","[data-character-id]","[data-model-id]"):
            loc=page.locator(selector)
            count=await loc.count()
            if count:
              try:
                await loc.first.click(timeout=4500)
                rec["click"]=selector+" (success)"
              except Exception as e:rec["click"]=selector+" (click failed)"
              break
          if rec["click"] is None:rec["click"]="No recognized model card selector"
        await page.wait_for_timeout(7000)
        rec["canvas_count"]=await page.locator("canvas").count()
        rec["viewer_elements"]={
          "l2d_alt":await page.get_by_alt_text("L2D Viewer").count(),
          "model_card":await page.locator(".character-card,.l2d-card,[data-model-id],[data-character-id]").count(),
          "buttons":await page.get_by_role("button").count()
        }
      except Exception as e:
        rec["errors"].append(type(e).__name__+": "+str(e)[:170])
      rec["asset_requests"]=events[:40]
      rec["request_counts"]={
        "model_format_requests":sum(ev["kind"]=="model_asset" for ev in events),
        "successful_model_requests":sum(ev["kind"]=="model_asset" and 200<=ev["status"]<300 for ev in events),
        "other_runtime_hints":sum(ev["kind"]=="resource_hint" for ev in events)
      }
      results.append(rec)
      await page.close()
    await browser.close()
  result={"probe":"UTTU public browser player smoke","method":"Chromium headless; metadata only","results":results,
          "technical_verdict":"Preview loading differs from editing/converting the underlying rig",
          "rights_verdict":"UTTU fan archive does not grant game-asset reuse rights",
          "no_copyrighted_model_artifacts_saved":True}
  (OUT/"report.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
  lines=["# UTTU browser model preview test","","No raw game assets, textures, screenshot or HAR saved.",""]
  for r in results:
    lines += ["## "+r["url"],f'- Page HTTP: {r["navigation"]}',f'- Click attempt: {r["click"]}',f'- Canvas elements: {r.get("canvas_count","unknown")}',f'- Model format requests: {r["request_counts"]["model_format_requests"]}',f'- Successful model format requests: {r["request_counts"]["successful_model_requests"]}',f'- Runtime hints: {r["request_counts"]["other_runtime_hints"]}',f'- Errors: {r["errors"]}',""]
  lines += ["## Interpretation","","A successful Live2D/Spine preview does not imply Rive can import the same model. UTTU is not an asset re-licensor."]
  (OUT/"summary.md").write_text("\n".join(lines)+"\n")
  print((OUT/"summary.md").read_text())
  print("RESOURCE METADATA ONLY:",json.dumps([r["asset_requests"] for r in results],ensure_ascii=False)[:4500])

if __name__=="__main__":
  asyncio.run(run())
  report=json.loads((OUT/"report.json").read_text())
  verified=any(
      r.get("navigation")==200 and r.get("canvas_count",0)>0
      and r["request_counts"]["successful_model_requests"]>0
      for r in report["results"])
  if not verified:
      print("BLOCKED: No browser successfully loaded and rendered a model. Not production-ready.")
      raise SystemExit(2)
