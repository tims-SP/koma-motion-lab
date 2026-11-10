const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-18-mode-comparison');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const result={checks:[],errors:[]};
 for(const viewport of [{width:1440,height:1000},{width:390,height:844}]){
  const page=await browser.newPage({viewport});
  page.on('pageerror',e=>result.errors.push(String(e)));
  page.on('requestfailed',r=>result.errors.push(r.url()+':'+r.failure()?.errorText));
  await page.goto('file://'+path.join(root,'index.html'),{waitUntil:'load'});
  const count=await page.locator('img').count();
  const loaded=await page.locator('img').evaluateAll(xs=>xs.filter(x=>x.complete&&x.naturalWidth===1024).length);
  await page.screenshot({path:path.join(root,'browser-'+viewport.width+'.png'),fullPage:true});
  result.checks.push({viewport:viewport.width,imageCount:count,loaded});
  await page.close();
 }
 await browser.close();
 if(result.errors.length||result.checks.some(x=>x.imageCount!==15||x.loaded!==15))throw Error(JSON.stringify(result));
 fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-18-browser-qa.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify(result));
})().catch(e=>{console.error(e);process.exit(1)});
