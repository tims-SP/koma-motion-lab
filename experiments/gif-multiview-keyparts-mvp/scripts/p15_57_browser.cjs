const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-57-multiview-audit');
(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox']});const q={schema:'KOMA-P15-57-BROWSER-V1',checks:[],errors:[]};try{
 for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
  const p=await b.newPage({viewport:v});p.on('pageerror',e=>q.errors.push(String(e)));p.on('requestfailed',e=>q.errors.push(e.url()));
  await p.goto('file://'+path.join(dir,'index.html'));
  const imgs=await p.locator('figure img').evaluateAll(xs=>xs.map(x=>x.complete&&x.naturalWidth>0));
  if(imgs.length!==8||!imgs.every(Boolean))throw Error('image load failure '+v.name);
  const name='browser-'+v.name+'.png';await p.screenshot({path:path.join(dir,name),fullPage:true});
  q.checks.push({viewport:v.name,images:imgs.length,file:name,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,name))).digest('hex')});await p.close();
 }
 if(q.errors.length)throw Error(q.errors.join(';'));q.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-57-browser-qa.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({checks:2,loadedImages:16,errors:0}));
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
