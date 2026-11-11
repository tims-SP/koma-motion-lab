#!/usr/bin/env python3
"""Build reproducible geometry control images, not a purported AI keyframe."""
import json, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-44-control-inputs'
D.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cam_path=R/'evidence/p15-12-camera-proxy-qa.json'
cam=json.loads(cam_path.read_text())
frame=next(f for f in cam['frames'] if f['yaw']==65)
src=R/'private-assets/p15-38-p0-registered-arc/yaw65/composite.png'
ident=R/'private-assets/p2-views/whole/yaw045.png'
assert src.exists() and ident.exists()
art=Image.open(src).convert('RGBA')
assert art.size==(1024,1024)
# Render edges of CURRENT registered 65-degree geometry, never hallucinate a novel pose.
background=Image.new('RGBA',art.size,'white')
background.alpha_composite(art)
gray=ImageOps.grayscale(background.convert('RGB'))
edges=gray.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(.6))
edges=edges.point(lambda v:255 if v>34 else 0)
# Mask removes background edge artifacts and preserves a narrow silhouette band.
alpha=art.getchannel('A')
silhouette=alpha.filter(ImageFilter.FIND_EDGES).point(lambda v:255 if v>10 else 0)
edges=ImageChops.lighter(edges,silhouette)
lineart=ImageOps.invert(edges).convert('RGB')
lineart.save(D/'lineart-65.png')
# High precision local anchors, separate from OpenPose body skeleton.
anchor_image=Image.new('RGB',art.size,(0,0,0))
dr=ImageDraw.Draw(anchor_image)
colors={'eye.near.iris':'#20e0ff','eye.far.iris':'#ff4ed6','nose':'#ffff24','mouth':'#ff9d24','face.chin':'#51ff44','hair.clip.center':'#ffd000'}
for key,color in colors.items():
    x,y=frame['anchors'][key]['xy']
    assert 0<=x<1024 and 0<=y<1024
    dr.ellipse((x-7,y-7,x+7,y+7),fill=color)
anchor_image.save(D/'facial-anchors-65.png')
# Only face landmarks region gets a mask; avoid accidentally controlling entire scene.
mask=Image.new('L',art.size,0)
md=ImageDraw.Draw(mask)
# Face-region ellipse covers both eyes, nose, mouth and jaw while excluding the hair clip.
md.ellipse((495,405,758,695),fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(8))
mask.save(D/'face-mask-65.png')
# Visual review includes a source sample and the only current identity reference; no inference here.
(D/'registered-65.png').write_bytes(src.read_bytes())
(D/'identity-45.png').write_bytes(ident.read_bytes())
items=['registered-65.png','identity-45.png','lineart-65.png','facial-anchors-65.png','face-mask-65.png']
report={
 'schema':'KOMA-P15-44-CONTROL-CONDITIONS-V1','characterId':'p0_character_001','yawDegrees':65,
 'sourceCameraEvidenceSHA256':sha(cam_path),'sourceRegisteredSHA256':sha(src),'sourceIdentitySHA256':sha(ident),
 'artifacts':{n:{'sha256':sha(D/n),'bytes':(D/n).stat().st_size} for n in items},
 'anchors':{k:frame['anchors'][k] for k in colors},
 'backendAssessment':{
 'hugging-apps/krea2-pose-controlnet':'interface verified; only skeleton pose input, not enough for facial and clip fidelity',
 'DjStompzone/FLUX-1-Dev-LineArt-ControlNet':'parameter inspection HTTP 503',
 'generatedWithConditioning':False,'modelImageAvailable':False},
 'acceptedAsAuthoredKeyframe':False,'existingVDDArtModified':False,
 'outstanding':'Find running model endpoint accepting image lineart/mask plus identity reference without exposing private assets; generate and visually inspect before art admission'
}
(R/'evidence/p15-44-control-conditions-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-44 · 显式控制图检查</title><style>body{margin:20px auto;padding:0 20px;max-width:1400px;background:#17222f;color:#e9f1ff;font:16px/1.5 system-ui}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:16px}figure{margin:0;background:#2a3a4a;padding:12px}img{width:100%;aspect-ratio:1;object-fit:contain;background:#ddd}figcaption{padding:8px 0}p{color:#c5d3de}</style><h1>P15-44 · 65° 控制条件验收</h1><p>仅是可复现的输入控制图，未生成或批准新原画。保留源注册画面和身份图以便对照。</p><main>'''
for n,label in zip(items,['注册65°（非已批准原画）','P0 45°身份参考','注册65°线稿控制','近/远眼、鼻、嘴、下巴、发夹锚点','面部局部Mask']):
 html+=f'<figure><img src="{n}" alt="{label}"><figcaption>{label}</figcaption></figure>'
html+='</main>'
(D/'index.html').write_text(html,encoding='utf8')
print(json.dumps({'artifacts':len(items),'anchors':len(colors),'sha256':sha(D/'lineart-65.png'),'modelGenerated':False}))
