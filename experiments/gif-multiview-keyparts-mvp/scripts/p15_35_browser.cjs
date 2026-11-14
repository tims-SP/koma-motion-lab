#!/usr/bin/env node
"use strict";
/** Browser/geometry QA for P15-35 independent 2.5D depth and hair UV review. */
const {chromium}=require("/root/koma-motion-r1999/work/browser/node_modules/playwright");
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const ROOT=path.resolve(__dirname,"../private-assets/exports/p15-35-face-depth-hair-review");
const QA=path.resolve(__dirname,"../evidence/p15-35-browser-qa.json");
const sha=p=>crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
async function main(){
 const result={schema:"KOMA-P15-35-CHROMIUM-DEPTH-REVIEW-V1",
   characterId:"p0_character_001",checks:[],captures:[],
   pageErrors:[],failedRequests:[],formalArtisticAcceptance:false};
 let browser;
 try{
  browser=await chromium.launch({headless:true,args:["--no-sandbox"]});
  for(const vp of [{width:1440,height:900},{width:390,height:844}]){
   const p=await browser.newPage({viewport:vp,deviceScaleFactor:1});
   p.on("pageerror",e=>result.pageErrors.push(String(e)));
   p.on("requestfailed",r=>result.failedRequests.push(r.url()+": "+r.failure()?.errorText));
   await p.goto("file://"+path.join(ROOT,"index.html"),{waitUntil:"load"});
   for(let frame=0;frame<9;frame++){
    await p.locator("#slider").fill(String(frame));
    await p.waitForFunction(()=>{
     const images=[...document.querySelectorAll("#cards img")];
     return images.length===11&&images.every(x=>x.complete&&x.naturalWidth>0);
    },{timeout:30000});
    const current=await p.evaluate(()=>{
     const idx=Number(document.querySelector("#slider").value);
     return {angle:window.__KOMA_P15_35.data[idx].yaw,
       images:[...document.querySelectorAll("#cards img")].map(x=>({
         source:x.getAttribute("src"),width:x.naturalWidth,height:x.naturalHeight}))};
    });
    if(current.images.some(im=>im.width!==im.height||![443,1024].includes(im.width)))
     throw Error("Unexpected role layer or full-canvas size");
    result.checks.push({viewport:vp.width,frame,angle:current.angle,images:current.images.length});
    if([2,4,6].includes(frame)){
     const f=path.join(ROOT,"chromium-"+vp.width+"-yaw"+String(current.angle).replace(".","p")+".png");
     await p.screenshot({path:f,fullPage:true});
     result.captures.push({viewport:vp.width,angle:current.angle,
       path:path.basename(f),sha256:sha(f)});
    }
   }
   await p.close();
  }
  if(result.pageErrors.length||result.failedRequests.length)throw Error(JSON.stringify(result));
  result.status="P15_35_NINE_FRAME_DEPTH_REVIEW_VERIFIED";
  result.viewportChecks=result.checks.length;
  result.imageLoads=result.checks.reduce((n,x)=>n+x.images,0);
  result.screenshotCount=result.captures.length;
  fs.writeFileSync(QA,JSON.stringify(result,null,2)+"\n");
  console.log(JSON.stringify({status:result.status,checks:result.viewportChecks,
   images:result.imageLoads,screenshots:result.screenshotCount,
   errors:result.pageErrors.length+result.failedRequests.length}));
 }finally{if(browser)await browser.close()}
}
main().catch(e=>{console.error(e.stack);process.exitCode=1});
