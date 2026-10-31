import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
const out=process.env.HEAD009_OUT??'out/head009';
await mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--disable-gpu-sandbox']});
const page=await browser.newPage({viewport:{width:700,height:700},deviceScaleFactor:1});
const measures:{yaw:number;changedFraction:number;affectedPixels:number}[]=[];
const organVisibility:{yaw:number;nearEye:number;farEye:number;nose:number;mouth:number;face:number}[]=[];
try{
 await page.goto(process.env.HEAD009_URL??'http://127.0.0.1:4173/',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>typeof window.head009?.frame==='function');
 for(let yaw=0;yaw<=90;yaw++){
  const diff=await page.evaluate(y=>{
   window.head009.frame(y);
   const canvas=document.querySelector<HTMLCanvasElement>('#stage')!;
   const scratch=document.createElement('canvas');
   scratch.width=canvas.width;scratch.height=canvas.height;
   const ctx=scratch.getContext('2d')!;
   ctx.drawImage(canvas,0,0);
   const rgba=ctx.getImageData(0,0,canvas.width,canvas.height).data;
   // page-only diagnostics; no animation information read from held-out art.
   const host=window as unknown as {lastSweepRGBA?:Uint8ClampedArray};
   const previous=host.lastSweepRGBA;
   let changed=0,active=0;
   if(previous)for(let i=0;i<rgba.length;i+=4){
    const change=Math.max(Math.abs(previous[i]-rgba[i]),Math.abs(previous[i+1]-rgba[i+1]),Math.abs(previous[i+2]-rgba[i+2]));
    if(change>25)changed++;
    const nonBg=Math.max(Math.abs(rgba[i]-41),Math.abs(rgba[i+1]-50),Math.abs(rgba[i+2]-73))>28;
    if(nonBg)active++;
   }
   host.lastSweepRGBA=new Uint8ClampedArray(rgba);
   return {changedFraction:previous?changed/(canvas.width*canvas.height):0,affectedPixels:active};
  },yaw);
  measures.push({yaw,...diff});
  await page.locator('canvas').screenshot({path:join(out,'sweep-'+String(yaw).padStart(3,'0')+'.png')});
  if(yaw%5===0){
   // Keep a whole-sweep visual contact sheet in the exact same WebGL session.
   await page.evaluate(y=>{
    const host=window as unknown as {sweepBoard?:HTMLCanvasElement};
    if(!host.sweepBoard){
     host.sweepBoard=document.createElement('canvas');
     host.sweepBoard.width=1280;host.sweepBoard.height=1024;
    }
    const board=host.sweepBoard,ctx=board.getContext('2d')!;
    const n=y/5,col=n%5,row=Math.floor(n/5),px=col*256,py=row*256;
    ctx.fillStyle='#293249';ctx.fillRect(px,py,256,256);
    ctx.drawImage(document.querySelector<HTMLCanvasElement>('#stage')!,px,py,256,256);
    ctx.fillStyle='#ffffff';ctx.fillRect(px,py,48,23);
    ctx.fillStyle='#202534';ctx.font='bold 14px sans-serif';ctx.fillText(y+'°',px+6,py+16);
   },yaw);
   const qa=await page.evaluate(y=>window.head009.qa(y),yaw);
   organVisibility.push({yaw,nearEye:qa.visibleParts.nearEye||0,farEye:qa.visibleParts.farEye||0,nose:qa.visibleParts.nose||0,mouth:qa.visibleParts.mouth||0,face:qa.visibleParts.face||0});
  }
 }
 const boardData=await page.evaluate(()=>{
  const board=(window as unknown as {sweepBoard?:HTMLCanvasElement}).sweepBoard;
  if(!board)throw Error('sweep storyboard absent');
  return board.toDataURL('image/jpeg',.76).split(',')[1];
 });
 await writeFile(join(out,'head90-sweep-board.jpg'),Buffer.from(boardData,'base64'));
 console.log('HEAD009_SWEEP_BOARD '+boardData);
 const positive=measures.filter(x=>x.yaw>0).map(x=>x.changedFraction).sort((a,b)=>a-b);
 const median=positive[Math.floor(positive.length/2)]||0;
 const peak=measures.reduce((a,b)=>a.changedFraction>b.changedFraction?a:b,measures[0]!);
 const checks={
   persistentEyeAlwaysVisible:organVisibility.every(x=>x.nearEye>75),
   farEyeInvisibleAtProfile:organVisibility.find(x=>x.yaw===90)?.farEye===0,
   farEyeDisappearsBy65:organVisibility.filter(x=>x.yaw>=65).every(x=>x.farEye===0),
   noseAndMouthVisible:organVisibility.every(x=>x.nose>20&&x.mouth>20),
   noSingleFrameHardJump:peak.changedFraction<.075
 };
 const report={schema:'HEAD009-TURN-SWEEP-V1',angleRange:[0,90],frames:measures.length,medianChangeFraction:median,
  peak,checks,organVisibility,frameDiffs:measures,status:Object.values(checks).every(Boolean)?'PASS_ENGINEERING_SWEEP':'FAIL_ENGINEERING_SWEEP',
  visualStatus:'PENDING_INDEPENDENT_VIDEO_REVIEW'};
 await writeFile(join(out,'head90-sweep-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log('HEAD009_SWEEP_SUMMARY '+JSON.stringify({frames:report.frames,median,peak,checks,status:report.status}));
 if(report.status!=='PASS_ENGINEERING_SWEEP')process.exitCode=1;
}catch(e){console.error(e);process.exitCode=1;}
finally{await browser.close();}
