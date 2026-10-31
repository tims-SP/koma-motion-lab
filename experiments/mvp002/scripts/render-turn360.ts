import {chromium} from 'playwright';
import * as THREE from 'three';
import {spawn,execFileSync} from 'node:child_process';
import {mkdirSync,readFileSync,statSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve,join} from 'node:path';
import type {FrameTrace,GateId,GateResult,AcceptanceIssue,Turn360AcceptanceReport,PartTrace} from '../src/qa/turn360-contract';
import {TURN360_PROFILE as P} from '../src/qa/turn360-contract';
import type {OcclusionRuleResult} from '../src/qa/occlusion-audit';

declare global {interface Window{
 renderTurn360:(yaw:number,frameIndex:number)=>{stats:{frame:number;time:number;yaw:number;headLocalYaw:number;partCount:number;keyViewCount:number;artMeshCount:number;ikError:number;handMinusTorsoDepth:number;armLocalYaw:number;lightAngle:number;shadowOffset:number;blink:number;targetX:number;handX:number};trace:FrameTrace};
 captureTurnPass:(pass:'id'|'depth'|'mask',includeImage:boolean)=>{counts:Record<string,number>;dataUrl?:string;bounds?:readonly [number,number,number,number]};
 turnSourceViews:{angles:number[];independent270:boolean;derivedPartIds:string[];authoredGeometry:{id:string;right:readonly (readonly [number,number])[];left:readonly (readonly [number,number])[];rightVDD:readonly [number,number];leftVDD:readonly [number,number]}[]};
 auditTurnOcclusion:()=>OcclusionRuleResult[];
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
  if(!id.bounds)throw Error('Missing actual ID-pass measured screen bbox');
  frame.trace.characterBoundingBoxPixels=[...id.bounds];
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
 const occlusionResults:OcclusionRuleResult[]=[];
 for(let i=0;i<P.sampleDegrees.length;i++){
  const yaw=P.sampleDegrees[i];
  const data=await page.evaluate(v=>window.renderTurn360(v.yaw,v.f),{yaw,f:192+i});
  keyTraces.push(data.trace);
  if([0,15,180,345].includes(yaw)){
    const audit=await page.evaluate(()=>window.auditTurnOcclusion());
    occlusionResults.push(...audit);
  }
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
 const fmt=probe.streams?.[0];const screenBoundsOkay=trace.every(f=>{
 const [x0,y0,x1,y1]=f.characterBoundingBoxPixels;
 return x1>x0&&y1>y0&&x0>=1&&y0>=1&&x1<=959&&y1<=539;
 });
 const videoGood=Number(fmt?.nb_read_frames)===192&&fmt?.width===960&&fmt?.height===540&&screenBoundsOkay;
 const brokenAngles=videoAngles.filter((x,i)=>Math.abs(x-i*360/192)>1e-7);
 gate('S01_ANGLE_COVERAGE',brokenAngles.length===0&&final.stats.yaw===360?'PASS':'FAIL',
  brokenAngles.length?'Frame angle mismatch':'');
 gate('S02_CYCLIC_SEAM',seamEqual?'PASS':'FAIL',
  seamEqual?undefined:'Actual identical 0/360 pose PNG bytes differ');
 const parts=trace.flatMap(f=>f.parts);
 const nonFinite=parts.filter(p=>p.geometryVerticesXY.some(v=>v.some(x=>!Number.isFinite(x)))||
   p.textureUV.some(v=>v.some(x=>!Number.isFinite(x))));
 const warning=parts.filter(p=>p.warningCodes.length>0);
 // Independently rebuild anchor and camera projection from serialized bone,
 // camera and local coordinates; never use the renderer's answer as a substitute.
 let maxAnchorAudit=0,maxProjectionAudit=0,maxDeformationAudit=0;
 for(const frame of trace){
   const view=new THREE.Matrix4().fromArray(frame.cameraViewMatrix);
   const proj=new THREE.Matrix4().fromArray(frame.cameraProjectionMatrix);
   const toPixels=(pos:THREE.Vector3):[number,number]=>{
     const h=new THREE.Vector4(pos.x,pos.y,pos.z,1).applyMatrix4(view).applyMatrix4(proj);
     return [(h.x/h.w+1)*480,(1-h.y/h.w)*270];
   };
   for(const p of frame.parts){
     const model=new THREE.Matrix4().fromArray(p.boneWorldMatrix);
     const reconstructed=new THREE.Vector3(...p.boneLocalAnchorXYZ).applyMatrix4(model);
     const actual=new THREE.Vector3(...p.worldAnchorXYZ);
     maxAnchorAudit=Math.max(maxAnchorAudit,actual.distanceTo(reconstructed));
     const projected=toPixels(reconstructed);
     maxProjectionAudit=Math.max(maxProjectionAudit,
       Math.hypot(projected[0]-p.anchorProjectionPixels[0],
                  projected[1]-p.anchorProjectionPixels[1]));
     const deformed=toPixels(reconstructed.add(new THREE.Vector3(...p.vddOffsetXY,0)));
     maxDeformationAudit=Math.max(maxDeformationAudit,
       Math.hypot(deformed[0]-p.deformedCenterPixels[0],
                  deformed[1]-p.deformedCenterPixels[1]));
   }
 }
 const s03ok=maxAnchorAudit<1e-5&&maxProjectionAudit<.05&&maxDeformationAudit<.05;
 gate('S03_ANCHOR_VDD_DECOMPOSITION',s03ok?'PASS':'FAIL',
  s03ok?undefined:'Real bone and projection audit discrepancies '+JSON.stringify({
   maxAnchorAudit,maxProjectionAudit,maxDeformationAudit}));
 // Geometric validity must also inspect *winding* and *projected area*.
 // Previously all vertices were finite but 225° / 315° views collapsed
 // because mirrored 270° landmarks reversed polygon winding.
 const area=(p:PartTrace)=>{
   const pts=p.geometryVerticesXY.slice(1);
   return pts.reduce((sum,[x,y],i)=>{
     const [nx,ny]=pts[(i+1)%pts.length];
     return sum+(x*ny-nx*y);
   },0)/2;
 };
 const references=new Map(trace[0].parts.map(p=>[p.id,area(p)]));
 const flippedOrCollapsed:{partId:string;yaw:number;area:number;ratio:number}[]=[];
 let minimumAreaRatio=Infinity;
 for(const frame of trace)for(const part of frame.parts){
   const original=references.get(part.id);
   if(!original||Math.abs(original)<1e-7)continue;
   const now=area(part),ratio=Math.abs(now/original);
   minimumAreaRatio=Math.min(minimumAreaRatio,ratio);
   if(original*now<=0||ratio<.18){
     if(flippedOrCollapsed.length<30)
       flippedOrCollapsed.push({partId:part.id,yaw:frame.yawDegrees,area:now,ratio});
   }
 }
 const meshOk=!nonFinite.length&&!warning.length&&!flippedOrCollapsed.length;
 gate('S04_ARTMESH_UV_TOPOLOGY',meshOk?'PASS':'FAIL',
   meshOk?undefined:JSON.stringify({
    meshWarnings:warning.slice(0,3).map(p=>p.id+':'+p.warningCodes.join(',')),
    flippedOrCollapsed
   }));
 const maxJump=Math.max(...trace.slice(1).map((frame,i)=>{
   const prev=trace[i];
   let jump=0;
   for(const p of frame.parts){
     const before=prev.parts.find(q=>q.id===p.id);
     if(before)jump=Math.max(jump,Math.hypot(p.projectedAnchorXY[0]-before.projectedAnchorXY[0],p.projectedAnchorXY[1]-before.projectedAnchorXY[1]));
   }
   return jump;
 }));
 const maxVertexJump=Math.max(...trace.slice(1).map((frame,i)=>{
   let max=0;const prior=trace[i];
   for(const p of frame.parts){
     const prev=prior.parts.find(q=>q.id===p.id);
     if(!prev||prev.geometryVerticesXY.length!==p.geometryVerticesXY.length)continue;
     for(let k=0;k<p.geometryVerticesXY.length;k++){
       max=Math.max(max,Math.hypot(p.geometryVerticesXY[k][0]-prev.geometryVerticesXY[k][0],
         p.geometryVerticesXY[k][1]-prev.geometryVerticesXY[k][1]));
     }
   }
   return max;
 }));
 gate('S05_PART_TRAJECTORY_CONTINUITY',maxJump<.22&&maxVertexJump<.25?'PASS':'FAIL',
   maxJump>=.22||maxVertexJump>=.25?
   'Large adjacent anchor/mesh vertex jumps: '+maxJump+' / '+maxVertexJump:undefined);
 const actualFrameCounts=trace.filter(f=>f.actualVisiblePartIds.length>=4).length;
 const occlusionWrong=occlusionResults.filter(x=>x.status==='FAIL');
 const occlusionUntested=occlusionResults.filter(x=>x.status==='UNTESTED');
 const occlusionOk=occlusionWrong.length===0&&occlusionUntested.length===0&&
   occlusionResults.length>=13;
 gate('S06_OCCLUSION_ACTUAL_RENDER',occlusionWrong.length?'FAIL':occlusionOk?'PASS':'BLOCKED',
   occlusionOk?undefined:JSON.stringify({rules:occlusionResults.length,
     wrong:occlusionWrong,untested:occlusionUntested,actualFrameCounts}));
 const geomProof=sources.authoredGeometry.length===12&&sources.authoredGeometry.every(p=>{
   if(p.right.length!==p.left.length||p.right.length<8)return false;
   // Independently stored 270 key must not be exactly a mirrored 90 key.
   const mirrored=p.right.map(([x,y])=>[-x,y]);
   const departure=Math.max(...p.left.map(([x,y],i)=>
     Math.hypot(x-mirrored[i][0],y-mirrored[i][1])));
   return departure>.015;
 });
 const at90=keyTraces.find(f=>f.yawDegrees===90);
 const at270=keyTraces.find(f=>f.yawDegrees===270);
 const find=(f:FrameTrace|undefined,id:string)=>f?.parts.find(p=>p.id===id);
 const emblem90=find(at90,'emblem'),emblem270=find(at270,'emblem');
 const torso90=find(at90,'torso'),torso270=find(at270,'torso');
 // A non-symmetric chest emblem moves from camera-right to camera-left.
 const semanticMarkerOk=!!emblem90&&!!emblem270&&!!torso90&&!!torso270&&
   emblem90.projectedAnchorXY[0]>torso90.projectedAnchorXY[0]+.1&&
   emblem270.projectedAnchorXY[0]<torso270.projectedAnchorXY[0]-.1;
 const s07ok=sources.independent270&&sources.derivedPartIds.length===0&&
   geomProof&&semanticMarkerOk;
 gate('S07_ANATOMICAL_ASYMMETRY',s07ok?'PASS':'FAIL',
   s07ok?undefined:'Independent left contours missing, equal to mirror, or chest-marker anatomical orientation wrong.',
   sources.derivedPartIds);
 gate('S08_RENDER_FRAME_INTEGRITY',videoGood?'PASS':'FAIL',
  videoGood?undefined:'FFprobe frame/resolution mismatch or ID-pass model bounding box clipped/empty');
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
   maxAnchorJump:maxJump,maxVertexJump,minimumAreaRatio,flippedOrCollapsed,maxAnchorAudit,maxProjectionAudit,maxDeformationAudit,actualFrameCounts,sources,videoBytes:statSync(video).size,
   partTracesCount:parts.length,screenBoundsOkay,occlusionResults,blockedGates:results.filter(x=>x.status==='BLOCKED').map(x=>x.id)};
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
