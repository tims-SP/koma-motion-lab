const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-107-companion-render');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const data=JSON.parse(fs.readFileSync(path.join(R,'evidence/p15-107-companion-review-qa.json')));
const report={schema:'KOMA_P15_107_COMPANION_BROWSER_V1',status:'STARTED',checks:[],errors:[]};
try{
for(const viewport of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const page=await browser.newPage({viewport:{width:viewport.width,height:viewport.height}});
 page.on('pageerror',e=>report.errors.push(String(e)));
 page.on('requestfailed',r=>{if(!String(r.failure()).includes('ERR_ABORTED'))report.errors.push('fetch '+r.url());});
 await page.goto('file://'+path.join(D,'index.html'));
 for(const method of Object.keys(data.methods)){
  await page.locator('#method').selectOption(method);
  await page.locator('#loop').evaluate(img=>img.decode());
  for(let i=0;i<data.renderedAngles.length;i++){
   await page.locator('#yaw').evaluate((x,v)=>{x.value=String(v);x.dispatchEvent(new Event('input',{bubbles:true}));},i);
   await page.locator('#frame').evaluate(img=>img.decode());
   const state=await page.evaluate(()=>({source:document.querySelector('#frame').getAttribute('src'),
     gif:document.querySelector('#loop').getAttribute('src'),
     images:[...document.querySelectorAll('img')].map(im=>({ok:im.complete&&im.naturalWidth>0,url:im.getAttribute('src')}))}));
   if(state.source!==data.methods[method][String(data.renderedAngles[i])]||
     state.gif!==method+'-loop.gif'||state.images.length<4||state.images.some(x=>!x.ok))
     throw Error(viewport.name+' '+method+' '+i+' '+JSON.stringify(state));
   report.checks.push({viewport:viewport.name,method,index:i,loadedImages:state.images.length});
  }
 }
 const shot=path.join(D,'browser-'+viewport.name+'.png');
 await page.screenshot({path:shot,fullPage:false});
 report.checks[report.checks.length-1].screenshotSHA256=crypto.createHash('sha256').update(fs.readFileSync(shot)).digest('hex');
 await page.close();
}
if(report.errors.length)throw Error(report.errors.join(';'));
report.status='PASS';
fs.writeFileSync(path.join(R,'evidence/p15-107-companion-browser-qa.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,checks:report.checks.length,errors:report.errors.length}));
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
