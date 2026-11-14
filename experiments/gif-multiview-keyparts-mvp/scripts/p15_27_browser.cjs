const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-27-occlusion-review');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const data={checks:[],errors:[]};
 for(const vp of [{width:1440,height:900},{width:390,height:844}]){
  const page=await browser.newPage({viewport:vp});
  page.on('pageerror',e=>data.errors.push(String(e)));
  page.on('requestfailed',r=>data.errors.push(r.url()+': '+r.failure()?.errorText));
  await page.goto('file://'+path.join(root,'index.html'),{waitUntil:'load'});
  for(let i=0;i<5;i++){
   await page.locator('#angle').selectOption(String(i));
   await page.waitForFunction(()=>[...document.images].length===8&&[...document.images].every(x=>x.complete&&x.naturalWidth===1024));
   const n=await page.locator('img').evaluateAll(xs=>xs.filter(x=>x.complete&&x.naturalWidth===1024).length);
   if(n!==8)throw Error('Expected 8 images got '+n);
   if(i===2)await page.screenshot({path:path.join(root,'chromium-'+vp.width+'-yaw60.png'),fullPage:true});
   data.checks.push({viewport:vp.width,index:i,loaded:n});
  }
  await page.close();
 }
 await browser.close();
 if(data.errors.length)throw Error(JSON.stringify(data.errors));
 fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-27-browser-qa.json'),JSON.stringify(data,null,2)+'\n');
 console.log(JSON.stringify({checks:data.checks.length,loaded:data.checks.reduce((a,x)=>a+x.loaded,0),errors:data.errors.length}));
})().catch(e=>{console.error(e);process.exit(1)});
