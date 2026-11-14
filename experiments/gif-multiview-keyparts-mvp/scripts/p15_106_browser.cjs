const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-106-three-key-render');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const report=JSON.parse(fs.readFileSync(path.join(R,'evidence/p15-106-review-qa.json'),'utf8'));
const qa={schema:'KOMA_P15_106_THREE_VIEW_BROWSER_V1',status:'STARTED',checks:[],errors:[]};
try{
for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
 page.on('pageerror',e=>qa.errors.push(String(e)));
 page.on('requestfailed',r=>{if(!String(r.failure()).includes('ERR_ABORTED'))qa.errors.push('fetch '+r.url());});
 await page.goto('file://'+path.join(D,'index.html'));
 for(const mode of Object.keys(report.frameFiles)){
  await page.locator('#method').selectOption(mode);
  await page.locator('#loop').evaluate(img=>img.decode());
  for(let i=0;i<report.renderAngles.length;i++){
   await page.locator('#yaw').evaluate((el,v)=>{el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}));},i);
   await page.locator('#frame').evaluate(img=>img.decode());
   const state=await page.evaluate(()=>({src:document.querySelector('#frame').getAttribute('src'),
       gif:document.querySelector('#loop').getAttribute('src'),
       images:[...document.querySelectorAll('img')].map(x=>({ok:x.complete&&x.naturalWidth>0,src:x.getAttribute('src')}))}));
   const expected=report.frameFiles[mode][String(report.renderAngles[i])];
   if(state.src!==expected||state.gif!==mode+'-loop.gif'||state.images.length<7||state.images.some(x=>!x.ok))
     throw Error(vp.name+' '+mode+' '+i+' '+JSON.stringify(state));
   qa.checks.push({viewport:vp.name,mode,index:i,loadedImages:state.images.length});
  }
 }
 const shot=path.join(D,'browser-'+vp.name+'.png');
 await page.screenshot({path:shot,fullPage:false});
 qa.checks[qa.checks.length-1].screenshotSHA256=crypto.createHash('sha256').update(fs.readFileSync(shot)).digest('hex');
 await page.close();
}
if(qa.errors.length)throw Error(qa.errors.join(';'));
qa.status='PASS';
fs.writeFileSync(path.join(R,'evidence/p15-106-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
