const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-96-yaw060-root-artmesh');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const qa={schema:'KOMA_P15_96_BROWSER_QA_V1',status:'RUNNING',checks:[],errors:[]};
try{for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
page.on('pageerror',e=>qa.errors.push(String(e)));page.on('requestfailed',r=>qa.errors.push('request '+r.url()));
await page.goto('file://'+path.join(dir,'index.html'));
for(let pose=0;pose<13;pose++){
await page.locator('#pose').evaluate((el,v)=>{el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}));},pose);
await page.waitForTimeout(110);
const state=await page.evaluate(()=>({text:document.querySelector('#offset').textContent,src:document.querySelector('#candidate').getAttribute('src'),
images:[...document.querySelectorAll('img')].map(x=>({src:x.getAttribute('src'),loaded:x.complete&&x.naturalWidth>0}))}));
if(state.text!==String(pose)||state.src!=='frame-'+String(pose).padStart(2,'0')+'.png'||state.images.some(x=>!x.loaded))throw Error(vp.name+' pose '+pose+' '+JSON.stringify(state));
qa.checks.push({viewport:vp.name,offsetPx:pose,imagesLoaded:state.images.length});
}
const file=path.join(dir,'browser-'+vp.name+'.png');await page.screenshot({path:file,fullPage:false});
qa.checks[qa.checks.length-1].screenshotSHA256=sha(file);await page.close();}
if(qa.errors.length)throw Error(qa.errors.join(';'));
qa.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-96-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
