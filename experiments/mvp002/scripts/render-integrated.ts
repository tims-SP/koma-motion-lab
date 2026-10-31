import { chromium } from 'playwright';
import { spawn,execFileSync } from 'node:child_process';
import { mkdirSync,statSync,writeFileSync } from 'node:fs';
import { resolve,join } from 'node:path';

type FrameStats={
  frame:number;time:number;yaw:number;headLocalYaw:number;
  partCount:number;keyViewCount:number;artMeshCount:number;
  ikError:number;handMinusTorsoDepth:number;armLocalYaw:number;
  lightAngle:number;shadowOffset:number;blink:number;
  targetX:number;handX:number;
};
declare global {interface Window {
 renderIntegrated:(frame:number,total:number)=>FrameStats;
 integratedInfo:Record<string,unknown>;
}}
const out=resolve('out/integrated');
mkdirSync(out,{recursive:true});
const server=spawn(process.execPath,[resolve('node_modules/vite/bin/vite.js'),
 '--host','127.0.0.1','--port','5176','--strictPort'],{stdio:['ignore','pipe','pipe']});
let logs='';
server.stdout.on('data',b=>logs+=b.toString());
server.stderr.on('data',b=>logs+=b.toString());
let browser:Awaited<ReturnType<typeof chromium.launch>>|undefined;
const frames=144;
try{
 let online=false;
 for(let i=0;i<90;i++){
   try{const x=await fetch('http://127.0.0.1:5176/integrated.html');if(x.ok){online=true;break;}}catch{}
   if(server.exitCode!==null)throw Error('vite died: '+logs);
   await new Promise(r=>setTimeout(r,250));
 }
 if(!online)throw Error('vite unavailable: '+logs);
 browser=await chromium.launch({headless:false,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1050,height:770},deviceScaleFactor:1});
 const errors:string[]=[];
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('http://127.0.0.1:5176/integrated.html',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>typeof window.renderIntegrated==='function');
 const info=await page.evaluate(()=>window.integratedInfo);
 if(Number(info.parts)!==12||Number(info.views)!==3)throw Error('Part/view contract failed');
 const meta:FrameStats[]=[];
 const sampleFrames=[0,8,16,24,32,40,48,56,68,80,88,100,112,128,143];
 const screenshots:string[]=[];
 for(let f=0;f<frames;f++){
  const state=await page.evaluate(({frame,total})=>window.renderIntegrated(frame,total),{frame:f,total:frames});
  if(Object.values(state).some(v=>typeof v==='number'&&!Number.isFinite(v)))throw Error('Non-finite state frame '+f);
  if(state.partCount!==12||state.artMeshCount<10||state.keyViewCount!==3)throw Error('Missing drawables at '+f+' '+JSON.stringify(state));
  meta.push(state);
  const file=join(out,'frame-'+String(f).padStart(3,'0')+'.png');
  await page.locator('#viewport').screenshot({path:file});
  if(statSync(file).size<5000)throw Error('Blank/trivial image at '+f);
  if(sampleFrames.includes(f))screenshots.push(file);
 }
 const verify=await page.evaluate(()=>window.renderIntegrated(144,144));
 if(meta[0].yaw!==0||Math.abs(meta[48].yaw-360)>1e-6||Math.abs(verify.yaw-360)>1e-6)
   throw Error('Rotation 360 seam timeline failed');
 if(meta[82].handMinusTorsoDepth>=-.08||meta[110].handMinusTorsoDepth<=.08)
   throw Error('Arm does not transition across torso depth: '+meta[82].handMinusTorsoDepth+', '+meta[110].handMinusTorsoDepth);
 const maxError=Math.max(...meta.map(x=>x.ikError));
 if(maxError>.07)throw Error('3D hand IK error too large '+maxError);
 if(Math.max(...meta.map(x=>x.blink))<.8)throw Error('Blink morph never activates');
 const shadows=meta.map(x=>x.shadowOffset);
 if(Math.max(...shadows)-Math.min(...shadows)<.20)throw Error('Light shadow direction did not move');
 if(errors.length)throw Error('Browser JS errors: '+errors.join(' | '));
 const video=join(out,'integrated-6sec.mp4');
 execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-framerate','24','-i',
  join(out,'frame-%03d.png'),'-vf','scale=960:540,setsar=1','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',
  '-r','24',video],{stdio:'pipe'});
 const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-select_streams','v:0','-count_frames',
  '-show_entries','stream=width,height,nb_read_frames,r_frame_rate','-of','json',video],{encoding:'utf8'}));
 const stream=probe.streams?.[0];
 if(Number(stream?.nb_read_frames)!==144||stream?.width!==960||stream?.height!==540)throw Error('MP4 wrong dimensions or frame count: '+JSON.stringify(stream));
 const sheet=join(out,'integrated-contact.png');
 const inputs=screenshots.map(s=>['-i',s]).flat();
 execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y',...inputs,
  '-filter_complex','hstack=inputs=15,scale=2250:84','-frames:v','1',sheet],{stdio:'pipe'});
 const report={
   status:'PASS_ENGINEERING_ONLY',visualReview:'REQUIRED',
   goal:'one continuous full-body 360 / 3D IK occlusion crossing / facial deformation and moving shadow',
   sourceArt:'original procedural 3-view stylized part textures, no third-party assets',
   drawables:12,explicitSourceKeyViews:3,
   syntheticLeftView:'mirrored side for this small symmetrical proxy, not a production solution',
   renderedFrames:144,framesPerSecond:24,width:960,height:540,
   maxIkError:maxError,behindArmDepthAt82:meta[82].handMinusTorsoDepth,
   inFrontArmDepthAt110:meta[110].handMinusTorsoDepth,
   maxBlink:Math.max(...meta.map(x=>x.blink)),
   shadowTravel:Math.max(...shadows)-Math.min(...shadows),
   videoBytes:statSync(video).size,
   limitations:['vector/procedural art rather than high fidelity anime illustration',
   'only three authored key angles, mirrored left profile',
   'simple fan-triangulated UV part mesh, not ARAP or full contour correspondence',
   'art-directed shading shapes, not physically correct normal mapping',
   '3D two-link arm IK, simple leg motion without ground-lock IK',
   'numerical gates and generated frames do not replace independent visual review'],
   checkpoints:meta.filter((_,i)=>sampleFrames.includes(i)),
 };
 writeFileSync(join(out,'integrated-report.json'),JSON.stringify(report,null,2)+'\n');
 writeFileSync(join(out,'integrated-frame-stats.json'),JSON.stringify(meta,null,2)+'\n');
 console.log('PASS_ENGINEERING_ONLY: 144 frames / one clip / 3 source views / 12 parts');
 console.log(JSON.stringify({maxError,behind:meta[82].handMinusTorsoDepth,ahead:meta[110].handMinusTorsoDepth,
 videoBytes:report.videoBytes,shadowTravel:report.shadowTravel}));
} finally{
 if(browser)await browser.close();
 server.kill('SIGTERM');
}
