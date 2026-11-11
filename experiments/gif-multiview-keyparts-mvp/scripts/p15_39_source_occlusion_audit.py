"""P15-39: independent P0 source and semantic occlusion evidence."""
from pathlib import Path
import hashlib, json
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 'e95a4b694777f4dcd2e085b25b10d76058d65cd1f8c6ef46971caa8005cb7e54'
ANGLES = ['yaw45','yaw47p5','yaw50','yaw52p5','yaw55','yaw56p25','yaw57p5','yaw58p75','yaw60','yaw61p25','yaw62p5','yaw63p75','yaw65']
BASE = ROOT / 'private-assets/p15-38-p0-registered-arc'
OUT = ROOT / 'evidence/p15-39-source-occlusion-audit.json'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def alpha(p):
    with Image.open(p) as im:
        if im.mode!='RGBA':raise ValueError(f'non-RGBA: {p}')
        return np.asarray(im.getchannel('A'),dtype=np.uint8)

def measure(a,b):
    both=(a>0)&(b>0)
    return {'overlapPixels':int(both.sum()),'firstOpaquePixels':int((a>0).sum()),'secondOpaquePixels':int((b>0).sum()),'overlapFractionOfFirst':round(float(both.sum()/max(1,(a>0).sum())),6)}

# Restrict identity search to local project asset roots, not arbitrary machine files.
roots=[Path('/root/koma-p0-designs'),ROOT/'private-assets',Path('/root/koma-motion-r1999/work/koma-motion-lab/docs')]
hero=[]
for r in roots:
    if r.exists():
        for p in r.rglob('*hero*'):
            if p.is_file() and p.suffix.lower() in ('.png','.webp','.jpg','.jpeg'):
                hero.append({'path':str(p),'sha256':sha(p)})
frames=[]; thumbs=[]
for angle in ANGLES:
    d=BASE/angle
    layers={role:alpha(d/(role+'.png')) for role in ('eye.far','nose','face.skin','hair.front','hair.clip.cross_gold')}
    shape={v.shape for v in layers.values()}
    if len(shape)!=1:raise ValueError(f'layer dimensions mismatch {angle}')
    comp=d/'composite.png'
    frames.append({'angle':angle,'compositeSHA256':sha(comp),'layersRGBA':True,
        'farEyeNose':measure(layers['eye.far'],layers['nose']),
        'farEyeFace':measure(layers['eye.far'],layers['face.skin']),
        'clipFrontHair':measure(layers['hair.clip.cross_gold'],layers['hair.front']),
        'clipAlphaCentroidXY':[round(float(np.average(np.indices(layers['hair.clip.cross_gold'].shape)[axis],weights=layers['hair.clip.cross_gold'])),3) if layers['hair.clip.cross_gold'].sum() else None for axis in (1,0)]})
    with Image.open(comp) as im:
        thumb=im.convert('RGBA');thumb.thumbnail((320,320));thumbs.append((angle,thumb.copy()))
# Real frames contact sheet for human inspection; no inferred artistic approval.
w=320*5;h=365*3
sheet=Image.new('RGB',(w,h),'#d5d5d5');draw=ImageDraw.Draw(sheet)
for i,(angle,im) in enumerate(thumbs):
    x=(i%5)*320;y=(i//5)*365
    sheet.paste(im,(x,y+25),im);draw.text((x+8,y+6),angle,fill='black')
contact=ROOT/'private-assets/exports/p15-39-45-to65-contact.png';contact.parent.mkdir(parents=True,exist_ok=True);sheet.save(contact)
result={'schema':'KOMA-P15-39-SOURCE-OCCLUSION-AUDIT-V1','characterId':'p0_character_001',
 'expectedApprovedHeroSHA256':EXPECTED,'heroCandidates':hero,'approvedHeroBytesVerified':any(x['sha256']==EXPECTED for x in hero),
 'frameCount':len(frames),'frames':frames,'contactSheet':str(contact.relative_to(ROOT)), 'contactSHA256':sha(contact),
 'artisticApproval':False,'notes':'Pixel intersections are diagnostic only; no hidden-paint or anatomical-depth certification.'}
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'frames':len(frames),'heroVerified':result['approvedHeroBytesVerified'],'heroCandidates':len(hero),'contact':str(contact),'sha256':result['contactSHA256']}))
