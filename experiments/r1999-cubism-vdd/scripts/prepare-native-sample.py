#!/usr/bin/env python3
"""Prepare the official Cubism Web 5-r.4 sample for a private model preview."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import subprocess


def replace_one(file: Path, old: str, new: str) -> None:
    contents = file.read_text()
    if contents.count(old) != 1:
        raise RuntimeError(f"{file}: expected exactly one occurrence of {old!r}")
    file.write_text(contents.replace(old, new))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--framework", type=Path, required=True)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--controls", type=Path, required=True)
    args = parser.parse_args()
    samples, framework = args.samples.resolve(), args.framework.resolve()
    for path in [samples, framework, args.core, args.assets, args.controls]:
        if not path.exists():
            raise FileNotFoundError(path)
    target_framework = samples / "Framework"
    shutil.copytree(framework, target_framework, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".git", "node_modules"))
    target_core = samples / "Core/live2dcubismcore.js"
    shutil.copy2(args.core, target_core)
    model_name = "302301_shisihangshi"
    target_model = samples / "Samples/Resources" / model_name
    shutil.copytree(args.assets, target_model, dirs_exist_ok=True)
    demo = samples / "Samples/TypeScript/Demo"
    define = demo / "src/lappdefine.ts"
    source = define.read_text()
    source, count = re.subn(r"export const ModelDir: string\[\] = \[[\s\S]*?\];",
                            f"export const ModelDir: string[] = ['{model_name}'];", source)
    if count != 1:
        raise RuntimeError("Cannot locate sample ModelDir declaration")
    source = source.replace("export const MotionGroupIdle = 'Idle';",
                            "export const MotionGroupIdle = 'b_idle';")
    define.write_text(source)
    manager = demo / "src/lapplive2dmanager.ts"
    replace_one(manager, "    model.update();",
                "    (window as any).__R1999_MODEL = model;\n"
                "    if (!(window as any).__R1999_PAUSED) model.update();")
    model = demo / "src/lappmodel.ts"
    fit = """
      // Register full-frame coordinates from the actual source drawable vertices.
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (let i = 0; i < this._model.getDrawableCount(); ++i) {
        const vertices = this._model.getDrawableVertexPositions(i);
        for (let j = 0; j < vertices.length; j += 2) {
          const x = vertices[j], y = vertices[j + 1];
          if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
          minX = Math.min(minX,x); maxX = Math.max(maxX,x);
          minY = Math.min(minY,y); maxY = Math.max(maxY,y);
        }
      }
      if (maxY > minY && maxX > minX) {
        const scale = Math.min(1.75 / (maxY - minY), 2.1 / (maxX - minX));
        this._modelMatrix.setHeight(scale * this._model.getCanvasHeight());
        this._modelMatrix.translateX(-(minX + maxX) * scale / 2);
        this._modelMatrix.translateY(-(minY + maxY) * scale / 2);
      }
"""
    replace_one(model, "      this._modelMatrix.setupFromLayout(layout);",
                "      this._modelMatrix.setupFromLayout(layout);" + fit)
    gl = demo / "src/lappglmanager.ts"
    replace_one(gl, "canvas.getContext('webgl2')",
                "canvas.getContext('webgl2', { preserveDrawingBuffer: true })")
    public = demo / "public"
    public.mkdir(exist_ok=True)
    shutil.copy2(args.controls, public / "review-controls.js")
    page = demo / "index.html"
    html = page.read_text()
    injection = """
  <style>
    body > canvas {position:fixed;inset:0;width:100vw;height:100vh;display:block;}
    #r1999-panel {position:fixed;z-index:20;top:12px;left:12px;width:262px;
      box-sizing:border-box;padding:15px;border-radius:15px;background:rgba(16,23,35,.90);
      backdrop-filter:blur(12px);color:#f8fafc;font:13px/1.5 system-ui,sans-serif;}
    #r1999-panel h1 {font-size:16px;line-height:1.2;margin:0 0 8px;}
    #r1999-panel .buttons {display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:10px 0;}
    #r1999-panel button, #r1999-panel select {font:inherit;min-height:32px;background:#2b3b51;
      color:inherit;border:1px solid #607082;border-radius:6px;padding:4px 8px;}
    #r1999-panel button {cursor:pointer;}
    #r1999-panel button:disabled {opacity:.45;cursor:default;}
    #r1999-panel select {width:100%;}
    #r1999-panel p {margin:7px 0;font-size:12px;}
    #r1999-runtime {color:#85dfbd;}
    @media(max-width:650px){#r1999-panel {width:calc(100vw - 12px);padding:8px;top:auto;bottom:6px;left:6px;font-size:11px;max-height:185px;overflow:auto;}\n    #r1999-panel h1 {display:none;} #r1999-panel p {margin:2px 0;}\n    #r1999-panel #r1999-motions {grid-template-columns:repeat(4,1fr);margin:5px 0;}\n    #r1999-panel button,#r1999-panel select {min-height:28px;padding:2px 4px;}}
  </style>
  <script src="/review-controls.js" defer></script>
"""
    markup = """
  <aside id="r1999-panel" aria-label="Cubism 原生人物验收">
    <h1>R1999 · Cubism</h1>
    <p id="r1999-runtime">模型正在加载</p>
    <div id="r1999-motions" class="buttons">
      <button type="button" data-motion="b_idle">待机 Idle</button>
      <button type="button" data-motion="b_diantou">点头</button>
      <button type="button" data-motion="b_yaotou">摇头</button>
      <button type="button" data-motion="b_yangtou">抬头</button>
    </div>
    <label for="r1999-expressions">表情</label>
    <select id="r1999-expressions">
      <option value="e_idle">默认</option>
      <option value="e_kaixin">开心</option>
      <option value="e_chijing">惊讶</option>
      <option value="e_haixiu">害羞</option>
      <option value="e_nanguo">难过</option>
      <option value="e_shengqi">生气</option>
    </select>
    <div class="buttons">
      <button type="button" id="r1999-pause">暂停</button>
      <button type="button" id="r1999-png">导出 PNG</button>
    </div>
    <p id="r1999-status" aria-live="polite">原生模式 · 模型动作与表情</p>
  </aside>
"""
    replace_one(page, "</head>", injection + "</head>")
    replace_one(page, "<body>", "<body>" + markup)
    print("PREPARED_NATIVE", {"samples": str(samples),
                             "frameworkHead": subprocess.check_output(
                                 ["git", "-C", str(framework), "rev-parse", "HEAD"],
                                 text=True).strip(), "model": model_name})


if __name__ == "__main__":
    main()
