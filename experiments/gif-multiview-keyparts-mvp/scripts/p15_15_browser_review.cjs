const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs');const path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-15-artmesh-review');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const result={pages:[],errors:[]};
 for(const viewport of [{width:1280,height:900},{width:390,height:844}]){
  const page=await browser.newPage({viewport});const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('requestfailed',req=>errors.push(req.url()+': '+req.failure()?.errorText));
  await page.goto('file://'+path.join(root,'index.html'),{waitUntil:'load'});
  for(let i=0;i<3;i++){
   await page.locator('#view').selectOption(String(i));
   await page.locator('#stage img').first().waitFor({state:'visible'});
   const count=await page.locator('#stage img').count();
   const loaded=await page.locator('#stage img').evaluateAll(images=>images.filter(img=>img.complete&&img.naturalWidth>0).length);
   if(count!==13||loaded!==13)throw new Error('Missing raster layers '+i+': '+loaded+'/'+count);
   const label=await page.locator('#missing').innerText();
   result.pages.push({viewport:viewport.width,index:i,loaded,errors:errors.length,missingLabel:label});
  }
  result.errors.push(...errors);
  await page.close();
 }
 await browser.close();
 if(result.errors.length)throw new Error(result.errors.join('; '));
 const out=path.resolve(__dirname,'../evidence/p15-15-browser-qa.json');
 fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({views:result.pages.length,imageLoads:result.pages.reduce((s,p)=>s+p.loaded,0),errors:result.errors.length}));
})().catch(e=>{console.error(e);process.exit(1)});
