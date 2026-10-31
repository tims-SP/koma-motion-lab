#!/usr/bin/env python3
"""Overlay accepted/candidate/proxy points on exact native images; never repaint art."""
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw
from prepare_core026_landmark_review import skeleton,verify

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out/core026/landmark-review'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    config=ROOT/'config/core026-landmark-review.json';review=json.loads(config.read_bytes())
    verify(review,skeleton())
    native=ROOT/'out/core026/reference'
    manifest=json.loads((native/'reference-manifest.json').read_bytes());OUT.mkdir(parents=True,exist_ok=True)
    frames=[]
    colors={'VERIFIED_IMAGE_FIDUCIAL':'#51ef87','BOUNDARY_PROXY_ONLY':'#ffbd5b','NCC_CANDIDATE':'#dd94ff'}
    for i,pose in enumerate(manifest['poses']):
        source=native/'frames'/Path(pose['head_png']).name
        assert sha(source)==pose['head_sha256']
        with Image.open(source) as image:
            overlay=Image.new('RGBA',image.size,'#888888');overlay.alpha_composite(image.convert('RGBA'))
        draw=ImageDraw.Draw(overlay)
        for r in review['records']:
            f=r['frames'][i]
            if f['xy'] is None:continue
            x,y=f['xy'];color=colors.get(f['state'],'white')
            draw.ellipse((x-3,y-3,x+3,y+3),outline=color,width=1)
            draw.text((x+4,y-7),r['id'],fill=color,stroke_width=1,stroke_fill='#202020')
        output=OUT/f'review_{i:02}.png';overlay.convert('RGB').save(output)
        frames.append({'raw_yaw':pose['raw_yaw'],'native_head_sha256':pose['head_sha256'],
                       'overlay':str(output.relative_to(ROOT)),'overlay_sha256':sha(output)})
    contact_image=Image.new('RGB',(1304,3410),'#252525');draw=ImageDraw.Draw(contact_image)
    for i,f in enumerate(frames):
        x,y=(i%2)*652,(i//2)*682
        with Image.open(ROOT/f['overlay']) as image:contact_image.paste(image,(x,y+30))
        draw.text((x+8,y+8),f"raw yaw {f['raw_yaw']} | green=image, amber=contour, purple=candidate",fill='white')
    path=OUT/'reviewed-contact.png';contact_image.save(path)
    report={'schema':'core026-visual-review-media/1','status':'OVERLAYS_ONLY_NOT_NEW_ART',
            'review_config_sha256':sha(config),'frames':frames,'contact_sha256':sha(path),
            'native_sources_unchanged':True,'media_policy':'ignored out/ and owner-only Draft Release; git/artifacts text only'}
    (OUT/'review-media-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CORE026_REVIEW_MEDIA',json.dumps({'status':'PASS','native_images_checked':9,'overlay_images':9}))

if __name__=='__main__':main()
