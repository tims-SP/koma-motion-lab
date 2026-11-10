#!/usr/bin/env node
"use strict";
/** P15-12 live Chromium angle and landmark review. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const {chromium}=require("playwright");
const root=path.resolve(__dirname,"../../.."),exp=path.resolve(__dirname,"..");
const output=path.join(exp,"private-assets/p15-12-camera-proxy/browser");
const hash=p=>crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
const mime={".html":"text/html;charset=utf-8",".png":"image/png",".jpg":"image/jpeg",".js":"text/javascript"};
const server=http.createServer((req,res)=>{
 try{
  const url=new URL(req.url,"http://localhost"),full=path.resolve(root,"."+decodeURIComponent(url.pathname));
  if(!full.startsWith(root+path.sep)||!fs.statSync(full).isFile())throw Error("not found");
  res.writeHead(200,{"Content-Type":mime[path.extname(full)]||"application/octet-stream"});
  fs.createReadStream(full).pipe(res);
 }catch(e){res.writeHead(404);res.end("missing")}
});
async function run(){
 fs.mkdirSync(output,{recursive:true});
 await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
 let browser;
 try{
  browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
  const shots=[],errors=[],requests=[];
  for(const setting of [{name:"desktop",width:1500,height:820,markers:false},
                         {name:"mobile",width:390,height:844,markers:true}]){
   const page=await browser.newPage({viewport:{width:setting.width,height:setting.height},deviceScaleFactor:1});
   page.on("pageerror",e=>errors.push(String(e)));
   page.on("requestfailed",r=>requests.push(r.url()+": "+r.failure()?.errorText));
   await page.goto("http://127.0.0.1:"+server.address().port+
     "/experiments/gif-multiview-keyparts-mvp/review/p15-12-pose-calibration.html",
     {waitUntil:"domcontentloaded",timeout:30000});
   await page.waitForFunction(()=>window.__KOMA_P15_12?.snapshot().ready,null,{timeout:30000});
   for(const angle of [57.5,60]){
     const status=await page.evaluate(({angle,markers})=>window.__KOMA_P15_12.select(angle,markers),
                                       {angle,markers:setting.markers});
     if(!status.ready||status.images.length!==3||status.errors.length)throw Error("Invalid image source "+JSON.stringify(status));
     const file=path.join(output,setting.name+"-yaw"+String(angle).replace(".","p")+".png");
     await page.locator(".gallery").screenshot({path:file});
     shots.push({viewport:setting.name,angle,markers:setting.markers,
       sourceCount:status.images.length,sourceImages:status.images,
       relativePath:path.relative(exp,file),sha256:hash(file)});
   }
   await page.close();
  }
  if(errors.length||requests.length)throw Error(JSON.stringify({errors,requests}));
  const qa={schema:"KOMA-P15-12-CHROMIUM-CAMERA-REVIEW-V1",characterId:"p0_character_001",
    status:"INTERACTIVE_CAMERA_PROXY_HTML_VERIFIED",captures:shots,
    screenshotCount:shots.length,sourceImageLoads:shots.reduce((x,y)=>x+y.sourceCount,0),
    javascriptErrors:errors,failedRequests:requests,artisticAdmission:"REVIEW_REQUIRED"};
  fs.writeFileSync(path.join(output,"qa.json"),JSON.stringify(qa,null,2)+"\n");
  console.log(JSON.stringify({status:qa.status,captures:qa.screenshotCount,images:qa.sourceImageLoads,
    jsErrors:errors.length,failedRequests:requests.length}));
 }finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve))}
}
run().catch(e=>{console.error(e.stack);server.close();process.exitCode=1});
