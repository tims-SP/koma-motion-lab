// Codex independent browser capture. Candidate color may come only from raw PNGs.
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT=path.dirname(fileURLToPath(import.meta.url));
const OUT=path.join(ROOT,'out/core026/runtime-supervisor');
const sha=b=>createHash('sha256').update(b).digest('hex');
const contract=JSON.parse(await readFile(path.join(ROOT,'config/core025-layer-contract.json'),'utf8'));
const raw=new Set(contract.layers.map(l=>'/'+l.raw_source_texture.file));
const requested=new Set(),blocked=[],errors=[];
const server=await createServer({root:ROOT,server:{host:'127.0.0.1',port:4187,strictPort:true}});
await mkdir(OUT,{recursive:true});
await server.listen();
let browser;
try{
  browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const context=await browser.newContext({viewport:{width:1630,height:1630},deviceScaleFactor:1,serviceWorkers:'block'});
  await context.route('**/*',async route=>{
    const url=new URL(route.request().url());
    const p=decodeURIComponent(url.pathname);
    if((url.protocol==='http:'&&url.hostname!=='127.0.0.1') ||
       (url.protocol!=='http:'&&url.protocol!=='data:'&&url.protocol!=='blob:') ||
       p.startsWith('/out/core025/') || p==='/core025.js' || p==='/core025.html' ||
       (/\.(png|webp|jpe?g)$/i.test(p)&&!raw.has(p))){
      blocked.push(p);await route.abort();return;
    }
    if(raw.has(p))requested.add(p);
    await route.continue();
  });
  const page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('favicon'))errors.push(m.text());});
  await page.goto('http://127.0.0.1:4187/core026.html',{waitUntil:'load'});
  await page.waitForFunction(()=>window.core026Ready===true,{},{timeout:90000});
  const meta=await page.evaluate(()=>window.core026.metadata);
  const canvas=(await page.locator('#stage').count())?page.locator('#stage'):page.locator('canvas:visible').first();
  const captures=[];
  async function capture(id,params,repeat=false){
    const pose=await page.evaluate(async p=>await window.core026.render(p),params);
    const bytes=await canvas.screenshot();
    await writeFile(path.join(OUT,id+'.png'),bytes);
    let again=null;
    if(repeat){await page.evaluate(async p=>await window.core026.render(p),params);again=sha(await canvas.screenshot());}
    captures.push({id,file:id+'.png',params,pose:pose??null,sha256:sha(bytes),repeat_sha256:again});
    return captures.at(-1);
  }
  for(const version of ['source','clean']){
    for(const background of ['white','black'])await capture(version+'_'+background,{version,background,pass:'beauty',size:1630},true);
    for(const pass of ['alpha','part_id'])await capture(version+'_'+pass,{version,background:'black',pass,size:1630});
  }
  await page.evaluate(()=>window.core026.setLayerUvOffset(28,[8,0]));
  await capture('source_pupilL_shift8',{version:'source',background:'white',pass:'beauty',size:1630});
  await page.evaluate(()=>window.core026.setLayerUvOffset(28,[0,0]));
  await capture('source_pupilL_reset',{version:'source',background:'white',pass:'beauty',size:1630});
  await page.evaluate(()=>window.core026.setEyeMaskPolicy('eye_white_only'));
  await capture('negative_hard_eye_white',{version:'source',background:'white',pass:'beauty',size:1630});
  await page.evaluate(()=>window.core026.setEyeMaskPolicy('source_paint_domain'));
  await capture('source_mask_policy_reset',{version:'source',background:'white',pass:'beauty',size:1630});
  const expectedFiles=['core026.html','core026.js','capture_core026.mjs','config/core025-layer-contract.json',
                       'config/core026-compositor-contract.json','config/core025-render.json','config/core026-eye-policy.json'];
  const inputs={};for(const file of expectedFiles)inputs[file]=sha(await readFile(path.join(ROOT,file)));
  const report={schema:'core026-supervisor-captures/1',inputs,metadata:meta,captures,
    requested_raw_pngs:[...requested].sort(),blocked_paths:blocked,page_errors:errors,
    supervisor_capture_sha256:sha(await readFile(fileURLToPath(import.meta.url))),
    scope:'DEFAULT_POSE_ONLY; source colors audited independently; no depth/turn claim'};
  await writeFile(path.join(OUT,'manifest.json'),JSON.stringify(report,null,2)+'\n');
  if(blocked.length||errors.length)throw Error('Candidate attempted forbidden color input or page errors: '+JSON.stringify({blocked,errors}));
  if(requested.size!==62)throw Error('Expected62 distinct raw PNG requests, observed '+requested.size);
  console.log(JSON.stringify({status:'CAPTURED_FOR_SUPERVISOR',captures:captures.length,raw_pngs:requested.size}));
}finally{if(browser)await browser.close();await server.close();}
