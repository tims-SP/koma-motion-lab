const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-80-front-hair');
(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox']});const qa={schema:'KOMA-P15-80-BROWSER-V1',checks:[],errors:[]};
try{for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const p=await b.newPage({viewport:v});p.on('pageerror',e=>qa.errors.push(String(e)));p.on('requestfailed',r=>qa.errors.push(r.url()));
await p.goto('file://'+path.join(dir,'index.html'));
if(!await p.locator('img').evaluateAll(xs=>xs.length===8&&xs.every(x=>x.complete&&x.naturalWidth>0)))throw Error('image load '+v.name);
for(const n of [0,9,18]){await p.locator('#shift').fill(String(n));await p.waitForFunction(dx=>document.querySelector('#motion').getAttribute('src')==='candidate-median3-'+String(dx).padStart(2,'0')+'.png',n);}
const shot=v.name==='desktop'?'browser-desktop.png':null;
if(shot)await p.screenshot({path:path.join(dir,shot),fullPage:false,timeout:20000});
qa.checks.push({viewport:v.name,imagesLoaded:8,offsets:[0,9,18],screenshot:shot,sha256:shot?crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,shot))).digest('hex'):null});await p.close();
}if(qa.errors.length)throw Error(qa.errors.join(';'));qa.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-80-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');console.log(JSON.stringify({checks:2,imagesLoaded:16,errors:0}));}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
