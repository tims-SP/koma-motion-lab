#!/usr/bin/env node
"use strict";
/** Real Chromium keyframe and HTML preview QA for 2.75D P0 P15-07. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),
      crypto=require("node:crypto");
const root=path.resolve(__dirname,"../../..");
const exp=path.resolve(__dirname,"..");
const out=path.join(exp,"private-assets/p15-07-browser");
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||"playwright");
const sha=f=>crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const mime={".html":"text/html;charset=utf-8",".js":"text/javascript",
            ".json":"application/json",".png":"image/png",".jpg":"image/jpeg"};
const server=http.createServer((req,res)=>{
  try{
    const requested=new URL(req.url,"http://127.0.0.1");
    const f=path.resolve(root,"."+decodeURIComponent(requested.pathname));
    if(!f.startsWith(root+path.sep)||!fs.statSync(f).isFile())throw Error("not found");
    res.writeHead(200,{"Content-Type":mime[path.extname(f)]||"application/octet-stream",
                       "Cache-Control":"no-store"});
    fs.createReadStream(f).pipe(res);
  }catch{
    res.writeHead(404,{"Content-Type":"text/plain"});res.end("not found");
  }
});
async function main(){
  fs.mkdirSync(out,{recursive:true});
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  let browser;
  try{
    browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
    const page=await browser.newPage({viewport:{width:1530,height:770},deviceScaleFactor:1});
    const errors=[],requests=[],screens=[];
    page.on("pageerror",e=>errors.push(String(e)));
    page.on("requestfailed",r=>requests.push(r.url()+": "+r.failure()?.errorText));
    await page.goto("http://127.0.0.1:"+server.address().port+
      "/experiments/gif-multiview-keyparts-mvp/review/p15-07-view.html",
      {waitUntil:"domcontentloaded",timeout:30000});
    await page.waitForFunction(()=>window.__KOMA_P15_07?.inspect().ready,null,{timeout:30000});
    for(const yaw of [45,55,65,67.5,72.5,77.5,85,90]){
      const result=await page.evaluate(y=>window.__KOMA_P15_07.setAngle(y),yaw);
      if(!result.ready||result.errors.length||
         result.loaded.length!==([65,67.5,72.5,77.5].includes(yaw)?4:3))
        throw Error("P15-07 HTML frame QA rejected: "+JSON.stringify(result));
      const name="yaw"+String(yaw).replace(".","p")+".png";
      const f=path.join(out,name);
      await page.locator("#gallery").screenshot({path:f});
      screens.push({yaw,sourceImagesLoaded:result.loaded.length,
        imageSizes:result.loaded.map(x=>[x.width,x.height]),
        sourcePaths:result.loaded.map(x=>x.path),
        screenPath:path.relative(exp,f),sha256:sha(f),bytes:fs.statSync(f).size});
    }
    const qa={schema:"KOMA-P15-07-CHROMIUM-SOURCE-INSPECTION-V1",
      characterId:"p0_character_001",
      browser:"Chromium Playwright",
      screenshotCount:screens.length,
      verifiedSourceImageLoads:screens.reduce((n,s)=>n+s.sourceImagesLoaded,0),
      screenshots:screens,
      javascriptErrors:errors,
      failedRequests:requests,
      status:"HTML_INTERACTIVE_SOURCE_LOAD_PASS",
      artisticAcceptance:"REVIEW_REQUIRED"};
    fs.writeFileSync(path.join(out,"qa.json"),JSON.stringify(qa,null,2)+"\n");
    console.log(JSON.stringify({status:qa.status,frames:qa.screenshotCount,
      loadedImages:qa.verifiedSourceImageLoads,errors,requests}));
  }finally{
    if(browser)await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
}
main().catch(e=>{console.error(e.stack);server.close();process.exitCode=1});
