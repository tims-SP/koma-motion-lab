const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),D=path.join(root,'private-assets/exports/p15-97-multiview-motion');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const qa={schema:'KOMA_P15_97_THREE_VIEW_BROWSER_QA_V1',status:'RUNNING',checks:[],errors:[]};
try{for(const viewport of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const page=await browser.newPage({viewport:{width:viewport.width,height:viewport.height}});
page.on('pageerror',e=>qa.errors.push(String(e)));page.on('requestfailed',r=>qa.errors.push('request '+r.url()));
await page.goto('file://'+path.join(D,'index.html'));
for(const [idx,yaw] of ['52p5','60','75'].entries()){
await page.locator('#angle').evaluate((el,v)=>{el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}));},idx);
for(let motion=0;motion<13;motion++){
await page.locator('#offset').evaluate((el,v)=>{el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}));},motion);
const expected='yaw'+yaw+'-frame-'+String(motion).padStart(2,'0')+'.png';
await page.locator('#candidate').evaluate(img=>img.decode());
const state=await page.evaluate(()=>({name:document.querySelector('#angle-label').textContent,
 src:document.querySelector('#candidate').getAttribute('src'),
 offset:document.querySelector('#offset-label').textContent,
 images:[...document.querySelectorAll('img')].map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0}))}));
if(state.src!==expected||state.offset!==motion+'px'||state.images.some(x=>!x.loaded)||state.images.length<4)
 throw Error(viewport.name+' '+yaw+' '+motion+' '+JSON.stringify(state));
qa.checks.push({viewport:viewport.name,yaw,offsetPx:motion,loadedImages:state.images.length});
}
}
const shot=path.join(D,'browser-'+viewport.name+'.png');await page.screenshot({path:shot,fullPage:false});
qa.checks[qa.checks.length-1].screenshotSHA256=sha(shot);await page.close();
}
if(qa.errors.length)throw Error(qa.errors.join(';'));
qa.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-97-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await browser.close();}})().catch(err=>{console.error(err);process.exitCode=1;});
