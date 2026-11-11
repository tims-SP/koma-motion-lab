#!/usr/bin/env node
"use strict";
/** Real browser witness of P0 45-degree registered thirteen-role 65-degree arc. */
const {chromium}=require("/root/koma-motion-r1999/work/browser/node_modules/playwright");
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const ROOT=path.resolve(__dirname,"../private-assets/exports/p15-38-original-p0-arc-review");
const OUTPUT=path.join(ROOT,"browser");
const QA=path.resolve(__dirname,"../evidence/p15-38-browser-qa.json");
const YAW=[45,47.5,50,52.5,55,56.25,57.5,58.75,60,61.25,62.5,63.75,65];
const sha=p=>crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
async function main(){
 fs.mkdirSync(OUTPUT,{recursive:true});let browser;
 const report={schema:"KOMA-P15-38-45_TO65_CHROMIUM-V1",
  characterId:"p0_character_001",checks:[],screenshots:[],
  errors:[],failedRequests:[],artisticAdmission:"INDEPENDENT_ORIGINAL_REVIEW"};
 try{
  browser=await chromium.launch({headless:true,args:["--no-sandbox"]});
  for(const viewport of [{name:"desktop",width:1440,height:850},
                          {name:"mobile",width:390,height:844}]){
   const page=await browser.newPage({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1});
   page.on("pageerror",e=>report.errors.push(String(e)));
   page.on("requestfailed",r=>report.failedRequests.push(r.url()+" "+(r.failure()?.errorText||"unknown")));
   await page.goto("file://"+path.join(ROOT,"index.html"),{waitUntil:"load",timeout:40000});
   await page.waitForFunction(()=>window.__KOMA_P15_38?.snapshot().ready,null,{timeout:40000});
   for(let index=0;index<YAW.length;index++){
    for(const mode of ["compare","face","hair"]){
     const state=await page.evaluate(({index,mode})=>window.__KOMA_P15_38.select(index,mode),{index,mode});
     if(!state.ready||state.images.length!==4||state.errors.length||
          state.index!==index||state.mode!==mode)
      throw Error("Failed angle/mode "+JSON.stringify(state));
     if(state.images.some(x=>![443,1024].includes(x.width)||x.width!==x.height))
      throw Error("Invalid referenced image size");
     report.checks.push({viewport:viewport.name,angle:YAW[index],mode,
        loadedImages:state.images.length});
     const screenshot=(mode==="compare"&&
       (viewport.name==="desktop"&&[0,2,4,6,8,12].includes(index)||
        viewport.name==="mobile"&&[2,4,8,12].includes(index)))||
        (viewport.name==="desktop"&&index===2&&["face","hair"].includes(mode));
     if(screenshot){
      const name=viewport.name+"-yaw"+String(YAW[index]).replace(".","p")+"-"+mode+".png";
      const out=path.join(OUTPUT,name);
      await page.locator("#gallery").screenshot({path:out,timeout:40000});
      report.screenshots.push({viewport:viewport.name,angle:YAW[index],mode,
        path:path.relative(path.resolve(__dirname,".."),out),sha256:sha(out)});
     }
    }
   }
   await page.close();
  }
  if(report.errors.length||report.failedRequests.length)throw Error(JSON.stringify(report));
  report.status="P15_38_ORIGINAL_P0_EXTENDED_ARTMESH_HTML_VERIFIED";
  report.viewportChecks=report.checks.length;
  report.imageLoads=report.checks.reduce((n,x)=>n+x.loadedImages,0);
  report.screenshotCount=report.screenshots.length;
  fs.writeFileSync(QA,JSON.stringify(report,null,2)+"\n");
  console.log(JSON.stringify({status:report.status,checks:report.viewportChecks,
    loaded:report.imageLoads,screenshots:report.screenshotCount,
    javascriptErrors:report.errors.length,requestErrors:report.failedRequests.length}));
 }finally{if(browser)await browser.close()}
}
main().catch(e=>{console.error(e.stack);process.exitCode=1});
