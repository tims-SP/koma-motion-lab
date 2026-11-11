const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-68-forehead');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const q={schema:'KOMA-P15-68-BROWSER-V1',checks:[],errors:[]};
try{for(const view of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const p=await browser.newPage({viewport:view});
p.on('pageerror',e=>q.errors.push(String(e)));p.on('requestfailed',r=>q.errors.push(r.url()));
await p.goto('file://'+path.join(dir,'index.html'));
const images=await p.locator('img').evaluateAll(xs=>xs.length===10&&xs.every(x=>x.complete&&x.naturalWidth>0));
if(!images)throw Error('images did not load');
for (const n of [0,9,18]) {await p.locator('#shift').fill(String(n));await p.waitForFunction(n=>document.querySelector('#whole').getAttribute('src')==='with-hair-eye-'+String(n).padStart(2,'0')+'.png',n);}
const screenshot=view.name==='desktop'?'browser-desktop.png':null;
if(screenshot) await p.screenshot({path:path.join(dir,screenshot),fullPage:false,timeout:20000});
q.checks.push({viewport:view.name,loadedImages:10,sliderOffsets:[0,9,18],screenshot,sha256:screenshot?crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,screenshot))).digest('hex'):null});await p.close();
}if(q.errors.length)throw Error(q.errors.join(';'));q.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-68-browser-qa.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({checks:2,loadedImages:20,errors:0}));}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
