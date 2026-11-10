#!/usr/bin/env node
"use strict";
/** Chromium P0 generated-keyview visual QA with per-image SHA verification. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const work=path.resolve(__dirname,"../../.."),exp=path.resolve(__dirname,"..");
const output=path.join(exp,"private-assets/p15-independent-candidates/browser");
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||"playwright");
const hash=f=>crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const mime={".html":"text/html;charset=utf-8",".js":"text/javascript",".json":"application/json",".png":"image/png"};
const server=http.createServer((req,res)=>{
 try{
  const loc=new URL(req.url,"http://localhost");
  const p=path.resolve(work,"."+decodeURIComponent(loc.pathname));
  if(!p.startsWith(work+path.sep)||!fs.statSync(p).isFile())throw Error("missing source");
  res.writeHead(200,{"Content-Type":mime[path.extname(p)]||"application/octet-stream","Cache-Control":"no-store"});
  fs.createReadStream(p).pipe(res);
 }catch{res.writeHead(404);res.end("Not Found")}
});
async function run(){
 fs.mkdirSync(output,{recursive:true});
 await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
 const browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
 const page=await browser.newPage({viewport:{width:1720,height:720},deviceScaleFactor:1});
 const errors=[],requests=[],screens=[];
 page.on("pageerror",e=>errors.push(String(e)));
 page.on("requestfailed",r=>requests.push(r.url()+":"+r.failure()?.errorText));
 try{
  await page.goto("http://127.0.0.1:"+server.address().port+
    "/experiments/gif-multiview-keyparts-mvp/review/p15-06-keyview-art.html",{waitUntil:"domcontentloaded",timeout:30000});
  await page.waitForFunction(()=>window.__KOMA_P15_06?.inspect().ready,null,{timeout:25000});
  const samples=[
   [65,"hair.back",false],[65,"face.skin",false],[65,"eye.near",false],
   [65,"hair.front",false],[77.5,"hair.back",false],[77.5,"face.skin",false],
   [77.5,"hair.back",true],[77.5,"hair.side",true]
  ];
  for(const [angle,role,underpaint] of samples){
   await page.evaluate(async x=>window.__KOMA_P15_06.choose(...x),[angle,role,underpaint]);
   const data=await page.evaluate(()=>window.__KOMA_P15_06.inspect());
   if(!data.ready||data.errors.length||data.verifiedImages!==4||!data.sourceMatch||
      data.yaw!==angle||data.role!==role||data.underpaint!==underpaint)
    throw Error("P15 HTML source validation failed: "+JSON.stringify(data));
   const filename="yaw"+String(angle).replace(".","p")+"-"+role.replace(".","-")+
     (underpaint?"-hidden":"")+".png";
   const file=path.join(output,filename);
   await page.locator("#review").screenshot({path:file});
   screens.push({yaw:angle,role,underpaint,sourceImagesHashVerified:4,
                 path:path.relative(exp,file),sha256:hash(file),bytes:fs.statSync(file).size});
  }
  const qa={
   schema:"KOMA-P0-P15-06-INDEPENDENT-KEYVIEW-CHROMIUM-QA-V1",
   characterId:"p0_character_001",
   browser:"Chromium Playwright",
   status:"PASS_SOURCE_HASHED_GENERATED_KEYVIEW_BROWSER_REVIEW",
   samples:screens,
   sourceImagesHashVerified:screens.reduce((n,x)=>n+x.sourceImagesHashVerified,0),
   screenshotCount:screens.length,
   javascriptErrors:errors,
   failedRequests:requests,
   artisticAcceptance:"PENDING_INDEPENDENT_VISUAL_APPROVAL"
  };
  fs.writeFileSync(path.join(output,"qa.json"),JSON.stringify(qa,null,2)+"\n");
  console.log(JSON.stringify({status:qa.status,screenshotCount:qa.screenshotCount,
    sourceImagesHashVerified:qa.sourceImagesHashVerified,errors,requests},null,2));
 }finally{await browser.close();await new Promise(ok=>server.close(ok))}
}
run().catch(e=>{console.error(e.stack);server.close();process.exitCode=2});
