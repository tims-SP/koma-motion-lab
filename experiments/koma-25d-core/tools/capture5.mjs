#!/usr/bin/env node
/** Capture real visually-derived 3D surface vs naive extrusion in Chromium. */
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {chromium} from '../viewer/node_modules/playwright/index.mjs';
const root=path.resolve(import.meta.dirname,'..');
const output=path.join(root,'out','core005');
const modes=['visual_hull','fixed_extrusion'];
for(const name of modes)fs.mkdirSync(path.join(output,name),{recursive:true});
const server=spawn('node',['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','4179'],
  {cwd:path.join(root,'viewer'),stdio:['ignore','pipe','pipe']});
let logs='';
server.stdout.on('data',c=>logs+=c.toString());
server.stderr.on('data',c=>logs+=c.toString());
let browser;
try{
 let ready=false;
 for(let attempt=0;attempt<70;attempt++){
  try{if((await fetch('http://127.0.0.1:4179/hull.html')).ok){ready=true;break;}}catch{}
  await new Promise(r=>setTimeout(r,200));
 }
 if(!ready)throw Error('Vite server failed '+logs.slice(-300));
 browser=await chromium.launch({headless:true,args:[
   '--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle',
   '--use-angle=swiftshader','--disable-dev-shm-usage'
 ]});
 const page=await browser.newPage({viewport:{width:640,height:640},deviceScaleFactor:1});
 const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('console',e=>{if(e.type()==='error')errors.push(e.text())});
 await page.goto('http://127.0.0.1:4179/hull.html',{waitUntil:'networkidle'});
 await page.waitForFunction('window.__hullReady===true || window.__hullError!==undefined',{timeout:55000});
 const info=await page.evaluate(()=>({ready:window.__hullReady,error:window.__hullError,model:window.__hullInfo}));
 if(!info.ready)throw Error('3D hull setup error '+info.error);
 if(info.model.source3DMeshUsed!==false)throw Error('Original VRM mesh leaked into reconstruction');
 for(const name of modes){
  for(let i=0;i<=72;i++){
   const yaw=i*2.5;
   await page.evaluate(pose=>window.__hullSetPose(pose),{name,yaw});
   await page.screenshot({path:path.join(output,name,String(i).padStart(4,'0')+'.png')});
  }
 }
 if(errors.length)throw Error('Three.js browser warnings/errors: '+errors.slice(0,8).join('; '));
 const capture={status:'RENDERED_NOT_ART_ACCEPTED',frame_count:73,source_views:[0,90,180],
   algorithms:modes,rig:'NONE_STATIC_HULL',provenance:info.model,
   facial_registration:'SHARED_WORLD_PROJECTED_TEXTURES_ONLY',
   original2dLayeredLive2D:'NO',animeQuality:'NOT_TESTED'};
 fs.writeFileSync(path.join(output,'capture.json'),JSON.stringify(capture,null,2)+'\n');
 console.log('CORE005_CAPTURE_OK',JSON.stringify(capture));
}finally{
 if(browser)await browser.close();
 server.kill('SIGTERM');
}
