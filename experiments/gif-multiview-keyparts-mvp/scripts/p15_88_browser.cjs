const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-88-painted-hidden-edge');
(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox']});const q={schema:'KOMA-P15-88-BROWSER-V1',checks:[],errors:[]};
try{for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const p=await b.newPage({viewport:v});p.on('pageerror',e=>q.errors.push(String(e)));p.on('requestfailed',r=>q.errors.push(r.url()));await p.goto('file://'+path.join(dir,'index.html'));
 const imgs=await p.locator('img').evaluateAll(xs=>xs.map(x=>({src:x.getAttribute('src'),ok:x.complete&&x.naturalWidth>0})));
 if(imgs.length!==9||imgs.some(x=>!x.ok))throw Error('images failed '+v.name+JSON.stringify(imgs));
 const shot=v.name==='desktop'?'browser-desktop.png':null;if(shot)await p.screenshot({path:path.join(dir,shot),fullPage:false});
 q.checks.push({viewport:v.name,imagesLoaded:9,screenshot:shot,sha256:shot?crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,shot))).digest('hex'):null});await p.close();
}if(q.errors.length)throw Error(q.errors.join(';'));q.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-88-browser-qa.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({checks:2,imagesLoaded:18,errors:0}));}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
