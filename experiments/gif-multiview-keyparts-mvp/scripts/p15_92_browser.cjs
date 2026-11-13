const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-92-angle-keyart');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const qa={schema:'KOMA-P15-92-KEYVIEW_BROWSER_QA_V1',status:'RUNNING',checks:[],errors:[]};
try{for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
page.on('pageerror',e=>qa.errors.push(String(e)));page.on('requestfailed',r=>qa.errors.push('request '+r.url()));
await page.goto('file://'+path.join(dir,'index.html'));
for(let pose=0;pose<7;pose++){
await page.locator('#angle').evaluate((el,n)=>{el.value=String(n);el.dispatchEvent(new Event('input',{bubbles:true}));},pose);
await page.waitForTimeout(100);
const state=await page.evaluate(()=>({label:document.getElementById('angle-label').textContent,
images:[...document.querySelectorAll('img')].map(e=>({src:e.getAttribute('src'),loaded:e.complete&&e.naturalWidth>0}))}));
if(state.images.some(x=>!x.loaded)||state.images.length<5)throw Error(vp.name+' image load failed '+JSON.stringify(state));
qa.checks.push({viewport:vp.name,index:pose,angle:state.label,imagesLoaded:state.images.length});
}
const shot=path.join(dir,'browser-'+vp.name+'.png');await page.screenshot({path:shot,fullPage:false});
qa.checks[qa.checks.length-1].screenshotSHA256=hash(shot);
await page.close();
}
if(qa.errors.length)throw Error(qa.errors.join(';'));
qa.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-92-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
