const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-112-visibility-vdd');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const rev=JSON.parse(fs.readFileSync(path.join(R,'evidence/p15-112-review-qa.json'),'utf8'));
const report={schema:'KOMA_P15_112_BROWSER_QA_V1',status:'STARTED',yawChecks:[],revealChecks:[],errors:[]};
try{
for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
 page.on('pageerror',e=>report.errors.push(String(e)));
 page.on('requestfailed',r=>{if(!String(r.failure()).includes('ERR_ABORTED'))report.errors.push('fetch '+r.url());});
 await page.goto('file://'+path.join(D,'index.html'));
 for(const method of Object.keys(rev.renderMethods)){
  await page.locator('#method').selectOption(method);
  await page.locator('#motion').evaluate(img=>img.decode());
  for(let i=0;i<rev.angles.length;i++){
   await page.locator('#yaw').evaluate((el,val)=>{el.value=String(val);el.dispatchEvent(new Event('input',{bubbles:true}));},i);
   await page.locator('#frame').evaluate(img=>img.decode());
   const state=await page.evaluate(()=>({src:document.querySelector('#frame').getAttribute('src'),gif:document.querySelector('#motion').getAttribute('src')}));
   if(state.src!==rev.renderMethods[method][String(rev.angles[i])]||state.gif!==method+'-loop.gif')
     throw Error('yaw '+vp.name+' '+method+' '+i+' '+JSON.stringify(state));
   report.yawChecks.push({viewport:vp.name,method,index:i});
  }
 }
 for(const view of rev.revealSourceViews){
  await page.locator('#sourceView').selectOption(view);
  for(const pose of rev.revealPoses){
   await page.locator('#pose').selectOption(pose);
   await page.locator('#revealOff').evaluate(img=>img.decode());
   await page.locator('#revealOn').evaluate(img=>img.decode());
   const state=await page.evaluate(()=>({off:document.querySelector('#revealOff').getAttribute('src'),
     on:document.querySelector('#revealOn').getAttribute('src'),
     ok:[...document.querySelectorAll('img')].every(i=>i.complete&&i.naturalWidth>0)}));
   const expected=rev.revealImageSources[view][pose];
   if(state.off!==expected.source_matte||state.on!==expected.with_underpaint||!state.ok)
     throw Error('reveal '+vp.name+' '+view+' '+pose+' '+JSON.stringify(state));
   report.revealChecks.push({viewport:vp.name,view,pose});
  }
 }
 const shot=path.join(D,'browser-'+vp.name+'.png');
 await page.screenshot({path:shot,fullPage:false});
 report.revealChecks[report.revealChecks.length-1].screenshotSHA256=crypto.createHash('sha256').update(fs.readFileSync(shot)).digest('hex');
 await page.close();
}
if(report.errors.length)throw Error(report.errors.join(';'));
report.status='PASS';
fs.writeFileSync(path.join(R,'evidence/p15-112-browser-qa.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,yawChecks:report.yawChecks.length,revealChecks:report.revealChecks.length,errors:report.errors.length}));
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
