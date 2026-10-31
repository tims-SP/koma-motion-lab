import {chromium} from 'playwright';
import {createServer} from 'vite';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.dirname(fileURLToPath(import.meta.url));
const out=path.join(root,'out/structure');await mkdir(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex');
const server=await createServer({root,server:{host:'127.0.0.1',port:4173,strictPort:true}});await server.listen();
let browser;
try{
 browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:512,height:512},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:4173');
 await page.waitForFunction(()=>window.factoryReady,{},{timeout:90000});
 const {contract,metadata}=await page.evaluate(()=>({contract:window.factory.contract,metadata:window.factory.metadata}));
 const manifest={schema:'koma-structure-evidence/1',sourceSha256:sha(await readFile(path.join(root,'out/source/reference.vrm'))),contractSha256:sha(await readFile(path.join(root,'contract.json'))),environment:{node:process.version,chromium:browser.version(),...metadata},reproducibility:'same-process pixel hash comparison; separate process comparison performed by qa.py',views:[]};
 for(const yaw of contract.world.angles_deg){
  const tag=String(yaw).replace('.','_').padStart(5,'0');const view={yaw_deg:yaw,passes:{}};
  for(const pass of ['beauty','silhouette','depth','normal','part_id']){
   const pose=await page.evaluate(({yaw,pass})=>window.factory.render(yaw,pass),{yaw,pass});
   const png=await page.locator('canvas').screenshot();
   await page.evaluate(({yaw,pass})=>window.factory.render(yaw,pass),{yaw,pass});
   const repeat=await page.locator('canvas').screenshot();
   if(sha(png)!==sha(repeat))throw new Error(`Non-deterministic ${yaw}/${pass}`);
   const filename=`${tag}_${pass}.png`;await writeFile(path.join(out,filename),png);
   view.passes[pass]={file:filename,sha256:sha(png),repeatIdentical:true};view.pose=pose;
  }
  manifest.views.push(view);
 }
 if(errors.length)throw new Error(errors.join('\n'));
 await writeFile(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log(JSON.stringify({status:'PASS',views:manifest.views.length,passes:45,environment:manifest.environment}));
}finally{await browser?.close();await server.close();}
