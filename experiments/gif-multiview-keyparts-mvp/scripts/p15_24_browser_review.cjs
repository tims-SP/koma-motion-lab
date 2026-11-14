const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-24-cross-clip-review');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const r={checks:[],errors:[]};
 for(const viewport of [{width:1440,height:920},{width:390,height:844}]){
  const page=await browser.newPage({viewport});
  page.on('pageerror',e=>r.errors.push(String(e)));
  page.on('requestfailed',req=>r.errors.push(req.url()+': '+req.failure()?.errorText));
  await page.goto('file://'+path.join(root,'index.html'),{waitUntil:'load'});
  for(let i=0;i<5;i++){
   await page.locator('#angle').selectOption(String(i));
   await page.waitForFunction(()=>[...document.images].length===5 && [...document.images].every(x=>x.complete&&x.naturalWidth===1024));
   const ok=await page.locator('img').evaluateAll(xs=>xs.filter(x=>x.complete&&x.naturalWidth===1024).length);
   if(ok!==5)throw Error('Image missing '+viewport.width+' index '+i);
   if(i===2)await page.screenshot({path:path.join(root,'chromium-'+viewport.width+'-yaw60.png'),fullPage:true});
   r.checks.push({viewport:viewport.width,index:i,loaded:ok});
  }
  await page.close();
 }
 await browser.close();
 if(r.errors.length)throw Error(JSON.stringify(r.errors));
 fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-24-browser-qa.json'),JSON.stringify(r,null,2)+'\n');
 console.log(JSON.stringify({checks:r.checks.length,imageLoads:r.checks.reduce((a,b)=>a+b.loaded,0),errors:r.errors.length}));
})().catch(e=>{console.error(e);process.exit(1)});
