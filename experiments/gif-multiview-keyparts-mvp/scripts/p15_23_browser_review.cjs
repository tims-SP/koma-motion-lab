const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-23-model-keyparts-review');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const out={checks:[],errors:[]};
 for(const vp of [{width:1440,height:900},{width:390,height:844}]){
  const page=await browser.newPage({viewport:vp});
  page.on('pageerror',e=>out.errors.push(String(e)));
  page.on('requestfailed',r=>out.errors.push(r.url()+':'+r.failure()?.errorText));
  await page.goto('file://'+path.join(root,'index.html'),{waitUntil:'load'});
  for(let i=0;i<4;i++){
   await page.locator('#role').selectOption(String(i));
   await page.waitForFunction(()=>document.querySelectorAll('img').length===5&&
     [...document.images].every(x=>x.complete&&x.naturalWidth>0));
   const imgs=await page.locator('img').evaluateAll(xs=>xs.filter(x=>x.complete&&x.naturalWidth>0).length);
   if(imgs!==5)throw Error('5 images did not load');
   if(i===3)await page.screenshot({path:path.join(root,'chromium-'+vp.width+'.png'),fullPage:true});
   out.checks.push({viewport:vp.width,roleIndex:i,imagesLoaded:imgs});
  }
  await page.close();
 }
 await browser.close();
 if(out.errors.length)throw Error(JSON.stringify(out.errors));
 fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-23-browser-qa.json'),JSON.stringify(out,null,2)+'\n');
 console.log(JSON.stringify({checks:out.checks.length,loaded:out.checks.reduce((s,x)=>s+x.imagesLoaded,0),errors:out.errors.length}));
})().catch(e=>{console.error(e);process.exit(1)});
