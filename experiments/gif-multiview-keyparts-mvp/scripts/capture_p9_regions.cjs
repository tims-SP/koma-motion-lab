#!/usr/bin/env node
"use strict";
/** Inspect approved original P0 source color-piece correspondences in Chromium. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const repo=path.resolve(__dirname,"../../..");
const exp=path.resolve(__dirname,"..");
const out=path.resolve(process.env.KOMA_P9_BROWSER_OUT||path.join(exp,"private-assets/p9-region-correspondence/browser"));
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||"playwright");
const sha=p=>crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
const types={".html":"text/html;charset=utf-8",".js":"application/javascript",".json":"application/json",".png":"image/png",".jpg":"image/jpeg",".gif":"image/gif"};
const server=http.createServer((request,response)=>{
 try{
  const url=new URL(request.url,"http://localhost");
  const target=path.resolve(repo,"."+decodeURIComponent(url.pathname));
  if(!target.startsWith(repo+path.sep)||!fs.statSync(target).isFile())throw Error("bad file");
  response.writeHead(200,{"Content-Type":types[path.extname(target)]||"application/octet-stream",
                          "Cache-Control":"no-store"});
  fs.createReadStream(target).pipe(response);
 }catch{
  response.writeHead(404);response.end("Not Found");
 }
});
async function run(){
 fs.mkdirSync(out,{recursive:true});
 await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
 const browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
 const page=await browser.newPage({viewport:{width:1400,height:980},deviceScaleFactor:1});
 const errors=[],networkFailures=[],shots=[];
 page.on("pageerror",e=>errors.push(String(e)));
 page.on("requestfailed",r=>networkFailures.push(r.url()+" "+(r.failure()?.errorText||"")));
 try{
  const url="http://127.0.0.1:"+server.address().port+"/experiments/gif-multiview-keyparts-mvp/review/p9-correspondence.html";
  await page.goto(url,{waitUntil:"domcontentloaded",timeout:30000});
  try {
   await page.waitForFunction(()=>window.__KOMA_P9?.inspect().ready,null,{timeout:15000});
  }catch(error){
   const diagnostic=await page.evaluate(()=>({
    state:window.__KOMA_P9?.inspect(),
    status:document.querySelector("#status")?.textContent,
    semanticOptions:[...document.querySelectorAll("#semantic option")].map(x=>x.value)
   }));
   throw Error("P9 viewer load: "+JSON.stringify(diagnostic)+"; "+error.message);
  }
  const first=await page.evaluate(()=>window.__KOMA_P9.inspect());
  if(first.characterId!=="p0_character_001"||first.sourcePairs!==22||first.matchedRegions!==155||first.errors.length)
   throw Error("Original P0 source-correspondence registration failed "+JSON.stringify(first));
  for(const [pair,role,cost] of [
   ["0-45","face.skin",47],
   ["0-45","hair.front",47],
   ["0-45","eye.near",47],
   ["45-90","face.skin",47],
   ["45-90","eye.near",47],
   ["45-90","hair.front",47]
  ]){
   await page.evaluate(async ({pair,role,cost})=>window.__KOMA_P9.choose(pair,role,cost),{pair,role,cost});
   const state=await page.evaluate(()=>window.__KOMA_P9.inspect());
   if(!state.ready||state.errors.length||state.current.pair!==pair||state.current.role!==role
      ||state.current.originalLayers.length!==2)
    throw Error("P0 original correspondence render mismatch "+JSON.stringify(state));
   const name="region-"+pair+"-"+role.replaceAll(".","-")+".png";
   const file=path.join(out,name);
   await page.locator("#viewer").screenshot({path:file});
   shots.push({pair,semanticId:role,threshold:cost,registeredRegionMatches:state.current.visible,
               originalLayerHashes:state.current.originalLayers,
               path:file,sha256:sha(file),bytes:fs.statSync(file).size});
  }
  const qa={
   schema:"KOMA-P0-P9-REGION-MATCH-BROWSER-QA-V1",
   characterId:"p0_character_001",
   browser:"Chromium Canvas2D original RGBA source",
   sourceRegisteredPairs:first.sourcePairs,
   sourceRegisteredRegions:first.matchedRegions,
   screenshotCount:shots.length,
   screenshots:shots,
   errors,failedRequests:networkFailures,
   status:shots.length===6&&!errors.length&&!networkFailures.length?
     "PASS_REAL_P0_REGION_CORRESPONDENCE_VIEW":"REVIEW_BROWSER_CHECK"
  };
  fs.writeFileSync(path.join(out,"browser-qa.json"),JSON.stringify(qa,null,2)+"\n");
  console.log(JSON.stringify({status:qa.status,
    registeredPairs:qa.sourceRegisteredPairs,
    registeredRegions:qa.sourceRegisteredRegions,
    screenshots:qa.screenshotCount,
    errors,failedRequests:networkFailures},null,2));
  if(qa.status!=="PASS_REAL_P0_REGION_CORRESPONDENCE_VIEW")process.exitCode=2;
 }finally{
  await browser.close();
  await new Promise(ok=>server.close(ok));
 }
}
run().catch(e=>{console.error(e.stack);server.close();process.exitCode=3;});
