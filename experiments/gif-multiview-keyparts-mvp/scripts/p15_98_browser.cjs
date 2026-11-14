const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-98-vdd-review');
const qa={schema:'KOMA_P15_98_VDD_BROWSER_QA_V1',status:'STARTED',checks:[],errors:[]};
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
try{for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
page.on('pageerror',e=>qa.errors.push(String(e)));page.on('requestfailed',r=>qa.errors.push('failed '+r.url()));
await page.goto('file://'+path.join(D,'index.html'));
for(const m of ['dis_blend','landmark_blend','landmark_eye_owner','landmark_visibility_union','landmark_visibility_eye_owner']){
 await page.locator('#method').selectOption(m);
 for(let i=0;i<9;i++){
  await page.locator('#yaw').evaluate((el,v)=>{el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}));},i);
  await page.locator('#current').evaluate(img=>img.decode());
  const s=await page.evaluate(()=>({src:document.querySelector('#current').getAttribute('src'),
     label:document.querySelector('#angle-value').textContent,
     images:[...document.querySelectorAll('img')].map(x=>({src:x.getAttribute('src'),ok:x.complete&&x.naturalWidth>0}))}));
  if(!s.src.startsWith(m+'-yaw')||s.images.some(x=>!x.ok)||s.images.length<4)throw Error(vp.name+' '+m+' '+i+' '+JSON.stringify(s));
  qa.checks.push({viewport:vp.name,method:m,index:i,imageCount:s.images.length});
 }
}
const shot=path.join(D,'browser-'+vp.name+'.png');await page.screenshot({path:shot,fullPage:false});
qa.checks[qa.checks.length-1].screenshotSHA256=crypto.createHash('sha256').update(fs.readFileSync(shot)).digest('hex');
await page.close();}
if(qa.errors.length)throw Error(qa.errors.join(';'));
qa.status='PASS';fs.writeFileSync(path.join(R,'evidence/p15-98-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
