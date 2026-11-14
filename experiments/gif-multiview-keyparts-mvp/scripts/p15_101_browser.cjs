const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-101-head-render');
const report=JSON.parse(fs.readFileSync(path.join(R,'evidence/p15-101-render-qa.json')));
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const qa={schema:'KOMA_P15_101_SHARED_HEAD_BROWSER_QA_V1',status:'STARTED',checks:[],errors:[]};
try{
 for(const viewport of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
  const page=await browser.newPage({viewport:{width:viewport.width,height:viewport.height}});
  page.on('pageerror',e=>qa.errors.push(String(e)));page.on('requestfailed',r=>qa.errors.push('failed '+r.url()));
  await page.goto('file://'+path.join(D,'index.html'));
  for(const method of Object.keys(report.methods)){
   await page.locator('#method').selectOption(method);
   for(let i=0;i<report.angles.length;i++){
    await page.locator('#yaw').evaluate((x,v)=>{x.value=String(v);x.dispatchEvent(new Event('input',{bubbles:true}));},i);
    await page.locator('#frame').evaluate(img=>img.decode());
    const state=await page.evaluate(()=>({src:document.querySelector('#frame').getAttribute('src'),
      gif:document.querySelector('#motion').getAttribute('src'),
      images:[...document.querySelectorAll('img')].map(x=>({src:x.getAttribute('src'),valid:x.complete&&x.naturalWidth>0}))}));
    if(!state.src.startsWith(method+'-yaw')||state.gif!==method+'-yaw-loop.gif'||state.images.length<5||state.images.some(x=>!x.valid))
     throw Error(viewport.name+' '+method+' '+i+' '+JSON.stringify(state));
    qa.checks.push({viewport:viewport.name,method,index:i,loadedImages:state.images.length});
   }
  }
  const shot=path.join(D,'browser-'+viewport.name+'.png');await page.screenshot({path:shot,fullPage:false});
  qa.checks[qa.checks.length-1].screenshotSHA256=crypto.createHash('sha256').update(fs.readFileSync(shot)).digest('hex');
  await page.close();
 }
 if(qa.errors.length)throw Error(qa.errors.join(';'));
 qa.status='PASS';
 fs.writeFileSync(path.join(R,'evidence/p15-101-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
 console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
