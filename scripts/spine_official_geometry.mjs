#!/usr/bin/env node
/** Spine 4.2 reference geometry. All coordinates remain in ephemeral CI runner.
 * This is an independent authoritative evaluator of the setup pose, including
 * Spine's transform/IK/path constraints and attachment metadata.
 */
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';

const [sourceJson, atlasFile, outFile] = process.argv.slice(2);
const entry = process.env.SPINE_CORE_ENTRY;
if (!sourceJson || !atlasFile || !outFile || !entry) throw Error('Missing inputs');
const spine = await import(pathToFileURL(entry).href);
const atlas = new spine.TextureAtlas(fs.readFileSync(atlasFile,'utf8'));
const loader = new spine.AtlasAttachmentLoader(atlas);
const reader = new spine.SkeletonJson(loader);
const data = reader.readSkeletonData(JSON.parse(fs.readFileSync(sourceJson,'utf8')));
const skeleton = new spine.Skeleton(data);
skeleton.setToSetupPose();
skeleton.updateWorldTransform();
const result = {spineVersion:data.version,bones:data.bones.length,
  slots:data.slots.length,atlasRegions:atlas.regions.length,
  mesh:{},regions:[],other:[],drawOrder:[]};
for(const slot of skeleton.drawOrder) {
  const attachment=slot.getAttachment();
  const name=slot.data.name;
  result.drawOrder.push(name);
  if (!attachment) {
    result.other.push({slot:name,type:'null'});
  } else if (attachment instanceof spine.MeshAttachment) {
    const verts=new Float32Array(attachment.worldVerticesLength);
    attachment.computeWorldVertices(slot,0,verts.length,verts,0,2);
    result.mesh[name]={
      attachment:attachment.name,
      path:attachment.path,
      region:attachment.region?.name,
      weighted:!!attachment.bones,
      vertices:[...verts],
      uvs:[...attachment.uvs],
      triangles:attachment.triangles.length
    };
  } else if(attachment instanceof spine.RegionAttachment) {
    result.regions.push(name);
  } else {
    result.other.push({slot:name,type:attachment.constructor.name});
  }
}
fs.writeFileSync(outFile,JSON.stringify(result));
console.log(JSON.stringify({
  status:'SPINE_4_2_REFERENCE_EVALUATED',
  spineVersion:result.spineVersion,bones:result.bones,slots:result.slots,
  activeMeshSlots:Object.keys(result.mesh).length,
  activeRegionSlots:result.regions.length,
  activeOtherSlots:result.other.length,
  atlasRegions:result.atlasRegions
}));
