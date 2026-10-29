#!/usr/bin/env node
/** CORE-006 real MIT Godot 2D rig: exact front-pixel mode, head yaw and elbow. */
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {chromium} from '../viewer/node_modules/playwright/index.mjs';

const root=path.resolve(import.meta.dirname,'..');
const out=path.join(root,'out','core006');
const scenarios=[
 {name:'head_yaw',opts:i=>({yaw:0,headYaw:38*Math.sin(Math.PI*i/47)})},
 {name:'elbow_bend',opts:i=>({yaw:25,elbow:64*Math.sin(Math.PI*i/47)})},
 {name:'camera_turn',opts:i=>({yaw:55*i/47})}
];
for(const s of scenarios)fs.mkdirSync(path.join(out,s.name),{recursive:true});
const server=spawn('node',['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','4179'],
  {cwd:path.join(root,'viewer'),stdio:['ignore','pipe','pipe']});
let logs='';
server.stdout.on('data',b=>logs+=b.toString());
server.stderr.on('data',b=>logs+=b.toString());
let browser;
try{
 let ok=false;
 for(let i=0;i<80;i++){
   try{if((await fetch('http://127.0.0.1:4179')).ok){ok=true;break;}}catch{}
   await new Promise(r=>setTimeout(r,250));
 }
 if(!ok)throw Error('Vite startup error '+logs.slice(-300));
 browser=await chromium.launch({headless:true,args:[
   '--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle',
   '--use-angle=swiftshader','--disable-dev-shm-usage'
 ]});
 const page=await browser.newPage({viewport:{width:960,height:540},deviceScaleFactor:1});
 const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:4179/',{waitUntil:'networkidle'});
 await page.waitForFunction('window.__komaReady===true || window.__komaError!==undefined',{timeout:45000});
 const initial=await page.evaluate(()=>({ready:window.__komaReady,error:window.__komaError,
   contract:window.__komaPartContract,diagnostics:window.__komaDiagnostics}));
 if(!initial.ready)throw Error('Koma rig did not initialize '+initial.error);
 if(!initial.contract || Object.keys(initial.contract.part_shells).length!==4)
   throw Error('Missing original part-shell conversion contract');

 await page.evaluate(()=>{
   window.__komaSetPartMode('source-front');
   window.__komaSetMotion({yaw:0});
 });
 await page.screenshot({path:path.join(out,'source_front.png')});
 await page.evaluate(()=>{
   window.__komaSetPartMode('part-shell');
   window.__komaSetMotion({yaw:0});
 });
 await page.screenshot({path:path.join(out,'part_front.png')});
 for(const scenario of scenarios){
   await page.evaluate(()=>window.__komaSetPartMode('part-shell'));
   for(let i=0;i<48;i++){
     await page.evaluate(p=>window.__komaSetMotion(p),scenario.opts(i));
     await page.screenshot({path:path.join(out,scenario.name,String(i).padStart(4,'0')+'.png')});
   }
 }
 if(errors.length)throw Error('Browser errors: '+errors.join('; '));
 const info={status:'RENDERED_AWAITING_INDEPENDENT_QA',
   original_source:'MIT Godot GBot Polygon2D/UV/Bone2D',
   scenarios:scenarios.map(s=>s.name),frames:48,
   metadata:initial,source2DReferencePixelParity:'NOT_TESTED_WITH_GODOT',
   sourceFrontVsPartFront:'TO_BE_VERIFIED',sideArtwork:'DIAGNOSTIC_ONLY',
   animeVisualQuality:'NOT_ACCEPTED'};
 fs.writeFileSync(path.join(out,'capture.json'),JSON.stringify(info,null,2)+'\n');
 console.log('CORE006_CAPTURE_OK',JSON.stringify(initial.diagnostics));
}finally{
 if(browser)await browser.close();
 server.kill('SIGTERM');
}
