const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-31-native-artmesh-review');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const result={checks:[],errors:[]};
 for(const viewport of [{width:1440,height:900},{width:390,height:844}]){
  const page=await browser.newPage({viewport});
  page.on('pageerror',e=>result.errors.push(String(e)));
  page.on('requestfailed',r=>result.errors.push(r.url()+': '+r.failure()?.errorText));
  await page.goto('file://'+path.join(root,'index.html'));
  for(let i=0;i<9;i++){
   await page.locator('#slider').fill(String(i));
   await page.waitForFunction(()=>document.querySelectorAll('#comps img').length===3&&
    document.querySelectorAll('#parts img').length===5&&
    [...document.images].every(x=>x.complete&&x.naturalWidth>0));
   const count=await page.locator('img').evaluateAll(xs=>xs.filter(x=>x.complete&&x.naturalWidth>0).length);
   if(count!==8)throw Error('Expected 8 visible images, got '+count);
   if(i===4)await page.screenshot({path:path.join(root,'chromium-'+viewport.width+'-yaw60.png'),fullPage:true});
   result.checks.push({viewport:viewport.width,frameIndex:i,loaded:count});
  }
  await page.close();
 }
 await browser.close();
 if(result.errors.length)throw Error(JSON.stringify(result.errors));
 fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-31-browser-qa.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({checks:result.checks.length,imageLoads:result.checks.reduce((a,x)=>a+x.loaded,0),errors:result.errors.length}));
})().catch(e=>{console.error(e);process.exit(1)});
