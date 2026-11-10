const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-19-quality-review');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const result={checks:[],errors:[]};
 for(const viewport of [{width:1440,height:920},{width:390,height:844}]){
  const page=await browser.newPage({viewport});
  page.on('pageerror',err=>result.errors.push(String(err)));
  page.on('requestfailed',req=>result.errors.push(req.url()+': '+req.failure()?.errorText));
  await page.goto('file://'+path.join(root,'index.html'),{waitUntil:'load'});
  for(let angle=0;angle<5;angle++){
   await page.locator('#angle').selectOption(String(angle));
   await page.locator('.three img').first().waitFor({state:'visible'});
   const imageCount=await page.locator('.three img').count();
   await page.waitForFunction(()=>[...document.querySelectorAll('.three img')].every(x=>x.complete&&x.naturalWidth>0));
   const loaded=await page.locator('.three img').evaluateAll(items=>items.filter(x=>x.naturalWidth>0&&x.complete).length);
   if(imageCount!==18||loaded!==18)throw Error('Failed to load 18 crops for angle '+angle);
   if(angle===2)await page.screenshot({path:path.join(root,'browser-'+viewport.width+'.png'),fullPage:true});
   result.checks.push({viewport:viewport.width,angleIndex:angle,imageCount,loaded});
  }
  await page.close();
 }
 await browser.close();
 if(result.errors.length)throw Error(JSON.stringify(result.errors));
 fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-19-browser-qa.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({checks:result.checks.length,loaded:result.checks.reduce((n,x)=>n+x.loaded,0),errors:result.errors.length}));
})().catch(err=>{console.error(err);process.exit(1)});
