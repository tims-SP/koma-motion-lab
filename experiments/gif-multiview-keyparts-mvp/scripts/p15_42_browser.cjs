const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');const R=path.resolve(__dirname,'..'),D=path.join(R,'private-assets/exports/p15-42-65-keyart-review');
(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox']});let qa={schema:'KOMA-P15-42-BROWSER-V1',checks:[],screenshots:[],errors:[]};try{
 for(const v of [{name:'desktop',width:1440,height:850},{name:'mobile',width:390,height:844}]){
  const p=await b.newPage({viewport:v});p.on('pageerror',e=>qa.errors.push(String(e)));p.on('requestfailed',e=>qa.errors.push(e.url()));await p.goto('file://'+path.join(D,'index.html'));
  for(const mode of ['angle','identity']){const ok=await p.evaluate(m=>window.__KOMA_P15_42.show(m),mode);if(!ok)throw Error('Image check failed '+mode);qa.checks.push({viewport:v.name,mode,images:mode==='angle'?4:3});const file=`browser-${v.name}-${mode}.png`;await p.locator('#gallery').screenshot({path:path.join(D,file)});qa.screenshots.push({file,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(D,file))).digest('hex')});}await p.close();}
 if(qa.errors.length)throw Error(qa.errors.join('\n'));qa.status='P15_42_SOURCE_IMAGES_BROWSER_REVIEW_VERIFIED';fs.writeFileSync(path.join(R,'evidence/p15-42-browser-qa.json'),JSON.stringify(qa,null,2)+'\n');console.log(JSON.stringify({checks:qa.checks.length,images:14,screenshots:qa.screenshots.length,errors:qa.errors.length}));
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
