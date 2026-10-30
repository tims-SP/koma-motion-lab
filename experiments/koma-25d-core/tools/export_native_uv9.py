#!/usr/bin/env python3
"""Extract REAL, untouched source ArtMesh verts/UV/triangles and texture IDs."""
import argparse,hashlib,io,json,struct
from pathlib import Path
from PIL import Image
SHA="dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f"
def pairs(a):
 if not a:return []
 if isinstance(a[0],list):return [[float(x),float(y)] for x,y in a]
 assert len(a)%2==0
 return [[float(a[i]),float(a[i+1])] for i in range(0,len(a),2)]
def bbox(a):return [min(x[0] for x in a),min(x[1] for x in a),max(x[0] for x in a),max(x[1] for x in a)]
def run(src,out):
 b=src.read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
 assert b[:8]==b"TRNSRTS\x00"
 n=struct.unpack(">I",b[8:12])[0];m=json.loads(b[12:12+n]);o=12+n
 assert b[o:o+8]==b"TEX_SECT";o+=8
 total=struct.unpack(">I",b[o:o+4])[0];o+=4
 textures=[]
 for i in range(total):
  sz=struct.unpack(">I",b[o:o+4])[0];o+=4
  fmt=b[o];o+=1
  im=Image.open(io.BytesIO(b[o:o+sz]));o+=sz
  textures.append({"index":i,"size":list(im.size),"format":fmt})
 parts=[];nodes=[]
 def walk(x,p="",depth=0):
  if depth>30:raise ValueError("Node hierarchy depth")
  name=x.get("name","").rstrip("\x00");path=p+"/"+name
  rec={"name":name,"path":path,"uuid":x.get("uuid"),"type":x.get("type"),"zsort":x.get("zsort")}
  nodes.append(rec)
  if isinstance(x.get("mesh"),dict):
   mesh=x["mesh"];v=pairs(mesh["verts"]);u=pairs(mesh["uvs"]);tri=mesh["indices"]
   if len(v)!=len(u) or not v or len(tri)%3 or not all(0<=i<len(v) for i in tri):
    raise ValueError("Invalid genuine mesh "+name)
   tid=x["textures"][0]
   if not isinstance(tid,int) or not 0<=tid<total:raise ValueError("Texture index "+name)
   parts.append({**rec,"psdLayerPath":x.get("psdLayerPath"),"texture_id":tid,
    "texture_dimensions":textures[tid]["size"],"vertex_count":len(v),
    "triangle_count":len(tri)//3,"vertex_bounds_original":bbox(v),
    "uv_bounds_original":bbox(u),"origin":mesh.get("origin"),
    "original_mesh_unchanged":True,"mesh":{"verts":v,"uvs":u,"indices":tri}})
  for y in x.get("children",[]) or []:walk(y,path,depth+1)
 walk(m["nodes"])
 assert len(parts)>=35
 doc={"schema":"koma009-actual-inx-artmesh/1","source":"Inochi2D/example-models/Aka.inx",
 "source_sha256":SHA,"original_artist":"seagetch","license":"CC BY 4.0",
 "provenance":"ACTUAL_NATIVE_SOURCE_INX_ARTMESH","gpt_newview_uv":"NOT_REGISTERED",
 "texture_count":total,"mesh_count":len(parts),"node_count":len(nodes),
 "total_vertices":sum(x["vertex_count"] for x in parts),
 "total_triangles":sum(x["triangle_count"] for x in parts),
 "textures":textures,"parts":parts,"nodes":nodes}
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(doc,ensure_ascii=False,separators=(",",":"))+"\n")
 summ={k:v for k,v in doc.items() if k not in ("parts","nodes","textures")}
 summ["part_names"]=[x["name"] for x in parts]
 summ["grouped_meshes"]=[{k:x[k] for k in ("name","uuid","texture_id","vertex_count","triangle_count","uv_bounds_original")}
  for x in parts]
 (out.parent/"source_mesh_summary.json").write_text(json.dumps(summ,ensure_ascii=False,indent=2)+"\n")
 print("CORE009_ACTUAL_MESH_SUMMARY",json.dumps(summ,ensure_ascii=False)[:13000])
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--input",type=Path,required=True);a.add_argument("--out",type=Path,required=True)
 x=a.parse_args();run(x.input,x.out)
