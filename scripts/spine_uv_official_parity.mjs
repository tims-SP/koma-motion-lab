#!/usr/bin/env node
/** Independent atlas-UV reference: official @esotericsoftware/spine-core 4.2.
 *  Purely numerical verification; no original texture data is emitted.
 */
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';

const [atlasPath, pythonExpected] = process.argv.slice(2);
const entry = process.env.SPINE_CORE_ENTRY;
if (!entry || !atlasPath || !pythonExpected) throw Error('Args: atlasPath expectedUV.json; SPINE_CORE_ENTRY');
const official = await import(pathToFileURL(entry).href);
const atlas = new official.TextureAtlas(fs.readFileSync(atlasPath, 'utf8'));
const expected = JSON.parse(fs.readFileSync(pythonExpected, 'utf8'));
let maxError = 0, tested = 0;
const mismatched = [];
for (const [name, vectors] of Object.entries(expected.regions)) {
  const region = atlas.findRegion(name);
  if (!region) throw Error('Official runtime missing region ' + name);
  const mesh = new official.MeshAttachment('audit-' + name, name);
  mesh.region = region;
  mesh.regionUVs = [0,0, 0.5,0.5, 1,1];
  mesh.updateRegion();
  for (let k=0;k<mesh.uvs.length;k++) {
    const got=Number(mesh.uvs[k]);
    const wanted=Number(vectors[Math.floor(k/2)][k%2]);
    const error=Math.abs(got-wanted);
    maxError=Math.max(maxError,error);
    tested++;
    if (error>1e-5 && mismatched.length<15) mismatched.push({name,index:k,error,got,wanted});
  }
}
const result={spineRuntime:'@esotericsoftware/spine-core 4.2.120',
  checkedAtlasRegions:Object.keys(expected.regions).length,
  checkedCoordinates:tested,maxAbsError:maxError,
  status:mismatched.length?'FAIL':'PASS',
  mismatches:mismatched};
console.log(JSON.stringify(result));
if (result.status!=='PASS') process.exit(1);
