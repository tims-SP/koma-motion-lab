#!/usr/bin/env node
"use strict";
/** P15-37 Chromium validation of nine poses and three source/role modes. */
const {chromium}=require("/root/koma-motion-r1999/work/browser/node_modules/playwright");
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const ROOT=path.resolve(__dirname,"../private-assets/exports/p15-37-temporal-art-review");
const OUT=path.join(ROOT,"browser");
const QA=path.resolve(__dirname,"../evidence/p15-37-browser-qa.json");
const sha=p=>crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
async function main(){
 fs.mkdirSync(OUT,{recursive:true});let browser;
 const report={schema:"KOMA-P15-37-PAINTED-VDD-CHROMIUM-V1",
  characterId:"p0_character_001",checks:[],screenshots:[],
  errors:[],failedRequests:[],artisticGate:"SOURCE_PAINTING_REVIEW"};
 try{
  browser=await chromium.launch({headless:true,args:["--no-sandbox"]});
  for(const viewport of [{name:"desktop",width:1440,height:850},
                          {name:"mobile",width:390,height:844}]){
   const page=await browser.newPage({viewport:{width:viewport.width,height:viewport.height},
       deviceScaleFactor:1});
   page.on("pageerror",e=>report.errors.push(String(e)));
   page.on("requestfailed",req=>report.failedRequests.push(req.url()+" "+(req.failure()?.errorText||"unknown")));
   await page.goto("file://"+path.join(ROOT,"index.html"),{waitUntil:"load",timeout:40000});
   await page.waitForFunction(()=>window.__KOMA_P15_37?.result().ready,null,{timeout:40000});
   for(let i=0;i<9;i++){
    for(const mode of ["compare","parts","sources"]){
     const data=await page.evaluate(({i,mode})=>window.__KOMA_P15_37.select(i,mode),{i,mode});
     if(!data.ready||data.images.length!==4||data.errors.length||data.index!==i||data.mode!==mode)
      throw Error("Failed review frame "+JSON.stringify(data));
     if(data.images.some(x=>x.width!==x.height||![443,1024].includes(x.width)))
      throw Error("Unexpected semantic canvas");
     report.checks.push({viewport:viewport.name,angle:windowAngle(i),mode,
       sourceCount:data.images.length});
     const needed=mode==="compare"&&
      (viewport.name==="desktop"&&[0,2,3,4,8].includes(i) ||
       viewport.name==="mobile"&&[2,4,8].includes(i))
       || mode==="parts"&&viewport.name==="desktop"&&[2,4].includes(i);
     if(needed){
      const filename=viewport.name+"-yaw"+String(windowAngle(i)).replace(".","p")+"-"+mode+".png";
      const file=path.join(OUT,filename);
      await page.locator("#gallery").screenshot({path:file,timeout:45000});
      report.screenshots.push({viewport:viewport.name,angle:windowAngle(i),mode,
        path:path.relative(path.resolve(__dirname,".."),file),sha256:sha(file)});
     }
    }
   }
   await page.close();
  }
  if(report.errors.length||report.failedRequests.length)
   throw Error(JSON.stringify({errors:report.errors,requests:report.failedRequests}));
  report.status="P15_37_NINE_FRAME_THREE_MODE_CHROMIUM_VERIFIED";
  report.viewportChecks=report.checks.length;
  report.imageLoads=report.checks.reduce((sum,r)=>sum+r.sourceCount,0);
  report.screenshotCount=report.screenshots.length;
  fs.writeFileSync(QA,JSON.stringify(report,null,2)+"\n");
  console.log(JSON.stringify({status:report.status,checks:report.viewportChecks,
    images:report.imageLoads,screenshots:report.screenshotCount,errors:0}));
 }finally{if(browser)await browser.close()}
}
function windowAngle(i){return [55,56.25,57.5,58.75,60,61.25,62.5,63.75,65][i]}
main().catch(e=>{console.error(e.stack);process.exitCode=1});
