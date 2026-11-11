const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-71-sam-semantic');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const qa={schema:'KOMA-P15-71-BROWSER-V1',checks:[],errors:[]};
try{for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const page=await browser.newPage({viewport:v});
 page.on('pageerror',e=>qa.errors.push(String(e)));page.on('requestfailed',r=>qa.errors.push(r.url()));
 await page.goto('file://'+path.join(dir,'index.html'));
 if(!await page.locator('img').evaluateAll(xs=>xs.length===9&&xs.every(x=>x.complete&&x.naturalWidth>0)))throw Error('images fail '+v.name);
 for (const dx of [0,9,18]) {
  await page.locator('#shift').fill(String(dx));
  await page.waitForFunction(n=>document.querySelector('#offset').textContent.includes(n+'px'),dx);
 }
 const shot=v.name==='desktop'?'browser-desktop.png':null;
 if(shot)await page.screenshot({path:path.join(dir,shot),fullPage:false,timeout:20000});
 qa.checks.push({viewport:v.name,imagesLoaded:9,sliderOffsets:[0,9,18],screenshot:shot,
 sha256:shot?crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,shot))).digest('hex'):null});
 await page.close();
}if(qa.errors.length)throw Error(qa.errors.join(';'));qa.status='PASS';
fs.writeFileSync(path.join(root,'evidence/p15-71-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
console.log(JSON.stringify({checks:2,imagesLoaded:18,errors:0}));}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
