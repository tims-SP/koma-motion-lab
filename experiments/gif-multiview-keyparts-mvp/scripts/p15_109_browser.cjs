const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-109-collar-render');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const review=JSON.parse(fs.readFileSync(path.join(R,'evidence/p15-109-review-qa.json')));
const qa={schema:'KOMA_P15_109_STROKE_PATH_BROWSER_QA_V1',status:'STARTED',checks:[],errors:[]};
try{
for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
 page.on('pageerror',e=>qa.errors.push(String(e)));
 page.on('requestfailed',r=>{if(!String(r.failure()).includes('ERR_ABORTED'))qa.errors.push(r.url());});
 await page.goto('file://'+path.join(D,'index.html'));
 for(const method of Object.keys(review.methods)){
  await page.locator('#method').selectOption(method);
  await page.locator('#loop').evaluate(img=>img.decode());
  for(let index=0;index<review.renderedAngles.length;index++){
   await page.locator('#yaw').evaluate((el,value)=>{el.value=String(value);el.dispatchEvent(new Event('input',{bubbles:true}));},index);
   await page.locator('#frame').evaluate(img=>img.decode());
   const s=await page.evaluate(()=>({src:document.querySelector('#frame').getAttribute('src'),
     gif:document.querySelector('#loop').getAttribute('src'),
     images:[...document.querySelectorAll('img')].map(x=>x.complete&&x.naturalWidth>0)}));
   if(s.src!==review.methods[method][String(review.renderedAngles[index])]||
      s.gif!==method+'-loop.gif'||s.images.length<7||s.images.some(x=>!x))
     throw Error(vp.name+' '+method+' '+index+' '+JSON.stringify(s));
   qa.checks.push({viewport:vp.name,method,index,loadedImages:s.images.length});
  }
 }
 const shot=path.join(D,'browser-'+vp.name+'.png');
 await page.screenshot({path:shot,fullPage:false});
 qa.checks[qa.checks.length-1].screenshotSHA256=crypto.createHash('sha256').update(fs.readFileSync(shot)).digest('hex');
 await page.close();
}
if(qa.errors.length)throw Error(qa.errors.join(';'));
qa.status='PASS';fs.writeFileSync(path.join(R,'evidence/p15-109-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
