const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{const root=path.resolve(__dirname,'../private-assets/exports/p15-33-anchor-vdd-review');
const b=await chromium.launch({headless:true,args:['--no-sandbox']});const q={checks:[],errors:[]};
for(const v of [{width:1440,height:900},{width:390,height:844}]){const p=await b.newPage({viewport:v});
p.on('pageerror',e=>q.errors.push(String(e)));p.on('requestfailed',r=>q.errors.push(r.url()+': '+r.failure()?.errorText));
await p.goto('file://'+path.join(root,'index.html'));
for(let i=0;i<9;i++){await p.locator('#slider').fill(String(i));
await p.waitForFunction(()=>document.querySelectorAll('#comps img').length===3&&document.querySelectorAll('#parts img').length===3&&[...document.images].every(x=>x.complete&&x.naturalWidth>0));
const loaded=await p.locator('img').evaluateAll(xs=>xs.filter(x=>x.complete&&x.naturalWidth>0).length);
if(loaded!==6)throw Error('image load count '+loaded);if(i===4)await p.screenshot({path:path.join(root,'chromium-'+v.width+'-yaw60.png'),fullPage:true});
q.checks.push({viewport:v.width,frame:i,loaded});}await p.close();}
await b.close();if(q.errors.length)throw Error(JSON.stringify(q.errors));
fs.writeFileSync(path.resolve(__dirname,'../evidence/p15-33-browser-qa.json'),JSON.stringify(q,null,2)+'\n');
console.log(JSON.stringify({checks:q.checks.length,images:q.checks.reduce((s,x)=>s+x.loaded,0),errors:q.errors.length}));})().catch(e=>{console.error(e);process.exit(1)});
