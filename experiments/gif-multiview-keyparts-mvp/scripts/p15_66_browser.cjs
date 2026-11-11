const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-66-front-bang');
(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox']});const q={schema:'KOMA-P15-66-BROWSER-V1',checks:[],errors:[]};
try {for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const p=await b.newPage({viewport:v});p.on('pageerror',e=>q.errors.push(String(e)));p.on('requestfailed',r=>q.errors.push(r.url()));
await p.goto('file://'+path.join(dir,'index.html'));
const loaded=await p.locator('img').evaluateAll(xs=>xs.length===9&&xs.every(x=>x.complete&&x.naturalWidth>0));if(!loaded)throw Error('image load '+v.name);
for (const dx of [0,9,18]) {await p.locator('#shift').fill(String(dx));await p.waitForFunction(n=>document.getElementById('whole').getAttribute('src')==='eye-shift-'+String(n).padStart(2,'0')+'-with-occlusion.png',dx);}
const file=v.name==='desktop'?'browser-desktop.png':null;
if(file)await p.screenshot({path:path.join(dir,file),fullPage:false,timeout:20000});
q.checks.push({viewport:v.name,initialImagesLoaded:9,sliderOffsets:[0,9,18],screenshot:file,sha256:file?crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,file))).digest('hex'):null});
await p.close();
}if(q.errors.length)throw Error(q.errors.join(';'));q.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-66-browser-qa.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({checks:2,loadedImages:18,errors:0}));}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
