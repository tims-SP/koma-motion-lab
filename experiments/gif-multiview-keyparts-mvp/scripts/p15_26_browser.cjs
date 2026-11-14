const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-26-local-repair-review');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const result={checks:[],errors:[]};
 for(const vp of [{width:1440,height:900},{width:390,height:844}]){
  const page=await browser.newPage({viewport:vp});
  page.on('pageerror',e=>result.errors.push(String(e)));
  page.on('requestfailed',r=>result.errors.push(r.url()+': '+r.failure()?.errorText));
  await page.goto('file://'+path.join(root,'index.html'),{waitUntil:'load'});
  for(let i=0;i<5;i++){
   await page.locator('#angle').selectOption(String(i));
   await page.waitForFunction(()=>[...document.images].filter(x=>x.closest('#parts')||x.id==='baseline'||x.id==='candidate').length===5&&
       [...document.images].every(x=>x.complete&&x.naturalWidth>0));
   const loaded=await page.locator('img').evaluateAll(xs=>xs.filter(x=>x.complete&&x.naturalWidth>0).length);
   if(loaded!==6)throw Error('Expected 6 loaded images: '+loaded);
   if(i===2)await page.screenshot({path:path.join(root,'chromium-'+vp.width+'-yaw60.png'),fullPage:true});
   result.checks.push({viewport:vp.width,angleIndex:i,loaded});
  }
  await page.close();
 }
 await browser.close();
 if(result.errors.length)throw Error(JSON.stringify(result.errors));
 fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-26-browser-qa.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({checks:result.checks.length,images:result.checks.reduce((a,x)=>a+x.loaded,0),errors:result.errors.length}));
})().catch(e=>{console.error(e);process.exit(1)});
