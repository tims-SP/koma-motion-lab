const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-29-defade-geometry-review');
 const b=await chromium.launch({headless:true,args:['--no-sandbox']});
 const report={checks:[],errors:[]};
 for(const viewport of [{width:1440,height:900},{width:390,height:844}]){
  const p=await b.newPage({viewport});
  p.on('pageerror',e=>report.errors.push(String(e)));
  p.on('requestfailed',req=>report.errors.push(req.url()+': '+req.failure()?.errorText));
  await p.goto('file://'+path.join(root,'index.html'));
  for(let i=0;i<5;i++){
   await p.locator('#angle').selectOption(String(i));
   await p.waitForFunction(()=>[...document.images].length===12&&[...document.images].every(x=>x.complete&&x.naturalWidth===1024));
   const count=await p.locator('img').evaluateAll(xs=>xs.filter(x=>x.complete&&x.naturalWidth===1024).length);
   if(count!==12)throw Error('Missing '+(12-count)+' images');
   if(i===2)await p.screenshot({path:path.join(root,'chromium-'+viewport.width+'-yaw60.png'),fullPage:true});
   report.checks.push({viewport:viewport.width,angleIndex:i,loaded:count});
  }
  await p.close();
 }
 await b.close();
 if(report.errors.length)throw Error(JSON.stringify(report.errors));
 fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-29-browser-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({checks:report.checks.length,imageLoads:report.checks.reduce((n,c)=>n+c.loaded,0),errors:report.errors.length}));
})().catch(e=>{console.error(e);process.exit(1)});
