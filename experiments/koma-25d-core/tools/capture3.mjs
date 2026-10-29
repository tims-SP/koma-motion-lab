#!/usr/bin/env node
/** CORE-003: visibly diagnostic multi-view projection. Never auto-accept art. */
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {chromium} from '../viewer/node_modules/playwright/index.mjs';

const root=path.resolve(import.meta.dirname,'..');
const output=path.join(root,'out','core003');
const N=73;
for(const p of [output,path.join(output,'turn')])fs.mkdirSync(p,{recursive:true});
const server=spawn('node',['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','4179'],
  {cwd:path.join(root,'viewer'),stdio:['ignore','pipe','pipe']});
let outputLogs='';
server.stdout.on('data',d=>outputLogs+=d.toString());
server.stderr.on('data',d=>outputLogs+=d.toString());
let browser;
try{
  let serving=false;
  for(let i=0;i<80;i++){
    try{const r=await fetch('http://127.0.0.1:4179');if(r.ok){serving=true;break;}}catch{}
    await new Promise(resolve=>setTimeout(resolve,220));
  }
  if(!serving)throw Error('viewer startup failure: '+outputLogs.slice(-400));
  browser=await chromium.launch({headless:true,args:[
    '--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle',
    '--use-angle=swiftshader','--disable-dev-shm-usage'
  ]});
  const page=await browser.newPage({viewport:{width:960,height:540},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:4179/',{waitUntil:'networkidle'});
  await page.waitForFunction('window.__komaReady === true',{timeout:45000});
  const d=await page.evaluate(()=>window.__komaDiagnostics);
  if(d.appearanceProvenance!=='SYNTHETIC_DIAGNOSTIC_ONLY'){
    throw Error('Canary source mislabeled');
  }
  await page.evaluate(()=>window.__komaSetViewMode('source-front'));
  await page.evaluate(()=>window.__komaSetMotion({yaw:0}));
  await page.screenshot({path:path.join(output,'original_front_only.png')});
  await page.evaluate(()=>window.__komaSetViewMode('diagnostic'));
  await page.evaluate(()=>window.__komaSetMotion({yaw:0}));
  await page.screenshot({path:path.join(output,'front_with_shell.png')});
  for(let i=0;i<N;i++){
    const yaw=i/(N-1)*180;
    await page.evaluate(a=>window.__komaSetMotion({yaw:a}),yaw);
    await page.screenshot({path:path.join(output,'turn',String(i).padStart(4,'0')+'.png')});
  }
  for(const yaw of [45,90,135,180]){
    await page.evaluate(a=>window.__komaSetMotion({yaw:a}),yaw);
    await page.screenshot({path:path.join(output,'diagnostic_'+yaw+'.png')});
    await page.evaluate(()=>window.__komaSetViewMode('source-front'));
    await page.evaluate(a=>window.__komaSetMotion({yaw:a}),yaw);
    await page.screenshot({path:path.join(output,'no_shell_'+yaw+'.png')});
    await page.evaluate(()=>window.__komaSetViewMode('diagnostic'));
  }
  if(errors.length)throw Error('Browser errors: '+errors.join(' ; '));
  const data={status:'DIAGNOSTIC_CAPTURE_COMPLETE_NOT_ART_ACCEPTED',
    source:d,frames:N,angles:[0,45,90,135,180],
    viewRegistration:'CANARY_PLACEHOLDER_ONLY',
    frontSourceTexturePreserved:true,
    genuineSideArt:false,genuineBackArt:false,
    sourceNativeParity:'NOT_TESTED',animeQuality:'NOT_TESTED'};
  fs.writeFileSync(path.join(output,'capture.json'),JSON.stringify(data,null,2)+'\n');
  console.log('CORE003_CAPTURE_OK',JSON.stringify(data));
}finally{
  if(browser)await browser.close();
  server.kill('SIGTERM');
}
