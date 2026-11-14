const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'private-assets/exports/p15-60-transition-visual');
(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox']});const q={schema:'KOMA-P15-60-BROWSER-V1',checks:[],errors:[]};
try{for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
const p=await b.newPage({viewport:v});p.on('pageerror',e=>q.errors.push(String(e)));p.on('requestfailed',e=>q.errors.push(e.url()));
await p.goto('file://'+path.join(dir,'index.html'));
const ready=await p.locator('img').evaluateAll(xs=>xs.length===5&&xs.every(x=>x.complete&&x.naturalWidth>0));
if(!ready)throw Error('initial images absent');
await p.locator('#frameSlider').fill('8');
await p.waitForFunction(()=>document.getElementById('whole').complete&&document.getElementById('whole').naturalWidth===1024&&document.getElementById('whole').getAttribute('src')==='frame-08.png');
if(!(await p.locator('#label').innerText()).includes('65°'))throw Error('slider not interactive');
await p.locator('#frameSlider').fill('4');
await p.waitForFunction(()=>document.getElementById('face').complete&&document.getElementById('face').naturalWidth>0&&document.getElementById('face').getAttribute('src')==='face-04.png');
const file='browser-'+v.name+'.png';await p.screenshot({path:path.join(dir,file),fullPage:true});
q.checks.push({viewport:v.name,images:5,interactiveSliderVerified:true,file,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,file))).digest('hex')});await p.close();
}if(q.errors.length)throw Error(q.errors.join(';'));q.status='PASS';fs.writeFileSync(path.join(root,'evidence/p15-60-browser-qa.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({checks:2,sliderChecks:2,loadedImages:10,errors:0}));}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
