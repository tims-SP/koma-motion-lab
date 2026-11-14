#!/usr/bin/env node
"use strict";
/** Real Chromium regression of nine original-P0 feature guided Mesh frames. */
const {chromium}=require("/root/koma-motion-r1999/work/browser/node_modules/playwright");
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const review=path.resolve(__dirname,"../private-assets/exports/p15-34-source-ink-mesh-review");
const QA=path.resolve(__dirname,"../evidence/p15-34-browser-qa.json");
const sha=file=>crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
async function main(){
 let browser;
 const result={schema:"KOMA-P15-34-CHROMIUM-V1",characterId:"p0_character_001",
   checks:[],screenshots:[],errors:[],failedRequests:[],
   productionRendererChanged:false,artisticallyAccepted:false};
 try{
  browser=await chromium.launch({headless:true,args:["--no-sandbox"]});
  for(const view of [{width:1440,height:900},{width:390,height:844}]){
   const page=await browser.newPage({viewport:view,deviceScaleFactor:1});
   page.on("pageerror",e=>result.errors.push(String(e)));
   page.on("requestfailed",r=>result.failedRequests.push(r.url()+": "+r.failure()?.errorText));
   await page.goto("file://"+path.join(review,"index.html"),{waitUntil:"load",timeout:30000});
   for(let i=0;i<9;i++){
    await page.locator("#slider").fill(String(i));
    await page.waitForFunction(()=>{
      const imgs=[...document.querySelectorAll("#cards img")];
      return imgs.length===7&&imgs.every(im=>im.complete&&im.naturalWidth>0);
    },{timeout:30000});
    const witness=await page.evaluate(()=>{
      const images=[...document.querySelectorAll("#cards img")];
      return {angle:window.__KOMA_P15_34.frames[+document.querySelector("#slider").value].yaw,
              images:images.map(x=>({width:x.naturalWidth,height:x.naturalHeight,
                                    source:x.getAttribute("src")}))};
    });
    if(witness.images.some(im=>!([443,1024].includes(im.width)&&im.width===im.height)))
      throw Error("Invalid RGBA canvas");
    result.checks.push({viewport:view.width,frame:i,angle:witness.angle,
                        sourceCount:witness.images.length});
    if([2,4,6].includes(i)){
     const f=path.join(review,"chromium-"+view.width+"-"+String(witness.angle).replace(".","p")+".png");
     await page.screenshot({path:f,fullPage:true});
     result.screenshots.push({viewport:view.width,angle:witness.angle,
        path:path.basename(f),sha256:sha(f)});
    }
   }
   await page.close();
  }
  if(result.errors.length||result.failedRequests.length)throw Error(JSON.stringify(result));
  result.status="NINE_FRAME_ROLE_MESH_REVIEW_VERIFIED";
  result.viewportChecks=result.checks.length;
  result.imageLoads=result.checks.reduce((sum,x)=>sum+x.sourceCount,0);
  result.screenshotCount=result.screenshots.length;
  fs.writeFileSync(QA,JSON.stringify(result,null,2)+"\n");
  console.log(JSON.stringify({status:result.status,checks:result.viewportChecks,
             images:result.imageLoads,screenshots:result.screenshotCount,
             errors:result.errors.length,requests:result.failedRequests.length}));
 }finally{if(browser)await browser.close()}
}
main().catch(e=>{console.error(e.stack);process.exitCode=1});
