const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-52-transparency-geometry');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const q={schema:'KOMA-P15-52-BROWSER-V1',checks:[],errors:[]};
try{for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
 const page=await browser.newPage({viewport:v});page.on('pageerror',e=>q.errors.push(String(e)));page.on('requestfailed',r=>q.errors.push(r.url()));
 await page.goto('file://'+path.join(dir,'index.html'));
 const images=await page.locator('main img').evaluateAll(xs=>xs.map(x=>({ready:x.complete&&x.naturalWidth===1024&&x.naturalHeight===1024})));
 if(images.length!==8||!images.every(x=>x.ready))throw new Error('not all images available '+v.name);
 const filename='browser-'+v.name+'.png';await page.screenshot({path:path.join(dir,filename),fullPage:true});
 q.checks.push({viewport:v.name,images:images.length,file:filename,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,filename))).digest('hex')});await page.close();
}if(q.errors.length)throw Error(q.errors.join(';'));q.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-52-browser-qa.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({checks:q.checks.length,loadedImages:16,errors:0}));}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
