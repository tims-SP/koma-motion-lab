#!/usr/bin/env node
"use strict";
/** Real Chromium checks for P0 67.5/72.5 painted ArtMesh and 37-frame VDD. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const root=path.resolve(__dirname,"../../.."),exp=path.resolve(__dirname,"..");
const output=path.resolve(process.env.KOMA_P14_BROWSER_OUT||
 path.join(exp,"private-assets/p14-authored-candidates/p14-browser"));
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||"playwright");
const sha=f=>crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const mime={".html":"text/html;charset=utf-8",".js":"text/javascript",".json":"application/json",
 ".png":"image/png",".jpg":"image/jpeg"};
const server=http.createServer((req,res)=>{
 try{
  const url=new URL(req.url,"http://localhost");
  const target=path.resolve(root,"."+decodeURIComponent(url.pathname));
  if(!target.startsWith(root+path.sep)||!fs.statSync(target).isFile())throw Error("bad path");
  res.writeHead(200,{"Content-Type":mime[path.extname(target)]||"application/octet-stream",
   "Cache-Control":"no-store"});
  fs.createReadStream(target).pipe(res);
 }catch{res.writeHead(404);res.end("Not Found");}
});
async function run(){
 fs.mkdirSync(output,{recursive:true});
 await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
 const browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
 const page=await browser.newPage({viewport:{width:1560,height:980},deviceScaleFactor:1});
 const errors=[],failedRequests=[],screens=[];
 page.on("pageerror",e=>errors.push(String(e)));
 page.on("requestfailed",r=>failedRequests.push(r.url()+" "+(r.failure()?.errorText||"")));
 try{
  const url="http://127.0.0.1:"+server.address().port+
   "/experiments/gif-multiview-keyparts-mvp/review/p14-painted-view.html";
  await page.goto(url,{waitUntil:"domcontentloaded",timeout:30000});
  try{await page.waitForFunction(()=>window.__KOMA_P14?.inspect().ready,null,{timeout:25000});}
  catch(e){
   const diag=await page.evaluate(()=>({status:document.querySelector("#status")?.textContent,
             state:window.__KOMA_P14?.inspect()}));
   throw Error("P14 source HTML "+JSON.stringify(diag)+" "+e.message);
  }
  const init=await page.evaluate(()=>window.__KOMA_P14.inspect());
  if(init.characterId!=="p0_character_001"||init.renderFrames!==37||init.semanticRoles!==13||
     init.paintedKeyViews.join(",")!=="67.5,72.5"||init.errors.length)
   throw Error("Original P0 P14 component provenance failed "+JSON.stringify(init));
  for(const [angle,partYaw,role] of [
   [45,67.5,"eye.near"],[65,67.5,"hair.front"],
   [67.5,67.5,"eye.near"],[70,72.5,"face.skin"],
   [72.5,72.5,"hair.ahoge"],[77.5,72.5,"hair.back"]
  ]){
   await page.evaluate(async vals=>window.__KOMA_P14.choose(vals.angle,vals.partYaw,vals.role),
    {angle,partYaw,role});
   const state=await page.evaluate(()=>window.__KOMA_P14.inspect());
   if(state.errors.length||!state.current||state.current.angle!==angle||
      state.current.partYaw!==partYaw||state.current.semanticId!==role||
      state.current.verifiedImages!==5)
    throw Error("P14 original-source SHA-256 mismatch "+JSON.stringify(state));
   const record={angle,paintedAngle:partYaw,semanticId:role,
                 originalSHA256VerifiedImages:5,screenshots:{}};
   const prefix="yaw"+String(angle).replace(".","p")+"-"+String(partYaw).replace(".","p")+
          "-"+role.replaceAll(".","-");
   for(const [kind,selector] of [["motion","#motion"],["semantic","#semantic"]]){
    const file=path.join(output,prefix+"-"+kind+".png");
    await page.locator(selector).screenshot({path:file});
    record.screenshots[kind]={path:file,sha256:sha(file),bytes:fs.statSync(file).size};
   }
   screens.push(record);
  }
  const qa={
   schema:"KOMA-P0-P14-REAL-CHROMIUM-PAINTED-ARTMESH-QA-V1",
   characterId:"p0_character_001",
   originalSourceAngles:[0,45,90],
   paintedCandidateAngles:[67.5,72.5],
   sourceRGBAFrames:37,
   semanticPartTypes:13,
   verifiedOriginalImagesPerSample:5,
   sourceScreenshots:screens,screenshotCount:screens.length*2,
   javascriptErrors:errors,failedRequests,
   status:screens.length===6&&!errors.length&&!failedRequests.length?
     "PASS_REAL_P0_PAINTED_KEYVIEW_REVIEW":"FAILED_SOURCE_REVIEW",
   artisticApproval:"PENDING_VISUAL_REVIEW_AT_65_AND_77P5"
  };
  fs.writeFileSync(path.join(output,"browser-qa.json"),JSON.stringify(qa,null,2)+"\n");
  console.log(JSON.stringify({status:qa.status,screenshots:qa.screenshotCount,
   semanticPartTypes:qa.semanticPartTypes,verifiedOriginalImages:5,
   errors,failedRequests},null,2));
  if(qa.status!=="PASS_REAL_P0_PAINTED_KEYVIEW_REVIEW")process.exitCode=2;
 }finally{await browser.close();await new Promise(ok=>server.close(ok));}
}
run().catch(e=>{console.error(e.stack);server.close();process.exitCode=3;});
