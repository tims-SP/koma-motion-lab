#!/usr/bin/env python3
"""CORE-005: front + true side silhouettes -> a 3D image-space visual hull.

Ground-truth views were rendered from ONE licensed CC0 anime VRM.
Inputs here are *only PNG views*: no original VRM mesh is read/used by this
geometry builder. Baseline = constant-depth extrusion of the same front view.
Candidate = intersection of calibrated front and side silhouette volumes.

Reference theory: Laurentini (1994) visual hull, voxel intersection;
marching_cubes is standard scikit-image, not a custom geometry engine.
Limitations: no rig, no part labels, concavities/hair topology unknown.
"""
from __future__ import annotations
import json, math, shutil
from pathlib import Path
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter, distance_transform_edt
from skimage.measure import marching_cubes
import trimesh
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"out"/"core005"
ASSETS=ROOT/"viewer"/"public"/"asset"
SRC=ROOT/"out"/"core004"/"reference"
GRID=(120,104,104)  # image Y, front X, side Z
BG=np.array([239,241,245],dtype=np.int16)

def mask_image(index):
    frame=cv2.imread(str(SRC/f"{index:04d}.png"),cv2.IMREAD_COLOR)
    if frame is None or frame.shape!=(640,640,3):
        raise RuntimeError(f"Missing actual rendered source view: {index}")
    rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB).astype(np.int16)
    delta=np.max(np.abs(rgb-BG),axis=2)
    fg=np.uint8(delta>22)
    fg=cv2.morphologyEx(fg,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    if fg.sum()<15000:raise RuntimeError(f"Almost blank {index}: {fg.sum()}")
    return fg

def occupancy_to_mesh(raw:np.ndarray,name):
    # Smoothed union-of-voxels surface, not a high-resolution exact model.
    smooth=gaussian_filter(raw.astype(np.float32),sigma=0.65)
    verts,faces,_,_=marching_cubes(smooth,level=0.45,allow_degenerate=False)
    ny,nx,nz=raw.shape
    # Three.js camera front is at -Z, right in screenshot means -X;
    # camera at +X for the profile, right in screenshot means -Z.
    x=(0.5-verts[:,1]/(nx-1))*2.0
    y=(0.5-verts[:,0]/(ny-1))*2.0
    z=(0.5-verts[:,2]/(nz-1))*2.0
    positions=np.stack((x,y,z),axis=1)
    tm=trimesh.Trimesh(vertices=positions,faces=faces,process=False)
    # No color/UV baked into GLB; appearance is independently projected.
    tm.fix_normals()
    tm.export(ASSETS/f"{name}.glb")
    return {
        "vertices":int(len(positions)),"triangles":int(len(faces)),
        "bbox":np.stack((positions.min(axis=0),positions.max(axis=0))).tolist(),
        "watertight":bool(tm.is_watertight),
        "volume_voxel_count":int(raw.sum())
    }

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    ASSETS.mkdir(parents=True,exist_ok=True)
    masks={}
    for key,idx in (("front",0),("side",36),("back",72)):
        masks[key]=mask_image(idx)
        shutil.copyfile(SRC/f"{idx:04d}.png",ASSETS/f"{key}.png")
    # Standard UV texture atlas eliminates fragile custom shader sampling.
    # Three image areas share a single well-tested MeshBasicMaterial texture.
    atlas=Image.new("RGB",(640*3,640))
    for slot,name in enumerate(("front","side","back")):
        original=np.asarray(Image.open(ASSETS/(name+".png")).convert("RGB"))
        foreground=np.max(np.abs(original.astype(np.int16)-BG),axis=2)>22
        if foreground.sum()<15000:raise ValueError("Not enough foreground pixels to pad "+name)
        # UV projection can sample just outside a silhouette at joints/sidewalls.
        # Use nearest-source-foreground extension, the standard texture border
        # padding principle. This does NOT reconstruct real hidden colors.
        missing=~foreground
        near=distance_transform_edt(missing,return_distances=False,return_indices=True)
        filled=original.copy()
        filled[missing]=original[near[0][missing],near[1][missing]]
        atlas.paste(Image.fromarray(filled,"RGB"),(slot*640,0))
    atlas.save(ASSETS/"atlas.png")
    ny,nx,nz=GRID
    f=cv2.resize(masks["front"],(nx,ny),interpolation=cv2.INTER_NEAREST)>0
    s=cv2.resize(masks["side"],(nz,ny),interpolation=cv2.INTER_NEAREST)>0
    # In a visual hull each voxel must appear inside both projected silhouettes.
    constrained=f[:,:,None]&s[:,None,:]
    # Naive comparison: same original front art, constant depth independent of y.
    zcoords=np.linspace(-1,1,nz)
    naive=f[:,:,None]&((np.abs(zcoords)<0.15)[None,None,:])
    naive=np.broadcast_to(naive,constrained.shape).copy()
    constrained=np.ascontiguousarray(constrained)
    baseline=np.ascontiguousarray(naive)
    results={
        "visual_hull":occupancy_to_mesh(constrained,"visual_hull"),
        "fixed_extrusion":occupancy_to_mesh(baseline,"fixed_extrusion")
    }
    (ASSETS/"hull_meta.json").write_text(json.dumps({
        "schema":"koma-shape-from-2d-views/1",
        "input_kind":"RENDERED_2D_IMAGE_VIEWS_ONLY",
        "input_angles":{"front":0,"side":90,"back":180},
        "reference_source_kind":"SEPARATE_GROUND_TRUTH_3D_CC0",
        "source_art_is_original_layered_live2d":False,
        "geometry_algorithm":"binary_silhouette_intersection_visual_hull",
        "source_reconstruction_uses_original_3d_mesh":False,
        "grid_yxz":GRID,"assets":results,
        "rig":"ABSENT","texture_semantics":"world-space orthographic projection",
        "atlas_padding":"NEAREST_SOURCE_FOREGROUND_NOT_HIDDEN_RECONSTRUCTION",
        "notes":["Static character only, no 3D skeleton/weights",
                 "This experiment does not solve missing views",
                 "2D projections are from matching original character"]
    },indent=2)+"\n")
    print("CORE005_GEOMETRY",json.dumps(results,indent=2))
if __name__=="__main__":main()
