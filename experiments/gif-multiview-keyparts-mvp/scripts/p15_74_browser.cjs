const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-74-bangs-repair');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const qa={schema:'KOMA-P15-74-BROWSER-V1',checks:[],errors:[]};
try{for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const p=await browser.newPage({viewport:v});p.on('pageerror',e=>qa.errors.push(String(e)));p.on('requestfailed',r=>qa.errors.push(r.url()));
await p.goto('file://'+path.join(dir,'index.html'));
if(!await p.locator('img').evaluateAll(xs=>xs.length===11&&xs.every(x=>x.complete&&x.naturalWidth>0)))throw Error('image load failure '+v.name);
for(const dx of [0,9,18]){await p.locator('#shift').fill(String(dx));await p.waitForFunction(n=>document.querySelector('#whole').getAttribute('src')==='eye-shift-'+String(n).padStart(2,'0')+'.png',dx);}
const shot=v.name==='desktop'?'browser-desktop.png':null;if(shot)await p.screenshot({path:path.join(dir,shot),fullPage:false,timeout:20000});
qa.checks.push({viewport:v.name,imagesLoaded:11,sliderOffsetsVerified:[0,9,18],screenshot:shot,sha256:shot?crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,shot))).digest('hex'):null});await p.close();
}if(qa.errors.length)throw Error(qa.errors.join(';'));qa.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-74-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');console.log(JSON.stringify({checks:2,imagesLoaded:22,errors:0}));}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
