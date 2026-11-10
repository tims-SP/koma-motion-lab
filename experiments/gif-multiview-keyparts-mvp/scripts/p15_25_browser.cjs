const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-25-four-role-review');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const report={checks:[],errors:[]};
 for(const viewport of [{width:1440,height:900},{width:390,height:844}]){
  const page=await browser.newPage({viewport});
  page.on('pageerror',e=>report.errors.push(String(e)));
  page.on('requestfailed',r=>report.errors.push(r.url()+': '+r.failure()?.errorText));
  await page.goto('file://'+path.join(root,'index.html'),{waitUntil:'load'});
  for(let i=0;i<5;i++){
   await page.locator('#angle').selectOption(String(i));
   await page.waitForFunction(()=>[...document.images].length===6&&
    [...document.images].every(x=>x.complete&&x.naturalWidth===1024));
   const loaded=await page.locator('img').evaluateAll(xs=>xs.filter(x=>x.complete&&x.naturalWidth===1024).length);
   if(loaded!==6)throw Error('Angle '+i+' failed');
   if(i===2)await page.screenshot({path:path.join(root,'chromium-'+viewport.width+'-yaw60.png'),fullPage:true});
   report.checks.push({viewport:viewport.width,angleIndex:i,loaded});
  }
  await page.close();
 }
 await browser.close();
 if(report.errors.length)throw Error(JSON.stringify(report.errors));
 fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-25-browser-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({checks:report.checks.length,images:report.checks.reduce((n,x)=>n+x.loaded,0),errors:report.errors.length}));
})().catch(e=>{console.error(e);process.exit(1)});
