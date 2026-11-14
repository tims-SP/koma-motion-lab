const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-110-path-vdd');
(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox']});
const doc=JSON.parse(fs.readFileSync(path.join(R,'evidence/p15-110-review-qa.json')));
const qa={schema:'KOMA_P15_110_BROWSER_QA_V1',status:'STARTED',checks:[],errors:[]};
try{
for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const p=await b.newPage({viewport:{width:vp.width,height:vp.height}});
 p.on('pageerror',e=>qa.errors.push(String(e)));
 p.on('requestfailed',r=>{if(!String(r.failure()).includes('ERR_ABORTED'))qa.errors.push('fetch '+r.url());});
 await p.goto('file://'+path.join(D,'index.html'));
 for(const m of Object.keys(doc.methodFrames)){
  await p.locator('#method').selectOption(m);
  await p.locator('#motion').evaluate(img=>img.decode());
  for(let i=0;i<doc.renderedAngles.length;i++){
   await p.locator('#yaw').evaluate((x,v)=>{x.value=String(v);x.dispatchEvent(new Event('input',{bubbles:true}));},i);
   await p.locator('#frame').evaluate(img=>img.decode());
   const state=await p.evaluate(()=>({src:document.querySelector('#frame').getAttribute('src'),
     gif:document.querySelector('#motion').getAttribute('src'),
     loaded:[...document.querySelectorAll('img')].map(x=>x.complete&&x.naturalWidth>0)}));
   if(state.src!==doc.methodFrames[m][String(doc.renderedAngles[i])]||
     state.gif!==m+'-loop.gif'||state.loaded.length<7||state.loaded.some(x=>!x))
      throw Error(vp.name+' '+m+' '+i+' '+JSON.stringify(state));
   qa.checks.push({viewport:vp.name,method:m,index:i,imagesLoaded:state.loaded.length});
  }
 }
 const shot=path.join(D,'browser-'+vp.name+'.png');
 await p.screenshot({path:shot,fullPage:false});
 qa.checks[qa.checks.length-1].screenshotSHA256=crypto.createHash('sha256').update(fs.readFileSync(shot)).digest('hex');
 await p.close();
}
if(qa.errors.length)throw Error(qa.errors.join(';'));
qa.status='PASS';
fs.writeFileSync(path.join(R,'evidence/p15-110-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
console.log(JSON.stringify({status:qa.status,checks:qa.checks.length,errors:qa.errors.length}));
}finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
