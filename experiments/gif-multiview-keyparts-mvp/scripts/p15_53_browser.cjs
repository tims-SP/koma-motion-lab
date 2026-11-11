const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-53-gold-clip-repair');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const q={schema:'KOMA-P15-53-BROWSER-V1',checks:[],errors:[]};
 try {
  for(const view of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]) {
   const page=await browser.newPage({viewport:view});
   page.on('pageerror',e=>q.errors.push(String(e)));page.on('requestfailed',req=>q.errors.push(req.url()));
   await page.goto('file://'+path.join(dir,'index.html'));
   const images=await page.locator('figure img').evaluateAll(xs=>xs.map(x=>x.complete&&x.naturalWidth>0));
   if(images.length!==9 || !images.every(Boolean))throw Error('missing image in '+view.name);
   const file='browser-'+view.name+'.png';await page.screenshot({path:path.join(dir,file),fullPage:true});
   q.checks.push({viewport:view.name,loadedImages:9,file,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,file))).digest('hex')});
   await page.close();
  }
  if(q.errors.length)throw Error(q.errors.join(';'));
  q.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-53-browser-qa.json'),JSON.stringify(q,null,2)+'\n');
  console.log(JSON.stringify({checks:q.checks.length,loadedImages:18,errors:0}));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
