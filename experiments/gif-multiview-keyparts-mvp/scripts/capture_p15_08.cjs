#!/usr/bin/env node
"use strict";
/** Chromium QA for original P0 yaw45, independent yaw65 and two yaw55 candidates. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const root=path.resolve(__dirname,"../../.."),exp=path.resolve(__dirname,"..");
const out=path.join(exp,"private-assets/p15-08-yaw055/browser");
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||"playwright");
const hash=file=>crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const types={".html":"text/html;charset=utf8",".js":"text/javascript",".png":"image/png",".jpg":"image/jpeg"};
const server=http.createServer((req,res)=>{
  try {
    const url=new URL(req.url,"http://localhost");
    const source=path.resolve(root,"."+decodeURIComponent(url.pathname));
    if(!source.startsWith(root+path.sep)||!fs.statSync(source).isFile())throw Error("not found");
    res.writeHead(200,{"Content-Type":types[path.extname(source)]||"application/octet-stream",
                       "Cache-Control":"no-store"});
    fs.createReadStream(source).pipe(res);
  }catch{res.writeHead(404);res.end("not found")}
});
async function run(){
 fs.mkdirSync(out,{recursive:true});
 await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
 let browser;
 try {
  browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
  const page=await browser.newPage({viewport:{width:1660,height:730},deviceScaleFactor:1});
  const errors=[],failed=[],captures=[];
  page.on("pageerror",e=>errors.push(String(e)));
  page.on("requestfailed",req=>failed.push(req.url()+":"+req.failure()?.errorText));
  await page.goto("http://127.0.0.1:"+server.address().port+
    "/experiments/gif-multiview-keyparts-mvp/review/p15-08-mid-angle.html",
    {waitUntil:"domcontentloaded",timeout:25000});
  for(const alpha of [true,false]){
    await page.locator("#alpha").setChecked(alpha);
    await page.waitForFunction(w=>window.__KOMA_P15_08?.ready&&window.__KOMA_P15_08.alpha===w,alpha,{timeout:25000});
    const info=await page.evaluate(()=>window.__KOMA_P15_08);
    if(info.errors.length||info.loaded.length!==5)throw Error("P15-08 source gallery incomplete");
    const f=path.join(out,alpha?"rgba-gallery.png":"source-gallery.png");
    await page.locator("#gallery").screenshot({path:f});
    captures.push({alpha,sources:info.loaded.map(i=>i.path),
                   capturedPath:path.relative(exp,f),sha256:hash(f),bytes:fs.statSync(f).size});
  }
  if(errors.length||failed.length)throw Error("Browser failed: "+JSON.stringify({errors,failed}));
  const report={schema:"KOMA-P15-08-POSE-CANDIDATE-CHROMIUM-QA-V1",
    characterId:"p0_character_001",
    status:"SOURCE_IMAGES_AND_ALPHA_GALLERY_PASS",
    captures,
    imageLoads:10,
    screenshotCount:2,
    pageErrors:errors,
    failedRequests:failed,
    artisticAcceptance:"PENDING_PHYSICAL_POSE_CORRESPONDENCE"};
  fs.writeFileSync(path.join(out,"qa.json"),JSON.stringify(report,null,2)+"\n");
  process.stdout.write(JSON.stringify({status:report.status,captures:2,images:10,errors,failed})+"\n");
 }finally{
  if(browser)await browser.close();
  await new Promise(ok=>server.close(ok));
 }
}
run().catch(err=>{console.error(err.stack);server.close();process.exitCode=1});
