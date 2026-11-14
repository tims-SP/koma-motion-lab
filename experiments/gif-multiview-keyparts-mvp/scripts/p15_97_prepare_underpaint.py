#!/usr/bin/env python3
"""Build original-identity masked underpainting reference crops for multiple views."""
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageFilter
import json,hashlib
R=Path(__file__).resolve().parents[1]
P=R/'private-assets'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
views={
 '52p5':{'image':'exports/p15-93-yaw0525-review/yaw052p5-registered.png',
         'mask':'exports/p15-97-sam3-yaw52p5/mask-2-1024.png',
         'face':[(625,325),(705,323),(755,355),(784,410),(786,490),(720,533),(622,508)]},
 '75':{'image':'exports/p15-92-angle-keyart/yaw075-registered.png',
       'mask':'exports/p15-97-sam3-yaw75/mask-1-1024.png',
       'face':[(665,328),(720,323),(767,355),(788,416),(782,505),(714,522),(656,475)]}
}
for view,settings in views.items():
 srcpath=P/settings['image'];sampath=P/settings['mask']
 src=Image.open(srcpath).convert('RGBA')
 sam=Image.open(sampath).convert('L')
 face=Image.new('L',src.size,0);ImageDraw.Draw(face).polygon(settings['face'],fill=255)
 mask=ImageChops.darker(sam,face)
 mask=mask.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(1.4))
 d=P/('p15-97-underpaint-'+view);d.mkdir(parents=True,exist_ok=True)
 mask.save(d/'mask-source-1024.png')
 crop=(430,260,850,680)
 white=Image.new('RGBA',src.size,'white');white.alpha_composite(src)
 ref=white.convert('RGB').crop(crop).resize((1024,1024),Image.Resampling.LANCZOS)
 cm=mask.crop(crop).resize((1024,1024),Image.Resampling.LANCZOS)
 ref.save(d/'closeup-reference.png');cm.save(d/'closeup-mask.png')
 overlay=Image.new('RGBA',ref.size,(236,42,51,0));overlay.putalpha(cm.point(lambda a:int(a*.48)))
 Image.alpha_composite(ref.convert('RGBA'),overlay).save(d/'reference-mask-preview.png')
 meta={'view':view,'sourceSHA256':sha(srcpath),'sam3MaskSHA256':sha(sampath),
       'inputReferenceSHA256':sha(d/'closeup-reference.png'),'inputMaskSHA256':sha(d/'closeup-mask.png'),
       'cropBox':list(crop),'maskBBox':mask.getbbox(),'faceRegion':settings['face']}
 (d/'source-info.json').write_text(json.dumps(meta,indent=2)+'\n')
 brief=f"""Use Codex built-in native image generation tool image_gen.imagegen for a TRUE newly painted anime character hidden-face underpaint, not a Python-generated image. The input is a crop of the already approved original character p0_character_001, at head yaw {view} degrees right. It has dusty pink short hair, burgundy/purple eyes, and gold cross hairpin. Reference PNG is a zoom around the face and front hair; mask PNG white region allows replacement of obscured skin; preview red marks this region. Paint natural underlying forehead and face/eye anatomy behind the fringe so a separately movable front-bangs ArtMesh can expose it naturally. Rebuild the forehead skin under the bangs and retain the original head silhouette and exact 2D eye positions. No duplicated eyes, new accessories, altered ear, major redraw, rotation, or changed framing. Preserve non-masked art exactly as an ideal, though you may only be able to use reference guidance; if editing is not pixel-accurate record that fact. Render one image only, consistent original Japanese animation line-art and skin tone, no composition change or background. Output native PNG to private-assets/p15-97-underpaint-{view}/model-native.png, actual native dimensions (may be 1254x1254). Include real generation-result.json with actual_image_tool_used=true only on successful native generator execution, tool, output_file, image_dimensions, sha256, and limitations. Do not modify Git, scripts, user secrets, or other files; no tests.
"""
 (d/'brief.txt').write_text(brief)
 print(view,meta,flush=True)
