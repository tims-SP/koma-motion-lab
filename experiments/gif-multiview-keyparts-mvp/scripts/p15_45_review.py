#!/usr/bin/env python3
import json,hashlib,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];P=R/'private-assets';D=P/'exports/p15-45-qwen21-controlnet-review';D.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=P/'p15-38-p0-registered-arc/yaw65/composite.png'
identity=P/'p2-views/whole/yaw045.png'
candidate=P/'exports/p15-45-qwen21-controlnet-candidate.png'
control=P/'exports/p15-45-space-output-2.png'
for name,path in [('registered-65.png',src),('identity-45.png',identity),('candidate.png',candidate),('control-fed.png',control)]:
 (D/name).write_bytes(path.read_bytes())
# Show original registered camera anchors on top of generated image; these are expected positions, not detected outputs.
im=Image.open(candidate).convert('RGBA');ov=Image.new('RGBA',im.size,(0,0,0,0));dr=ImageDraw.Draw(ov)
cam=json.loads((R/'evidence/p15-12-camera-proxy-qa.json').read_text());f=next(x for x in cam['frames'] if x['yaw']==65)
labels=['eye.near.iris','eye.far.iris','nose','mouth','face.chin','hair.clip.center']
for k in labels:
 x,y=f['anchors'][k]['xy'];c=(255,60,60,235) if 'far' in k else (40,220,255,235)
 dr.ellipse((x-11,y-11,x+11,y+11),outline=c,width=4);dr.line((x-17,y,x+17,y),fill=c,width=2);dr.line((x,y-17,x,y+17),fill=c,width=2)
 (D/'candidate-anchor-overlay.png').write_bytes(Image.alpha_composite(im,ov).convert('RGB').tobytes()) if False else None
Image.alpha_composite(im,ov).convert('RGB').save(D/'candidate-anchor-overlay.png')
ims={}
for name in ['registered-65.png','identity-45.png','candidate.png','control-fed.png','candidate-anchor-overlay.png']:
 p=D/name
 with Image.open(p) as x:ims[name]={'sha256':sha(p),'bytes':p.stat().st_size,'size':x.size,'mode':x.mode}
report={
 'schema':'KOMA-P15-45-QWEN21-CONTROLNET-REVIEW-V1','characterId':'p0_character_001','targetYaw':65,
 'backend':'hugging-apps/qwen-image-2-1-controlnet-union-demo','runtime':'ZeroGPU A10G',
 'endpoint':'/gradio_api/call/generate','preprocessor':'None (already a control map; precomputed Lineart fed as control_image)',
 'controlContextScale':1.0,'resolution':1024,'steps':24,'seed':65445,'guidanceScale':1.0,
 'inpaintSourceSHA256':sha(src),'lineartSHA256':'029f173e4eaad50ac3f44a86f6929ffab52361707cb21da53cf3cd7d8f3d4a6c',
 'maskSHA256':'37d12bb930a6baf64f1b2b8a96e24779f12796b71490ed65476f9955da38b8b8',
 'outputSHA256':sha(candidate),'outputSize':Image.open(candidate).size,
 'visualObservations':{
  'cameraDirection':'appears right-facing; no obvious mirror reversal',
  'eyes':'both eyes visible after face inpainting; far eye is smaller than near eye',
  'hairClip':'gold crossed clip remains on image-right',
  'hair':'dusty rose/lavender bob and single ahoge retained',
  'identity':'visually consistent with P0 traits, but no formal Hero reference match or identity embedding test',
  'yaw':'exact 65-degree pose not independently established; face appears less profile-like than registered source',
  'artQuality':'cleaner face than source registration; small linework/edge artifacts remain outside face in original composite'
 },
 'secondSeedAttempt':{'seed':65446,'status':'BLOCKED_ZERO_GPU_QUOTA_EXCEEDED'},
 'candidateAcceptedAsFormalKeyframe':False,'identityAccepted':False,'exactYawAccepted':False,'artMeshModified':False,
 'images':ims,
 'status':'ONE_REAL_CONTROLLED_INPAINT_GENERATION_COMPLETE_VISUAL_REVIEW_REQUIRED'
}
(R/'evidence/p15-45-qwen21-controlnet-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-45 · Qwen 2.1 65° 控制生成审查</title><style>body{margin:20px auto;padding:0 18px;max-width:1500px;background:#172330;color:#edf3fb;font:15px/1.5 system-ui}h1{font-size:24px}p{color:#c4d1df}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}figure{margin:0;padding:12px;background:#293c50}img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d5dce5 0 25%,#fff 0 50%) 50%/20px 20px}figcaption{margin-top:8px;font-weight:600}small{color:#bac9d8} .warn{color:#ffcf82}</style><h1>P15-45 · Qwen-Image-2.1 Lineart + Inpainting</h1><p>真实推理输出；输入包括注册65°图、面部Mask和Lineart控制图。模型返回候选原画，不代表已通过正式关键帧验收。</p><p class="warn">视觉初审：右向、双眼和右侧发夹均得到保留；精确65°和身份一致性仍未通过正式门禁。</p><div class="grid">'''
for n,label in [('registered-65.png','输入：65° 注册原画'),('identity-45.png','身份参考：批准的45°原画'),('control-fed.png','模型实际接收的 Lineart 控制图'),('candidate.png','真实生成候选 · seed 65445'),('candidate-anchor-overlay.png','原65°相机锚点叠加（红/蓝十字为目标坐标）')]:
 html+=f'<figure><img src="{n}" alt="{label}"><figcaption>{label}</figcaption></figure>'
html+='</div><p>输出哈希、条件哈希和模型参数见同目录 QA JSON。</p>'
(D/'index.html').write_text(html,encoding='utf8')
z=P/'exports/p15-45-qwen21-controlnet-review.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:
 for p in sorted(D.iterdir()):
  if p.is_file():f.write(p,p.name)
print(json.dumps({'images':len(ims),'output_sha256':sha(candidate),'archive_sha256':sha(z),'archive_bytes':z.stat().st_size}))
