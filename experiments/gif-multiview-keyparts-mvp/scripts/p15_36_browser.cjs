#!/usr/bin/env node
"use strict";
/** Chromium QA for P15-36 source image, semantic RGBA and underpaint review. */
const {chromium}=require("/root/koma-motion-r1999/work/browser/node_modules/playwright");
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const ROOT=path.resolve(__dirname,"../private-assets/exports/p15-36-original-keypart-review");
const QA=path.resolve(__dirname,"../evidence/p15-36-browser-qa.json");
const sha=p=>crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
async function main(){
 let browser;
 const report={schema:"KOMA-P15-36-KEYPART-CHROMIUM-V1",
  characterId:"p0_character_001",checks:[],screenshots:[],pageErrors:[],failedRequests:[],
  newlyPaintedCompleteKeyviewsAccepted:0};
 try{
  browser=await chromium.launch({headless:true,args:["--no-sandbox"]});
  for(const v of [{name:"desktop",width:1440,height:880},{name:"mobile",width:390,height:844}]){
   const page=await browser.newPage({viewport:{width:v.width,height:v.height},deviceScaleFactor:1});
   page.on("pageerror",e=>report.pageErrors.push(String(e)));
   page.on("requestfailed",r=>report.failedRequests.push(r.url()+": "+r.failure()?.errorText));
   await page.goto("file://"+path.join(ROOT,"index.html"),{waitUntil:"load",timeout:30000});
   await page.waitForFunction(()=>window.__KOMA_P15_36?.result().ready,null,{timeout:30000});
   for(const yaw of [57.5,60]){
    for(const mode of ["compare","parts","hidden"]){
     const state=await page.evaluate(({yaw,mode})=>window.__KOMA_P15_36.select(yaw,mode),{yaw,mode});
     if(!state.ready||state.images.length!==4||state.errors.length)throw Error("Source witness missing: "+JSON.stringify(state));
     if(state.images.some(x=>![443,1024].includes(x.width)||x.width!==x.height))throw Error("Non-square canvas");
     report.checks.push({viewport:v.name,yaw,mode,imageCount:state.images.length,
                         sources:state.images});
     if(v.name==="desktop"||mode==="compare"){
      const name=v.name+"-yaw"+String(yaw).replace(".","p")+"-"+mode+".png";
      const target=path.join(ROOT,name);
      await page.locator("#gallery").screenshot({path:target,timeout:30000});
      report.screenshots.push({viewport:v.name,yaw,mode,file:name,sha256:sha(target)});
     }
    }
   }
   await page.close();
  }
  if(report.pageErrors.length||report.failedRequests.length)throw Error(JSON.stringify(report));
  report.status="P15_36_KEYPART_SOURCE_HTML_VERIFIED";
  report.viewportChecks=report.checks.length;
  report.imageLoads=report.checks.reduce((sum,x)=>sum+x.imageCount,0);
  report.screenshotCount=report.screenshots.length;
  fs.writeFileSync(QA,JSON.stringify(report,null,2)+"\n");
  console.log(JSON.stringify({status:report.status,checks:report.viewportChecks,
   images:report.imageLoads,screenshots:report.screenshotCount,errors:0}));
 }finally{if(browser)await browser.close()}
}
main().catch(e=>{console.error(e.stack);process.exitCode=1});
