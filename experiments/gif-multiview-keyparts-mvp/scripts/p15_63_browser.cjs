const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-63-masked-lama');
(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox']});const q={schema:'KOMA-P15-63-BROWSER-V1',checks:[],errors:[]};
try{for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const p=await b.newPage({viewport:v});p.on('pageerror',e=>q.errors.push(String(e)));p.on('requestfailed',e=>q.errors.push(e.url()));
await p.goto('file://'+path.join(dir,'index.html'));
const loaded=await p.locator('figure img').evaluateAll(xs=>xs.length===9&&xs.every(x=>x.complete&&x.naturalWidth>0));
if(!loaded)throw Error('image load '+v.name);
const file=v.name==='desktop'?'browser-desktop.png':null;if(file){await p.screenshot({path:path.join(dir,file),fullPage:false,timeout:20000});}
q.checks.push({viewport:v.name,imagesLoaded:9,screenshot:file,sha256:file?crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,file))).digest('hex'):null});await p.close();
}if(q.errors.length)throw Error(q.errors.join(';'));q.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-63-browser-qa.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({checks:2,imagesLoaded:18,errors:0}));}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
