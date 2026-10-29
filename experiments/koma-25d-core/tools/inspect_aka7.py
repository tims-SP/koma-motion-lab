#!/usr/bin/env python3
"""Read official Aka PSD and INX *without* inventing an image layer/rig.

Outputs diagnostics and source-raster reference. The INX packet spec is
public (Inochi2D TRNSRTS\0, big endian JSON length, TEX_SECT textures).
"""
from __future__ import annotations
import argparse,hashlib,io,json,struct
from pathlib import Path
from psd_tools import PSDImage
from PIL import Image

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def inspect_psd(path,out):
    psd=PSDImage.open(path)
    entries=[]
    def walk(nodes,parent=""):
        for node in nodes:
            name=parent+"/"+str(node.name)
            bbox=[int(node.left),int(node.top),int(node.right),int(node.bottom)]
            record={"path":name,"visible":bool(node.is_visible()),"group":bool(node.is_group()),
                    "bbox":bbox,"blend_mode":str(node.blend_mode),
                    "opacity":int(node.opacity)}
            entries.append(record)
            if node.is_group():walk(node,name)
    walk(psd)
    src=psd.composite()
    if src is None:raise ValueError("PSD could not be composited")
    src=src.convert("RGBA")
    if min(src.size)<128:raise ValueError("PSD canvas too small")
    src.save(out/"original_psd.png")
    return {"source_sha256":digest(path),"size":src.size,"layers":entries,
            "leaf_layer_count":sum(not a["group"] for a in entries),
            "visible_leaf_count":sum(a["visible"] and not a["group"] for a in entries)}

def inspect_inx(path,out):
    data=path.read_bytes()
    if data[:8]!=b"TRNSRTS\x00":raise ValueError("Not supported INX1 (header="+repr(data[:8])+")")
    length=struct.unpack(">I",data[8:12])[0]
    if length<100 or length>len(data)-12:raise ValueError("INX bad length")
    model=json.loads(data[12:12+length])
    pos=12+length
    if data[pos:pos+8]!=b"TEX_SECT":raise ValueError("Missing INX texture section")
    pos+=8
    count=struct.unpack(">I",data[pos:pos+4])[0];pos+=4
    if count>1000:raise ValueError("Impossible texture count")
    tex=[]
    for i in range(count):
        n=struct.unpack(">I",data[pos:pos+4])[0];pos+=4
        fmt=data[pos];pos+=1
        payload=data[pos:pos+n];pos+=n
        if len(payload)!=n:raise ValueError("INX truncated image")
        image=Image.open(io.BytesIO(payload)).convert("RGBA")
        image.save(out/f"inx_texture_{i:02d}.png")
        tex.append({"index":i,"format_id":fmt,"size":list(image.size),"bytes":n})
    def paths(x,prefix="",depth=0):
        if depth>14:return []
        if isinstance(x,dict):
            found=[]
            if any(k in x for k in ("name","type","mesh","deform","parameters")):
                found.append({"path":prefix,"keys":list(x.keys())[:25],
                   "name":x.get("name"),"type":x.get("type"),
                   "mesh_keys":list(x["mesh"].keys()) if isinstance(x.get("mesh"),dict) else [],
                   "part_textures":x.get("textures") if isinstance(x.get("textures"),list) else None})
            for k,v in x.items():found.extend(paths(v,prefix+"/"+str(k),depth+1))
            return found
        if isinstance(x,list):
            found=[]
            for i,v in enumerate(x):found.extend(paths(v,prefix+"/"+str(i),depth+1))
            return found
        return []
    return {"source_sha256":digest(path),"total_bytes":len(data),
      "root_keys":list(model.keys()),"model":model.get("meta",{}),
      "texture_count":count,"textures":tex,
      "object_index":paths(model)[:400],
      "structure_provenance":"ACTUAL_INOCHI2D_INX_RIG_NOT_TRANSLATED",
      "full_runtime_parity":"NOT_TESTED"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--psd",type=Path,required=True)
    ap.add_argument("--inx",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    result={
      "source_repo":"Inochi2D/inochi2d-docs",
      "source_revision":"593c657855d5679f01443ef311346298fd25e117",
      "source_character":"Aka head, original illustration credited to seagetch",
      "license":"CC BY 4.0 according to Inochi2D/example-models README",
      "license_notice":"Aka — design & rigging: seagetch, Creative Commons Attribution 4.0",
      "psd":inspect_psd(a.psd,a.out),
      "inx":inspect_inx(a.inx,a.out),
    }
    if result["psd"]["visible_leaf_count"]<5:raise ValueError("Not layered art")
    if result["inx"]["texture_count"]<1:raise ValueError("INX contains no textures")
    (a.out/"source_audit.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("CORE007_ACTUAL_LAYERS",json.dumps({
     "psd_canvas":result["psd"]["size"],
     "leaf_layers":result["psd"]["leaf_layer_count"],
     "inx_root_keys":result["inx"]["root_keys"],
     "inx_textures":result["inx"]["textures"],
     "inx_object_count":len(result["inx"]["object_index"]),
     "layer_paths":[x["path"] for x in result["psd"]["layers"]][:80],
     "inx_nodes":result["inx"]["object_index"][:35]
    },ensure_ascii=False))
if __name__=="__main__":main()
