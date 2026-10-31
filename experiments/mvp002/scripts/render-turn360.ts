import {chromium} from 'playwright';
import {spawn,execFileSync} from 'node:child_process';
import {mkdirSync,readFileSync,statSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve,join} from 'node:path';
import type {FrameTrace,GateId,GateResult,AcceptanceIssue,Turn360AcceptanceReport,PartTrace} from '../src/qa/turn360-contract';
import {TURN360_PROFILE as P} from '../src/qa/turn360-contract';

declare global {interface Window{
 renderTurn360:(yaw:number,frameIndex:number)=>{stats:{frame:number;time:number;yaw:number;headLocalYaw:number;partCount:number;keyViewCount:number;artMeshCount:number;ikError:number;handMinusTorsoDepth:number;armLocalYaw:number;lightAngle:number;shadowOffset:number;blink:number;targetX:number;handX:number};trace:FrameTrace};
 captureTurnPass:(pass:'id'|'depth'|'mask',includeImage:boolean)=>{counts:Record<string,number>;dataUrl?:string};
 turnSourceViews:{angles:number[];independent270:boolean;derivedPartIds:string[]};
}}
const output=resolve('out/turn360');
mkdirSync(output,{recursive:true});
const server=spawn(process.execPath,[resolve('node_modules/vite/bin/vite.js'),
  '--host','127.0.0.1','--port','5179','--strictPort'],{stdio:['ignore','pipe','pipe']});
let serverLog='';
server.stdout.on('data',d=>serverLog+=String(d));
server.stderr.on('data',d=>serverLog+=String(d));
let browser:Awaited<ReturnType<typeof chromium.launch>>|undefined;
const issues:AcceptanceIssue[]=[];
const results:GateResult[]=[];
const trace:FrameTrace[]=[];
const reason=(gate:GateId,status:'FAIL'|'BLOCKED',observation:string,partIds:string[]=[],yaw?:number)=>{
 const id='ISSUE-'+String(issues.length+1).padStart(3,'0');
 issues.push({id,gateId:gate,severity:status==='FAIL'?'P0':'P1',yawDegrees:yaw,
  partIds,observation,evidenceFile:'turn360-traces.json',
  suggestedFix:'Repair the corresponding original model data and rerun this same acceptance.',
  reviewer:'ts-structural',status:'open'});
 return id;
};
function gate(id:GateId,status:'PASS'|'FAIL'|'BLOCKED',why?:string,partIds:string[]=[],yaw?:number):void {
 const issueIds=why?[reason(id,status==='PASS'?'BLOCKED':status,why,partIds,yaw)]:[];
 results.push({id,status,evidenceFiles:['turn360-traces.json','angle-board.png'],issueIds});
}
const sha=(path:string)=>createHash('sha256').update(readFileSync(path)).digest('hex');
function saveImage(file:string,base64:string|undefined):void{
 if(!base64||!base64.startsWith('data:image/png;base64,'))throw Error('Missing real rendered PNG '+file);
 writeFileSync(join(output,file),Buffer.from(base64.split(',')[1],'base64'));
}
const sampleFiles:string[]=[];
const debugFiles:string[]=[];
try{
 let ready=false;
 for(let i=0;i<90;i++){
  try{if((await fetch('http://127.0.0.1:5179/integrated.html')).ok){ready=true;break;}}catch{}
  if(server.exitCode!==null)throw Error('Vite failed: '+serverLog);
  await new Promise(r=>setTimeout(r,250));
 }
 if(!ready)throw Error('Vite unreachable: '+serverLog);
 browser=await chromium.launch({headless:false,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1030,height:760},deviceScaleFactor:1});
 const jsErrors:string[]=[];
 page.on('pageerror',err=>jsErrors.push(String(err)));
 await page.goto('http://127.0.0.1:5179/integrated.html',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>typeof window.renderTurn360==='function');
 const sources=await page.evaluate(()=>window.turnSourceViews);
 const bboxMap:number[]=[];
 const videoAngles:number[]=[];
 const frameFiles:string[]=[];
 for(let f=0;f<P.videoFrames;f++){
  const yaw=f*360/P.videoFrames;
  const frame=await page.evaluate(v=>window.renderTurn360(v.yaw,v.f),{yaw,f});
  const id=await page.evaluate(()=>window.captureTurnPass('id',false));
  for(const p of frame.trace.parts)p.visiblePixelCountFromIdPass=id.counts[p.id]??0;
  frame.trace.actualVisiblePartIds=frame.trace.parts.filter(p=>p.visiblePixelCountFromIdPass>0).map(p=>p.id);
  trace.push(frame.trace);
  videoAngles.push(frame.stats.yaw);
  bboxMap.push(frame.trace.parts.reduce((a,p)=>a+p.visiblePixelCountFromIdPass,0));
  const path=join(output,'frame-'+String(f).padStart(3,'0')+'.png');
  await page.locator('#viewport').screenshot({path});
  if(statSync(path).size<4000)throw Error('Blank screenshot '+f);
  frameFiles.push(path);
 }
 const seam0=frameFiles[0],seam360=join(output,'seam-360.png');
 const final=await page.evaluate(()=>window.renderTurn360(360,192));
 await page.locator('#viewport').screenshot({path:seam360});
 const seamEqual=sha(seam0)===sha(seam360);
 const keyTraces:FrameTrace[]=[];
 for(let i=0;i<P.sampleDegrees.length;i++){
  const yaw=P.sampleDegrees[i];
  const data=await page.evaluate(v=>window.renderTurn360(v.yaw,v.f),{yaw,f:192+i});
  keyTraces.push(data.trace);
  const file='sample-'+String(i).padStart(3,'0')+'.png';
  await page.locator('#viewport').screenshot({path:join(output,file)});
  sampleFiles.push(file);
  if([0,45,90,135,180,225,270,315,360].includes(yaw)){
    for(const pass of ['id','depth','mask'] as const){
      const out=await page.evaluate(p=>window.captureTurnPass(p,true),pass);
      const filename='pass-'+pass+'-'+String(yaw).padStart(3,'0')+'.png';
      saveImage(filename,out.dataUrl);debugFiles.push(filename);
    }
  }
 }
 for(const yaw of [0,90,180,270]){
  for(const offset of [-1,1]){
   const angle=(yaw+offset+360)%360;
   await page.evaluate(v=>window.renderTurn360(v.yaw,300),{yaw:angle});
   await page.locator('#viewport').screenshot({path:join(output,'boundary-'+String(yaw)+'-'+(offset<0?'minus':'plus')+'.png')});
  }
 }
 if(jsErrors.length)throw Error('Browser errors: '+jsErrors.join(' / '));
 // Actual contact board with fixed human-readable angle labels.
 const board=await browser.newPage({viewport:{width:1200,height:1550}});
 const boardCards=sampleFiles.map((name,i)=>({
  label:P.sampleDegrees[i]+'°',
  png:readFileSync(join(output,name)).toString('base64')
 }));
 await board.setContent('<html><head><style>'+
  'body{background:#111c30;color:#f3f5fa;font:16px sans-serif;margin:8px}'+
  'section{display:grid;grid-template-columns:repeat(5,1fr);gap:7px}'+
  'article{background:#25324a;padding:6px;border-radius:5px}'+
  'img{width:215px;aspect-ratio:16/9;object-fit:contain}header{text-align:center;font-weight:bold}'+
  '</style></head><body><section>'+boardCards.map(x=>
   '<article><header>'+x.label+'</header><img src="data:image/png;base64,'+x.png+'"/></article>'
  ).join('')+'</section></body></html>');
 await board.screenshot({path:join(output,'angle-board.png'),fullPage:true});
 await board.close();
 // One page of actual most significant face and ID/depth evidence.
 const detail=await browser.newPage({viewport:{width:1100,height:1040}});
 const interesting=['sample-003.png','sample-009.png','sample-015.png','sample-021.png',
                    'pass-id-045.png','pass-depth-135.png','pass-id-225.png','pass-id-315.png'];
 await detail.setContent('<html><head><style>'+
  'body{background:#131e30;color:white;font:14px sans-serif} main{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}'+
  'div{background:#2a344a;padding:9px}img{width:100%}</style></head><body><main>'+
  interesting.map(x=>'<div><b>'+x+'</b><img src="data:image/png;base64,'+
   readFileSync(join(output,x)).toString('base64')+'"></div>').join('')+'</main></body></html>');
 await detail.screenshot({path:join(output,'detail-board.png'),fullPage:true});
 await detail.close();
 const video=join(output,'turn360-8s.mp4');
 execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-framerate','24',
   '-i',join(output,'frame-%03d.png'),'-vf','scale=960:540,setsar=1',
   '-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-r','24',video],{stdio:'pipe'});
 const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-select_streams','v:0','-count_frames',
   '-show_entries','stream=width,height,nb_read_frames','-of','json',video],{encoding:'utf8'}));
 const fmt=probe.streams?.[0];const videoGood=Number(fmt?.nb_read_frames)===192&&fmt?.width===960&&fmt?.height===540;
 const brokenAngles=videoAngles.filter((x,i)=>Math.abs(x-i*360/192)>1e-7);
 gate('S01_ANGLE_COVERAGE',brokenAngles.length===0&&final.stats.yaw===360?'PASS':'FAIL',
  brokenAngles.length?'Frame angle mismatch':'');
 gate('S02_CYCLIC_SEAM',seamEqual?'PASS':'FAIL',
  seamEqual?undefined:'Actual identical 0/360 pose PNG bytes differ');
 const parts=trace.flatMap(f=>f.parts);
 const nonFinite=parts.filter(p=>p.geometryVerticesXY.some(v=>v.some(x=>!Number.isFinite(x)))||
   p.textureUV.some(v=>v.some(x=>!Number.isFinite(x))));
 const warning=parts.filter(p=>p.warningCodes.some(w=>w!=='VIEW_270_MIRRORED_SOURCE'));
 gate('S03_ANCHOR_VDD_DECOMPOSITION','BLOCKED',
  'Current worldAnchorXYZ is the projected part center; original local anchor, joint bind pose and independent projection audit are not yet exposed.');
 gate('S04_ARTMESH_UV_TOPOLOGY',nonFinite.length||warning.length?'FAIL':'PASS',
   warning.length?'Geometry issues: '+warning.slice(0,3).map(p=>p.id+':'+p.warningCodes.join(',')).join(' | '):undefined);
 const maxJump=Math.max(...trace.slice(1).map((frame,i)=>{
   const prev=trace[i];
   let jump=0;
   for(const p of frame.parts){
     const before=prev.parts.find(q=>q.id===p.id);
     if(before)jump=Math.max(jump,Math.hypot(p.projectedAnchorXY[0]-before.projectedAnchorXY[0],p.projectedAnchorXY[1]-before.projectedAnchorXY[1]));
   }
   return jump;
 }));
 gate('S05_PART_TRAJECTORY_CONTINUITY',maxJump<.22?'PASS':'FAIL',
   maxJump>=.22?'Large adjacent anchor jump '+maxJump:undefined);
 const actualFrameCounts=trace.filter(f=>f.actualVisiblePartIds.length>=4).length;
 gate('S06_OCCLUSION_ACTUAL_RENDER','BLOCKED',
   'ID pass is real and '+actualFrameCounts+'/192 frames have >=4 visible parts, but no verified occlusion constraint/mask table for crossing hair, face and arms.');
 gate('S07_ANATOMICAL_ASYMMETRY',sources.independent270?'PASS':'FAIL',
   sources.independent270?undefined:'270° view geometry is automatically derived by mirroring 90° for '+sources.derivedPartIds.length+' parts.',sources.derivedPartIds);
 gate('S08_RENDER_FRAME_INTEGRITY',videoGood?'PASS':'FAIL',
  videoGood?undefined:'FFprobe frame/resolution mismatch');
 const finalStatus=results.some(g=>g.status!=='PASS')?'FAIL_STRUCTURE':'PASS_STRUCTURE_PENDING_VISUAL';
 const report:Turn360AcceptanceReport={
  schemaVersion:'MVP-006-360-V1',characterAssetHash:trace[0].characterAssetHash,
  rendererCommit:process.env.GITHUB_SHA||'local-uncommitted',
  runUrl:process.env.GITHUB_RUN_ID?'https://github.com/tims-SP/koma-motion-lab/actions/runs/'+process.env.GITHUB_RUN_ID:'local',
  videoFile:'turn360-8s.mp4',videoFrameCount:P.videoFrames,sampledAngleImages:sampleFiles,
  frameTraceFile:'turn360-traces.json',renderPassEvidenceFiles:debugFiles,gateResults:results,issues,
  coreStatus:finalStatus,highFidelityAnimeArtAccepted:false
 };
 const diagnostics={seamEqual,frameCount:P.videoFrames,boundaryImages:8,independentSampleAngles:25,
   maxAnchorJump:maxJump,actualFrameCounts,sources,videoBytes:statSync(video).size,
   partTracesCount:parts.length,blockedGates:results.filter(x=>x.status==='BLOCKED').map(x=>x.id)};
 writeFileSync(join(output,'turn360-traces.json'),JSON.stringify({frames:trace,sampled:keyTraces},null,1));
 writeFileSync(join(output,'turn360-qa.json'),JSON.stringify({report,diagnostics},null,2)+'\n');
 console.log('QA360_RESULT '+JSON.stringify({status:finalStatus,diagnostics,
   gates:results.map(x=>x.id+'='+x.status),issueCount:issues.length}));
 // A model failing its acceptance gates must still publish the diagnostic
 // artifacts so that it can be fixed; infrastructure failure exits nonzero.
}finally{
 if(browser)await browser.close();
 server.kill('SIGTERM');
}
