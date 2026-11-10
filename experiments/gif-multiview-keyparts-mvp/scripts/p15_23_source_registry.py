#!/usr/bin/env python3
"""Provenance registry for P15-23 real Hugging Face generation calls."""
import hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
AS=ROOT/'private-assets/p15-23-hf-independent-parts'
QA=ROOT/'evidence/p15-23-model-source-registry.json'
GENERATIONS=[
 {"key":"hair.ahoge","file":"ahoge-yaw060-raw.webp","model":"Qwen-Image-Fast","space":"mcp-tools/Qwen-Image-Fast","account":"wfswhytrjutrj","seed":602302,
  "prompt":"Single isolated Japanese anime hairstyle asset: exactly ONE thin upward curved ahoge cowlick hair strand, mauve lavender pink hair with darker plum anime ink outline and subtle cel shading, tapered tip, rooted at bottom center, natural gently swaying curved strand appropriate to short neck-length bob-haired girl at right-facing 60-degree three-quarter pose. One strand ONLY, centered, pure white flat background, no face, no head, no other hair, no hair clip, no text, clean anime lineart high quality separable ArtMesh original illustration.",
  "observation":"Whole purple-haired head generated rather than single ahoge"},
 {"key":"hair.side","file":"side-hair-yaw060-raw.webp","model":"Qwen-Image-Fast","space":"mcp-tools/Qwen-Image-Fast","account":"kkdcgtx","seed":602304,
  "prompt":"Isolated original 2D anime hair asset for original anime girl mauve-pink neck-length short bob: ONE left-side layered lock of lavender dusty pink hair, seen at 60 degree right-facing three-quarter angle, naturally tapered smoothly curved strand reaching jaw and neck, elegant soft purple-pink cel shading with dark plum ink line art, consistent narrow strand structure and soft edge. Hair tuft only, no face, no body, no other hair, no accessories, no text, pure WHITE background, centered large individual ArtMesh illustration.",
  "observation":"Whole pink-haired anime head generated rather than independent side lock"},
 {"key":"eye.far","file":"far-eye-yaw060-raw.webp","model":"Qwen-Image-Fast","space":"mcp-tools/Qwen-Image-Fast","account":"dfvswegwseg","seed":602303,
  "prompt":"Isolated original cel-shaded Japanese anime distant FAR EYE component for a 60-degree right-facing three-quarter female face: ONE very narrow partially-occluded violet pink anime eye, small iris with warm magenta center, dark thin upper lashes, slight foreshortening and eyelid contour, flat pure white background, exact eye only, no face, skin, hair, text, second eye, no other objects, separable original anime component for ArtMesh layered compositing.",
  "observation":"Close-up of face and large near eye generated, far-eye narrow-angle requirement not met"},
 {"key":"hair.clip.cross_gold","file":"clip-yaw060-raw.webp","model":"Qwen-Image-Fast","space":"mcp-tools/Qwen-Image-Fast","account":"kkdcgtx","seed":602301,
  "prompt":"Isolated original 2D Japanese TV-anime cel animation accessory asset: a single small GOLD METAL X-SHAPED CROSSED HAIR CLIP, two slim diagonal metallic gold bars crossing at center, precisely drawn edges and warm gold highlights, slight 60 degree profile foreshortening, facing right on the original girl's hair side. One object ONLY, centered, large crisp silhouette on a pure flat white background, no hair, no head, no skin, no letters, no text, no shadows, no other accessories. Designed as a separable transparent ArtMesh illustration component.",
  "observation":"Crossed clip drawn on brown-haired character head, incompatible base identity"},
 {"key":"hair.clip.cross_gold","file":"clip-flux-isolated-raw.webp","model":"FLUX.1 Schnell","space":"evalstate/flux1_schnell","account":"wfswhytrjutrj","seed":602305,
  "prompt":"Product cutout for an anime character rig: only one isolated gold X shaped crossed metallic hairpin, two narrow straight gold rods crossing. Perfect clear silhouette. Flat white empty background. No hair, no head, no face, no person, no props, no text. Precisely drawn clean cel-shaded anime accessory asset, centered, fills half canvas.",
  "observation":"Golden cross and brown hair together, not isolated clip"}
]
for rec in GENERATIONS:
 p=AS/rec['file']
 rec['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 with Image.open(p) as im:
  rec['canvas']=list(im.size);rec['mode']=im.mode
 rec['acceptedAsIsolatedTransparentAsset']=False
qa={"schema":"KOMA-P15-23-HF-GENERATED-SOURCE-REGISTRY-V1","characterId":"p0_character_001",
 "authenticatedConnectorAccountsUsed":3,"imageGenerationSucceeded":len(GENERATIONS),
 "independentSinglePartPaintingsApproved":0,
 "generatedImageSourceContent":"MODEL_GENERATED_REAL_IMAGES_NO_REFERENCE_CONDITIONING",
 "referenceConditionedIdentityVerification":"FAILED_OR_NOT_PERFORMED",
 "sourceFilenamesNotCommitted":True,
 "sources":GENERATIONS}
QA.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({"generated":len(GENERATIONS),"approved":0,"sha256":[x["sha256"][:12] for x in GENERATIONS]}))
