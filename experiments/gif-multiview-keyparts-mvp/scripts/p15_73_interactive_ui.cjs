const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');const fs=require('fs'),path=require('path');
(async()=>{const b=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});const p=await b.newPage({viewport:{width:1280,height:1100}});p.setDefaultTimeout(25000);p.on('pageerror',e=>console.log('PAGEERR',String(e)));p.on('console',m=>{if(m.type()==='error')console.log('CONSOLE',m.text())});
await p.goto('https://basimbashir-segment-anything-webui.hf.space/',{waitUntil:'domcontentloaded',timeout:90000});console.log('PAGE_LOADED');await p.waitForTimeout(3000);
await p.locator('input[type=file]').nth(0).setInputFiles(path.resolve('private-assets/exports/p15-73-interactive-sam/input-512.png'));console.log('IMAGE_UPLOADED');await p.waitForTimeout(3500);
await p.addStyleTag({content:'.image-container img.selectable{width:512px!important;height:512px!important;max-height:none!important;object-fit:fill!important}.image-container{height:512px!important;min-height:512px!important}'});
let im=p.locator('img.selectable').first();console.log('RECT',await im.boundingBox(),'NATURAL',await im.evaluate(x=>[x.naturalWidth,x.naturalHeight]));
const pos=[[250,245],[300,220],[340,260],[205,270]];for(const [x,y] of pos){await im.click({position:{x,y}});await p.waitForTimeout(250);}console.log('POSITIVE_DONE');
await p.getByText('background_point',{exact:true}).click();await p.waitForTimeout(300);
const neg=[[240,345],[250,415],[390,170],[400,390]];for(const [x,y] of neg){await im.click({position:{x,y}});await p.waitForTimeout(250);}console.log('NEGATIVE_DONE');
await p.screenshot({path:'private-assets/exports/p15-73-interactive-sam/ui-points-real.png',fullPage:false});
await p.getByRole('button',{name:'Auto!',exact:true}).first().click();console.log('INFERENCE_STARTED');
await p.waitForFunction(()=>[...document.querySelectorAll('img')].some(x=>x.naturalWidth>=500&&x!==document.querySelector('img.selectable')&&x.getBoundingClientRect().top>250),null,{timeout:240000}).catch(e=>console.log('OUTPUT_WAIT_TIMEOUT',e.message));await p.waitForTimeout(2000);
const imgs=await p.locator('img').evaluateAll(xs=>xs.map((x,i)=>({i,src:x.src,alt:x.alt,natural:[x.naturalWidth,x.naturalHeight],rect:(()=>{let r=x.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})()})).filter(x=>x.natural[0]>=500));console.log('OUTPUTS',imgs.map(x=>({i:x.i,alt:x.alt,natural:x.natural,src:x.src.slice(0,70),rect:x.rect})));
let n=0;for(const x of imgs){if(x.src.startsWith('data:image')){const m=x.src.match(/^data:image\/([^;]+);base64,(.+)$/);if(m){const name='ui-real-output-'+n+'.png';fs.writeFileSync(path.join('private-assets/exports/p15-73-interactive-sam',name),Buffer.from(m[2],'base64'));console.log('SAVED',name);n++;}}}
await p.screenshot({path:'private-assets/exports/p15-73-interactive-sam/ui-real-result.png',fullPage:false});await b.close();
})().catch(e=>{console.error('FATAL',e);process.exitCode=1});
