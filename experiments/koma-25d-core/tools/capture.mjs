#!/usr/bin/env node
/** Render real MIT sample using Three.js + Chromium. Fail closed on blanks/errors. */
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from '../viewer/node_modules/playwright/index.mjs';
const root=path.resolve(import.meta.dirname,'..');
const dir=path.join(root,'out');
const frames=path.join(dir,'frames');
fs.mkdirSync(frames,{recursive:true});
const server=spawn('node',['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','4179'],
  {cwd:path.join(root,'viewer'),stdio:['ignore','pipe','pipe']});
let serverLogs='';
server.stderr.on('data',b=>{serverLogs+=b.toString();});
server.stdout.on('data',b=>{serverLogs+=b.toString();});
async function ready(){
  for(let i=0;i<60;i++){
    try{const r=await fetch('http://127.0.0.1:4179');if(r.ok)return;}catch{}
    await new Promise(r=>setTimeout(r,350));
  }
  throw Error('Vite not responding: '+serverLogs.slice(-500));
}
let browser;
try{
  await ready();
  browser=await chromium.launch({headless:true,args:[
    '--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader',
    '--disable-dev-shm-usage'
  ]});
  const page=await browser.newPage({viewport:{width:960,height:540},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:4179/',{waitUntil:'networkidle'});
  await page.waitForFunction('window.__komaReady === true',{timeout:45000});
  const diagnostics=await page.evaluate(()=>window.__komaDiagnostics);
  if(diagnostics.meshes<3||diagnostics.verts<20)throw Error('Incomplete source geometry');
  const N=48;
  for(let i=0;i<N;i++){
    const angle=(i/(N-1))*90;
    await page.evaluate(a=>window.__komaSetAngle(a),angle);
    await page.screenshot({path:path.join(frames,String(i).padStart(4,'0')+'.png')});
  }
  if(errors.length)throw Error('Browser errors: '+errors.join('; '));
  fs.writeFileSync(path.join(dir,'capture.json'),JSON.stringify({
    status:'RENDERED_NOT_ART_ACCEPTED',frames:N,
    angles:[0,45,90],source:diagnostics,playwright_errors:errors,
    reference_2d_parity:'NOT_TESTED',anime_quality:'NOT_TESTED',
    full_3d_body:'NOT_SUPPORTED',runtime_animation_parity:'NOT_TESTED'
  },null,2));
  console.log('CAPTURE_OK',JSON.stringify(diagnostics));
}finally{
  if(browser)await browser.close();
  server.kill('SIGTERM');
}
