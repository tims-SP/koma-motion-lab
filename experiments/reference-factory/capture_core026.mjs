// Fixed-work-order capture: true browser rendering, never old baseline inputs.
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const ROOT=path.dirname(fileURLToPath(import.meta.url)),OUT=path.join(ROOT,'out/core026/runtime');
const sha=b=>createHash('sha256').update(b).digest('hex');
await mkdir(OUT,{recursive:true});
const server=await createServer({root:ROOT,server:{host:'127.0.0.1',port:4186,strictPort:true}});await server.listen();let browser;const errors=[];
try{
  browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1630,height:1630},deviceScaleFactor:1});
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('favicon'))errors.push(m.text());});
  await page.goto('http://127.0.0.1:4186/core026.html',{waitUntil:'load'});await page.waitForFunction(()=>window.core026Ready===true,{},{timeout:120000});
  const captures=[];
  async function snap(id,params,repeat=false){
    const pose=await page.evaluate(p=>window.core026.render(p),params),bytes=await page.locator('#stage').screenshot();
    await writeFile(path.join(OUT,id+'.png'),bytes);let again=null;
    if(repeat){await page.evaluate(p=>window.core026.render(p),params);again=sha(await page.locator('#stage').screenshot());if(again!==sha(bytes))throw Error('Repeated capture differs');}
    captures.push({id,file:id+'.png',params,pose,sha256:sha(bytes),repeat_sha256:again});
  }
  for(const version of ['source','clean']){
    for(const background of ['white','black'])await snap(version+'_'+background,{version,background,pass:'beauty',size:1630},true);
    for(const pass of ['alpha','part_id'])await snap(version+'_'+pass,{version,background:'black',pass,size:1630});
  }
  await page.evaluate(()=>window.core026.setLayerUvOffset(28,[8,0]));await snap('source_pupilL_shift8',{version:'source',background:'white',pass:'beauty',size:1630});
  await page.evaluate(()=>window.core026.setLayerUvOffset(28,[0,0]));await snap('source_pupilL_reset',{version:'source',background:'white',pass:'beauty',size:1630});
  const inputs={};for(const file of ['core026.html','core026.js','capture_core026.mjs','config/core025-layer-contract.json','config/core026-compositor-contract.json','config/core026-eye-policy.json'])inputs[file]=sha(await readFile(path.join(ROOT,file)));
  const metadata=await page.evaluate(()=>window.core026.metadata);
  await writeFile(path.join(OUT,'manifest.json'),JSON.stringify({schema:'core026-runtime-captures/1',inputs,metadata,captures,errors,physical_depth:'NOT_RECOVERED',dynamic_occlusion:'NOT_IMPLEMENTED'},null,2)+'\n');
  if(errors.length)throw Error(JSON.stringify(errors));
  console.log(JSON.stringify({status:'ACTUAL_DEFAULT_BROWSER_CAPTURES_READY',captures:captures.length,source_count:metadata.source_count,receivers:metadata.receiver_count,logical_passes:metadata.logical_pass_count}));
}catch(error){await writeFile(path.join(OUT,'capture-failure.json'),JSON.stringify({status:'CAPTURE_FAILED',message:String(error),page_errors:errors},null,2)+'\n');throw error;
}finally{if(browser)await browser.close();await server.close();}
