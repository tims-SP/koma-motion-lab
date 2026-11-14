const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-102-neck-eye-profile');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const qa={schema:'KOMA_P15_102_NECK_EYE_BROWSER_QA_V1',status:'STARTED',checks:[],errors:[]};
const review=JSON.parse(fs.readFileSync(path.join(R,'evidence/p15-102-review-qa.json'),'utf8'));
try{
for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const page=await browser.newPage({viewport:{width:vp.width,height:vp.height}});
 page.on('pageerror',e=>qa.errors.push(String(e)));page.on('requestfailed',r=>{const err=String(r.failure());if(!err.includes('ERR_ABORTED'))qa.errors.push('fetch '+r.url()+' '+err);});
 await page.goto('file://'+path.join(D,'index.html'));
 for(const method of Object.keys(review.methods)){
  await page.locator('#method').selectOption(method);
  await page.locator('#motion').evaluate(img=>img.decode());
  for(let i=0;i<review.angles.length;i++){
   await page.locator('#yaw').evaluate((x,v)=>{x.value=String(v);x.dispatchEvent(new Event('input',{bubbles:true}));},i);
   await page.locator('#frame').evaluate(img=>img.decode());
   const s=await page.evaluate(()=>({src:document.querySelector('#frame').getAttribute('src'),
      loop:document.querySelector('#motion').getAttribute('src'),images:[...document.querySelectorAll('img')].map(x=>({src:x.getAttribute('src'),loaded:x.complete&&x.naturalWidth>0}))}));
   const expected=review.methods[method][String(review.angles[i])];
   if(s.src!==expected||s.loop!==method+'-loop.gif'||s.images.length<6||s.images.some(x=>!x.loaded))
    throw Error(vp.name+' '+method+' '+i+' '+JSON.stringify(s));
   qa.checks.push({viewport:vp.name,method,angleIndex:i,imageCount:s.images.length});
  }
 }
 const png=path.join(D,'browser-'+vp.name+'.png');
 await page.screenshot({path:png,fullPage:false});
 qa.checks[qa.checks.length-1].screenshotSHA256=crypto.createHash('sha256').update(fs.readFileSync(png)).digest('hex');
 await page.close();
}
if(qa.errors.length)throw Error(qa.errors.join('; '));
qa.status='PASS';
fs.writeFileSync(path.join(R,'evidence/p15-102-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
