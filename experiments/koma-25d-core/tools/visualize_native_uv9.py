#!/usr/bin/env python3
"""Show source Aka INX ArtMesh in local XY vs its original UV coordinates.

This deliberately does not use GPT view artwork or claim it is mapped.
"""
import argparse,json,math
from pathlib import Path
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument("--mesh",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
a=p.parse_args();mesh=json.loads(a.mesh.read_text())
names=["Face","Ear:: Left","Ear:: Right","Front Hair:: Center","Eye:: Left:: Eyeball","Eye:: Right:: Eyeball","Side Hair:: Left","Leaf"]
idx={x["name"]:x for x in mesh["parts"]}
W,H=520,340
board=Image.new("RGB",(4*W,2*H),(239,242,245));d=ImageDraw.Draw(board)
for i,name in enumerate(names):
 if name not in idx:raise ValueError("Missing actual native ArtMesh "+name)
 m=idx[name];left=(i%4)*W;top=(i//4)*H
 d.text((left+14,top+8),name+" | original INX",fill=(31,42,51))
 for col,key in enumerate(("verts","uvs")):
  pts=m["mesh"][key];tri=m["mesh"]["indices"]
  bx0=min(x[0] for x in pts);by0=min(x[1] for x in pts);bx1=max(x[0] for x in pts);by1=max(x[1] for x in pts)
  x0=left+col*260+10;y0=top+44
  dim=248
  scale=min((dim-20)/max(1e-3,bx1-bx0),(dim-20)/max(1e-3,by1-by0))
  pix=[(x0+10+(x-bx0)*scale,y0+10+(y-by0)*scale) for x,y in pts]
  d.rectangle((x0+3,y0+3,x0+250,y0+250),outline=(175,181,188))
  for k in range(0,len(tri),3):
   q=[pix[tri[k+j]] for j in range(3)]
   d.line((q[0],q[1],q[2],q[0]),fill=(150,162,177),width=1)
  for x,y in pix[::max(1,len(pix)//90)]:
   d.ellipse((x-1,y-1,x+1,y+1),fill=(90,116,151))
  d.text((x0+3,top+303),("local verts" if col==0 else "source UV")+" ("+str(len(pts))+")",fill=(45,55,70))
board.save(a.out)
jpg=a.out.with_suffix(".jpg");board.thumbnail((1560,650));board.save(jpg,quality=88,optimize=True)
print("CORE009_NATIVE_ARTMESH_WIREFRAME",str(a.out),len(names))
