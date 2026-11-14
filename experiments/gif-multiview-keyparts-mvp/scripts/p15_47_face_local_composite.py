#!/usr/bin/env python3
"""Constrain already-generated face edit to registered source; never call this a new model output."""
from pathlib import Path
from PIL import Image, ImageChops
import hashlib, json, zipfile

R = Path(__file__).resolve().parents[1]
P = R / "private-assets"
D = P / "exports/p15-47-face-local-review"
D.mkdir(parents=True, exist_ok=True)
SOURCE = P / "p15-38-p0-registered-arc/yaw65/composite.png"
GENERATED = P / "exports/p15-45-qwen21-controlnet-candidate.png"
MASK = P / "exports/p15-46-anchor-guides/face-mask-narrow-65.png"
GUIDE = P / "exports/p15-46-anchor-guides/facial-geometry-guide-65.png"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

src = Image.open(SOURCE).convert("RGBA")
gen = Image.open(GENERATED).convert("RGBA")
mask = Image.open(MASK).convert("L")
assert src.size == gen.size == mask.size == (1024, 1024)
# Crop is for diagnostics only; original asset pixels are never modified.
merged = Image.composite(gen, src, mask)
merged.putalpha(src.getchannel("A"))
out = D / "face-local-engineering-composite.png"
merged.save(out)
# Diagnostics expose the actual affected region (including soft-mask feather).
diff = ImageChops.difference(src, gen)
diff.save(D / "model-unconstrained-difference.png")
composite_diff = ImageChops.difference(src, merged)
composite_diff.save(D / "face-local-difference.png")
for name, path in [("registered-65.png", SOURCE), ("original-model-output.png", GENERATED),
                   ("narrow-mask-65.png", MASK), ("geometry-guide-65.png", GUIDE)]:
    (D / name).write_bytes(path.read_bytes())

srcpix, genpix, blendpix, mpix = src.load(), gen.load(), merged.load(), mask.load()
original_out_changes = 0
out_changes_after = 0
outside = 0
alpha_changed_original = 0
composite_alpha_changed = 0
new_pixels = 0
for y in range(1024):
    for x in range(1024):
        a, b, c = srcpix[x, y], genpix[x, y], blendpix[x, y]
        if a[3] != b[3]:
            alpha_changed_original += 1
        if a[3] != c[3]:
            composite_alpha_changed += 1
        if mpix[x, y] == 0:
            outside += 1
            if max(abs(a[i] - b[i]) for i in range(4)) > 3:
                original_out_changes += 1
            if a != c:
                out_changes_after += 1
        if a != c:
            new_pixels += 1
assert out_changes_after == 0
assert composite_alpha_changed == 0
assert 0 < new_pixels < 1024 * 1024
result = {
    "schema": "KOMA-P15-47-LOCAL-COMPOSITE-V1",
    "sourceSHA256": sha(SOURCE), "modelOutputSHA256": sha(GENERATED),
    "maskSHA256": sha(MASK), "controlGuideSHA256": sha(GUIDE),
    "compositeSHA256": sha(out),
    "modelOutput": "P15-45 seed 65445; not a new inference",
    "sourceAlphaRange": src.getchannel("A").getextrema(),
    "generatedAlphaRange": gen.getchannel("A").getextrema(),
    "maskZeroPixelCount": outside,
    "modelChangedOutsideMaskPixels": original_out_changes,
    "modelChangedOutsideMaskRatio": round(original_out_changes / outside, 6),
    "compositeChangedOutsideMaskPixels": out_changes_after,
    "modelChangedAlphaPixels": alpha_changed_original,
    "compositeChangedAlphaPixels": composite_alpha_changed,
    "compositeChangedPixels": new_pixels,
    "newInferenceStatus": "BLOCKED_ZERO_GPU_QUOTA_EXCEEDED",
    "pose65Accepted": False, "identityAccepted": False,
    "formalArtMeshModified": False,
    "notes": "Face-local RGB repair engineering witness only; camera landmarks still not visually approved."
}
qpath = R / "evidence/p15-47-face-local-qa.json"
qpath.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

tiles = [
    ("registered-65.png", "既有 65° 注册图"),
    ("original-model-output.png", "P15-45 模型原始输出（面部以外也发生变化）"),
    ("model-unconstrained-difference.png", "模型原始输出相对注册图的像素差异"),
    ("narrow-mask-65.png", "P15-46 收窄面部 Mask"),
    ("geometry-guide-65.png", "P15-46 几何 Lineart"),
    ("face-local-engineering-composite.png", "P15-47 面部限定修补（不是新模型生成）"),
    ("face-local-difference.png", "修补前后像素差异"),
]
style = """body{margin:20px auto;padding:0 18px;max-width:1450px;background:#172330;color:#eff3fb;font:15px/1.5 system-ui}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:16px}
figure{margin:0;padding:10px;background:#26394d}img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#dee3e9 0 25%,#fff 0 50%) 50%/24px 24px}
figcaption{padding:6px 0}p{color:#c9d5e4}.flag{color:#fcd597}"""
html = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-47 · 局部修补验收</title><style>' + style + '</style>'
html += '<h1>P15-47 · 65° 候选输出局部修补验收</h1>'
html += ('<p class="flag">这不是新模型推理，仍未满足精确 65° 和角色身份门禁。</p>'
         '<p>已实测模型原始结果会修改面部之外的像素，并改变透明通道；下方限定合成严格保留原图 Mask 外所有 RGBA 像素。</p><main>')
for filename, label in tiles:
    html += f'<figure><img src="{filename}" alt="{label}"><figcaption>{label}</figcaption></figure>'
html += '</main><p>像素统计与 SHA256 见 evidence/p15-47-face-local-qa.json。</p>'
(D / "index.html").write_text(html, encoding="utf8")
print(json.dumps({k: result[k] for k in ["modelChangedOutsideMaskRatio", "compositeChangedOutsideMaskPixels",
      "modelChangedAlphaPixels", "compositeChangedAlphaPixels", "compositeSHA256"]}))
