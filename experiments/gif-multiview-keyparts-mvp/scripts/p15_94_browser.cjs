const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-94-sam3-yaw060');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const qa={schema:'KOMA-P15-94-SAM3_BROWSER_QA_V1',status:'RUNNING',checks:[],errors:[]};
try{for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
page.on('pageerror',e=>qa.errors.push(String(e)));page.on('requestfailed',r=>qa.errors.push('request '+r.url()));
await page.goto('file://'+path.join(D,'index.html'));
for(let n=0;n<=1;n++){
await page.locator('#choice').evaluate((el,v)=>{el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}));},n);
await page.waitForTimeout(130);
const state=await page.evaluate(()=>({src:document.getElementById('candidate').getAttribute('src'),loaded:[...document.querySelectorAll('img')].map(x=>x.complete&&x.naturalWidth>0)}));
if(!state.src.includes('hair-candidate-'+n)||state.loaded.some(x=>!x))throw Error(vp.name+' candidate '+n+' '+JSON.stringify(state));
qa.checks.push({viewport:vp.name,candidate:n,imagesLoaded:state.loaded.length});
}
const shot=path.join(D,'browser-'+vp.name+'.png');await page.screenshot({path:shot,fullPage:false});qa.checks[qa.checks.length-1].screenshotSHA256=sha(shot);await page.close();
}
if(qa.errors.length)throw Error(qa.errors.join(';'));qa.status='PASS';fs.writeFileSync(path.join(R,'evidence/p15-94-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
