const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-95-elastic-review');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const qa={schema:'KOMA-P15-95-UNDERPAINT_BROWSER_QA_V1',status:'RUNNING',checks:[],errors:[]};
try{for(const vp of [{id:'desktop',width:1440,height:900},{id:'mobile',width:390,height:844}]){
const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
page.on('pageerror',e=>qa.errors.push(String(e)));page.on('requestfailed',r=>qa.errors.push('request '+r.url()));
await page.goto('file://'+path.join(dir,'index.html'));
for(let i=0;i<4;i++){
const dx=[0,4,8,12][i],id=String(dx).padStart(2,'0');
await page.locator('#pose').evaluate((el,v)=>{el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}));},i);
await page.waitForTimeout(120);
const state=await page.evaluate(()=>({pose:document.getElementById('step').textContent,
pics:[...document.querySelectorAll('img')].map(e=>({src:e.getAttribute('src'),ok:e.complete&&e.naturalWidth>0}))}));
if(state.pose!==String(dx)||state.pics.some(x=>!x.ok)||!state.pics[1].src.includes('baseline-'+id)||!state.pics[2].src.includes('feather-2-'+id))throw Error(vp.id+' dx='+dx+' '+JSON.stringify(state));
qa.checks.push({viewport:vp.id,offsetPx:dx,loadedImages:state.pics.length});
}
const shot=path.join(dir,'browser-'+vp.id+'.png');await page.screenshot({path:shot,fullPage:false});qa.checks[qa.checks.length-1].screenshotSHA256=sha(shot);await page.close();
}if(qa.errors.length)throw Error(qa.errors.join(';'));
qa.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-95-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
