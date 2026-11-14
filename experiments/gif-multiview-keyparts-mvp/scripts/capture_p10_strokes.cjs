#!/usr/bin/env node
"use strict";
/** P10 original P0 3-view line-identity HTML verification in true Chromium. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const repo=path.resolve(__dirname,"../../..");
const exp=path.resolve(__dirname,"..");
const out=path.resolve(process.env.KOMA_P10_BROWSER_OUT||path.join(exp,"private-assets/p10-stroke-identity/browser"));
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||"playwright");
const sha=file=>crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const types={".html":"text/html;charset=utf-8",".js":"application/javascript",".json":"application/json",".png":"image/png",".jpg":"image/jpeg",".gif":"image/gif"};
const server=http.createServer((request,response)=>{
 try{
  const url=new URL(request.url,"http://localhost");
  const target=path.resolve(repo,"."+decodeURIComponent(url.pathname));
  if(!target.startsWith(repo+path.sep)||!fs.statSync(target).isFile())throw Error("Bad path");
  response.writeHead(200,{"Content-Type":types[path.extname(target)]||"application/octet-stream","Cache-Control":"no-store"});
  fs.createReadStream(target).pipe(response);
 }catch{response.writeHead(404);response.end("Not Found");}
});
async function run(){
 fs.mkdirSync(out,{recursive:true});
 await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
 const browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
 const page=await browser.newPage({viewport:{width:1610,height:970},deviceScaleFactor:1});
 const errors=[],networkFailures=[],shots=[];
 page.on("pageerror",e=>errors.push(String(e)));
 page.on("requestfailed",r=>networkFailures.push(r.url()+" "+(r.failure()?.errorText||"")));
 try{
  const url="http://127.0.0.1:"+server.address().port+"/experiments/gif-multiview-keyparts-mvp/review/p10-stroke.html";
  await page.goto(url,{waitUntil:"domcontentloaded",timeout:30000});
  try{
   await page.waitForFunction(()=>window.__KOMA_P10?.inspect().ready,null,{timeout:15000});
  }catch(error){
   const diag=await page.evaluate(()=>({status:document.querySelector("#status")?.textContent,inspect:window.__KOMA_P10?.inspect()}));
   throw Error("P10 viewer first paint "+JSON.stringify(diag)+" "+error.message);
  }
  const first=await page.evaluate(()=>window.__KOMA_P10.inspect());
  if(first.characterId!=="p0_character_001"||first.semanticPairs!==22||first.strokeCandidates!==24||first.originalRGBAFrames!==37||first.errors.length)
   throw Error("P0 stroke QA source registry differs "+JSON.stringify(first));
  for(const [pair,role,confidence,yaw] of [
   ["0-45","hair.front",0.45,22.5],
   ["0-45","eye.near",0.45,22.5],
   ["0-45","hair.ahoge",0.45,22.5],
   ["45-90","hair.front",0.45,67.5],
   ["45-90","face.skin",0.45,67.5],
   ["45-90","hair.front",0.45,72.5]
  ]){
   await page.evaluate(async vals=>window.__KOMA_P10.choose(vals.pair,vals.role,vals.confidence,vals.yaw),
                       {pair,role,confidence,yaw});
   const stat=await page.evaluate(()=>window.__KOMA_P10.inspect());
   if(stat.errors.length||stat.last.pair!==pair||stat.last.role!==role||stat.last.angle!==yaw||stat.last.verifiedSources!==3)
    throw Error("Stroke P0 browser provenance failed "+JSON.stringify(stat));
   const name="p10-"+pair+"-"+role.replaceAll(".","-")+"-yaw"+String(yaw).replace(".","p")+".png";
   const file=path.join(out,name);
   await page.locator("#panel").screenshot({path:file});
   shots.push({pair,semanticId:role,threshold:confidence,yaw,
               displayedStrokeCandidates:stat.last.visible,
               path:file,sha256:sha(file),bytes:fs.statSync(file).size});
  }
  const qa={
   schema:"KOMA-P0-P10-INK_STROKE-BROWSER-QA-V1",
   characterId:"p0_character_001",
   method:"P0 original source RGBA SHA-256 + P8 original-derived intermediate renderer + P10 candidate stroke overlays",
   semanticPairs:first.semanticPairs,
   strokeCandidates:first.strokeCandidates,
   nativeRGBAFrameCount:first.originalRGBAFrames,
   screenshots:shots,
   screenshotCount:shots.length,
   errors,failedRequests:networkFailures,
   status:shots.length===6&&!errors.length&&!networkFailures.length?
        "PASS_REAL_ORIGINAL_P0_STROKE_REVIEW":"FAILED_BROWSER_REVIEW",
   artisticApproval:"PENDING"
  };
  fs.writeFileSync(path.join(out,"browser-qa.json"),JSON.stringify(qa,null,2)+"\n");
  console.log(JSON.stringify({status:qa.status,sourcePairs:qa.semanticPairs,
     sourceStrokeCandidates:qa.strokeCandidates,realBrowserScreenshots:qa.screenshotCount,
     errors,failedRequests:networkFailures},null,2));
  if(qa.status!=="PASS_REAL_ORIGINAL_P0_STROKE_REVIEW")process.exitCode=2;
 }finally{
  await browser.close();
  await new Promise(ok=>server.close(ok));
 }
}
run().catch(e=>{console.error(e.stack);server.close();process.exitCode=3;});
