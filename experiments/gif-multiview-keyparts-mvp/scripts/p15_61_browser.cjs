const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-61-semantic-feasibility');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const result={schema:'KOMA-P15-61-BROWSER-V1',checks:[],errors:[]};
try{for(const view of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const page=await browser.newPage({viewport:view});page.on('pageerror',e=>result.errors.push(String(e)));page.on('requestfailed',r=>result.errors.push(r.url()));
await page.goto('file://'+path.join(dir,'index.html'));
const loaded=await page.locator('figure img').evaluateAll(xs=>xs.length===11&&xs.every(x=>x.complete&&x.naturalWidth>0));
if(!loaded)throw Error('Missing review art '+view.name);
const file='browser-'+view.name+'.png';await page.screenshot({path:path.join(dir,file),fullPage:true});
result.checks.push({viewport:view.name,imagesLoaded:11,file,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,file))).digest('hex')});await page.close();
}if(result.errors.length)throw Error(result.errors.join(';'));result.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-61-browser-qa.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({checks:2,imagesLoaded:22,errors:0}));}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
