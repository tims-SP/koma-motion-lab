const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-55-registration');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const q={schema:'KOMA-P15-55-BROWSER-V1',checks:[],errors:[]};try{
 for(const view of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
  const p=await browser.newPage({viewport:view});
  p.on('pageerror',e=>q.errors.push(String(e)));p.on('requestfailed',r=>q.errors.push(r.url()));
  await p.goto('file://'+path.join(dir,'index.html'));
  const imgs=await p.locator('figure img').evaluateAll(xs=>xs.map(x=>x.complete&&x.naturalWidth>0));
  if(imgs.length!==9 || !imgs.every(Boolean))throw Error('missing image in '+view.name);
  const screenshot='browser-'+view.name+'.png';await p.screenshot({path:path.join(dir,screenshot),fullPage:true});
  q.checks.push({viewport:view.name,loadedImages:imgs.length,file:screenshot,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,screenshot))).digest('hex')});
  await p.close();
 }
 if(q.errors.length)throw Error(q.errors.join(';'));
 q.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-55-browser-qa.json'),JSON.stringify(q,null,2)+'\n');
 console.log(JSON.stringify({checks:q.checks.length,loadedImages:18,errors:0}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
