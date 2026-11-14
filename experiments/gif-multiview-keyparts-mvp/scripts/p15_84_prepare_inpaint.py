from pathlib import Path
from PIL import Image,ImageChops,ImageFilter
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-84-clean-brow-inpaint';D.mkdir(parents=True,exist_ok=True)
srcp=P/'p15-56-edge-matting/candidate-erode-2.png'
eyep=P/'p15-65-eyelid-refinement/eye.near.refined-layer.png'
browp=P/'p15-79-brow-split/eyebrow.same-view.png'
hairp=P/'p15-81-image-layered/sam3-027-aligned-alpha.png'
src=Image.open(srcp).convert('RGBA')
eye=Image.open(eyep).convert('RGBA').getchannel('A')
brow=Image.open(browp).convert('RGBA').getchannel('A')
hair=Image.open(hairp).convert('L')
# Remove complete old eye and eyebrow, plus a narrow 8px blend margin.
eye=eye.point(lambda x:255 if x>16 else 0).filter(ImageFilter.MaxFilter(17))
brow=brow.point(lambda x:255 if x>16 else 0).filter(ImageFilter.MaxFilter(11))
mask=ImageChops.lighter(eye,brow)
# Never erase visible front hair: it remains a separate foreground layer.
mask=ImageChops.multiply(mask,ImageChops.invert(hair.point(lambda x:255 if x>40 else 0)))
# crop chosen to cover the full eye/brow and adjacent blending region.
box=(380,300,892,812)
rgb=Image.new('RGBA',src.size,(255,255,255,255));rgb.alpha_composite(src)
rgb.crop(box).convert('RGB').save(D/'input-512.png')
mask.crop(box).save(D/'mask-512.png')
mask.save(D/'mask-full.png')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
q={'schema':'KOMA-P15-84-REAL-HIDDEN-BROW-EYE-INPAINT-V1','sourceSHA256':sha(srcp),
 'eyeLayerSHA256':sha(eyep),'browLayerSHA256':sha(browp),'hairMaskSHA256':sha(hairp),
 'cropBox':list(box),'inputSHA256':sha(D/'input-512.png'),'maskSHA256':sha(D/'mask-512.png'),
 'maskMethod':'union of independently extracted full near-eye and eyebrow alpha, dilated 8px eye / 5px brow; subtract SAM3 foreground bangs',
 'maskPixels':sum(v>0 for v in mask.getdata()),
 'provider':'pg56714/Inpaint-Anything','model':'LaMa neural inpainting CPU',
 'modelStatus':'PREPARED','formalArtMeshAccepted':False,'formalKeyframeAccepted':False}
(R/'evidence/p15-84-qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(q,ensure_ascii=False),flush=True)
