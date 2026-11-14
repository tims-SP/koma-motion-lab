#!/usr/bin/env python3
"""Construct explicit high-contrast facial lineart from registered 65-degree anchors."""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
R=Path(__file__).resolve().parents[1];P=R/'private-assets';D=P/'exports/p15-46-anchor-guides';D.mkdir(parents=True,exist_ok=True)
cam=json.loads((R/'evidence/p15-12-camera-proxy-qa.json').read_text())
f=next(x for x in cam['frames'] if x['yaw']==65);a=f['anchors']
im=Image.new('RGB',(1024,1024),'white');d=ImageDraw.Draw(im)
def pt(k):return tuple(round(v) for v in a[k]['xy'])
def line(points,width=5):d.line(points,fill='black',width=width,joint='curve')
def eye(cx,cy,rx,ry,width):
 d.arc((cx-rx,cy-ry,cx+rx,cy+ry),190,350,fill='black',width=width)
 d.arc((cx-rx,cy-ry,cx+rx,cy+ry),10,170,fill='black',width=width)
 d.ellipse((cx-5,cy-ry+5,cx+5,cy+ry-5),outline='black',width=3)
# Eye centers are explicit geometry, far eye deliberately narrower.
nx,ny=pt('eye.near.iris');fx,fy=pt('eye.far.iris')
eye(nx,ny,34,19,6);eye(fx,fy,13,15,5)
# Brows and nose bridge/tip.
line([(nx-31,ny-29),(nx-5,ny-34),(nx+24,ny-27)],4)
line([(fx-13,fy-23),(fx+5,fy-27)],3)
nose=pt('nose');line([(nose[0]-15,nose[1]-44),(nose[0]-7,nose[1]-19),(nose[0],nose[1]-2)],4)
d.arc((nose[0]-7,nose[1]-5,nose[0]+13,nose[1]+7),185,340,fill='black',width=4)
# Mouth, jaw contour and cheek guide.
mx,my=pt('mouth');line([(mx-16,my),(mx,my+2),(mx+16,my)],4)
jx,jy=pt('face.jaw.near');cx,cy=pt('face.chin')
line([(jx,jy),(jx+23,jy+38),(cx-18,cy-4),(cx,cy)],5)
line([(cx,cy),(cx+42,cy-7),(cx+73,cy-36)],4)
# Hair clip center and two crossing strokes, in image-right coordinates.
hx,hy=pt('hair.clip.center')
line([(hx-13,hy-17),(hx+13,hy+17)],7);line([(hx+12,hy-17),(hx-12,hy+17)],7)
base=Image.open(P/'exports/p15-44-control-inputs/lineart-65.png').convert('RGB')
# Combine the full registered edge map with the explicit high-contrast anchor geometry.
im=ImageChops.darker(base,im)
im.save(D/'facial-geometry-guide-65.png')
# Tighten inpaint to the face region, excluding hairclip and hair mass.
mask=Image.new('L',(1024,1024),0);md=ImageDraw.Draw(mask)
md.polygon([(520,425),(565,410),(635,410),(705,425),(746,470),(748,535),(722,605),(676,658),(625,670),(570,642),(530,595),(510,530)],fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(5));mask.save(D/'face-mask-narrow-65.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
q={'schema':'KOMA-P15-46-ANCHOR-GUIDES-V1','yaw':65,'sourceCameraSHA256':sha(R/'evidence/p15-12-camera-proxy-qa.json'),'anchors':{k:a[k] for k in ['eye.near.iris','eye.far.iris','nose','mouth','face.jaw.near','face.chin','hair.clip.center']},'guide':{'path':'facial-geometry-guide-65.png','sha256':sha(D/'facial-geometry-guide-65.png')},'mask':{'path':'face-mask-narrow-65.png','sha256':sha(D/'face-mask-narrow-65.png')},'modelInferenceAttempted':False,'reason':'ZeroGPU quota exceeded after first successful P15-45 generation'}
(R/'evidence/p15-46-anchor-guides-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-46 · 锚点强化控制图</title><style>body{max-width:1100px;margin:20px auto;padding:0 18px;background:#172330;color:#edf3fb;font:16px system-ui}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;padding:12px;background:#293c50}img{width:100%;background:white}figcaption{padding:8px 0}@media(max-width:650px){.grid{grid-template-columns:1fr}}</style><h1>P15-46 · 65° 显式五官几何引导</h1><p>红线/锚点来自相机注册数据，近眼、远眼、鼻、口、下颌与发夹分别绘制。此图是模型条件输入，不是角色原画。</p><div class="grid"><figure><img src="facial-geometry-guide-65.png"><figcaption>高对比五官与发夹几何 Lineart</figcaption></figure><figure><img src="face-mask-narrow-65.png"><figcaption>收窄后的面部 Inpainting Mask</figcaption></figure></div>'''
(D/'index.html').write_text(html,encoding='utf8')
print(json.dumps({'guide':q['guide'],'mask':q['mask']}))
