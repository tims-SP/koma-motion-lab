#!/usr/bin/env node
"use strict";
/** P13 verify actual P0 source-aware 37-frame motion and 26 RGBA parts in Chromium. */
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const root=path.resolve(__dirname,"../../.."),exp=path.resolve(__dirname,"..");
const out=path.resolve(process.env.KOMA_P13_BROWSER_OUT||path.join(exp,"private-assets/p13-source-priority/browser"));
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||"playwright");
const sha=file=>crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const MIME={".html":"text/html;charset=utf-8",".js":"text/javascript",".json":"application/json",
 ".png":"image/png",".jpg":"image/jpeg",".gif":"image/gif"};
const server=http.createServer((req,res)=>{
 try{
  const url=new URL(req.url,"http://localhost");
  const target=path.resolve(root,"."+decodeURIComponent(url.pathname));
  if(!target.startsWith(root+path.sep)||!fs.statSync(target).isFile())throw Error("bad path");
  res.writeHead(200,{"Content-Type":MIME[path.extname(target)]||"application/octet-stream",
   "Cache-Control":"no-store"});
  fs.createReadStream(target).pipe(res);
 }catch{res.writeHead(404);res.end("Not Found");}
});
async function run(){
 fs.mkdirSync(out,{recursive:true});
 await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
 const browser=await chromium.launch({headless:true,args:["--no-sandbox","--use-angle=swiftshader"]});
 const page=await browser.newPage({viewport:{width:1580,height:970},deviceScaleFactor:1});
 const errors=[],failedRequests=[],screens=[];
 page.on("pageerror",e=>errors.push(String(e)));
 page.on("requestfailed",r=>failedRequests.push(r.url()+" "+(r.failure()?.errorText||"")));
 try{
  const url="http://127.0.0.1:"+server.address().port+
    "/experiments/gif-multiview-keyparts-mvp/review/p13-intermediate.html";
  await page.goto(url,{waitUntil:"domcontentloaded",timeout:30000});
  try{await page.waitForFunction(()=>window.__KOMA_P13?.inspect().ready,null,{timeout:25000});}
  catch(e){
   const details=await page.evaluate(()=>({state:window.__KOMA_P13?.inspect(),status:document.querySelector("#status")?.textContent}));
   throw Error("P13 viewport source loading "+JSON.stringify(details)+e.message);
  }
  const source=await page.evaluate(()=>window.__KOMA_P13.inspect());
  if(source.characterId!=="p0_character_001"||source.sourceFrames!==37||
     source.sourceSemanticLayers!==26||source.registeredAngles.join(",")!=="67.5,72.5"||
     source.errors.length)throw Error("P13 source registration differs "+JSON.stringify(source));
  const samples=[
   [22.5,67.5,"hair.front"],
   [67.5,67.5,"eye.near"],
   [67.5,67.5,"hair.front"],
   [72.5,72.5,"face.skin"],
   [72.5,72.5,"hair.clip.cross_gold"],
   [90,72.5,"hair.back"]
  ];
  for(const [angle,layerAngle,role] of samples){
   await page.evaluate(async args=>
      window.__KOMA_P13.choose(args.angle,args.layerAngle,args.role),
      {angle,layerAngle,role});
   const state=await page.evaluate(()=>window.__KOMA_P13.inspect());
   if(state.errors.length||state.current.angle!==angle||
      state.current.layerAngle!==layerAngle||state.current.role!==role||
      state.current.verifiedImages!==5)
    throw Error("P0 original plus P13 source layer bitmap mismatch "+JSON.stringify(state));
   const image={
    yaw:angle,layerYaw:layerAngle,semanticId:role,
    verifiedSHAImages:state.current.verifiedImages,alphaPixels:state.current.sourceAlphaPixels,
    captures:{}
   };
   const name="yaw"+String(angle).replace(".","p")+"-layer"+String(layerAngle).replace(".","p")+"-"+role.replaceAll(".","-");
   for(const [type,selector] of [["motion","#motion"],["parts","#parts"]]){
    const file=path.join(out,name+"-"+type+".png");
    await page.locator(selector).screenshot({path:file});
    image.captures[type]={path:file,sha256:sha(file),bytes:fs.statSync(file).size};
   }
   screens.push(image);
  }
  const qa={
   schema:"KOMA-P0-P13-INTERMEDIATE-RGBA-REAL-BROWSER-QA-V1",
   characterId:"p0_character_001",
   originalSourceKeyViews:[0,45,90],
   sourceRGBAFrames:source.sourceFrames,
   registeredSemanticLayerFrames:source.sourceSemanticLayers,
   verifiedPNGPerSample:5,
   screens,screenshotCount:screens.length*2,
   errors,failedRequests,
   status:screens.length===6&&!errors.length&&!failedRequests.length?
    "PASS_REAL_ORIGINAL_P0_INTERMEDIATE_LAYER_REVIEW":"BROWSER_SOURCE_REVIEW_FAILED",
   artisticApproval:"PENDING"
  };
  fs.writeFileSync(path.join(out,"browser-qa.json"),JSON.stringify(qa,null,2)+"\n");
  console.log(JSON.stringify({status:qa.status,sourceFrames:qa.sourceRGBAFrames,
   originalRGBAsemanticLayers:qa.registeredSemanticLayerFrames,
   screenshotCount:qa.screenshotCount,errors,failedRequests},null,2));
  if(qa.status!=="PASS_REAL_ORIGINAL_P0_INTERMEDIATE_LAYER_REVIEW")process.exitCode=2;
 }finally{
  await browser.close();
  await new Promise(ok=>server.close(ok));
 }
}
run().catch(e=>{console.error(e.stack);server.close();process.exitCode=3;});
