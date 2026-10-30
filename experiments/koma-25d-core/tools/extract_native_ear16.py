#!/usr/bin/env python3
"""CORE016: authenticate and export the TWO ORIGINAL Aka ear ArtMesh parts.

This parses FULL INX source (not Github LFS pointer). UV arrays and triangles
are saved UNCHANGED, including out-of-range UVs and texture indices. Source
pixels are extracted as RGBA PNGs from actual original TGA texture payloads.
NOT a side-skin UV fit or 3D conversion.
"""
from pathlib import Path
import argparse,io,json,hashlib,struct,base64,textwrap
from PIL import Image,ImageDraw,ImageOps
SHA="dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f"
NAMES={"Ear:: Left","Ear:: Right"}
def xy(seq):
    if isinstance(seq[0],list):return seq
    assert len(seq)%2==0
    return [seq[i:i+2] for i in range(0,len(seq),2)]
def main(inp,out):
    out.mkdir(parents=True,exist_ok=True)
    b=inp.read_bytes()
    assert hashlib.sha256(b).hexdigest()==SHA, "full genuine Aka INX SHA mismatch"
    assert b[:8]==b"TRNSRTS\x00"
    n=struct.unpack(">I",b[8:12])[0]
    data=json.loads(b[12:12+n])
    pos=12+n
    assert b[pos:pos+8]==b"TEX_SECT";pos+=8
    count=struct.unpack(">I",b[pos:pos+4])[0];pos+=4
    textures=[]
    for i in range(count):
        ln=struct.unpack(">I",b[pos:pos+4])[0];pos+=4
        fmt=b[pos];pos+=1
        raw=b[pos:pos+ln];pos+=ln
        with Image.open(io.BytesIO(raw)) as im:
            textures.append((fmt,im.convert("RGBA").copy()))
    found=[]
    def visit(node):
        if node.get("name") in NAMES:
            mesh=node["mesh"]
            v=xy(mesh["verts"]);uv=xy(mesh["uvs"]);faces=mesh["indices"]
            assert len(v)==len(uv) and len(faces)%3==0 and all(0<=z<len(v) for z in faces)
            tid=node["textures"][0]
            tex=textures[tid][1]
            texpath=out/("original_"+node["name"].replace(":","").replace(" ","_")+".png")
            tex.save(texpath)
            def bb(points):return [float(min(p[k] for p in points)) for k in (0,1)]+[float(max(p[k] for p in points)) for k in (0,1)]
            found.append({"part":node["name"],"uuid":node["uuid"],"texture_id":tid,
                 "texture_dimensions":list(tex.size),"texture_sha256":hashlib.sha256(texpath.read_bytes()).hexdigest(),
                 "vertex_count":len(v),"triangle_count":len(faces)//3,
                 "vertex_bounds":bb(v),"uv_bounds":bb(uv),"origin":mesh.get("origin"),
                 "mesh":{"verts":v,"uvs":uv,"indices":faces}})
        for child in node.get("children",[]) or []:visit(child)
    visit(data["nodes"])
    assert len(found)==2, "must retrieve both genuine source ears"
    assert sorted(x["vertex_count"] for x in found)==[57,59]
    doc={"schema":"core016-authentic-ear-inx/1","source_sha256":SHA,
         "original_creator":"seagetch","license":"CC BY 4.0",
         "textures_from":"real_INX_TEX_SECT_TGA",
         "original_native_artmesh_unchanged":True,
         "new_view_uv_registered":False,
         "native_param_pose_replayed":False,
         "profile_to_volume_binding":"NOT_VALIDATED",
         "ears":found}
    (out/"native_ear_parts.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n")
    board=Image.new("RGB",(1200,650),(242,244,247))
    d=ImageDraw.Draw(board)
    for k,entry in enumerate(found):
        png=out/("original_"+entry["part"].replace(":","").replace(" ","_")+".png")
        im=Image.open(png).convert("RGBA")
        im.thumbnail((500,530))
        x=k*600+50;y=65
        board.paste(im,(x,y),im)
        d.text((x,16),f'ORIGINAL {entry["part"]} / native uv / verts={entry["vertex_count"]}',fill=(25,32,45))
    board.save(out/"native_ear_texture_contact.png")
    board.thumbnail((960,530))
    board.save(out/"native_ear_texture_contact.jpg",quality=78)
    print("CORE016_TRUE_NATIVE_INX_EAR_UV",json.dumps([
        {x:e[x] for x in ("part","uuid","vertex_count","triangle_count","vertex_bounds","uv_bounds","texture_dimensions","texture_id")}
        for e in found],ensure_ascii=False))
    tag="CORE016_REAL_EAR_TEXTURE_PREVIEW"
    print(tag+"_BEGIN")
    for line in textwrap.wrap(base64.b64encode((out/"native_ear_texture_contact.jpg").read_bytes()).decode(),120):print(line)
    print(tag+"_END")
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args();main(a.input,a.out)
