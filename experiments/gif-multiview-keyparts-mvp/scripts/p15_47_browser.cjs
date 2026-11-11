const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const r=path.resolve(__dirname,'..'),d=path.join(r,'private-assets/exports/p15-47-face-local-review');
(async()=>{
  const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  const result={schema:'KOMA-P15-47-BROWSER-V1',checks:[],screenshots:[],errors:[]};
  try {
    for(const v of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]) {
      const page=await browser.newPage({viewport:v});
      page.on('pageerror',err=>result.errors.push(String(err)));
      page.on('requestfailed',req=>result.errors.push(req.url()));
      await page.goto('file://'+path.join(d,'index.html'));
      const ok=await page.locator('main img').evaluateAll(imgs=>
        imgs.length===7 && imgs.every(img=>img.complete && img.naturalWidth===1024 && img.naturalHeight===1024));
      if(!ok)throw Error('visual asset load failure for '+v.name);
      const filename='browser-'+v.name+'.png';
      await page.screenshot({path:path.join(d,filename),fullPage:true});
      result.checks.push({viewport:v.name,imageLoads:7});
      result.screenshots.push({file:filename,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(d,filename))).digest('hex')});
      await page.close();
    }
    if(result.errors.length)throw Error(result.errors.join('\n'));
    result.status='P15_47_REVIEW_HTML_VERIFIED';
    fs.writeFileSync(path.join(r,'evidence/p15-47-browser-qa.json'),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify({checks:result.checks.length,images:14,screenshots:2,errors:0}));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
