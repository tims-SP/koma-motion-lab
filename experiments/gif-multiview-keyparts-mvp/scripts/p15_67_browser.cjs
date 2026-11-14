const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-67-front-hair');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const qa={schema:'KOMA-P15-67-BROWSER-V1',checks:[],errors:[]};
try{for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const page=await browser.newPage({viewport:v});page.on('pageerror',e=>qa.errors.push(String(e)));page.on('requestfailed',r=>qa.errors.push(r.url()));
 await page.goto('file://'+path.join(dir,'index.html'));
 const loaded=await page.locator('img').evaluateAll(xs=>xs.length===9&&xs.every(x=>x.complete&&x.naturalWidth>0));
 if(!loaded)throw Error('images failed '+v.name);
 for(const n of [0,9,18]){await page.locator('#shift').fill(String(n));await page.waitForFunction(x=>document.querySelector('#main').getAttribute('src')==='eye-shift-'+String(x).padStart(2,'0')+'-v2.png',n);}
 const file=v.name==='desktop'?'browser-desktop.png':null;
 if(file)await page.screenshot({path:path.join(dir,file),fullPage:false,timeout:20000});
 qa.checks.push({viewport:v.name,imagesLoaded:9,sliderOffsets:[0,9,18],screenshot:file,sha256:file?crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,file))).digest('hex'):null});
 await page.close();
}if(qa.errors.length)throw Error(qa.errors.join(';'));qa.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-67-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');console.log(JSON.stringify({checks:2,imagesLoaded:18,errors:0}));}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
