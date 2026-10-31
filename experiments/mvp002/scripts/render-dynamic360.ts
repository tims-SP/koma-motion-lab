import * as THREE from 'three';
import {chromium} from 'playwright';
import {spawn,execFileSync} from 'node:child_process';
import {mkdirSync,readFileSync,statSync,writeFileSync} from 'node:fs';
import {resolve,join} from 'node:path';
import type {FrameTrace} from '../src/qa/turn360-contract';

const OUT=resolve('out/dynamic360');
mkdirSync(OUT,{recursive:true});
const FRAMES=192,FPS=24,WIDTH=960,HEIGHT=540;
type Frame={
 frame:number;yaw:number;time:number;headLocalYaw:number;ikError:number;
 handMinusTorsoDepth:number;blink:number;faceVisibility:number;faceShadowOpacity:number;headMatteBend:number;
 pose:{reach:number;fore:number;headLocalYaw:number;shoulderXYZ:number[];elbowXYZ:number[];
 handXYZ:number[];targetXYZ:number[];handDistance:number;footLXYZ:number[];
 footRXYZ:number[];poseTime:number;handTorsoLocalZ:number};
 trace:FrameTrace;visibleCounts:Record<string,number>;
};
const cli=spawn(process.execPath,[resolve('node_modules/vite/bin/vite.js'),
 '--host','127.0.0.1','--port','5181','--strictPort'],{stdio:['ignore','pipe','pipe']});
let viteLog='';
cli.stdout.on('data',x=>viteLog+=String(x));cli.stderr.on('data',x=>viteLog+=String(x));
let browser:Awaited<ReturnType<typeof chromium.launch>>|undefined;
try{
 let ready=false;
 for(let i=0;i<90;i++){
  try{if((await fetch('http://127.0.0.1:5181/integrated.html')).ok){ready=true;break;}}catch{}
  if(cli.exitCode!==null)throw Error('vite exited: '+viteLog);
  await new Promise(r=>setTimeout(r,250));
 }
 if(!ready)throw Error('vite not ready: '+viteLog);
 browser=await chromium.launch({headless:false,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1040,height:750},deviceScaleFactor:1});
 const pageErrors:string[]=[];
 page.on('pageerror',e=>pageErrors.push(String(e)));
 await page.goto('http://127.0.0.1:5181/integrated.html',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>typeof window.renderDynamic360==='function');
 const data:Frame[]=[];
 const visualSamples:number[]=[0,12,24,36,48,60,72,84,96,108,120,132,144,156,168,180];
 const imageFiles:string[]=[];
 const alarms:string[]=[];
 for(let i=0;i<FRAMES;i++){
  const yaw=i*360/FRAMES;
  const frame=await page.evaluate(v=>window.renderDynamic360(v.yaw,v.i),{yaw,i});
  const readback=await page.evaluate(()=>window.captureTurnPass('id',false));
  if(!readback.bounds)throw Error('Missing observed part-ID bounding box at '+i);
  frame.trace.characterBoundingBoxPixels=[...readback.bounds];
  for(const p of frame.trace.parts)p.visiblePixelCountFromIdPass=readback.counts[p.id]||0;
  frame.trace.actualVisiblePartIds=frame.trace.parts.filter(p=>p.visiblePixelCountFromIdPass>0).map(p=>p.id);
  data.push({
    frame:i,yaw:frame.stats.yaw,time:frame.stats.time,
    headLocalYaw:frame.stats.headLocalYaw,ikError:frame.stats.ikError,
    handMinusTorsoDepth:frame.stats.handMinusTorsoDepth,
    blink:frame.stats.blink,faceVisibility:frame.stats.faceVisibility,
    faceShadowOpacity:frame.stats.faceShadowOpacity,headMatteBend:frame.stats.headMatteBend,pose:frame.pose,trace:frame.trace,visibleCounts:readback.counts
  });
  const png=join(OUT,'frame-'+String(i).padStart(3,'0')+'.png');
  await page.locator('#viewport').screenshot({path:png});
  if(statSync(png).size<4000)throw Error('Blank frame '+i);
  if(visualSamples.includes(i))imageFiles.push(png);
  if(i%24===0)console.log('FRAME '+i+' '+JSON.stringify({
    yaw,head:frame.pose.headLocalYaw,IK:frame.pose.handDistance,depth:frame.pose.handTorsoLocalZ}));
 }
 if(pageErrors.length)throw Error('Browser errors: '+pageErrors.join(' / '));
 // Key-angle pose 0/360 must hold at EXACT same time for seam comparison.
 const poseIndex=96;
 const pose0=await page.evaluate(v=>window.renderDynamic360(v.yaw,v.frame),{yaw:0,frame:poseIndex});
 const png0=join(OUT,'same-pose-yaw0.png');await page.locator('#viewport').screenshot({path:png0});
 const pose360=await page.evaluate(v=>window.renderDynamic360(v.yaw,v.frame),{yaw:360,frame:poseIndex});
 const png360=join(OUT,'same-pose-yaw360.png');await page.locator('#viewport').screenshot({path:png360});
 const seamSame=Buffer.compare(readFileSync(png0),readFileSync(png360))===0;
 const probes:number[]=[0,45,90,135,180,225,270,315];
 for(const deg of probes) {
  const idx=Math.round(deg*FRAMES/360);
  await page.evaluate(v=>window.renderDynamic360(v.yaw,v.frame),{yaw:deg,frame:idx});
  for(const pass of ['id','depth','mask'] as const){
   const result=await page.evaluate(p=>window.captureTurnPass(p,true),pass);
   if(!result.dataUrl)throw Error('No '+pass+' pass at yaw '+deg);
   writeFileSync(join(OUT,pass+'-'+String(deg).padStart(3,'0')+'.png'),
     Buffer.from(result.dataUrl.split(',')[1],'base64'));
  }
 }
 // Actual transition images from THIS exact rendering run.
 for(const [id,indices] of [
  ['transition-038-045',Array.from({length:8},(_,i)=>38+i)],
  ['transition-128-136',Array.from({length:9},(_,i)=>128+i)]
 ] as const) {
  const board=await browser.newPage({viewport:{width:1280,height:700}});
  const cards=indices.map(i=>'<figure><figcaption>frame '+i+'</figcaption><img src="data:image/png;base64,'+
   readFileSync(join(OUT,'frame-'+String(i).padStart(3,'0')+'.png')).toString('base64')+'"></figure>');
  await board.setContent('<html><style>body{background:#18253b;color:white;font:13px sans-serif}main{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}figure{margin:0}img{width:100%}</style><main>'+
    cards.join('')+'</main></html>');
  await board.screenshot({path:join(OUT,id+'.png'),fullPage:true});
  await board.close();
 }
 const clip=join(OUT,'dynamic360-8s.mp4');
 execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-framerate',String(FPS),
  '-i',join(OUT,'frame-%03d.png'),'-vf','scale=960:540,setsar=1',
  '-c:v','libx264','-crf','21','-pix_fmt','yuv420p','-r',String(FPS),clip],{stdio:'pipe'});
 const info=JSON.parse(execFileSync('ffprobe',['-v','error','-count_frames','-select_streams','v:0',
 '-show_entries','stream=nb_read_frames,width,height','-of','json',clip],{encoding:'utf8'}));
 const vid=info.streams?.[0];
 const videoOk=Number(vid?.nb_read_frames)===FRAMES&&vid?.width===WIDTH&&vid?.height===HEIGHT;
 const board=await browser.newPage({viewport:{width:1250,height:1100}});
 const samples=imageFiles.map((f,i)=>({name:String(visualSamples[i]*360/FRAMES)+'° · '+(visualSamples[i]/24).toFixed(1)+'s',
   src:readFileSync(f).toString('base64')}));
 await board.setContent('<!DOCTYPE html><html><head><style>'+
 'body{background:#152137;color:#ecf2fc;font:14px sans-serif;margin:10px}main{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}'+
 'section{background:#263956;padding:6px;border-radius:4px}img{display:block;width:100%;aspect-ratio:16/9}header{text-align:center}'+
 '</style></head><body><h2>Same character · 360° while acting (real frames)</h2><main>'+
 samples.map(x=>'<section><header>'+x.name+'</header><img src="data:image/png;base64,'+x.src+'"></section>').join('')+
 '</main></body></html>');
 await board.screenshot({path:join(OUT,'dynamic-angle-board.png'),fullPage:true});
 await board.close();

 const violations:{id:string;status:'PASS'|'FAIL'|'BLOCKED';evidence:string}[]=[];
 const check=(id:string,ok:boolean,evidence:string)=>violations.push({id,status:ok?'PASS':'FAIL',evidence});
 check('D01_CONCURRENT_FULL_YAW',data.every((x,i)=>Math.abs(x.yaw-i*360/FRAMES)<1e-7), '192 frames / 360 yaw while pose changes');
 check('D02_SAME_TIME_CYCLIC_SEAM',seamSame, 'same pose/time 0° vs 360° PNG byte equivalence');
 const headRange=Math.max(...data.map(x=>x.headLocalYaw))-Math.min(...data.map(x=>x.headLocalYaw));
 check('D03_HEAD_LOCAL_TURN',headRange>25&&headRange<56, 'head-local yaw span '+headRange.toFixed(3));
 const maxIK=Math.max(...data.map(x=>x.pose.handDistance));
 const handTravel=Math.hypot(...[0,1,2].map(k=>Math.max(...data.map(x=>x.pose.handXYZ[k]))-
   Math.min(...data.map(x=>x.pose.handXYZ[k]))));
 check('D04_IK_HAND_REACH',maxIK<.05&&handTravel>.6, 'maxIK='+maxIK+' worldHandTravel='+handTravel);
 const localDepthMin=Math.min(...data.map(x=>x.pose.handTorsoLocalZ));
 const localDepthMax=Math.max(...data.map(x=>x.pose.handTorsoLocalZ));
 check('D05_LOCAL_DEPTH_CROSSING',localDepthMin<-.15&&localDepthMax>.15,
  'pose-local hand depth range '+localDepthMin+' → '+localDepthMax);
 const ankleHeightError=Math.max(...data.flatMap(x=>[x.pose.footLXYZ[1],x.pose.footRXYZ[1]]).map(h=>Math.abs(h-.12)));
 check('D06_FOOT_GROUND_HEIGHT',ankleHeightError<1e-6, 'foot Y max deviation='+ankleHeightError+
  ' (only height lock; footprint sliding not validated)');
 let maxAnchorError=0,maxProjectionError=0,traceIssues=0,validFrames=0;
 for(const frame of data){
  const f=frame.trace,v=new THREE.Matrix4().fromArray(f.cameraViewMatrix),
   proj=new THREE.Matrix4().fromArray(f.cameraProjectionMatrix);
  for(const p of f.parts){
   const bone=new THREE.Matrix4().fromArray(p.boneWorldMatrix);
   const local=new THREE.Vector3(...p.boneLocalAnchorXYZ);
   const world=local.applyMatrix4(bone);
   const current=new THREE.Vector3(...p.worldAnchorXYZ);
   maxAnchorError=Math.max(maxAnchorError,world.distanceTo(current));
   const h=new THREE.Vector4(world.x,world.y,world.z,1).applyMatrix4(v).applyMatrix4(proj);
   const px=[(h.x/h.w+1)*480,(1-h.y/h.w)*270];
   maxProjectionError=Math.max(maxProjectionError,
     Math.hypot(px[0]-p.anchorProjectionPixels[0],px[1]-p.anchorProjectionPixels[1]));
   if(p.warningCodes.length||p.geometryVerticesXY.some(x=>x.some(v=>!Number.isFinite(v))))traceIssues++;
  }
  const [x0,y0,x1,y1]=f.characterBoundingBoxPixels;
  if(x1>x0&&y1>y0&&x0>=0&&y0>=0&&x1<=960&&y1<=540&&f.actualVisiblePartIds.length>=4)validFrames++;
 }
 check('D07_DYNAMIC_ANCHOR_REPROJECTION',maxAnchorError<1e-5&&maxProjectionError<.05,
  'max bone error='+maxAnchorError+' max proj pixel error='+maxProjectionError);
 check('D08_RENDER_MESH_AND_FRAMES',traceIssues===0&&validFrames===192&&videoOk,
  'mesh warnings='+traceIssues+' goodBounds='+validFrames+'/192 video='+videoOk);
 const bytes=execFileSync('ffmpeg',['-v','error','-i',clip,'-vf','scale=320:180,format=gray',
  '-f','rawvideo','pipe:1'],{maxBuffer:16*1024*1024});
 const n=320*180;if(bytes.length!==n*FRAMES)throw Error('Decode incomplete for temporal QA');
 const diffs:number[]=[];
 for(let i=1;i<FRAMES;i++){
  let sum=0;
  for(let y=25;y<165;y++)for(let x=100;x<220;x++){
   const k=y*320+x;sum+=Math.abs(bytes[i*n+k]-bytes[(i-1)*n+k]);
  }
  diffs.push(sum/(140*120));
 }
 const sorted=[...diffs].sort((a,b)=>a-b);
 const median=sorted[Math.floor(sorted.length/2)];
 const peak=Math.max(...diffs),peakAt=diffs.indexOf(peak)+1,ratio=peak/Math.max(median,.00001);
 check('D09_TEMPORAL_IMAGE_SPIKES',ratio<3.2,'peak/median='+ratio.toFixed(3)+' peakFrame='+peakAt);
 const maxShadowMismatch=Math.max(...data.map(x=>Math.abs(x.faceShadowOpacity-.27*Math.pow(x.faceVisibility,3))));
 const minFaceVisibility=Math.min(...data.map(x=>x.faceVisibility));
 const maxFaceVisibility=Math.max(...data.map(x=>x.faceVisibility));
 check('D11_VIEW_DEPENDENT_FACE_SHADOW',
   maxShadowMismatch<1e-8&&minFaceVisibility<.001&&maxFaceVisibility>.5,
   'face shadow follows cubic view-visibility envelope; max mismatch='+maxShadowMismatch+
   '; face visibility range '+minFaceVisibility+'..'+maxFaceVisibility);
 const targetBends=[...Array.from({length:8},(_,i)=>38+i),...Array.from({length:9},(_,i)=>128+i)].map(i=>data[i].headMatteBend);
 check('D12_CONTOUR_MASK_BEND',targetBends.every(x=>Number.isFinite(x)&&x>.008),
  'True morphed-face contour bend, min='+Math.min(...targetBends).toFixed(5)+'; visual review required');
 const status=violations.every(x=>x.status==='PASS')?'PASS_STRUCTURE_PENDING_VISUAL':'FAIL_STRUCTURE';
 const report={
   phase:'MVP008_DYNAMIC_360',
   status,quality:'NOT_ACCEPTED',
   disclaimer:'Static yaw core and dynamic simplified IK do not prove arbitrary articulated anime 360 or complete occlusion.',
   sampleCharacter:'same 12-part authored TS RGBA/VDD proxy as MVP007',
   video:'dynamic360-8s.mp4',fps:FPS,frames:FRAMES,width:WIDTH,height:HEIGHT,
   checks:violations,
   data:{
    maxIK,headRange,handTravel,localDepthMin,localDepthMax,ankleHeightError,
    maxShadowMismatch,minFaceVisibility,maxFaceVisibility,
    maxAnchorError,maxProjectionError,traceIssues,validFrames,seamSame,
    medianFrameDiff:median,peakFrameDiff:peak,peakAt,temporalRatio:ratio,
    reachRange:[Math.min(...data.map(x=>x.pose.reach)),Math.max(...data.map(x=>x.pose.reach))],
    foreRange:[Math.min(...data.map(x=>x.pose.fore)),Math.max(...data.map(x=>x.pose.fore))]
   },
   blocked:{
     localOcclusionPoseSweep:'NOT_VERIFIED: head/arm overlap ID-vs-isolated Alpha not yet asserted for moving pose.',
     projectedArmForeshortening:'NOT_VERIFIED: correct 3D joint positions do not prove quality of view-dependent arm silhouette.',
     fullFootIK:'NOT_IMPLEMENTED: Y-height lock only; footprint cannot be certified.',
     videoHumanAcceptance:'PENDING',
     highFidelityAnimeAsset:'NOT_PROVIDED'
   }
 };
 writeFileSync(join(OUT,'dynamic360-qa.json'),JSON.stringify(report,null,2)+'\n');
 writeFileSync(join(OUT,'dynamic360-trace.json'),JSON.stringify(data,null,1));
 console.log('DYNAMIC360_RESULT '+JSON.stringify({status,checks:violations,data:report.data,blocked:report.blocked,videoBytes:statSync(clip).size}));
}finally{
 if(browser)await browser.close();
 cli.kill('SIGTERM');
}
