#!/usr/bin/env python3
"""Deliver three-angle original P0 PSD source inventory and native profile layers."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as fp:
  for chunk in iter(lambda:fp.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def read(file):return json.loads(Path(file).read_text(encoding="utf8"))

def package(exp,out):
 exp=Path(exp).resolve();base=exp/"private-assets"
 p11=base/"p11-profile-psd/yaw090"
 source=read(p11/"qa.json")
 registry=read(base/"p5-see-through/mv-candidate/parts.json")
 if source["characterId"]!="p0_character_001" or registry["characterId"]!="p0_character_001":
  raise ValueError("Original P0 identity mismatch")
 if source["nativeLayerCount"]!=13 or not source["sourceReconstructionPixelExact"]:
  raise ValueError("Original P0 side-view layer source incomplete")
 if source["PSDCompositeAlphaMaxDifference"]!=0 or source["PSDCompositeVisibleColorMaxDifference"]>1:
  raise ValueError("PSD did not recover native P0 side artwork")
 files={}
 def add(path,expected=None):
  file=Path(path).resolve()
  if not file.is_file() or not file.is_relative_to(exp):
   raise FileNotFoundError(file)
  fingerprint=sha(file)
  if expected and fingerprint!=expected:
   raise ValueError("P0 source SHA256 changed "+str(file))
  files[str(file.relative_to(exp))]=file
 add(base/source["psdPath"],source["psdSHA256"])
 add(base/source["sourceRGBAPreviewPath"],source["sourceRGBAPreviewSHA256"])
 add(base/source["PSDCompositePath"],source["PSDCompositeSHA256"])
 add(base/source["sourceComparisonPath"],source["sourceComparisonSHA256"])
 for rec in registry["parts"]:
  add(base/rec["path"],rec["frameSha256"])
 for rec in registry["wholeViews"]:
  add(base/rec["path"],rec["sha256"])
 for yaw,filename in (
  (0,"p4-see-through/front/p0-character-001-see-through.psd"),
  (45,"p5-see-through/yaw045/p0-character-001-see-through.psd")
 ):
  add(base/filename)
 for rel in (
  "p11-profile-psd/yaw090/qa.json",
  "p5-see-through/mv-candidate/parts.json",
  "p5-see-through/mv-candidate/landmark-qa.json",
  "p8-semantic-occlusion/selective-sequence/qa.json",
  "p8-semantic-occlusion/selective-sequence/temporal-qa.json",
  "p8-semantic-occlusion/p0-semantic-occlusion-turn.qa.json",
  "p8-semantic-occlusion/p0-semantic-occlusion-turn.gif"
 ):
  add(base/rel)
 for rel in (
  "scripts/p11_build_profile_psd.py",
  "scripts/p11_package_profile.py",
  "tests/test_p11_profile_psd.py"
 ):
  add(exp/rel)
 manifest={
  "schema":"KOMA-P0-P11-THREE-ANGLE-EDITABLE-PSD-SOURCE-V1",
  "characterId":"p0_character_001",
  "originalAuthoredViews":[0,45,90],
  "PSDAssetsByView":{
   "0":{"path":"p4-see-through/front/p0-character-001-see-through.psd",
        "type":"See-through inferred P0 semantic layers"},
   "45":{"path":"p5-see-through/yaw045/p0-character-001-see-through.psd",
         "type":"See-through inferred P0 semantic layers"},
   "90":{"path":source["psdPath"],
         "type":"P0 original profile semantic PNG layers assembled losslessly into editable PSD"}
  },
  "sourceSemanticArtMeshSlots":len(registry["parts"]),
  "yaw90PSDNativeLayers":13,
  "yaw90OriginalRGBAExactlyReconstructed":True,
  "yaw90PSDDecodedAlphaMaxDifference":0,
  "yaw90PSDDecodedVisibleRGBMaxDifference":source["PSDCompositeVisibleColorMaxDifference"],
  "sourceCanvas":[1024,1024],
  "P8AnimationReference":"p8-semantic-occlusion/p0-semantic-occlusion-turn.gif",
  "visualApproval":"PROFILE_ORIGINAL_90_SOURCE_VERIFIED",
  "dynamicTurnArtApproval":"PENDING_VISIBLE_AND_OCCLUDED_SOURCE_CORRESPONDENCE",
  "files":[{"path":k,"bytes":v.stat().st_size,"sha256":sha(v)} for k,v in sorted(files.items())]
 }
 README="""# p0_character_001 · Editable 0° / 45° / 90° P0 Source PSD

This archive contains three PSD files and the original approved P0 anime
character's view/part registry. The 90-degree PSD has 13 editable
individually transparent semantic layers (each a full 1024x1024 canvas)
and reproduces the original side view pixel-for-pixel using original
source PNG composition. The decoded PSD retains exact layer alpha,
with maximum visible RGB deviation of 1/255 from the input.

0° and 45° PSDs are generated from the prior independent See-through
semantic extraction. 90° PSD is reconstructed from original registered
P0 semantic RGBA assets, not inferred from an independent model.

The PSD and layer source hashes are registered in:
  private-assets/p11-profile-psd/yaw090/qa.json

Original view previews and comparison:
  private-assets/p11-profile-psd/yaw090/p0-90-psd-source-comparison.jpg
  private-assets/p8-semantic-occlusion/p0-semantic-occlusion-turn.gif

Layer visibility and original source IDs are in:
  private-assets/p5-see-through/mv-candidate/parts.json

The editable side PSD provides the authentic visible profile. Any
anatomical surfaces hidden by the visible 90° drawing need separate
artwork for high-quality continuous 360-degree rotation.
"""
 out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
  for name,file in sorted(files.items()):z.write(file,arcname=name)
  z.writestr("README.md",README)
  z.writestr("package-manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
 with zipfile.ZipFile(out) as z:
  if z.testzip() is not None:raise ValueError("P11 ZIP CRC failure")
  stored=json.loads(z.read("package-manifest.json"))
  for item in stored["files"]:
   if hashlib.sha256(z.read(item["path"])).hexdigest()!=item["sha256"]:
    raise ValueError("Source asset ZIP SHA256 mismatch "+item["path"])
 report={
  "schema":"KOMA-P0-P11-THREE-ANGLE-PSD-PACKAGE-QA-V1",
  "characterId":"p0_character_001",
  "archivePath":str(out),"bytes":out.stat().st_size,
  "sha256":sha(out),"entryCount":len(files)+2,
  "PSDViewAngles":[0,45,90],
  "yaw90OriginalSemanticLayers":13,
  "sourceArtMeshViewSlots":39,
  "yaw90OriginalSourcePixelsExact":True,
  "yaw90PSDCompositeAlphaMaxDifference":0,
  "yaw90PSDCompositeRGBMaxDifference":source["PSDCompositeVisibleColorMaxDifference"],
  "internalHashesVerified":True
 }
 (p11/"package-qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(report,ensure_ascii=False,indent=2))
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--experiment",required=True)
 p.add_argument("--output",required=True)
 a=p.parse_args()
 package(a.experiment,a.output)
