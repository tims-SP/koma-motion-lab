"""Reproducible headless orthographic views of a privately licensed PMX reference.

Run inside Blender 4.0+ with MMD Tools. Output retains model-derived provenance
and must not be counted as independently authored 2D artwork.
"""
import bpy, sys, math, os, json, logging, hashlib
from pathlib import Path
from mathutils import Vector
from math import sin, cos, radians
logging.disable(logging.INFO)

import argparse
parser=argparse.ArgumentParser(description='Render structural 360-degree reference from an authorized MMD PMX')
parser.add_argument('--model-file',type=Path,required=True)
parser.add_argument('--mmd-tools-path',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
PMX=args.model_file.resolve()
SRC=PMX.parent
DEST=args.output_dir.resolve()
if not PMX.is_file():raise FileNotFoundError(PMX)
if not (args.mmd_tools_path/'mmd_tools/__init__.py').is_file():raise FileNotFoundError(args.mmd_tools_path)

DEST.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(args.mmd_tools_path.resolve()))
import mmd_tools
mmd_tools.register()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mmd_tools.import_model(filepath=str(PMX),types={'MESH','ARMATURE','MORPHS'},scale=0.08)
mesh=next(o for o in bpy.data.objects if o.type=='MESH')
bpy.context.view_layer.update()
corners=[mesh.matrix_world@Vector(v) for v in mesh.bound_box]
minimum=Vector(tuple(min(p[j] for p in corners) for j in range(3)))
maximum=Vector(tuple(max(p[j] for p in corners) for j in range(3)))
center=(minimum+maximum)*0.5
dimensions=maximum-minimum
print('MODEL_BBOX',list(minimum),list(maximum),'DIMENSIONS',list(dimensions))
print('MATERIALS',len(mesh.data.materials),[(m.name if m else None) for m in mesh.data.materials][:60])
print('TEXTURE_IMAGES',len(bpy.data.images),[(img.name,img.filepath) for img in bpy.data.images][:25])
images_fixed=[]
for im in bpy.data.images:
 try:
  if im.source!='FILE':continue
  current=Path(bpy.path.abspath(im.filepath))
  if current.is_file():continue
  basename=current.name.replace('\\','/')
  # basename from a PMX path can be Windows-delimited.
  basename=basename.rsplit('/',1)[-1]
  candidates=[x for x in SRC.rglob('*') if x.is_file() and x.name.lower()==basename.lower()]
  if candidates:
   im.filepath=str(candidates[0])
   im.reload()
   images_fixed.append(im.name)
 except Exception as e:print('TEXTURE_RELINK_WARN',im.name,str(e))
print('TEXTURE_RELINKED',images_fixed)
# Render the PMX base-color texture at a controlled brightness. The MMD FX
# sphere-map/shadow nodes are tailored to MMD and can turn hair black in Cycles.
mapping={
 'Face':'Face_base.png','Hair_HL':'Hair_HL_base.png','Hair':'Hair_base.png',
 'Body_Metal':'Boby_Metal_base.png','Body':'Body_base.png',
}
def base_image_for(mat):
 name=mat.name
 for prefix,img in mapping.items():
  if name.startswith(prefix):
   return bpy.data.images.get(img)
 return None
for mat in mesh.data.materials:
 if mat is None:continue
 mat.use_nodes=True
 mat.node_tree.nodes.clear()
 n=mat.node_tree.nodes
 out=n.new('ShaderNodeOutputMaterial')
 em=n.new('ShaderNodeEmission')
 em.inputs['Strength'].default_value=1.0
 tex_img=base_image_for(mat)
 if tex_img is None:
  em.inputs['Color'].default_value=mat.diffuse_color
  mat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
  continue
 tex=n.new('ShaderNodeTexImage');tex.image=tex_img;tex.interpolation='Linear'
 mat.node_tree.links.new(tex.outputs['Color'],em.inputs['Color'])
 trans=n.new('ShaderNodeBsdfTransparent')
 mix=n.new('ShaderNodeMixShader')
 mat.node_tree.links.new(tex.outputs['Alpha'],mix.inputs[0])
 mat.node_tree.links.new(trans.outputs[0],mix.inputs[1])
 mat.node_tree.links.new(em.outputs[0],mix.inputs[2])
 mat.node_tree.links.new(mix.outputs[0],out.inputs['Surface'])
 print('FLAT_MATERIAL',mat.name,tex_img.name)



# The PMX hair-highlight shell is coplanar with the base hair material.
# Render the textured base layer for transparent-turnaround structure reference.
# This modifies only the in-memory render copy of the PMX mesh.
import bmesh
bm=bmesh.new();bm.from_mesh(mesh.data)
highlight_index=next((i for i,m in enumerate(mesh.data.materials) if m and m.name=='Hair_HL'),None)
if highlight_index is not None:
 doomed=[f for f in bm.faces if f.material_index==highlight_index]
 print('HIGHLIGHT_OVERLAY_FACES',len(doomed))
 bmesh.ops.delete(bm,geom=doomed,context='FACES')
bm.to_mesh(mesh.data);mesh.data.update();bm.free()

scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=4
scene.cycles.use_denoising=False
scene.render.resolution_x=768
scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=True
scene.view_settings.view_transform='Standard'
scene.view_settings.look='Medium High Contrast'
scene.view_settings.exposure=0
scene.render.image_settings.color_depth='8'
scene.world.color=(0.7,0.7,0.7)
scene.camera=None

def light(name,xyz,power,size):
 data=bpy.data.lights.new(name,'AREA')
 obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
 obj.location=xyz
 direction=Vector((0,0,center.z))-obj.location
 obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
 data.energy=power
 data.shape='DISK'
 data.size=size

light('Key',(-2.0,-2.5,3.3),900,4.0)
light('Fill',(2.0,1.0,2.6),600,4.0)
cam_data=bpy.data.cameras.new('OrtCamera')
cam=bpy.data.objects.new('OrtCamera',cam_data)
bpy.context.collection.objects.link(cam)
scene.camera=cam
cam_data.type='ORTHO'

head_target=Vector((center.x,center.y,minimum.z+0.77*dimensions.z))
head_scale=max(dimensions.x*0.78, dimensions.z*0.40)
head_scale=max(head_scale,0.75)
print('HEAD_TARGET',list(head_target),'HEAD_ORTHO_SCALE',head_scale)
cam_data.ortho_scale=head_scale
cam_data.lens=55

manifest={'schema':'R1999-SONETTO-PMX-3D-STRUCTURAL-REF-V1',
'usage':'private 3D structural view references; not independent 2D VDD authored art',
'license':'WTHN_Ross PMX v1.1 English/Japanese ReadMe (private noncommercial reference, creator credit required)',
'inputModel':str(PMX),'renderEngine':scene.render.engine,
'meshVertices':len(mesh.data.vertices),'meshPolygons':len(mesh.data.polygons),
'meshMaterials':len(mesh.data.materials),'geometryBoundingBox':[list(minimum),list(maximum)],
'headTarget':list(head_target),'cameraScale':head_scale,'views':[]}
for heading, direction in [
 ('yaw000_front',Vector((0,-1,0))),
 ('yaw045_three_quarter',Vector((math.sin(math.pi/4),-math.cos(math.pi/4),0))),
 ('yaw090_profile',Vector((1,0,0))),
 ('yaw135_back_three_quarter',Vector((math.sin(math.pi*3/4),-math.cos(math.pi*3/4),0))),
 ('yaw180_back',Vector((0,1,0))),
 ('yaw225_back_three_quarter',Vector((math.sin(math.pi*5/4),-math.cos(math.pi*5/4),0))),
 ('yaw270_profile',Vector((-1,0,0))),
 ('yaw315_three_quarter',Vector((math.sin(math.pi*7/4),-math.cos(math.pi*7/4),0))),
]:
 cam.location=head_target+direction*3
 vec=head_target-cam.location
 cam.rotation_euler=vec.to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(DEST/(heading+'.png'))
 bpy.ops.render.render(write_still=True)
 f=Path(scene.render.filepath)
 sha=hashlib.sha256(f.read_bytes()).hexdigest()
 print('RENDERED_VIEW',heading,f.stat().st_size,sha)
 manifest['views'].append({'viewId':heading,'cameraOffset':list(direction),'file':str(f),
                          'sizeBytes':f.stat().st_size,'sha256':sha,'provenance':'third_party_3d_render_reference'})
(DEST/'reference-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
print('REFERENCE_MODEL_RENDER_COMPLETE')
