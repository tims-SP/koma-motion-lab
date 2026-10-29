#!/usr/bin/env python3
"""KOMA-25D CORE-001: convert the real MIT Godot GBot Polygon2D rig to an
intermediate textured 2.5D mesh. No game art is committed to this repository.

This is a structure/UV/lift pilot, NOT full Godot animation-runtime equivalence.
"""
from __future__ import annotations
import argparse, json, math, re, struct, urllib.request
from pathlib import Path

REPO = "https://raw.githubusercontent.com/godotengine/godot-demo-projects"
REV = "b761b4cd5718a7118f2c95eb55f181d0a5f004f1"
BASE = f"{REPO}/{REV}/2d/skeleton/player"
SCALE = 0.012

def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "koma-25d-core001"})
    with urllib.request.urlopen(req, timeout=50) as r:
        return r.read(5_000_001)

def pairs(raw: str) -> list[list[float]]:
    vals = [float(v.strip()) for v in raw.split(",") if v.strip()]
    if len(vals) % 2: raise ValueError("Odd Vector2 coordinate count")
    return [vals[i:i + 2] for i in range(0, len(vals), 2)]

def vec(text: str, name: str, default=(0.0, 0.0)):
    m = re.search(r"^" + re.escape(name) + r" = Vector2\(([^)]*)\)", text, re.M)
    return pairs(m.group(1))[0] if m else list(default)

def field(text: str, name: str, prefix: str):
    m = re.search(r"^" + re.escape(name) + r" = " + prefix + r"\(([^)]*)\)", text, re.M)
    if not m: raise ValueError(f"Missing {name}")
    return m.group(1)

def earclip(poly: list[int], pts: list[list[float]]) -> list[int]:
    """Triangulate one simple Godot subpolygon, retaining vertex indices."""
    if len(poly) < 3: return []
    signed = sum(pts[a][0] * pts[b][1] - pts[b][0] * pts[a][1]
                 for a, b in zip(poly, poly[1:] + poly[:1]))
    ccw = signed > 0
    rem = poly[:]
    out = []
    while len(rem) > 3:
        found = False
        for i in range(len(rem)):
            a, b, c = rem[i-1], rem[i], rem[(i+1) % len(rem)]
            ax, ay = pts[a]; bx, by = pts[b]; cx, cy = pts[c]
            cross = (bx-ax)*(cy-ay) - (by-ay)*(cx-ax)
            if (cross > 1e-7) != ccw: continue
            def inside(p):
                px, py = pts[p]
                def side(x1,y1,x2,y2):
                    return (x2-x1)*(py-y1)-(y2-y1)*(px-x1)
                s = [side(ax,ay,bx,by), side(bx,by,cx,cy), side(cx,cy,ax,ay)]
                return all(v>=-1e-7 for v in s) or all(v<=1e-7 for v in s)
            if any(inside(p) for p in rem if p not in (a,b,c)): continue
            out += [a,b,c] if ccw else [a,c,b]
            rem.pop(i); found=True; break
        if not found: raise ValueError("Non-simple or degenerate polygon")
    out += rem if ccw else [rem[0],rem[2],rem[1]]
    return out

def convert(scene: str, png: bytes, depth: float) -> dict:
    if png[:8] != b"\x89PNG\r\n\x1a\n": raise ValueError("Not a PNG")
    width, height = struct.unpack(">II", png[16:24])
    blocks = re.findall(r"(?m)^\[node [^\n]*\]\n(?:(?!^\[).*\n?)*", scene)
    nodes = []
    for block in blocks:
        head = block.splitlines()[0]
        m = re.match(r'\[node name="([^"]+)" type="([^"]+)" parent="([^"]+)"', head)
        if m: nodes.append((m.group(1), m.group(2), m.group(3), block))
    bones = []
    for name, kind, parent, block in nodes:
        if kind != "Bone2D": continue
        prefix = "Sprite2D/Skeleton2D"
        if not parent.startswith(prefix): continue
        path = (parent[len(prefix):].strip("/") + "/" + name).strip("/")
        parpath = "/".join(path.split("/")[:-1])
        bypath = {b["path"]: i for i,b in enumerate(bones)}
        if parpath and parpath not in bypath: raise ValueError("Unordered bone hierarchy")
        parent_id = bypath.get(parpath, -1)
        loc = vec(block,"position")
        if parent_id < 0: world = loc[:]
        else:
            pw = bones[parent_id]["world_px"]
            world = [pw[0]+loc[0],pw[1]+loc[1]]
        bones.append({"name":name,"path":path,"parent":parent_id,
                      "local":[loc[0]*SCALE,-loc[1]*SCALE,0],
                      "world_px":world})
    if not bones: raise ValueError("No Bone2D joints")
    bone_by_path = {b["path"]:i for i,b in enumerate(bones)}
    meshes=[]
    for name,kind,parent,block in nodes:
        if kind != "Polygon2D": continue
        xy = pairs(field(block,"polygon","PackedVector2Array"))
        uv = pairs(field(block,"uv","PackedVector2Array"))
        if len(xy)!=len(uv) or len(xy)<3: raise ValueError(f"{name}: wrong vertices")
        polyline = re.search(r"^polygons = \[(.*)\]$",block,re.M)
        faces = [list(map(int, re.findall(r"-?\d+",p))) for p in re.findall(
            r"PackedInt32Array\(([^)]*)\)", polyline.group(1))] if polyline else [list(range(len(xy)))]
        tris = []
        for face in faces: tris += earclip(face,xy)
        if not tris or any(j>=len(xy) or j<0 for j in tris): raise ValueError("Invalid triangle indices")
        bone_line = re.search(r"^bones = \[(.*)\]$",block,re.M)
        channels = []
        if bone_line:
            for path,vals in re.findall(r'"([^"]+)", PackedFloat32Array\(([^)]*)\)',bone_line.group(1)):
                weights = [float(w.strip()) for w in vals.split(",") if w.strip()]
                if len(weights)!=len(xy): raise ValueError(f"{name}: bad skin channels")
                if path in bone_by_path: channels.append((bone_by_path[path],weights))
        offset = vec(block,"position")
        center_x = (min(p[0] for p in xy)+max(p[0] for p in xy))/2
        halfwidth = max(4,(max(p[0] for p in xy)-min(p[0] for p in xy))/2)
        verts = []
        skinidx=[]; skinweight=[]
        for i,(p,t) in enumerate(zip(xy,uv)):
            r = min(1,abs(p[0]-center_x)/halfwidth)
            z = depth * max(0.0,1-r*r)**0.5
            verts.append([(p[0]+offset[0])*SCALE,-(p[1]+offset[1])*SCALE,z])
            ranked = sorted([(bid,ws[i]) for bid,ws in channels if ws[i]>1e-5],
                            key=lambda v:v[1],reverse=True)[:4]
            if not ranked: ranked=[(0,1.)]
            total = sum(w for _,w in ranked)
            skinidx.append([bid for bid,_ in ranked]+[0]*(4-len(ranked)))
            skinweight.append([w/total for _,w in ranked]+[0.]*(4-len(ranked)))
        meshes.append({"name":name,"vertices":verts,"uv":[[u/width,1-v/height] for u,v in uv],
                       "indices":tris, "skinIndex":skinidx,"skinWeight":skinweight,
                       "layer":len(meshes)})
    if not meshes: raise ValueError("No Polygon2D meshes")
    points=[v for m in meshes for v in m["vertices"]]
    bounds=[[min(v[k] for v in points),max(v[k] for v in points)] for k in (0,1,2)]
    return {"schema":"koma-25d-pilot/1","source":"Godot Skeleton2D GBot MIT",
            "source_revision":REV,"source_animation_parity":"NOT_TESTED",
            "source_uv_preserved":True,"width":width,"height":height,
            "depth":depth,"bounds":bounds,"bones":bones,"meshes":meshes,
            "limitations":["2D bone rotations not yet retargeted",
                           "generated depth is an open front shell, not a complete 360-degree character",
                           "back/side texture not available; no new artwork is invented",
                           "source Polygon2D color/animation path parity not yet validated"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source", type=Path, help="local player.tscn; otherwise download pinned MIT sample")
    p.add_argument("--image", type=Path, help="local gBot.png")
    p.add_argument("--out", type=Path, default=Path("viewer/public/asset"))
    p.add_argument("--depth",type=float,default=0.16)
    a=p.parse_args()
    if not (0 <= a.depth <= 2): raise ValueError("Depth outside allowed range")
    scene = a.source.read_text() if a.source else download(BASE+"/player.tscn").decode()
    image = a.image.read_bytes() if a.image else download(BASE+"/gBot.png")
    doc = convert(scene,image,a.depth)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"character.json").write_text(json.dumps(doc,separators=(",",":")),encoding="utf-8")
    (a.out/"gBot.png").write_bytes(image)
    report={"source_revision":REV,"meshes":len(doc["meshes"]),"bones":len(doc["bones"]),
            "vertices":sum(len(x["vertices"]) for x in doc["meshes"]),
            "triangles":sum(len(x["indices"])//3 for x in doc["meshes"]),
            "source_texture_dimensions":[doc["width"],doc["height"]],
            "geometry_status":"PASS","animation_parity":"NOT_TESTED",
            "art_quality":"NOT_TESTED","full_3d_character":"NO"}
    (a.out/"import-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
