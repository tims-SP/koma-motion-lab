#!/usr/bin/env node
"use strict";
/** Real Chromium source loading and 2.5-degree pose/semantic screenshot review. */
const fs=require("node:fs");
const path=require("node:path");
const http=require("node:http");
const crypto=require("node:crypto");
const {chromium}=require("playwright");
const root=path.resolve(__dirname,"../../..");
const exp=path.resolve(__dirname,"..");
const output=path.join(exp,"private-assets/p15-10-semantic-pose/browser");
const sha=file=>crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const type={".html":"text/html",".js":"text/javascript",".png":"image/png",".jpg":"image/jpeg"};
const server=http.createServer((req,res)=>{
 try{
  const request=new URL(req.url,"http://localhost");
  const full=path.resolve(root,"."+decodeURIComponent(request.pathname));
  if(!full.startsWith(root+path.sep)||!fs.statSync(full).isFile())throw Error("file");
  res.writeHead(200,{"Content-Type":type[path.extname(full)]||"application/octet-stream"});
  fs.createReadStream(full).pipe(res);
 }catch(e){res.writeHead(404);res.end("missing")}
});
async function main(){
 fs.mkdirSync(output,{recursive:true});
 await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
 let browser;
 try {
  browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
  const page=await browser.newPage({viewport:{width:1570,height:790},deviceScaleFactor:1});
  const errors=[],requests=[],screens=[];
  page.on("pageerror",e=>errors.push(String(e)));
  page.on("requestfailed",r=>requests.push(r.url()+":"+(r.failure()?.errorText||"unknown")));
  await page.goto("http://127.0.0.1:"+server.address().port+
   "/experiments/gif-multiview-keyparts-mvp/review/p15-10-semantic.html",
   {waitUntil:"domcontentloaded",timeout:25000});
  await page.waitForFunction(()=>window.__KOMA_P15_10?.snapshot().ready,null,{timeout:30000});
  for (const angle of [55,57.5,60,62.5,65]) {
   const item=await page.evaluate(x=>window.__KOMA_P15_10.setView(x.angle,x.part),
                                  {angle,part:"eye.far"});
   if(!item.ready||item.sources.length!==4||item.errors.length)
    throw Error("P15-10 image source validation failed: "+JSON.stringify(item));
   const file=path.join(output,"yaw"+String(angle).replace(".","p")+".png");
   await page.locator(".views").screenshot({path:file});
   screens.push({angle,part:"eye.far",sourceCount:4,source:item.sources,
                 path:path.relative(exp,file),sha256:sha(file)});
  }
  for (const role of ["hair.clip.cross_gold","hair.front","eye.near"]) {
   const item=await page.evaluate(x=>window.__KOMA_P15_10.setView(60,x),role);
   if(!item.ready||item.part!==role)throw Error("Semantic role image failed: "+role);
   const file=path.join(output,"role-"+role+".png");
   await page.locator(".views").screenshot({path:file});
   screens.push({angle:60,part:role,sourceCount:4,source:item.sources,
                 path:path.relative(exp,file),sha256:sha(file)});
  }
  const qa={schema:"KOMA-P15-10-CHROMIUM-REVIEW-V1",characterId:"p0_character_001",
   status:"INTERACTIVE_ARTMESH_HTML_VERIFIED",screenshots:screens,
   screenshotCount:screens.length,imageLoads:screens.length*4,
   javascriptErrors:errors,failedRequests:requests,
   visualStatus:"PENDING_ART_SOURCE_APPROVAL"};
  fs.writeFileSync(path.join(output,"qa.json"),JSON.stringify(qa,null,2)+"\n");
  if(errors.length||requests.length)throw Error("Chromium JavaScript or requests failed");
  console.log(JSON.stringify({status:qa.status,captures:screens.length,loads:qa.imageLoads,
    errors:errors.length,failedRequests:requests.length}));
 }finally{
  if(browser)await browser.close();
  await new Promise(ok=>server.close(ok));
 }
}
main().catch(e=>{console.error(e.stack);server.close();process.exitCode=1});
