#!/usr/bin/env python3
"""Render reserved PMX angles (55, 67, 82) to evaluate semantic VDD interpolation.

These orthographic images are independent *3D camera renders*, not independently
painted 2D artwork. They are withheld from 45/90 proxy keyframe generation.
Requires the args of render-sonetto-structural-views.py.
"""
import hashlib, json, math
from pathlib import Path
base=Path(__file__).with_name('render-sonetto-structural-views.py').read_text()
anchor="manifest={'schema':'R1999-SONETTO-PMX-3D-STRUCTURAL-REF-V1'"
if anchor not in base:raise RuntimeError('Structural renderer initialization contract changed')
exec(compile(base.split(anchor)[0],str(Path(__file__).with_name('render-sonetto-structural-views.py')),'exec'),globals())
from PIL import Image
# Mask out clothing to match the semantic head-only keyframe render camera.
for mat in mesh.data.materials:
 if mat and mat.name.startswith('Body_') and mat.name!='Body_Skin':
  mat.use_nodes=True
  nodes=mat.node_tree.nodes;nodes.clear()
  out=nodes.new('ShaderNodeOutputMaterial')
  transparent=nodes.new('ShaderNodeBsdfTransparent')
  mat.node_tree.links.new(transparent.outputs['BSDF'],out.inputs['Surface'])
scene.cycles.transparent_max_bounces=64
angles=[55,67,82]
sources=[]
for angle in angles:
 theta=math.radians(angle)
 direction=Vector((math.sin(theta),-math.cos(theta),0))
 cam.location=head_target+direction*3
 cam.rotation_euler=(head_target-cam.location).to_track_quat('-Z','Y').to_euler()
 bpy.context.view_layer.update()
 original=DEST/f'holdout-yaw{angle:03d}-original.png'
 scene.render.filepath=str(original)
 bpy.ops.render.render(write_still=True)
 im=Image.open(original).convert('RGBA')
 im=im.resize((600,600),Image.Resampling.LANCZOS)
 view=Image.new('RGBA',(640,640))
 view.paste(im,(20,20))
 target=DEST/f'holdout-yaw{angle:03d}-head.png'
 view.save(target,optimize=True)
 source_sha=hashlib.sha256(target.read_bytes()).hexdigest()
 print('R1999_PMX_HOLDOUT_RENDER',angle,target.stat().st_size,source_sha,flush=True)
 sources.append({'yawDeg':angle,'file':target.name,'sha256':source_sha,
   'bytes':target.stat().st_size,'sourceRole':'third_party_3d_holdout','independent2DArt':False})
manifest={'schema':'R1999-PMX-HOLDOUT-3D-V1','source':'WTHN_Ross Sonetto PMX',
          'camera':'same orthographic geometry as 45 and 90 PMX semantic proxy',
          'angles':angles,'modelSourceSha256':'47438b89335e0363b98f0bd80bd99607e69ee9eae72f15142fec93d77a81b863',
          'independent2DArtCoverage':0,'holdoutViews':sources}
(DEST/'holdout-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('HOLDOUT_RENDER_PASS',len(sources))
