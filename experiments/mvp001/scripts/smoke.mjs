import { chromium } from 'playwright';
import { spawn, execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync, statSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const project = process.cwd();
const out = resolve(project, 'out');
const frames = join(out, 'frames');
mkdirSync(frames, { recursive:true });

const server = spawn(process.execPath, [resolve('node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', '5173', '--strictPort'], {
  cwd: project, stdio:['ignore','pipe','pipe']
});
let serverLogs='';
for (const stream of [server.stdout, server.stderr]) {
  stream.on('data', d => { serverLogs+=String(d); });
}
let browser;
try {
  let ready=false;
  for (let retry=0;retry<50;retry++){
    if (server.exitCode!==null) throw new Error('Vite exited: '+serverLogs);
    try {
      const response=await fetch('http://127.0.0.1:5173');
      if(response.ok){ready=true;break;}
    }catch{}
    await new Promise(r=>setTimeout(r,300));
  }
  if(!ready) throw new Error('Preview server did not start: '+serverLogs);
  browser=await chromium.launch({headless:false, args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({ viewport:{width:720,height:440},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  await page.goto('http://127.0.0.1:5173', {waitUntil:'networkidle'});
  await page.waitForFunction(()=>typeof window.renderFrame==='function', {timeout:20000});
  const metadata=await page.evaluate(()=>window.m0Metadata);
  if(!metadata || metadata.partNames.length<20) throw new Error('Expected 20+ actual named mesh parts');
  const samples=[];
  for(let f=0;f<=24;f++){
    const sample=await page.evaluate(f=>window.renderFrame(f),f);
    samples.push(sample);
    if(f<24) {
      const filename=join(frames,'frame-'+String(f).padStart(3,'0')+'.png');
      await page.locator('#viewport').screenshot({path:filename});
      if(statSync(filename).size<1500) throw new Error('Screenshot unusually small: '+filename);
    }
  }
  if(errors.length) throw new Error('Browser runtime errors: '+errors.join('; '));
  if(samples[0].yawDeg!==0 || samples[24].yawDeg!==360) throw new Error('Incorrect angle endpoints');
  if(Math.abs(samples[0].viewMatrix[0]-samples[24].viewMatrix[0])>0.00001) throw new Error('Rotation loop seam mismatch');
  const rgbaSet=new Set(samples.slice(0,24).map(s=>s.sampleRGBA.join(',')));
  if(rgbaSet.size<2) throw new Error('All sample pixels identical: possible blank/failed rendering');
  execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-framerate','24','-i',join(frames,'frame-%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-r','24',join(out,'mvp001-m0-engineering-smoke.mp4')]);
  const movieBytes=statSync(join(out,'mvp001-m0-engineering-smoke.mp4')).size;
  if(movieBytes<3000) throw new Error('Encoded video unusually small');
  const report={
    phase:'M0',result:'PASS_INFRA_ONLY',animeQuality:'NOT_TESTED',fullBody360Quality:'NOT_TESTED',fullBodyAction:'NOT_TESTED',faceFX:'NOT_TESTED',
    frames:24, fps:24, resolution:'640x360',partCount:metadata.partNames.length,
    webglVersion:metadata.glVersion,renderer:metadata.renderer,rgbaVariants:rgbaSet.size,
    movieBytes,frame0:samples[0],frame24:samples[24],browserErrors:errors,
    message:'Procedural fixture tests Chromium WebGL layered mesh, deterministic seek, screenshots, ffmpeg. It does not prove any anime character quality or complete multi-view model.'
  };
  writeFileSync(join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
  writeFileSync(join(out,'summary.md'),`# MVP-001 M0 — PASS_INFRA_ONLY

- Chrome/WebGL: ${metadata.glVersion}
- Mesh part count: ${metadata.partNames.length}
- Screenshots: 24, PNG 640x360
- MP4: ${movieBytes} bytes, 24 frames at 24 fps
- 0/360 transform seam checked.
- **NOT TESTED**: multi-view art, facial fidelity, full-body IK, normal/SDF effects.
`);
  process.stdout.write(readFileSync(join(out,'summary.md'),'utf8'));
} finally {
  if(browser) await browser.close();
  server.kill('SIGTERM');
}
