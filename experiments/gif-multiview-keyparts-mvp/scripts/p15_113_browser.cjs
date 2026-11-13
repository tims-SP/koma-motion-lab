const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-113-canonical-topology');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const doc=JSON.parse(fs.readFileSync(path.join(R,'evidence/p15-113-review-qa.json')));
const report={schema:'KOMA_P15_113_CANONICAL_MESH_BROWSER_V1',status:'STARTED',checks:[],errors:[]};
try{
for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
 page.on('pageerror',e=>report.errors.push(String(e)));
 page.on('requestfailed',r=>{if(!String(r.failure()).includes('ERR_ABORTED'))report.errors.push(r.url());});
 await page.goto('file://'+path.join(D,'index.html'));
 for(const mode of Object.keys(doc.methodFrames)){
  await page.locator('#method').selectOption(mode);
  await page.locator('#loop').evaluate(img=>img.decode());
  for(let index=0;index<doc.renderedAngles.length;index++){
   await page.locator('#yaw').evaluate((x,v)=>{x.value=String(v);x.dispatchEvent(new Event('input',{bubbles:true}));},index);
   await page.locator('#frame').evaluate(img=>img.decode());
   const z=await page.evaluate(()=>({src:document.querySelector('#frame').getAttribute('src'),
     gif:document.querySelector('#loop').getAttribute('src'),
     images:[...document.querySelectorAll('img')].map(i=>i.complete&&i.naturalWidth>0)}));
   if(z.src!==doc.methodFrames[mode][String(doc.renderedAngles[index])]||
      z.gif!==mode+'-loop.gif'||z.images.length<4||z.images.some(x=>!x))
      throw Error(vp.name+' '+mode+' '+index+' '+JSON.stringify(z));
   report.checks.push({viewport:vp.name,method:mode,index,imagesLoaded:z.images.length});
  }
 }
 const screenshot=path.join(D,'browser-'+vp.name+'.png');
 await page.screenshot({path:screenshot,fullPage:false});
 report.checks[report.checks.length-1].screenshotSHA256=crypto.createHash('sha256').update(fs.readFileSync(screenshot)).digest('hex');
 await page.close();
}
if(report.errors.length)throw Error(report.errors.join(';'));
report.status='PASS';fs.writeFileSync(path.join(R,'evidence/p15-113-browser-qa.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,checks:report.checks.length,errors:report.errors.length}));
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
