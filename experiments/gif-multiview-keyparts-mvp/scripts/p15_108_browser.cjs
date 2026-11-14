const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-108-stroke-render');
(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox']});
const doc=JSON.parse(fs.readFileSync(path.join(R,'evidence/p15-108-review-qa.json')));
const report={schema:'KOMA_P15_108_BROWSER_QA_V1',status:'RUNNING',checks:[],errors:[]};
try{
for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const page=await b.newPage({viewport:{width:vp.width,height:vp.height}});
 page.on('pageerror',e=>report.errors.push(String(e)));
 page.on('requestfailed',r=>{if(!String(r.failure()).includes('ERR_ABORTED'))report.errors.push(r.url());});
 await page.goto('file://'+path.join(D,'index.html'));
 for(const m of Object.keys(doc.methodFrames)){
  await page.locator('#method').selectOption(m);
  await page.locator('#loop').evaluate(img=>img.decode());
  for(let j=0;j<doc.renderAngles.length;j++){
   await page.locator('#yaw').evaluate((e,index)=>{e.value=String(index);e.dispatchEvent(new Event('input',{bubbles:true}));},j);
   await page.locator('#frame').evaluate(img=>img.decode());
   const state=await page.evaluate(()=>({src:document.querySelector('#frame').getAttribute('src'),
    gif:document.querySelector('#loop').getAttribute('src'),
    images:[...document.querySelectorAll('img')].map(i=>i.complete&&i.naturalWidth>0)}));
   if(state.src!==doc.methodFrames[m][String(doc.renderAngles[j])]||
     state.gif!==m+'-loop.gif'||state.images.length<5||state.images.some(x=>!x))
      throw Error(JSON.stringify({view:vp.name,method:m,index:j,state}));
   report.checks.push({viewport:vp.name,method:m,index:j,loaded:state.images.length});
  }
 }
 const screenshot=path.join(D,'browser-'+vp.name+'.png');
 await page.screenshot({path:screenshot,fullPage:false});
 report.checks[report.checks.length-1].screenSHA256=crypto.createHash('sha256').update(fs.readFileSync(screenshot)).digest('hex');
 await page.close();
}
if(report.errors.length)throw Error(report.errors.join(','));
report.status='PASS';fs.writeFileSync(path.join(R,'evidence/p15-108-browser-qa.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,checks:report.checks.length,errors:report.errors.length}));
}finally{await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
