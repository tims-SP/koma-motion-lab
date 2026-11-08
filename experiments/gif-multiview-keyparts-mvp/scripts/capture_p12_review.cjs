#!/usr/bin/env node
"use strict";
/** Screenshot actual P0 keyframe-proven P12 semantic source-gap and VDD review. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const root=path.resolve(__dirname,"../../.."),exp=path.resolve(__dirname,"..");
const output=path.resolve(process.env.KOMA_P12_BROWSER_OUT||path.join(exp,"private-assets/p12-comparison/browser"));
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||"playwright");
const sha=p=>crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
const types={".html":"text/html;charset=utf-8",".js":"text/javascript",".json":"application/json",".png":"image/png",".jpg":"image/jpeg",".gif":"image/gif"};
const server=http.createServer((request,response)=>{
 try{
  const url=new URL(request.url,"http://localhost");
  const file=path.resolve(root,"."+decodeURIComponent(url.pathname));
  if(!file.startsWith(root+path.sep)||!fs.statSync(file).isFile())throw Error("unsafe or missing original P0 file");
  response.writeHead(200,{"Content-Type":types[path.extname(file)]||"application/octet-stream",
    "Cache-Control":"no-store"});
  fs.createReadStream(file).pipe(response);
 }catch{response.writeHead(404);response.end("Not Found");}
});
async function run(){
 fs.mkdirSync(output,{recursive:true});
 await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
 const browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
 const page=await browser.newPage({viewport:{width:1450,height:950},deviceScaleFactor:1});
 const errors=[],networkFailures=[],images=[];
 page.on("pageerror",e=>errors.push(String(e)));
 page.on("requestfailed",r=>networkFailures.push(r.url()+" "+(r.failure()?.errorText||"")));
 try{
  await page.goto("http://127.0.0.1:"+server.address().port+
    "/experiments/gif-multiview-keyparts-mvp/review/p12-inspection.html",
    {waitUntil:"domcontentloaded",timeout:30000});
  try{await page.waitForFunction(()=>window.__KOMA_P12?.inspect().ready,null,{timeout:18000});}
  catch(e){
   const diagnostic=await page.evaluate(()=>({state:window.__KOMA_P12?.inspect(),status:document.querySelector("#status")?.textContent}));
   throw Error("P12 source viewer initialization "+JSON.stringify(diagnostic)+" "+e.message);
  }
  const original=await page.evaluate(()=>window.__KOMA_P12.inspect());
  if(original.characterId!=="p0_character_001"||original.methodCount!==5||original.regionCount!==13)
   throw Error("P12 source viewer source registry mismatch "+JSON.stringify(original));
  for(const [angle,variant,part] of [
   [22.5,"anatomy","eye.near"],
   [22.5,"anatomy-strokes","hair.front"],
   [67.5,"anatomy-strokes","hair.front"],
   [67.5,"stroke-wide","ear.near"],
   [67.5,"affine-face","face.skin"],
   [72.5,"anatomy","nose"]
  ]){
   await page.evaluate(async state=>window.__KOMA_P12.choose(state.angle,state.variant,state.part),
      {angle,variant,part});
   const state=await page.evaluate(()=>window.__KOMA_P12.inspect());
   if(state.errors.length||state.current.angle!==angle||state.current.mode!==variant
      ||state.current.part!==part||state.current.verifiedImages!==3)
    throw Error("P12 original PNG check failed "+JSON.stringify(state));
   const filebase="yaw"+String(angle).replace(".","p")+"-"+variant+"-"+part.replaceAll(".","-");
   const record={angle,variant,semanticId:part,verifiedSourceImages:state.current.verifiedImages,
     gapRatio:state.current.gapRatio,screenshots:{}};
   for(const [role,selector] of [["motion","#motion"],["occlusion","#occlusion"]]){
    const file=path.join(output,filebase+"-"+role+".png");
    await page.locator(selector).screenshot({path:file});
    record.screenshots[role]={path:file,sha256:sha(file),bytes:fs.statSync(file).size};
   }
   images.push(record);
  }
  const qa={
   schema:"KOMA-P0-P12-MOTION-VARIANT-AND-OCCLUSION-BROWSER-QA-V1",
   characterId:"p0_character_001",
   sourceOriginalViewAngles:original.originalSourceViews,
   nativeSourceResolution:[1024,1024],
   methodCount:original.methodCount,
   sourcePartGapCount:original.regionCount,
   screens:images,
   screenshotCount:images.length*2,
   errors,failedRequests:networkFailures,
   status:images.length===6&&!errors.length&&!networkFailures.length?
          "PASS_REAL_SOURCE_ARTMESH_P12_REVIEW":"BROWSER_SOURCE_REVIEW_FAILED",
   artisticAcceptance:"PENDING_ORIGINAL_REFERENCE_REVIEW"
  };
  fs.writeFileSync(path.join(output,"browser-qa.json"),JSON.stringify(qa,null,2)+"\n");
  console.log(JSON.stringify({status:qa.status,
   originalSourceViews:qa.sourceOriginalViewAngles,methods:qa.methodCount,
   semanticGaps:qa.sourcePartGapCount,
   realBrowserScreenshots:qa.screenshotCount,errors,networkFailures},null,2));
  if(qa.status!=="PASS_REAL_SOURCE_ARTMESH_P12_REVIEW")process.exitCode=2;
 }finally{
  await browser.close();
  await new Promise(ok=>server.close(ok));
 }
}
run().catch(e=>{console.error(e.stack);server.close();process.exitCode=3;});
