#!/usr/bin/env node
/**
 * Capture an actual anime-styled CC0 model in 3D from 0–180 degrees.
 * These are multi-view SOURCE ART references, not final 2D reconstructed art.
 */
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {chromium} from '../viewer/node_modules/playwright/index.mjs';
const root=path.resolve(import.meta.dirname,'..');
const out=path.join(root,'out','core004'), frames=path.join(out,'reference');
fs.mkdirSync(frames,{recursive:true});
const proc=spawn('node',['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','4179'],
 {cwd:path.join(root,'viewer'),stdio:['ignore','pipe','pipe']});
let log='';
proc.stdout.on('data',x=>log+=x.toString());
proc.stderr.on('data',x=>log+=x.toString());
let browser;
try{
 let healthy=false;
 for(let n=0;n<70;n++){
  try{if((await fetch('http://127.0.0.1:4179/reference.html')).ok){healthy=true;break}}catch{}
  await new Promise(resolve=>setTimeout(resolve,250));
 }
 if(!healthy)throw Error('Server failed: '+log.slice(-700));
 browser=await chromium.launch({headless:true,args:[
  '--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle',
  '--use-angle=swiftshader','--disable-dev-shm-usage'
 ]});
 const page=await browser.newPage({viewport:{width:640,height:640},deviceScaleFactor:1});
 const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:4179/reference.html',{waitUntil:'networkidle'});
 await page.waitForFunction('window.__referenceReady===true || window.__referenceError!==undefined',{timeout:75000});
 const diagnostic=await page.evaluate(()=>({ready:window.__referenceReady,err:window.__referenceError,info:window.__referenceInfo}));
 if(!diagnostic.ready)throw Error('CC0 VRM render failure: '+diagnostic.err);
 for(let i=0;i<=72;i++){
  const yaw=i*2.5;
  await page.evaluate(angle=>window.__renderReference(angle),yaw);
  await page.screenshot({path:path.join(frames,String(i).padStart(4,'0')+'.png')});
 }
 if(errors.length)throw Error('WebGL error '+errors.join('; '));
 fs.writeFileSync(path.join(out,'source.json'),JSON.stringify({
  reference:diagnostic.info,
  frameCount:73,angleStep:2.5,angles:[0,45,90,135,180],
  license:'CC0 sample with official licensing check',
  sourceFile:'reference.vrm',
  sourceArtKind:'REAL_TEXTURED_3D_ANIME_REFERENCE',
  camera:'orthographic',original2DFromThisSource:'DERIVED_BY_RENDERING',
  multiViewRigConversion:'NOT_YET_PERFORMED'
 },null,2)+'\n');
 console.log('CORE004_REFERENCE_OK',JSON.stringify(diagnostic.info));
}finally{
 if(browser)await browser.close();
 proc.kill('SIGTERM');
}
