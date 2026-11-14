#!/usr/bin/env node
"use strict";
/** Chromium source-hash and canvas review for P15 original P0 facial strokes. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const root=path.resolve(__dirname,"../../.."),exp=path.resolve(__dirname,"..");
const output=path.join(exp,"private-assets/p15-facial-strokes/browser");
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||"playwright");
const sha=f=>crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const MIME={".html":"text/html;charset=utf-8",".js":"text/javascript",".json":"application/json",".png":"image/png"};
const server=http.createServer((req,res)=>{
 try{
  const uri=new URL(req.url,"http://localhost");
  const target=path.resolve(root,"."+decodeURIComponent(uri.pathname));
  if(!target.startsWith(root+path.sep)||!fs.statSync(target).isFile())throw Error("invalid path");
  res.writeHead(200,{"Content-Type":MIME[path.extname(target)]||"application/octet-stream","Cache-Control":"no-store"});
  fs.createReadStream(target).pipe(res);
 }catch{res.writeHead(404);res.end("Not Found")}
});
async function run(){
 fs.mkdirSync(output,{recursive:true});
 await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
 const browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
 const page=await browser.newPage({viewport:{width:1490,height:920},deviceScaleFactor:1});
 const errors=[],failed=[],reviews=[];
 page.on("pageerror",e=>errors.push(String(e)));
 page.on("requestfailed",r=>failed.push(r.url()+":"+r.failure()?.errorText));
 try{
  const target="http://127.0.0.1:"+server.address().port+
     "/experiments/gif-multiview-keyparts-mvp/review/p15-facial-strokes.html";
  await page.goto(target,{waitUntil:"domcontentloaded",timeout:30000});
  await page.waitForFunction(()=>window.__KOMA_P15&&window.__KOMA_P15.inspect().ready,null,{timeout:25000});
  for(const role of ["face.skin","eye.near","nose","mouth"]){
   await page.evaluate(async r=>window.__KOMA_P15.choose(r),role);
   const status=await page.evaluate(()=>window.__KOMA_P15.inspect());
   if(!status.ready||status.role!==role||status.verified!==4||status.pairs!==12||status.errors.length)
    throw Error("P15 source or identity mismatch: "+JSON.stringify(status));
   const file=path.join(output,role.replace(".","-")+".png");
   await page.locator("#overview").screenshot({path:file});
   reviews.push({semanticId:role,sourceImagesHashVerified:status.verified,
     acceptedStrokeMatches:status.matches,physicalAnchorReferences:status.anchors,
     path:path.relative(exp,file),sha256:sha(file),bytes:fs.statSync(file).size});
  }
  const qa={schema:"KOMA-P0-P15-04-CHROMIUM-FACIAL-CORRESPONDENCE-QA-V1",
   characterId:"p0_character_001",status:"PASS_SOURCE_HASH_CHROMIUM",
   semanticRoles:reviews.map(x=>x.semanticId),screenshotCount:reviews.length,
   verifiedSourceImages:reviews.reduce((n,x)=>n+x.sourceImagesHashVerified,0),
   acceptedStrokeMatches:reviews.reduce((n,x)=>n+x.acceptedStrokeMatches,0),
   reviews,javascriptErrors:errors,failedRequests:failed,
   visualAcceptance:"PENDING_INDEPENDENT_ARTISTIC_REVIEW"};
  fs.writeFileSync(path.join(output,"qa.json"),JSON.stringify(qa,null,2)+"\n");
  console.log(JSON.stringify({status:qa.status,screenshots:qa.screenshotCount,
   verifiedSourceImages:qa.verifiedSourceImages,matchedStrokes:qa.acceptedStrokeMatches,
   javascriptErrors:errors,failedRequests:failed},null,2));
 }finally{await browser.close();await new Promise(ok=>server.close(ok))}
}
run().catch(e=>{console.error(e.stack);server.close();process.exitCode=2});
