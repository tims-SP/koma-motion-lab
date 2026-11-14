const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../private-assets/exports/p15-30-tracked-review');
 const b=await chromium.launch({headless:true,args:['--no-sandbox']});
 const report={checks:[],frames:[],errors:[]};
 for(const vp of [{width:1440,height:900},{width:390,height:844}]){
  const p=await b.newPage({viewport:vp});
  p.on('pageerror',e=>report.errors.push(String(e)));
  p.on('requestfailed',r=>report.errors.push(r.url()+': '+r.failure()?.errorText));
  await p.goto('file://'+path.join(root,'index.html'));
  for(let i=0;i<5;i++){
   await p.locator('#angle').selectOption(String(i));
   await p.waitForFunction(()=>document.querySelectorAll('#comparison img').length===6&&
    [...document.querySelectorAll('#comparison img')].every(x=>x.complete&&x.naturalWidth===1024));
   report.checks.push({viewport:vp.width,angleIndex:i,loaded:6});
  }
  for(let i=0;i<9;i++){
   await p.locator('#timeline').fill(String(i));
   await p.waitForFunction(i=>document.querySelector('#timelineImage').complete&&
     document.querySelector('#timelineImage').naturalWidth===1024&&
     document.querySelector('#timelineLabel').textContent.includes(
       ({0:55,1:56.25,2:57.5,3:58.75,4:60,5:61.25,6:62.5,7:63.75,8:65})[i]+'°'),i);
   report.frames.push({viewport:vp.width,index:i,loaded:1});
  }
  await p.locator('#angle').selectOption('2');
  await p.locator('#timeline').fill('4');
  await p.screenshot({path:path.join(root,'chromium-'+vp.width+'-yaw60.png'),fullPage:true});
  await p.close();
 }
 await b.close();
 if(report.errors.length)throw Error(JSON.stringify(report.errors));
 fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-30-browser-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({checks:report.checks.length,timelineFrames:report.frames.length,imageLoads:report.checks.length*6+report.frames.length,errors:report.errors.length}));
})().catch(e=>{console.error(e);process.exit(1)});
