import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {mkdirSync,statSync,writeFileSync} from 'node:fs';
import {resolve,join} from 'node:path';
import type {OcclusionRuleResult} from '../src/qa/occlusion-audit';

const out=resolve('out/dynamic-occlusion');
mkdirSync(out,{recursive:true});
const server=spawn(process.execPath,[resolve('node_modules/vite/bin/vite.js'),
 '--host','127.0.0.1','--port','5183','--strictPort'],{stdio:['ignore','pipe','pipe']});
let log='';server.stdout.on('data',v=>log+=v.toString());server.stderr.on('data',v=>log+=v.toString());
let browser:Awaited<ReturnType<typeof chromium.launch>>|undefined;
const cases=[{yaw:0,frame:150},{yaw:90,frame:150},{yaw:180,frame:150},{yaw:270,frame:150},
             {yaw:0,frame:46},{yaw:180,frame:46}] as const;
try{
 let ready=false;
 for(let i=0;i<90;i++){
  try{if((await fetch('http://127.0.0.1:5183/integrated.html')).ok){ready=true;break;}}catch{}
  if(server.exitCode!==null)throw Error('Vite stopped: '+log);
  await new Promise(r=>setTimeout(r,250));
 }
 if(!ready)throw Error('Vite unavailable');
 browser=await chromium.launch({headless:false,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1040,height:740},deviceScaleFactor:1});
 await page.goto('http://127.0.0.1:5183/integrated.html',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>typeof window.auditTurnOcclusion==='function');
 const result:{yaw:number;frame:number;localDepth:number;rules:OcclusionRuleResult[];facePixels:number}[]=[];
 for(const scenario of cases){
  const state=await page.evaluate(s=>window.renderDynamic360(s.yaw,s.frame),scenario);
  const readback=await page.evaluate(()=>window.captureTurnPass('id',false));
  const rules=await page.evaluate(()=>window.auditTurnOcclusion());
  const name='actual-pose-'+scenario.yaw+'-'+scenario.frame+'.png';
  await page.locator('#viewport').screenshot({path:join(out,name)});
  if(statSync(join(out,name)).size<4000)throw Error('Blank scenario '+name);
  result.push({yaw:scenario.yaw,frame:scenario.frame,
    localDepth:state.pose.handTorsoLocalZ,rules,facePixels:readback.counts.face??0});
 }
 const required=result.filter(r=>r.frame===150);
 const all=required.filter(x=>x.yaw!==90).flatMap(x=>x.rules.map(y=>({...y,frame:x.frame})));
 const backFaceInvisible=required.filter(x=>[90,180].includes(x.yaw)).every(x=>x.facePixels<3);
 const bad=all.filter(x=>x.status==='FAIL');
 const untested=all.filter(x=>x.status==='UNTESTED');
 const covered=all.filter(x=>x.status==='PASS');
 const frontalArm=all.filter(x=>x.angle===0&&(x.front==='rightArm'||x.front==='leftArm'));
 const rearArm=all.filter(x=>x.angle===180&&(x.back==='rightArm'||x.back==='leftArm'));
 const depthFront=required.find(x=>x.yaw===0)?.localDepth??0;
 const depthRear=required.find(x=>x.yaw===180)?.localDepth??0;
 const crossing=depthFront>.15&&depthRear>.15;
 // Different world-camera occlusion should follow the same pose-local
 // hand depth at 0° and 180°, not the opposite sign of raw world-z.
 const pass=bad.length===0&&untested.length===0&&covered.length>=9&&
   frontalArm.every(x=>x.status==='PASS')&&rearArm.every(x=>x.status==='PASS')&&
   frontalArm.length===2&&rearArm.length===2&&crossing&&backFaceInvisible;
 const status=pass?'PASS_DYNAMIC_LOCAL_OCCLUSION':
   bad.length?'FAIL_DYNAMIC_LOCAL_OCCLUSION':'BLOCKED_DYNAMIC_LOCAL_OCCLUSION';
 const report={status,verifiedAtFrame:150,cases:result,
   counts:{bad:bad.length,untested:untested.length,covered:covered.length,
     frontalArm:frontalArm.length,rearArm:rearArm.length},
   limits:['Tests only named overlapping pairs at representative poses.',
     'No guarantee of arbitrary torso/arm alpha topology or all 192 frames.',
     'Complete model/visual 360° acceptance still requires full video review.']};
 writeFileSync(join(out,'dynamic-occlusion-audit.json'),JSON.stringify(report,null,2)+'\n');
 console.log('DYNAMIC_OCCLUSION_RESULT '+JSON.stringify({status,counts:report.counts,
   depthFront,depthRear,bad,untested,backFaceInvisible}));
}finally{
 if(browser)await browser.close();
 server.kill('SIGTERM');
}
