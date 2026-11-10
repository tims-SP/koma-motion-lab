#!/usr/bin/env node
"use strict";
/** Playwright verification of P15-11 generated painting sources. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const {chromium}=require("playwright");
const root=path.resolve(__dirname,"../../.."),exp=path.resolve(__dirname,"..");
const output=path.join(exp,"private-assets/p15-11-generation/browser");
const hash=f=>crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const mime={".html":"text/html;charset=utf-8",".js":"text/javascript",".png":"image/png",".jpg":"image/jpeg"};
const server=http.createServer((req,res)=>{
  try{
   const uri=new URL(req.url,"http://127.0.0.1");
   const file=path.resolve(root,"."+decodeURIComponent(uri.pathname));
   if(!file.startsWith(root+path.sep)||!fs.statSync(file).isFile())throw Error("Not found");
   res.writeHead(200,{"Content-Type":mime[path.extname(file)]||"application/octet-stream"});
   fs.createReadStream(file).pipe(res);
  }catch(e){res.writeHead(404);res.end("Not found")}
});
async function main(){
 fs.mkdirSync(output,{recursive:true});
 await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
 let browser;
 try{
  browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
  const errors=[],requests=[],captures=[];
  for(const viewport of [{name:"desktop",width:1440,height:900},{name:"mobile",width:390,height:844}]){
   const page=await browser.newPage({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1});
   page.on("pageerror",e=>errors.push(String(e)));
   page.on("requestfailed",r=>requests.push(r.url()+": "+r.failure()?.errorText));
   await page.goto("http://127.0.0.1:"+server.address().port+
       "/experiments/gif-multiview-keyparts-mvp/review/p15-11-keyview-art.html",
       {waitUntil:"domcontentloaded",timeout:30000});
   await page.waitForFunction(()=>window.__KOMA_P15_11?.ready,null,{timeout:30000});
   const witness=await page.evaluate(()=>window.__KOMA_P15_11);
   if(!witness.ready||witness.sourceCount!==6||witness.errors.length)throw Error("Source load failed");
   const dest=path.join(output,"p15-11-"+viewport.name+".png");
   await page.screenshot({path:dest,fullPage:true});
   captures.push({viewport:viewport.name,path:path.relative(exp,dest),sha256:hash(dest),
                  sourceCount:witness.sourceCount,sources:witness.sources});
   await page.close();
  }
  if(errors.length||requests.length)throw Error(JSON.stringify({errors,requests}));
  const qa={schema:"KOMA-P15-11-CHROMIUM-ARTWORK-REVIEW-V1",characterId:"p0_character_001",
    screenshots:captures,captureCount:captures.length,sourceImageLoads:12,
    javascriptErrors:errors,requestFailures:requests,
    status:"SOURCE_PREVIEW_AND_BROWSER_VERIFIED",
    formalArtAdmission:"PENDING_INDEPENDENT_ANATOMICAL_APPROVAL"};
  fs.writeFileSync(path.join(output,"qa.json"),JSON.stringify(qa,null,2)+"\n");
  console.log(JSON.stringify({status:qa.status,captures:qa.captureCount,loads:qa.sourceImageLoads,
                             errors:errors.length,requests:requests.length}));
 }finally{
  if(browser)await browser.close();
  await new Promise(resolve=>server.close(resolve));
 }
}
main().catch(e=>{console.error(e.stack);server.close();process.exitCode=1});
