#!/usr/bin/env node
'use strict';
/** Capture actual uncomposited ArtMesh canvas PNGs for anatomical VDD QA. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),http=require('node:http');
const repo=path.resolve(__dirname,'../../..');
const experiment=path.resolve(__dirname,'..');
const dest=path.resolve(process.env.KOMA_P3_CANVAS_OUT||path.join(experiment,'private-assets/p2-views/vdd-canvases'));
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||'playwright');
const mime={'.html':'text/html;charset=utf-8','.js':'text/javascript;charset=utf-8','.json':'application/json','.png':'image/png','.gif':'image/gif'};
const sha=(p)=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const httpd=http.createServer((req,res)=>{
 try{
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  const target=path.resolve(repo,'.'+pathname);
  if(!target.startsWith(repo+path.sep)||!fs.statSync(target).isFile())throw Error('path invalid');
  res.writeHead(200,{'Content-Type':mime[path.extname(target)]||'application/octet-stream','Cache-Control':'no-store'});
  fs.createReadStream(target).pipe(res);
 }catch{
  res.writeHead(404);res.end('Not Found');
 }
});
async function start(){
 fs.mkdirSync(dest,{recursive:true});
 await new Promise(ok=>httpd.listen(0,'127.0.0.1',ok));
 let browser;
 const errors=[],outputs=[];
 try{
  browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader']});
  const page=await browser.newPage({viewport:{width:1450,height:900}});
  page.on('pageerror',err=>errors.push(String(err)));
  const url='http://127.0.0.1:'+httpd.address().port+'/experiments/gif-multiview-keyparts-mvp/review/index.html?mode=candidate';
  await page.goto(url,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>window.__KOMA_P0_VIEWER&&window.__KOMA_P0_VIEWER.inspect().ready,null,{timeout:18000});
  for(const angle of [0,22.5,45,67.5,90]){
   await page.evaluate(v=>window.__KOMA_P0_VIEWER.renderAt(v),angle);
   const encoded=await page.evaluate(()=>document.getElementById('result').toDataURL('image/png').split(',')[1]);
   const p=path.join(dest,'yaw'+String(angle).replace('.','p')+'.png');
   fs.writeFileSync(p,Buffer.from(encoded,'base64'));
   outputs.push({yaw:angle,path:p,bytes:fs.statSync(p).size,sha256:sha(p)});
  }
  const report={schema:'KOMA-P0-VDD-RAW-CANVAS-EVIDENCE-V1',characterId:'p0_character_001',
                sourceRole:'recovered_original_39_part_RGBA_art',
                rendering:'HTML Canvas2D piecewise ArtMesh vertices',
                outputs,errors,status:errors.length?'BROWSER_RENDER_ERRORS':'CAPTURED_FOR_ANATOMICAL_INSPECTION'};
  fs.writeFileSync(path.join(dest,'canvas-qa.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,frames:outputs.length,errors,files:outputs.map(o=>o.path)},null,2));
  process.exitCode=errors.length?2:0;
 }finally{
  if(browser)await browser.close();
  await new Promise(ok=>httpd.close(ok));
 }
}
start().catch(e=>{console.error(e.stack);httpd.close();process.exitCode=3;});
