const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-51-camera-angle-review');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const qa={schema:'KOMA-P15-51-BROWSER-V1',checks:[],errors:[]};
 try{
  for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
   const page=await browser.newPage({viewport:v});page.on('pageerror',e=>qa.errors.push(String(e)));
   await page.goto('file://'+path.join(dir,'index.html'));
   const n=await page.locator('.card img').evaluateAll(xs=>xs.length===3&&xs.every(x=>x.complete&&x.naturalWidth===1024&&x.naturalHeight===1024));
   if(!n)throw Error('review image load failure');
   const f='browser-'+v.name+'.png';await page.screenshot({path:path.join(dir,f),fullPage:true});
   qa.checks.push({viewport:v.name,images:3,screenshot:f,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,f))).digest('hex')});await page.close();
  }
  if(qa.errors.length)throw Error(qa.errors.join(';'));
  qa.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-51-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
  console.log(JSON.stringify({checks:qa.checks.length,images:6,errors:0}));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
