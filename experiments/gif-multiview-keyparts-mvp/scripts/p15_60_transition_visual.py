#!/usr/bin/env python3
"""Visual continuity gate for nominal 45->65: diagnostics only, not VDD implementation."""
import json,hashlib
from pathlib import Path
from PIL import Image, ImageChops
R=Path(__file__).resolve().parents[1];P=R/'private-assets'
D=P/'exports/p15-60-transition-visual';D.mkdir(parents=True,exist_ok=True)
SOURCE=P/'p2-views/whole/yaw045.png'
TARGET=P/'exports/p15-56-edge-matting/candidate-erode-2.png'
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
source=Image.open(SOURCE).convert('RGBA')
target=Image.open(TARGET).convert('RGBA')
assert source.size==target.size==(1024,1024)
assert sha(SOURCE)=='78a08d5f010a8f449efda915a710a2de8958c3b1a32375df491d806fca251e40'
assert sha(TARGET)=='e2682450d960de63b5fcdac3ec22e69bdb57bf93ba2879e2105256cd8105c2ed'
def premul_blend(a,b,t):
    # Composite each image onto transparent via alpha-scaling to produce premultiplied blend.
    # Pillow alpha_composite is sequential, so use direct pure-Python channel operations.
    x=a.tobytes();y=b.tobytes();data=bytearray(len(x))
    for i in range(0,len(x),4):
        aa=x[i+3]/255;bb=y[i+3]/255
        al=(1-t)*aa+t*bb
        if al<1e-6:data[i:i+4]=b'\x00\x00\x00\x00';continue
        for c in range(3):
            data[i+c]=max(0,min(255,round(((1-t)*x[i+c]*aa+t*y[i+c]*bb)/al)))
        data[i+3]=max(0,min(255,round(al*255)))
    return Image.frombytes('RGBA',a.size,bytes(data))
frames=[]
for i in range(9):
    t=i/8
    im=source.copy() if i==0 else target.copy() if i==8 else premul_blend(source,target,t)
    name=f'frame-{i:02d}.png'
    im.save(D/name)
    # Eye/nose/clip composite inspection: preserves frame provenance.
    crop=im.crop((425,270,820,700)).resize((395,430),Image.Resampling.LANCZOS)
    crop.save(D/f'face-{i:02d}.png')
    aa=im.getchannel('A');frames.append({
        'index':i,'nominalYawParameter':round(45+20*t,2),'blendFactor':t,
        'frameSHA256':sha(D/name),'frame':name,'faceCrop':f'face-{i:02d}.png',
        'alphaBBox':list(aa.getbbox())})
# Pixel transition measurements: no geometry synthesis or independent art added.
middle=Image.open(D/'frame-04.png').convert('RGBA')
# Both endpoint's projected foreground are visibly separated in many facial details.
ma=middle.getchannel('A')
rgb_a=source.convert('RGB');rgb_b=target.convert('RGB')
source_support=source.getchannel('A').point(lambda v:255 if v>=192 else 0)
target_support=target.getchannel('A').point(lambda v:255 if v>=192 else 0)
union=ImageChops.lighter(source_support,target_support)
intersection=ImageChops.darker(source_support,target_support)
hist_u=union.histogram();hist_i=intersection.histogram()
union_px=hist_u[255];intersection_px=hist_i[255]
change=ImageChops.difference(rgb_a,rgb_b).convert('L')
eye_roi=(445,365,790,540)
face_roi=(390,300,820,710)
stats={
 'sourceSupportPixels':source_support.histogram()[255],
 'targetSupportPixels':target_support.histogram()[255],
 'supportIoU':round(intersection_px/union_px,6),
 'eyeRegionMeanRGBDelta':round(sum(ImageChops.difference(rgb_a.crop(eye_roi),rgb_b.crop(eye_roi)).convert('L').getdata()) / ((eye_roi[2]-eye_roi[0])*(eye_roi[3]-eye_roi[1])),2),
 'midpointAlphaBBox':list(ma.getbbox())
}
# The endpoints can pass hashing while the intermediate still contains transparent double exposure.
q={'schema':'KOMA-P15-60-VISUAL-TRANSITION-DIAGNOSTIC-V1','characterId':'p0_character_001',
   'source45SHA256':sha(SOURCE),'targetRelativePlus20SHA256':sha(TARGET),
   'parameterDomain':{'start':45,'end':65,'meaning':'NOMINAL_VDD_PARAMETER_NOT_PHYSICAL_CAMERA_YAW'},
   'method':'PREMULTIPLIED_RGBA_WHOLE_FRAME_CROSSFADE_DIAGNOSTIC_ONLY',
   'frames':frames,'metrics':stats,
   'independent65Painting':False,'trueViewDependentDeformation':False,
   'visualGate':'PENDING_DIRECT_INSPECTION',
   'formalKeyframeAccepted':False,'productionArtMeshModified':False,
   'next':'Inspect midpoint for double eyes, nose contours and hairclip ghosting. If present, reject whole-frame crossfade and require independent semantic layers plus view-dependent mesh/occlusion.'}
(R/'evidence/p15-60-transition-visual-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'frames':len(frames),'supportIoU':stats['supportIoU'],'eyeDelta':stats['eyeRegionMeanRGBDelta']}))
