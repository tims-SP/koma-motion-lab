// Codex independent eye-control capture. No generated image is a color input.
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const ROOT=path.dirname(fileURLToPath(import.meta.url)),OUT=path.join(ROOT,'out/core026/eyes-supervisor');
const sha=b=>createHash('sha256').update(b).digest('hex');
const contract=JSON.parse(await readFile(path.join(ROOT,'config/core025-layer-contract.json'),'utf8'));
const raw=new Set(contract.layers.map(l=>'/'+l.raw_source_texture.file));
const requested=new Set(),blocked=[],errors=[],captures=[],invalidControls=[];
await mkdir(OUT,{recursive:true});
const server=await createServer({root:ROOT,server:{host:'127.0.0.1',port:4188,strictPort:true}});
await server.listen();let browser;
try{
  browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const context=await browser.newContext({viewport:{width:1630,height:1630},deviceScaleFactor:1,serviceWorkers:'block'});
  await context.route('**/*',async route=>{
    const u=new URL(route.request().url()),p=decodeURIComponent(u.pathname);
    if(u.origin!=='http://127.0.0.1:4188'||p.startsWith('/out/core025/')||p==='/core025.js'||p==='/core025.html'||
       (/\.(png|webp|jpe?g)$/i.test(p)&&!raw.has(p))){blocked.push(p);await route.abort();return;}
    if(raw.has(p))requested.add(p);await route.continue();
  });
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('favicon'))errors.push(m.text());});
  await page.goto('http://127.0.0.1:4188/core026.html',{waitUntil:'load'});
  await page.waitForFunction(()=>window.core026Ready===true,{},{timeout:90000});
  async function snap(state,version,background,control){
    const params={version,background,pass:'beauty',size:1630};
    const pose=await page.evaluate(p=>window.core026.render(p),params);
    const bytes=await page.locator('#stage').screenshot(),id=`${state}_${version}_${background}`;
    await writeFile(path.join(OUT,id+'.png'),bytes);
    captures.push({id,file:id+'.png',state,params,control,pose,sha256:sha(bytes)});
  }
  async function four(state,control){
    for(const version of ['source','clean'])for(const background of ['white','black'])await snap(state,version,background,control);
  }
  await four('default',{eye:'both',dx:0});
  for(const [eye,dx] of [['left',9],['right',-9],['both',1.5],['left','8'],['unknown',0]]){
    const result=await page.evaluate(([eye,dx])=>{try{window.core026.setEyeGaze(eye,dx);return 'ACCEPTED';}catch(e){return e.message;}},[eye,dx]);
    invalidControls.push({eye,dx,result});if(result==='ACCEPTED')throw Error('Invalid eye control accepted');
  }
  const invalidPose=await page.evaluate(()=>window.core026.render({version:'source',background:'white',pass:'beauty',size:1630}));
  const invalidControlState={pose:invalidPose,sha256:sha(await page.locator('#stage').screenshot())};
  for(const eye of ['left','right','both'])for(const dx of [-8,8]){
    await page.evaluate(([eye,dx])=>{window.core026.reset();window.core026.setEyeGaze(eye,dx);},[eye,dx]);
    await four(eye+(dx<0?'_minus8':'_plus8'),{eye,dx});
  }
  await page.evaluate(()=>window.core026.setEyeGaze('both',0));await four('reset',{eye:'both',dx:0});
  for(const [eye,highlight] of [['left',29],['right',39]]){
    await page.evaluate(([eye,highlight])=>{window.core026.reset();window.core026.setEyeGaze(eye,8);window.core026.setLayerUvOffset(highlight,[0,0]);},[eye,highlight]);
    await snap('negative_'+eye+'_highlight_static','source','white',{eye,dx:8,negative:'PUPIL_ONLY_HIGHLIGHT_STATIC'});
  }
  for(const [eye,pupil,highlight] of [['left',28,29],['right',38,39]]){
    await page.evaluate(([pupil,highlight])=>{window.core026.reset();window.core026.setLayerUvOffset(pupil,[8,0]);window.core026.setLayerUvOffset(highlight,[8,0]);},[pupil,highlight]);
    await snap('negative_'+eye+'_fixed_domain','source','white',{eye,dx:8,negative:'FIXED_REST_DOMAIN_CUTS_MOVED_IRIS'});
  }
  const inputs={};for(const f of ['core026.html','core026.js','config/core026-eye-policy.json','config/core025-layer-contract.json',
    'config/core026-compositor-contract.json','config/core025-render.json','capture_core026_eyes_supervisor.mjs'])inputs[f]=sha(await readFile(path.join(ROOT,f)));
  const report={schema:'core026-eye-captures/1',inputs,metadata:await page.evaluate(()=>window.core026.metadata),captures,
    invalid_controls:invalidControls,invalid_control_state:invalidControlState,requested_raw_pngs:[...requested].sort(),blocked_paths:blocked,page_errors:errors,
    scope:'ARTIST_OVERRIDE; DISCRETE_HORIZONTAL_DEFAULT_POSE_ONLY; NOT_NATIVE_CLIP_OR_NATURAL_TURN'};
  await writeFile(path.join(OUT,'manifest.json'),JSON.stringify(report,null,2)+'\n');
  if(blocked.length||errors.length||requested.size!==62)throw Error('Source audit/page error');
  console.log(JSON.stringify({status:'EYES_CAPTURED_FOR_INDEPENDENT_REVIEW',captures:captures.length,raw_pngs:requested.size}));
}finally{if(browser)await browser.close();await server.close();}
