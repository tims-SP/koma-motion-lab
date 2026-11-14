const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-21-layered-review');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const report={checks:[],errors:[],interactiveChecks:0};
 for(const viewport of [{width:1440,height:900},{width:390,height:844}]){
  const page=await browser.newPage({viewport});
  page.on('pageerror',e=>report.errors.push(String(e)));
  page.on('requestfailed',r=>report.errors.push(r.url()+': '+r.failure()?.errorText));
  await page.goto('file://'+path.join(root,'index.html'),{waitUntil:'load'});
  for(let i=0;i<5;i++){
   await page.locator('#yaw').selectOption(String(i));
   await page.waitForFunction(()=>[...document.images].length===14 &&
       [...document.images].every(x=>x.complete&&x.naturalWidth===1024));
   const loaded=await page.locator('img').evaluateAll(a=>a.filter(x=>x.naturalWidth===1024&&x.complete).length);
   const parts=await page.locator('#layers input[type=checkbox]').count();
   if(loaded!==14||parts!==13)throw Error('Missing images/role toggles: '+i+' '+loaded+' '+parts);
   if(i===2){
    const first=page.locator('#layers input[type=checkbox]').first();
    await first.uncheck();
    const hidden=await page.locator('#composed img').first().evaluate(x=>x.style.display==='none');
    if(!hidden)throw Error('Layer toggle failed');
    report.interactiveChecks++;
    await page.locator('#none').click();
    const off=await page.locator('#composed img').evaluateAll(xs=>xs.every(x=>x.style.display==='none'));
    if(!off)throw Error('Hide all failed');
    report.interactiveChecks++;
    await page.locator('#all').click();
    const on=await page.locator('#composed img').evaluateAll(xs=>xs.every(x=>x.style.display==='block'));
    if(!on)throw Error('Show all failed');
    report.interactiveChecks++;
    await page.screenshot({path:path.join(root,'chromium-'+viewport.width+'-yaw60.png'),fullPage:true});
   }
   report.checks.push({viewport:viewport.width,yawIndex:i,loaded,parts});
  }
  await page.close();
 }
 await browser.close();
 if(report.errors.length)throw Error(JSON.stringify(report.errors));
 fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-21-browser-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({checks:report.checks.length,imageLoads:report.checks.reduce((n,x)=>n+x.loaded,0),
   interactions:report.interactiveChecks,errors:report.errors.length}));
})().catch(e=>{console.error(e);process.exit(1)});
