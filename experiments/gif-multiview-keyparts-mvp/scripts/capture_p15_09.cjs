#!/usr/bin/env node
"use strict";
/** P15-09 live Chromium comparison and source-image inspection. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const root=path.resolve(__dirname,"../../.."),exp=path.resolve(__dirname,"..");
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||"playwright");
const output=path.join(exp,"private-assets/p15-09-midarc/browser");
const sha=p=>crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
const types={".html":"text/html",".js":"text/javascript",".png":"image/png",".json":"application/json",".jpg":"image/jpeg"};
const server=http.createServer((req,res)=>{
 try{
  const u=new URL(req.url,"http://localhost");
  const p=path.resolve(root,"."+decodeURIComponent(u.pathname));
  if(!p.startsWith(root+path.sep)||!fs.statSync(p).isFile())throw Error("404");
  res.writeHead(200,{"Content-Type":types[path.extname(p)]||"application/octet-stream"});
  fs.createReadStream(p).pipe(res);
 }catch(e){res.writeHead(404);res.end("missing")}
});
async function main(){
 fs.mkdirSync(output,{recursive:true});
 await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
 let browser;
 try{
  browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
  const page=await browser.newPage({viewport:{width:1520,height:790},deviceScaleFactor:1});
  const errors=[],requests=[],screens=[];
  page.on("pageerror",e=>errors.push(String(e)));
  page.on("requestfailed",r=>requests.push(r.url()+":"+(r.failure()?.errorText||"unknown")));
  await page.goto("http://127.0.0.1:"+server.address().port+
   "/experiments/gif-multiview-keyparts-mvp/review/p15-09-midarc.html",
   {waitUntil:"domcontentloaded",timeout:30000});
  await page.waitForFunction(()=>window.__KOMA_P15_09?.inspect().ready,null,{timeout:20000});
  for(const angle of [45,50,55,57.5,60,65]){
   const data=await page.evaluate(y=>window.__KOMA_P15_09.choose(y),angle);
   if(!data.ready||data.angle!==angle||data.images.length!==3||data.errors.length)
     throw Error("P15-09 browser source check failed "+JSON.stringify(data));
   const file=path.join(output,"yaw"+String(angle).replace(".","p")+".png");
   await page.locator(".gallery").screenshot({path:file});
   screens.push({angle,imageCount:data.images.length,
    sourcePaths:data.images.map(x=>x.path),imageResolution:data.images.map(x=>[x.width,x.height]),
    imagePath:path.relative(exp,file),sha256:sha(file)});
  }
  const qa={"schema":"KOMA-P15-09-HTML-REVIEW-V1","characterId":"p0_character_001",
   "status":"HTML_SOURCE_AND_RENDERED_FRAMES_VERIFIED",
   "screenshots":screens,"captureCount":screens.length,
   "sourceImagesLoaded":screens.reduce((v,s)=>v+s.imageCount,0),
   "javascriptErrors":errors,"failedRequests":requests,
   "artisticAcceptance":"PENDING"};
  fs.writeFileSync(path.join(output,"qa.json"),JSON.stringify(qa,null,2)+"\n");
  console.log(JSON.stringify({status:qa.status,screenshots:qa.captureCount,
    loaded:qa.sourceImagesLoaded,jsErrors:errors.length,requests:requests.length}));
 }finally{if(browser)await browser.close();await new Promise(ok=>server.close(ok))}
}
main().catch(e=>{console.error(e.stack);server.close();process.exitCode=1});
