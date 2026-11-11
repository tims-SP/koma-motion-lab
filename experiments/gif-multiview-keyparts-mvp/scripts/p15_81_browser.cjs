const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-81-image-layered');
(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox']});const q={schema:'KOMA-P15-81-BROWSER-V1',checks:[],errors:[]};
try{for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const p=await b.newPage({viewport:v});p.on('pageerror',e=>q.errors.push(String(e)));p.on('requestfailed',r=>q.errors.push(r.url()));await p.goto('file://'+path.join(dir,'index.html'));
const img=await p.locator('img').evaluateAll(xs=>xs.map(x=>({src:x.getAttribute('src'),loaded:x.complete&&x.naturalWidth>0})));
if(img.length!==11||img.some(x=>!x.loaded))throw Error('images failed '+v.name+' '+JSON.stringify(img));
for(const n of [0,9,18]){await p.locator('#shift').fill(String(n));await p.waitForFunction(x=>document.querySelector('#pose').textContent.includes('位移 '+x+'px'),n);const url=await p.locator('#whole').getAttribute('src');if(!url.includes(n===0?'rest-composite':'motion-'+String(n).padStart(2,'0')))throw Error('slider mismatch')}
const shot=v.name==='desktop'?'browser-desktop.png':null;
if(shot)await p.screenshot({path:path.join(dir,shot),fullPage:false,timeout:20000});
q.checks.push({viewport:v.name,imagesLoaded:11,offsets:[0,9,18],screenshot:shot,sha256:shot?crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,shot))).digest('hex'):null});await p.close();
}if(q.errors.length)throw Error(q.errors.join(';'));q.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-81-browser-qa.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({checks:2,imagesLoaded:22,errors:0}));}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
