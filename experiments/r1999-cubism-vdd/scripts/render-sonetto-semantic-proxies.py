#!/usr/bin/env python3
"""Generate 45/90 semantic RGBA proxy layers from a licensed PMX 3D reference.

Materials + head-space face-region classifiers create depth-visible pixels.
Each layer is identified as third_party_3d_proxy, never independent_art.
Requires Blender 4.0 + MMD Tools v4.0.0. Use the same arguments as
render-sonetto-structural-views.py.
"""
from pathlib import Path
import sys, json, hashlib, math

# Reuse the validated PMX import, material, camera and render initialization.
base = Path(__file__).with_name('render-sonetto-structural-views.py').read_text()
if "manifest={'schema':'R1999-SONETTO-PMX-3D-STRUCTURAL-REF-V1'" not in base:
    raise RuntimeError('Base structural renderer contract changed')
prefix = base.split("manifest={'schema':'R1999-SONETTO-PMX-3D-STRUCTURAL-REF-V1'")[0]
exec(compile(prefix, 'render-sonetto-structural-views.py', 'exec'), globals())

from PIL import Image
import collections
parts=['hair.back','face.skin','ear.near','hair.side','eye.near','nose','mouth','hair.front']
palettes=[(245,34,35),(238,195,156),(58,245,42),(171,42,243),
          (15,235,231),(236,21,172),(243,218,22),(25,91,249)]
all_names=parts+['body.extra']
palettes.append((20,20,20))
semantic_mats=[]
for i,(name,rgb) in enumerate(zip(all_names,palettes)):
    mat=bpy.data.materials.new('SEMANTIC_'+name)
    mat.diffuse_color=tuple(c/255 for c in rgb)+(1,)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    nodes.clear()
    out=nodes.new('ShaderNodeOutputMaterial')
    light=nodes.new('ShaderNodeEmission')
    light.inputs['Color'].default_value=tuple(c/255 for c in rgb)+(1,)
    light.inputs['Strength'].default_value=1
    mat.node_tree.links.new(light.outputs['Emission'],out.inputs['Surface'])
    semantic_mats.append(mat)

original_materials=list(mesh.data.materials)
# Isolate head/hair while keeping their internal geometry occlusions.
# Clothing surfaces are rendered transparent so long hair remains complete
# beneath the neck and cape, unlike a cropped whole-body screenshot.
for original in original_materials:
    if original and original.name.startswith('Body_') and original.name!='Body_Skin':
        original.use_nodes=True
        nodes=original.node_tree.nodes;nodes.clear()
        output=nodes.new('ShaderNodeOutputMaterial')
        transparent=nodes.new('ShaderNodeBsdfTransparent')
        original.node_tree.links.new(transparent.outputs['BSDF'],output.inputs['Surface'])
semantic_extra=semantic_mats[-1]
semantic_extra.node_tree.nodes.clear()
output=semantic_extra.node_tree.nodes.new('ShaderNodeOutputMaterial')
transparent=semantic_extra.node_tree.nodes.new('ShaderNodeBsdfTransparent')
semantic_extra.node_tree.links.new(transparent.outputs['BSDF'],output.inputs['Surface'])
scene.cycles.transparent_max_bounces=64
offset=len(original_materials)
for mat in semantic_mats:
    mesh.data.materials.append(mat)

centers=[]
original_ids=[]
partition_counts=collections.Counter()
for poly in mesh.data.polygons:
    mid=poly.material_index
    original_ids.append(mid)
    x,y,z=mesh.matrix_world@poly.center
    original_name=original_materials[mid].name if original_materials[mid] else ''
    if original_name=='Hair':
        if y > 0.015 or z < 1.285:
            semantic='hair.back'
        elif y < -0.045 and z > 1.455:
            semantic='hair.front'
        else:
            semantic='hair.side'
    elif original_name.startswith(('Hair_Ribbons','Hair_Metal')):
        semantic='hair.front'
    elif original_name=='Face':
        if x > 0.067 and y > -0.045 and 1.405 < z < 1.50:
            semantic='ear.near'
        elif abs(x)<0.028 and y < -0.082 and 1.405<z<1.468:
            semantic='nose'
        else:
            semantic='face.skin'
    elif original_name in ('Face_Eyes','Face_Eyebrows','Face_Exp','Face_Blush'):
        semantic='eye.near'
    elif original_name=='Face_Mouth':
        semantic='mouth'
    elif original_name=='Body_Skin':
        semantic='face.skin'
    else:
        semantic='body.extra'
    centers.append(semantic)
    partition_counts[semantic]+=1
print('CLASSIFIER_FACE_COUNTS',dict(partition_counts),flush=True)
if min(partition_counts.get(p,0) for p in parts)<8:
    raise AssertionError('Insufficient source polygons for some anatomical parts')

def convert_and_split(yaw,beauty_path,mask_path,features):
    src=Image.open(beauty_path).convert('RGBA')
    mask=Image.open(mask_path).convert('RGBA')
    # Fit the full source-frame into a fixed 640x640 transparent canvas,
    # preserving 20px margins to make bounds checks deterministic.
    canvas=640
    src=src.resize((600,600),Image.Resampling.LANCZOS)
    mask=mask.resize((600,600),Image.Resampling.NEAREST)
    img_src=Image.new('RGBA',(canvas,canvas))
    img_src.paste(src,(20,20))
    img_mask=Image.new('RGBA',(canvas,canvas))
    img_mask.paste(mask,(20,20))
    # Compare distance to the expected output palette with a maximum tolerance.
    # Cycles Standard color management is applied equally across categories.
    lookup=[]
    for rr,gg,bb in palettes:
        def srgb(v):
            return int(round(255 * (12.92*v if v<=0.0031308 else 1.055*(v**(1/2.4))-0.055)))
        lookup.append((srgb(rr/255),srgb(gg/255),srgb(bb/255)))
    rgba=img_src.load()
    seg=img_mask.load()
    output=[Image.new('RGBA',(canvas,canvas)) for p in parts]
    dest=[im.load() for im in output]
    counts=[0]*len(parts)
    for yy in range(20,620):
        for xx in range(20,620):
            r,g,b,a=seg[xx,yy]
            if a<=12:continue
            idx=min(range(len(lookup)),key=lambda i:
                    (r-lookup[i][0])**2+(g-lookup[i][1])**2+(b-lookup[i][2])**2)
            if idx>=len(parts):continue
            color=rgba[xx,yy]
            opacity=min(color[3],a)
            if opacity<12:continue
            dest[idx][xx,yy]=color[:3]+(opacity,)
            counts[idx]+=1
    # Keep the nose within the projected original 3D nose polygons.
    # This eliminates palette anti-aliasing bleed into the orange hair.
    nx0,ny0,nx1,ny1=features['nose']
    for yy in range(canvas):
        for xx in range(canvas):
            if xx<nx0-3 or xx>nx1+3 or yy<ny0-3 or yy>ny1+3:
                dest[parts.index('nose')][xx,yy]=(0,0,0,0)
    # In this PMX the mouth geometry is inside the face volume and its own
    # material is occluded. Isolate visible mouth-region pixels by projecting
    # that original PMX polygon region onto the fully shaded beauty frame.
    # The result is a visible-source-pixel proxy, not repainted mouth art.
    mx0,my0,mx1,my1=features['mouth']
    cx=(mx0+mx1)*.5;cy=(my0+my1)*.5
    rx=max(8,(mx1-mx0)*.48);ry=max(4,(my1-my0)*.72)
    for yy in range(max(20,int(cy-ry-2)),min(620,int(cy+ry+3))):
        for xx in range(max(20,int(cx-rx-2)),min(620,int(cx+rx+3))):
            distance=((xx-cx)/rx)**2+((yy-cy)/ry)**2
            if distance>=1:continue
            sr,sg,sb,sa=rgba[xx,yy]
            if sa<30:continue
            alpha=int(sa*min(1.0,max(0.0,(1-distance)*3.5)))
            if alpha<12:continue
            dest[parts.index('mouth')][xx,yy]=(sr,sg,sb,alpha)
            # Keep source pixels in a single semantic layer.
            dest[parts.index('face.skin')][xx,yy]=(0,0,0,0)
    counts=[sum(1 for a in image.getchannel('A').getdata() if a>0) for image in output]
    layers=[]
    for i,name in enumerate(parts):
        file=DEST/('yaw%03d_%s.png'%(yaw,name))
        output[i].save(file,optimize=True)
        alpha=output[i].getchannel('A')
        bbox=alpha.getbbox()
        layers.append({'yawDeg':yaw,'semanticId':name,'path':file.name,
              'role':'third_party_3d_proxy',
              'sourceId':'WTHN_Ross_Sonetto_PMX_v1.1',
              'sourceModelSha256':'47438b89335e0363b98f0bd80bd99607e69ee9eae72f15142fec93d77a81b863',
              'license':'noncommercial_personal_reference; no model data redistributed',
              'pixels':counts[i],
              'bbox':list(bbox) if bbox else None,
              'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
              'bytes':file.stat().st_size})
    return layers

manifest={'schema':'R1999-PMX-SEMANTIC-PROXY-V1','source':'WTHN_Ross Sonetto PMX',
          'sourceRole':'third_party_3d_proxy','independentArtCoverage':0,
          'renderer':'Blender Cycles CPU, material segmentation and planar pixel matching',
          'canvas':[640,640], 'requiredAngles':[45,90], 'parts':parts,
          'polygonCountByClass':dict(partition_counts),'layers':[]}
for yaw,vec in ((45,Vector((math.sin(math.pi/4),-math.cos(math.pi/4),0))),
                (90,Vector((1,0,0)))):
    cam.location=head_target+vec*3
    cam.rotation_euler=(head_target-cam.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    from bpy_extras.object_utils import world_to_camera_view
    features={}
    for sem in ('nose','ear.near','mouth','eye.near'):
        pts=[]
        for poly,tag in zip(mesh.data.polygons,centers):
            if tag!=sem:continue
            for idx in poly.vertices:
                proj=world_to_camera_view(scene,cam,mesh.matrix_world@mesh.data.vertices[idx].co)
                pts.append((20+600*proj.x,20+600*(1-proj.y)))
        if pts:
            features[sem]=[round(min(p[0] for p in pts),1),round(min(p[1] for p in pts),1),
                           round(max(p[0] for p in pts),1),round(max(p[1] for p in pts),1)]
    print('PROJECTED_FEATURE_BOUNDS',yaw,features,flush=True)
    beauty=DEST/('yaw%03d_beauty.png'%yaw)
    scene.render.filepath=str(beauty)
    bpy.ops.render.render(write_still=True)
    for poly,semantic in zip(mesh.data.polygons,centers):
        poly.material_index=offset+all_names.index(semantic)
    scene.render.filepath=str(DEST/('yaw%03d_semantic_id.png'%yaw))
    bpy.ops.render.render(write_still=True)
    # Revert before rendering the next beauty frame.
    for poly,mid in zip(mesh.data.polygons,original_ids):
        poly.material_index=mid
    layers=convert_and_split(yaw,beauty,Path(scene.render.filepath),features)
    manifest.setdefault('featureBounds',{})[str(yaw)]=features
    manifest['layers'].extend(layers)
    print('SEMANTIC_CAPTURE',yaw,[(x['semanticId'],x['pixels']) for x in layers],flush=True)
(DEST/'proxy-semantic-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('SEMANTIC_PROXY_RENDERED',len(manifest['layers']))
