const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const r=path.resolve(__dirname,'..'),d=path.join(r,'private-assets/exports/p15-44-control-inputs');
(async()=>{
 const b=await chromium.launch({headless:true,args:['--no-sandbox']});const qa={schema:'KOMA-P15-44-BROWSER-V1',checks:[],screenshots:[],errors:[]};
 try{
  for(const view of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
   const p=await b.newPage({viewport:view});p.on('pageerror',e=>qa.errors.push(String(e)));
   p.on('requestfailed',e=>qa.errors.push(e.url()));
   await p.goto('file://'+path.join(d,'index.html'));await p.locator('main img').first().waitFor();
   const images=await p.locator('main img').evaluateAll(xs=>xs.map(x=>({ok:x.complete&&x.naturalWidth===1024,width:x.naturalWidth})));
   if(images.length!==5||!images.every(x=>x.ok))throw Error('images not loaded '+view.name+' '+JSON.stringify(images));
   const out='browser-'+view.name+'.png';await p.screenshot({path:path.join(d,out),fullPage:true});
   qa.checks.push({viewport:view.name,images:images.length});
   qa.screenshots.push({file:out,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(d,out))).digest('hex')});await p.close();
  }
  if(qa.errors.length)throw Error(qa.errors.join(';'));
  qa.status='P15_44_CONTROL_INPUTS_BROWSER_VERIFIED_NO_MODEL_GENERATION';
  fs.writeFileSync(path.join(r,'evidence/p15-44-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
  console.log(JSON.stringify({checks:qa.checks.length,loads:10,screenshots:qa.screenshots.length,errors:0}));
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
