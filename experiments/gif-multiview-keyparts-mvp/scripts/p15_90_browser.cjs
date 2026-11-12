const { chromium }=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-90-precision-mask');
const digest=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const report={schema:'KOMA-P15-90-CHROMIUM_VISUAL_REVIEW_V1',checks:[],errors:[]};
try{for(const vp of [{id:'desktop',width:1440,height:900},{id:'mobile',width:390,height:844}]){
const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
page.on('pageerror',e=>report.errors.push(String(e)));
page.on('requestfailed',r=>report.errors.push('request '+r.url()));
await page.goto('file://'+path.join(dir,'index.html'));
for(const step of [0,9,18]){
await page.locator('#shift').evaluate((el,v)=>{el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}));},step);
await page.waitForTimeout(250);
const state=await page.evaluate(()=>({pose:document.querySelector('#pose').textContent,
imgs:[...document.querySelectorAll('img')].map(el=>({loaded:el.complete&&el.naturalWidth>0,src:el.getAttribute('src')}))}));
if(state.pose!==String(step)||state.imgs.some(x=>!x.loaded)||!state.imgs[0].src.includes('frame-'+String(step).padStart(2,'0'))||!state.imgs[1].src.includes('r4-'+String(step).padStart(2,'0')))throw Error('viewport '+vp.id+' pose '+step+' '+JSON.stringify(state));
report.checks.push({viewport:vp.id,pose:step,imagesLoaded:state.imgs.length});
}
const shot=path.join(dir,'browser-'+vp.id+'.png');await page.screenshot({path:shot,fullPage:false});report.checks[report.checks.length-1].screenshotSHA256=digest(shot);
await page.close();
}
if(report.errors.length)throw Error(report.errors.join(';'));
report.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-90-browser-qa.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,checks:report.checks.length,errors:report.errors.length}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
