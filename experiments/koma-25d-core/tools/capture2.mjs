#!/usr/bin/env node
/** CORE-002: isolate camera yaw from source planar clip and true 3D arm pose. */
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from '../viewer/node_modules/playwright/index.mjs';

const root=path.resolve(import.meta.dirname,'..');
const base=path.join(root,'out','core002');
const N=48;
fs.mkdirSync(base,{recursive:true});
const server=spawn('node',['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','4179'],
  {cwd:path.join(root,'viewer'),stdio:['ignore','pipe','pipe']});
let logs='';
server.stdout.on('data',b=>logs+=b.toString());
server.stderr.on('data',b=>logs+=b.toString());
let browser;
try {
  let ok=false;
  for(let i=0;i<80;i++){
    try{const r=await fetch('http://127.0.0.1:4179/');if(r.ok){ok=true;break;}}catch{}
    await new Promise(r=>setTimeout(r,250));
  }
  if(!ok)throw new Error('Server did not start: '+logs.slice(-450));
  browser=await chromium.launch({headless:true,args:[
    '--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle',
    '--use-angle=swiftshader','--disable-dev-shm-usage'
  ]});
  const page=await browser.newPage({viewport:{width:960,height:540},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:4179/',{waitUntil:'networkidle'});
  await page.waitForFunction('window.__komaReady===true',{timeout:45000});
  const diagnostics=await page.evaluate(()=>window.__komaDiagnostics);
  if(!diagnostics.clips.includes('walk'))throw Error('Godot source walk clip not found');
  const scenarios=[
    {name:'yaw', pose:i=>({yaw:i/(N-1)*90})},
    {name:'walk',pose:i=>({yaw:0,clip:'walk',time:2.4*i/(N-1)})},
    {name:'reach',pose:i=>({yaw:25,clip:'idle',time:0.3,reach:(1-Math.cos(2*Math.PI*i/(N-1)))/2})},
  ];
  for(const scenario of scenarios){
    const out=path.join(base,scenario.name);
    fs.mkdirSync(out,{recursive:true});
    for(let i=0;i<N;i++){
      const opts=scenario.pose(i);
      await page.evaluate(v=>window.__komaSetMotion(v),opts);
      await page.screenshot({path:path.join(out,String(i).padStart(4,'0')+'.png')});
    }
  }
  if(errors.length)throw Error('Browser page exceptions: '+errors.join(' | '));
  const report={
    status:'CAPTURED_AWAITING_QA',framesPerScenario:N,
    scenarios:scenarios.map(s=>s.name),source:diagnostics,
    source_clip_sampling:'LINEAR_APPROXIMATION',
    motion_skinning:'GPU_SkinnedMesh',
    source_reference_pixel_parity:'NOT_TESTED',
    true_3d_rig:'PARTIAL_SINGLE_LIMB',
    side_back_original_art:'NOT_AVAILABLE',
    anime_quality:'NOT_TESTED',
    browser_errors:errors
  };
  fs.writeFileSync(path.join(base,'capture.json'),JSON.stringify(report,null,2)+'\n');
  console.log('CORE002_CAPTURE_OK',JSON.stringify(report));
}finally {
  if(browser)await browser.close();
  server.kill('SIGTERM');
}
