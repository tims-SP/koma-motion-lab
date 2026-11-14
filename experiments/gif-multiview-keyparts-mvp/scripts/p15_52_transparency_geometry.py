#!/usr/bin/env python3
"""Extract an exterior-black keyed alpha for an isolated candidate without changing approved ArtMesh."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "private-assets"
OUT = ASSETS / "exports/p15-52-transparency-geometry"
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ASSETS / "exports/p15-51-qwen-angle-plus20deg.webp"
ORIGINAL = ASSETS / "exports/p15-38-original-p0-arc-review/p0-yaw45-original.png"
TARGET65 = ASSETS / "p15-38-p0-registered-arc/yaw65/composite.png"
CAMERA = ROOT / "evidence/p15-12-camera-proxy-qa.json"

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

image = Image.open(SOURCE).convert("RGB")
assert image.size == (1024,1024)
r,g,b = image.split()
brightness = ImageChops.lighter(ImageChops.lighter(r,g), b)
# A pixel darker than this threshold is eligible for exterior black.
# Only exterior-connected near-black pixels are removed; interior pupils and uniform stay intact.
threshold=12
dark = brightness.point(lambda v: 255 if v <= threshold else 0)
flood = dark.copy()
# mark the exterior-connected black region with a distinct value
ImageDraw.floodfill(flood, (0,0), 128, border=0, thresh=0)
# Remove exterior-connected dark pixels and the enclosed black void inside the ahoge loop.
for corner in [(1023,0),(0,1023),(1023,1023),(520,80)]:
    if flood.getpixel(corner)==255:
        ImageDraw.floodfill(flood, corner,128,border=0,thresh=0)
exterior = flood.point(lambda v: 255 if v==128 else 0)
# Keep non-exterior at full alpha; gently feather only the 1px silhouette boundary.
alpha = ImageOps.invert(exterior).filter(ImageFilter.GaussianBlur(0.8))
# Preserve opaque interior detail exactly; eroded silhouette is guaranteed opaque.
interior = ImageOps.invert(exterior).filter(ImageFilter.MinFilter(3))
alpha = ImageChops.lighter(alpha, interior)
rgba = image.copy().convert("RGBA")
rgba.putalpha(alpha)
rgba.save(OUT / "camera-plus20-transparent.png")
alpha.save(OUT / "silhouette-alpha.png")

# Compare on both light and saturated backgrounds to reveal halos, clipped hair tips and dark outfit.
from PIL import ImageDraw as ID
for name,bgcolor in [("light",(237,238,244,255)),("blue",(51,119,176,255)),("pink",(246,195,207,255))]:
    plate=Image.new("RGBA",rgba.size,bgcolor)
    plate.alpha_composite(rgba)
    plate.convert("RGB").save(OUT / ("preview-"+name+".png"))
# Annotated camera anchors are reference expectations, not measured landmarks in the candidate.
cam=json.loads(CAMERA.read_text())
anchor_frame=next(item for item in cam["frames"] if item["yaw"] == 65)
mapped_keys=[
    "eye.near.iris","eye.far.iris","nose","mouth",
    "face.chin","face.jaw.near","hair.clip.center","hair.ahoge.root"
]
annotation=rgba.copy()
overlay=Image.new("RGBA",rgba.size,(0,0,0,0))
draw=ImageDraw.Draw(overlay)
colors={"eye.near.iris":"#00d7ff","eye.far.iris":"#f93bdd","nose":"#ffb000",
        "mouth":"#f9f24d","face.chin":"#25ff83","face.jaw.near":"#46e4c7",
        "hair.clip.center":"#ff513c","hair.ahoge.root":"#bd90ff"}
for key in mapped_keys:
    x,y=anchor_frame["anchors"][key]["xy"]
    x,y=round(x),round(y)
    col=colors[key]
    draw.line(((x-12,y),(x+12,y)),fill=col,width=3)
    draw.line(((x,y-12),(x,y+12)),fill=col,width=3)
    draw.ellipse((x-6,y-6,x+6,y+6),outline=col,width=2)
annotation=Image.alpha_composite(annotation,overlay)
plate=Image.new("RGBA",rgba.size,(238,239,247,255))
plate.alpha_composite(annotation)
plate.convert("RGB").save(OUT/"candidate-anchor-overlay.png")
# Reference original and registered 65 camera guide for side-by-side visual assessment.
(OUT/"source45.png").write_bytes(ORIGINAL.read_bytes())
(OUT/"registered65.png").write_bytes(TARGET65.read_bytes())
# Count threshold/alpha and ensure no accidental source mutation.
hist=alpha.histogram()
transparent=hist[0]
opaque=hist[255]
partial=1024*1024-transparent-opaque
edge_pixels=sum(hist[1:255])
assert opaque > 250000 and transparent > 200000 and partial > 0
# The current candidate is not a validated formal 65-degree view.
report={
    "schema":"KOMA-P15-52-TRANSPARENCY-GEOMETRY-V1",
    "characterId":"p0_character_001",
    "sourceAngleLoRA":{
        "referenceYaw":45,"commandedRelativeCameraRotate":20,"absoluteYawCalibrated":False,
        "sourcePath":str(SOURCE.relative_to(ROOT)),"sourceSHA256":sha(SOURCE),
        "controlSeed":65451,"model":"Qwen Image Edit 2509 + Multiple Angles LoRA"
    },
    "blackKey":{"thresholdMaxRGB":threshold,"enclosedHairLoopSeed":[520,80],"method":"exterior-connected black flood fill + 0.8px edge feather",
        "opaquePixels":opaque,"fullyTransparentPixels":transparent,"partialAlphaPixels":partial,
        "alphaRange":list(alpha.getextrema()),"preservesInteriorDarkFeatures":True},
    "output":{"path":str((OUT/"camera-plus20-transparent.png").relative_to(ROOT)),
        "sha256":sha(OUT/"camera-plus20-transparent.png"),"mode":"RGBA","size":[1024,1024]},
    "cameraProxy":{"path":str(CAMERA.relative_to(ROOT)),"sha256":sha(CAMERA),
        "annotatedAnchorCount":len(mapped_keys),"anchorCoordinatesAreExpectedNotMeasured":True,
        "absoluteYaw65Verified":False},
    "visualFindings":{
        "facingDirection":"right-facing three-quarter/profile candidate",
        "nearEye":"visible and dominant",
        "farEye":"narrow and partly occluded",
        "noseBridge":"visible profile shift",
        "hairAndAhoge":"pink-lavender bob and single ahoge retained",
        "goldCrossHairClip":"FAIL: gold clip at far-right silhouette has collapsed toward a narrow partly hidden mark; full crossed geometry is not preserved",
        "darkUniformEdge":"requires visual halo assessment on white/blue/pink backgrounds",
        "geometry":"camera anchor overlay is a reference comparison, not independently detected landmarks or absolute yaw proof"
    },
    "formalKeyframeAccepted":False,
    "artMeshModified":False,
    "next":"Correct gold crossed hair-clip perspective, verify silhouette halo and exact pose landmarks before accepting as formal keyframe"
}
(ROOT/"evidence/p15-52-transparency-geometry-qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"transparent":transparent,"opaque":opaque,"partial":partial,
                  "alphaRange":alpha.getextrema(),"sha256":report["output"]["sha256"]}))
