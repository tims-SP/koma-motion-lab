#!/usr/bin/env node
"use strict";
/** P0 independently audited 37-frame RGBA interpolation HTML preview capture. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const repo=path.resolve(__dirname,"../../..");
const exp=path.resolve(__dirname,"..");
const out=path.resolve(process.env.KOMA_P8_BROWSER_OUT||path.join(exp,"private-assets/p8-semantic-occlusion/browser"));
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||"playwright");
const sha=file=>crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const types={".html":"text/html;charset=utf-8",".js":"application/javascript",".json":"application/json",".png":"image/png",".jpg":"image/jpeg",".gif":"image/gif"};
const server=http.createServer((request,response)=>{
 try{
  const url=new URL(request.url,"http://localhost");
  const target=path.resolve(repo,"."+decodeURIComponent(url.pathname));
  if(!target.startsWith(repo+path.sep)||!fs.statSync(target).isFile())throw Error("invalid path");
  response.writeHead(200,{"Content-Type":types[path.extname(target)]||"application/octet-stream","Cache-Control":"no-store"});
  fs.createReadStream(target).pipe(response);
 }catch{
  response.writeHead(404);response.end("Not Found");
 }
});
async function run(){
 fs.mkdirSync(out,{recursive:true});
 await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
 const browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
 const page=await browser.newPage({viewport:{width:1680,height:1030},deviceScaleFactor:1});
 const errors=[],failedRequests=[],screens=[];
 page.on("pageerror",err=>errors.push(String(err)));
 page.on("requestfailed",req=>failedRequests.push(req.url()+" "+(req.failure()?.errorText||"")));
 try{
  const url="http://127.0.0.1:"+server.address().port+"/experiments/gif-multiview-keyparts-mvp/review/p8-motion.html";
  await page.goto(url,{waitUntil:"domcontentloaded",timeout:30000});
  await page.waitForFunction(()=>window.__KOMA_P8_VIEWER?.inspect().ready,null,{timeout:30000});
  const initial=await page.evaluate(()=>window.__KOMA_P8_VIEWER.inspect());
  if(!initial.ready||initial.methodCount!==3||initial.frameCount!==37||initial.errors.length)
   throw Error("P7 viewer source register incomplete: "+JSON.stringify(initial));
  for(const yaw of [0,22.5,45,67.5,72.5,90]){
   await page.evaluate(async v=>window.__KOMA_P8_VIEWER.renderAt(v),yaw);
   const result=await page.evaluate(()=>window.__KOMA_P8_VIEWER.inspect());
   if(result.angle!==yaw||result.errors.length)throw Error("P7 angle render failed "+yaw);
   const name="p8-motion-yaw"+String(yaw).replace(".","p")+".png";
   const file=path.join(out,name);
   await page.locator(".gallery").screenshot({path:file});
   const canvasPNGs=[];
   for(const method of ["p6-mesh","p7-guided","p8-selective"]){
    const bytes=await page.evaluate(m=>{
     const canvas=document.querySelector('article[data-method="'+m+'"] canvas');
     return canvas.toDataURL("image/png").split(",")[1];
    },method);
    const candidate=path.join(out,name.replace(".png","")+"-"+method+".png");
    fs.writeFileSync(candidate,Buffer.from(bytes,"base64"));
    canvasPNGs.push({method,path:candidate,sha256:sha(candidate),bytes:fs.statSync(candidate).size});
   }
   screens.push({yaw,path:file,sha256:sha(file),bytes:fs.statSync(file).size,canvases:canvasPNGs});
  }
  const report={
   schema:"KOMA-P0-P8-INTERACTIVE-HTML-REAL-BROWSER-QA-V1",
   characterId:"p0_character_001",
   source:"P0 original 0,45,90; See-through 0,45 independent semantic PSD",
   registeredRGBASequenceFrames:37,
   methodCount:3,
   initial,
   screens,
   errors,
   failedRequests,
   status:screens.length===6&&errors.length===0&&failedRequests.length===0?
    "PASS_REAL_BROWSER_TEXTURE_PREVIEW":"REVIEW_BROWSER_RENDER_ERRORS",
   artisticAcceptance:"PENDING_ANATOMICAL_VISUAL_REVIEW"
  };
  fs.writeFileSync(path.join(out,"browser-qa.json"),JSON.stringify(report,null,2)+"\n");
  console.log(JSON.stringify({status:report.status,angles:screens.map(x=>x.yaw),
    capturedCanvases:screens.reduce((n,x)=>n+x.canvases.length,0),
    errors,failedRequests},null,2));
  if(report.status!=="PASS_REAL_BROWSER_TEXTURE_PREVIEW")process.exitCode=2;
 }finally{
  await browser.close();
  await new Promise(ok=>server.close(ok));
 }
}
run().catch(e=>{console.error(e.stack);server.close();process.exitCode=3;});
