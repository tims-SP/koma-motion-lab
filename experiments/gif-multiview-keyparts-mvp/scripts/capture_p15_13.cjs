#!/usr/bin/env node
"use strict";
/** Real-Chromium QA for P15-13 deterministic conditioning and art comparison. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const {chromium}=require("playwright");
const root=path.resolve(__dirname,"../../.."),exp=path.resolve(__dirname,"..");
const output=path.join(exp,"private-assets/p15-13-structural/browser");
const sha=file=>crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const mime={".html":"text/html;charset=utf-8",".png":"image/png",".jpg":"image/jpeg"};
const server=http.createServer((req,res)=>{
 try{
  const url=new URL(req.url,"http://localhost"),file=path.resolve(root,"."+decodeURIComponent(url.pathname));
  if(!file.startsWith(root+path.sep)||!fs.statSync(file).isFile())throw Error("file not found");
  res.writeHead(200,{"Content-Type":mime[path.extname(file)]||"application/octet-stream"});
  fs.createReadStream(file).pipe(res);
 }catch(e){res.writeHead(404);res.end("missing")}
});
async function main(){
 fs.mkdirSync(output,{recursive:true});
 await new Promise(done=>server.listen(0,"127.0.0.1",done));
 let browser;
 try{
  browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
  const captures=[],javascriptErrors=[],failedRequests=[];
  for(const view of [{name:"desktop",width:1440,height:820,channels:["preview","heatmap","lineart","owner"]},
                     {name:"mobile",width:390,height:844,channels:["preview"]}]){
   const page=await browser.newPage({viewport:{width:view.width,height:view.height},deviceScaleFactor:1});
   page.on("pageerror",e=>javascriptErrors.push(String(e)));
   page.on("requestfailed",r=>failedRequests.push(r.url()+": "+(r.failure()?.errorText||"unknown")));
   await page.goto("http://127.0.0.1:"+server.address().port+
      "/experiments/gif-multiview-keyparts-mvp/review/p15-13-structure.html",
      {waitUntil:"domcontentloaded",timeout:30000});
   await page.waitForFunction(()=>window.__KOMA_P15_13?.report().ready,null,{timeout:30000});
   for(const angle of [57.5,60]){
    for(const channel of view.channels){
     const data=await page.evaluate(({angle,channel})=>window.__KOMA_P15_13.select(angle,channel),
        {angle,channel});
     if(!data.ready||data.angle!==angle||data.channel!==channel||data.images.length!==4||data.errors.length)
      throw Error("Structural reference source failed: "+JSON.stringify(data));
     const name=view.name+"-"+String(angle).replace(".","p")+"-"+channel+".png";
     const file=path.join(output,name);
     await page.locator(".gallery").screenshot({path:file});
     captures.push({viewport:view.name,angle,channel,sourceCount:data.images.length,
       relativePath:path.relative(exp,file),sha256:sha(file),
       sourceImages:data.images});
    }
   }
   await page.close();
  }
  if(javascriptErrors.length||failedRequests.length)throw Error(JSON.stringify({javascriptErrors,failedRequests}));
  const qa={schema:"KOMA-P15-13-CHROMIUM-CONTROL-REVIEW-V1",characterId:"p0_character_001",
   status:"STRUCTURAL_CHANNELS_HTML_VERIFIED",captureCount:captures.length,
   totalImageLoads:captures.reduce((n,f)=>n+f.sourceCount,0),captures,
   javascriptErrors,failedRequests,artistApproval:"INDEPENDENT_KEYART_REVIEW_REQUIRED"};
  fs.writeFileSync(path.join(output,"qa.json"),JSON.stringify(qa,null,2)+"\n");
  console.log(JSON.stringify({status:qa.status,captures:qa.captureCount,loaded:qa.totalImageLoads,
    errors:javascriptErrors.length,failedRequests:failedRequests.length}));
 }finally{if(browser)await browser.close();await new Promise(ok=>server.close(ok))}
}
main().catch(e=>{console.error(e.stack);server.close();process.exitCode=1});
