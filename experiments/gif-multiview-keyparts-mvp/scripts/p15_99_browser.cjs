const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-99-vdd-review');
(async()=>{
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const qa={schema:'KOMA_P15_99_TOPOLOGY_BROWSER_QA_V1',status:'STARTED',checks:[],errors:[]};
try{
 for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
  const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
  page.on('pageerror',e=>qa.errors.push(String(e)));
  page.on('requestfailed',r=>qa.errors.push('request '+r.url()));
  await page.goto('file://'+path.join(dir,'index.html'));
  for(const m of ['topology_nearest','topology_blended_skin','topology_staged','topology_rear_owner']){
   await page.locator('#method').selectOption(m);
   for(let i=0;i<9;i++){
    await page.locator('#yaw').evaluate((el,v)=>{el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}));},i);
    await page.locator('#current').evaluate(img=>img.decode());
    const state=await page.evaluate(()=>({src:document.querySelector('#current').getAttribute('src'),
      gif:document.querySelector('#animated').getAttribute('src'),
      images:[...document.querySelectorAll('img')].map(x=>({src:x.getAttribute('src'),ok:x.complete&&x.naturalWidth>0}))}));
    if(!state.src.startsWith(m+'-yaw')||state.gif!==m+'-yaw-motion.gif'||state.images.length<5||state.images.some(x=>!x.ok))
     throw Error(vp.name+' '+m+' '+i+' '+JSON.stringify(state));
    qa.checks.push({viewport:vp.name,method:m,index:i,loadedImages:state.images.length});
   }
  }
  const shot=path.join(dir,'browser-'+vp.name+'.png');
  await page.screenshot({path:shot,fullPage:false});
  qa.checks[qa.checks.length-1].screenshotSHA256=crypto.createHash('sha256').update(fs.readFileSync(shot)).digest('hex');
  await page.close();
 }
 if(qa.errors.length)throw Error(qa.errors.join(';'));
 qa.status='PASS';
 fs.writeFileSync(path.join(root,'evidence/p15-99-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
 console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
