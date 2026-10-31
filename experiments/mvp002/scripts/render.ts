import { chromium } from 'playwright';
import { spawn, execFileSync } from 'node:child_process';
import { mkdirSync, statSync, writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';

const root=process.cwd();
const out=resolve(root,'out');
mkdirSync(out,{recursive:true});
const server=spawn(process.execPath,[resolve(root,'node_modules/vite/bin/vite.js'),'--host','127.0.0.1','--port','5174','--strictPort'],
 {cwd:root,stdio:['ignore','pipe','pipe']});
let serverLog='';
server.stdout.on('data',d=>serverLog+=String(d));
server.stderr.on('data',d=>serverLog+=String(d));
let browser:Awaited<ReturnType<typeof chromium.launch>>|undefined;
const errors:string[]=[];
type Shot = 'turn' | 'action' | 'fx';
const specs:Shot[]=['turn','action','fx'];
const frames=72;
try{
 let ready=false;
 for(let i=0;i<80;i++){
   if(server.exitCode!==null)throw Error('Vite stopped: '+serverLog);
   try{if((await fetch('http://127.0.0.1:5174')).ok){ready=true;break;}}catch{}
   await new Promise(ok=>setTimeout(ok,300));
 }
 if(!ready)throw Error('Vite failed to start: '+serverLog);
 browser=await chromium.launch({headless:false,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1080,height:760},deviceScaleFactor:1});
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('http://127.0.0.1:5174',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>typeof window.demoRender==='function');
 const info=await page.evaluate(()=>window.demoInfo);
 if(JSON.stringify(info).includes('null'))throw Error('Bad info');
 const report:Record<string,unknown>={phase:'MVP002',result:'NOT_VALIDATED_YET',info,shots:{},purpose:'Integrated core visual proxy, not anime production quality'};
 for(const shot of specs){
   const frameDir=join(out,shot+'-frames');mkdirSync(frameDir,{recursive:true});
   const framesMeta:Record<string,unknown>[]=[];
   for(let f=0;f<frames;f++){
     const meta=await page.evaluate(({shot,frame,frames})=>window.demoRender(shot,frame,frames),{shot,frame:f,frames});
     framesMeta.push(meta);
     const file=join(frameDir,'frame-'+String(f).padStart(3,'0')+'.png');
     await page.locator('#viewport').screenshot({path:file});
     if(statSync(file).size<3000)throw Error('Blank/trivial frame: '+file);
   }
   // 360 is an extra sample, not included in the 0°..355° video.
   if(shot==='turn'){
     const loop=await page.evaluate(({shot,frames})=>window.demoRender(shot,frames,frames),{shot,frames});
     if(Math.abs(Number(loop.yaw)-360)>.000001)throw Error('360-degree seam evaluation absent');
     if(Number(framesMeta[0].yaw)!==0)throw Error('Start angle not zero');
   }
   if(shot==='action'){
     const end=framesMeta[frames-1];
     if(Number(end.reachError)>.06) throw Error('IK target unreachable: '+end.reachError);
   }
   const video=join(out,shot+'.mp4');
   execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-framerate','24','-i',
      join(frameDir,'frame-%03d.png'),'-vf','scale=960:540,setsar=1','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-r','24',video],
      {stdio:'pipe'});
   const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-count_frames','-select_streams','v:0',
     '-show_entries','stream=nb_read_frames,width,height,r_frame_rate','-of','json',video],{encoding:'utf8'}));
   const stream=probe.streams?.[0];
   if(!stream||Number(stream.nb_read_frames)!==frames||stream.width!==960||stream.height!==540)
      throw Error('Unexpected encoded frames/resolution for '+shot+': '+JSON.stringify(stream));
   // Contact sheet: actual frames, no "generated" still image invented.
   const thumbs=[0,9,18,27,36,45,54,63];
   const inputArgs=thumbs.flatMap(f=>['-i',join(frameDir,'frame-'+String(f).padStart(3,'0')+'.png')]);
   execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y',...inputArgs,
      '-filter_complex','hstack=inputs=8,scale=1920:135','-frames:v','1',join(out,shot+'-contact.png')],{stdio:'pipe'});
   (report.shots as Record<string,unknown>)[shot]={
     frames,videoBytes:statSync(video).size,resolution:'960x540',durationSeconds:3,
     first:framesMeta[0],middle:framesMeta[36],last:framesMeta[71],
     maxReachError:Math.max(...framesMeta.map(x=>Number(x.reachError)))
   };
   process.stdout.write(shot+': '+frames+' frames, '+statSync(video).size+' bytes\n');
 }
 if(errors.length)throw Error('Browser page errors: '+errors.join('; '));
 report.result='PASS_ENGINEERING_RENDER_ONLY';
 report.visualQuality='NOT_REVIEWED';
 report.notProven=['commercial anime quality','full RGBA textured mesh','full 3D IK','automatic asset production','complete ARAP','real normal maps'];
 writeFileSync(join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
 process.stdout.write('MVP002: 3 clips emitted; inspect actual videos for visual correctness.\n');
}finally{
 if(browser)await browser.close();
 server.kill('SIGTERM');
}
