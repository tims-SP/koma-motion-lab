#!/usr/bin/env python3
"""Create a detached gold-cross clip from preexisting approved art; composite only into a review candidate."""
import hashlib,json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops
R=Path(__file__).resolve().parents[1]
P=R/'private-assets'
D=P/'exports/p15-53-gold-clip-repair'
D.mkdir(parents=True,exist_ok=True)
basepath=P/'exports/p15-52-transparency-geometry/camera-plus20-transparent.png'
clippath=P/'exports/p15-38-original-p0-arc-review/yaw65/gold-clip.png'
base=Image.open(basepath).convert('RGBA')
clip=Image.open(clippath).convert('RGBA')
assert base.size==(1024,1024) and clip.size==(443,443)
# The original 443x443 arc asset uses its own registered coordinate system.
# Map to the 1024 coordinate frame using the exact scale recorded for this source family.
scale=1024/443
clip=clip.resize((1024,1024),Image.Resampling.LANCZOS)
original_bbox=clip.getchannel('A').getbbox()
assert original_bbox and 700<original_bbox[0]<800
# Translate inward so both arms of cross remain legible against hair rather than floating beyond silhouette.
dx=-28
mapped=Image.new('RGBA',(1024,1024),(0,0,0,0))
mapped.paste(clip,(dx,0),clip)
# Build a separate independent 1024px RGBA clip layer.
mapped.save(D/'hair.clip.cross_gold.png')
# Remove the old, collapsed gold mark in a tight ROI; preserve every pixel outside.
# A locally sampled near-left hair color fills only pixels passing a gold-color criterion;
# the underlying original alpha remains unchanged, to prevent hard rectangular holes.
clean=base.copy()
src=base.load();dst=clean.load()
removed=0
for y in range(276,385):
    for x in range(744,788):
        r,g,b,a=src[x,y]
        is_gold=(a>80 and r>98 and g>65 and
                 r> b*1.30 and g> b*1.10 and (r-g)>12)
        if is_gold:
            # Pick a nearby stable hair pixel, never a black exterior pixel.
            replacements=[src[xx,y] for xx in (x-26,x-31,x-35,x-40) if xx>=0 and src[xx,y][3]>230]
            if replacements:
                rr=sorted(p[0] for p in replacements)[len(replacements)//2]
                gg=sorted(p[1] for p in replacements)[len(replacements)//2]
                bb=sorted(p[2] for p in replacements)[len(replacements)//2]
                dst[x,y]=(rr,gg,bb,a)
                removed+=1
# Preserve existing alpha elsewhere. Clip is a separate later compositing layer.
# Remove the residual detached pink tuft from the original collapsed clip.
# This is confined to the old clip's right-side silhouette; the new clip remains a separate overlay.
trimmed=0
for y in range(335,388):
    edge=round(778-(y-335)*0.20)
    for x in range(max(edge,0),800):
        r,g,b,a=dst[x,y]
        if a>0:
            dst[x,y]=(r,g,b,0)
            trimmed+=1
clean.save(D/'underlay-repaired.png')
out=Image.alpha_composite(clean,mapped)
out.save(D/'candidate-gold-cross-restored.png')
# High resolution visual crop, one before and one after, with transparent background.
for fname,im in [('before',base),('after',out),('source-clip',mapped)]:
    region=im.crop((675,235,850,415))
    region.resize((700,720),Image.Resampling.NEAREST).save(D/(fname+'-clip-zoom.png'))
for name,bg in [('light',(238,240,247,255)),('blue',(65,115,176,255)),('pink',(244,199,214,255))]:
    plate=Image.new('RGBA',(1024,1024),bg)
    plate.alpha_composite(out)
    plate.convert('RGB').save(D/('preview-'+name+'.png'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=mapped.getchannel('A')
qa={
 'schema':'KOMA-P15-53-GOLD-CLIP-COMPOSITE-V1',
 'characterId':'p0_character_001',
 'sourceRegisteredClip':{'path':str(clippath.relative_to(R)),'sha256':sha(clippath)},
 'sourceTransparentCandidate':{'path':str(basepath.relative_to(R)),'sha256':sha(basepath)},
 'independentClip':{'file':'hair.clip.cross_gold.png','sha256':sha(D/'hair.clip.cross_gold.png'),'bbox':a.getbbox(),'alphaRange':list(a.getextrema())},
 'underlayRepaired':{'sha256':sha(D/'underlay-repaired.png'),'goldPixelsReplaced':removed,'detachedTuftAlphaPixelsRemoved':trimmed},
 'composite':{'file':'candidate-gold-cross-restored.png','sha256':sha(D/'candidate-gold-cross-restored.png'),'size':[1024,1024]},
 'horizontalRegisteredOffsetPx':dx,
 'sourceScale':scale,
 'method':'Reuse registered 65-degree P0 cross clip, alpha-composite detached layer after targeted gold-color cleanup',
 'verification':{'bothCrossingArmsReused':True,'noWholeCharacterRegeneration':True,
                 'absoluteYaw65Verified':False,'manualIdentityAccepted':False,
                 'artMeshModified':False,'formalKeyframeAccepted':False},
 'uncertainty':'Source arc clip is previously registered but not an independently artist-approved yaw65 view; occlusion/attachment requires visual review.'
}
assert a.getbbox() and removed>0
(R/'evidence/p15-53-gold-clip-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'clipBBox':a.getbbox(),'removedGoldPixels':removed,'trimmedTuftPixels':trimmed,'SHA':qa['composite']['sha256']}))
