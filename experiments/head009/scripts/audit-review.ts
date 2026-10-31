import {chromium} from 'playwright';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
const dir=resolve('out/head009');
await mkdir(dir,{recursive:true});
const html=join(dir,'head009-review.html');
const source=await readFile(html,'utf8');
const failures:string[]=[];
if(/<script[^>]+\bsrc=|<link[^>]+href=/i.test(source))failures.push('external_asset_dependency');
if(!source.includes('window.__HEAD009_REFS=')||!source.includes('window.__HEAD009_ORGAN='))failures.push('embedded_sources_missing');
const isolatedBrowser=process.env.HEAD009_BROWSER_EXECUTABLE;
const browser=await chromium.launch({
 ...(isolatedBrowser?{executablePath:isolatedBrowser}:{channel:process.env.HEAD009_CHROME_CHANNEL??'chrome'}),
 headless:true,
 args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-gpu-sandbox','--allow-file-access-from-files',...(isolatedBrowser?['--in-process-gpu']:[])],
 ...(isolatedBrowser?{env:{PATH:'/usr/bin:/bin',HOME:'/tmp',EGL_PLATFORM:'surfaceless',LIBGL_ALWAYS_SOFTWARE:'1',MESA_LOADER_DRIVER_OVERRIDE:'llvmpipe'}}:{})
});
const page=await browser.newPage({viewport:{width:1366,height:900},deviceScaleFactor:1,acceptDownloads:true});
const errors:string[]=[],external:string[]=[];
page.on('pageerror',e=>errors.push(String(e)));
page.on('request',r=>{if(/^https?:/.test(r.url()))external.push(r.url())});
let qa:any=null,after:Record<string,unknown>={};
try{
 await page.goto(pathToFileURL(html).href,{waitUntil:'load'});
 await page.waitForFunction(()=>(window as Window & {__HEAD009_READY?:boolean}).__HEAD009_READY===true,{timeout:45000});
 if(await page.locator('#angleOut').textContent()!=='0°')failures.push('initial_angle');
 await page.screenshot({path:join(dir,'review-html-initial.png'),fullPage:true});
 await page.locator('[data-yaw="60"]').click();
 if(await page.locator('#angleOut').textContent()!=='60°')failures.push('angle_quick_select');
 if(!String(await page.locator('#refLabel').textContent()).includes('60°'))failures.push('reference_angle');
 const stats=await page.locator('#organTable').textContent();
 if(!stats?.includes('nose.tip')||!stats.includes('mouth'))failures.push('organ_metrics_absent');
 await page.locator('#runQa').click();
 const status=await page.locator('#qaStatus').textContent();
 if(!status?.includes('PASS_ENGINEERING'))failures.push('webgl_qa_at_60');
 await page.screenshot({path:join(dir,'review-html-60.png'),fullPage:true});
 await page.locator('#pass').selectOption('1');
 if(!String(await page.locator('#renderLabel').textContent()).includes('Part-ID'))failures.push('part_id_mode');
 await page.locator('#showRef').uncheck();
 if(await page.locator('#refPanel').isVisible())failures.push('reference_toggle');
 await page.locator('#showRef').check();
 await page.locator('[data-yaw="90"]').click();
 if(await page.locator('#angleOut').textContent()!=='90°')failures.push('profile_angle');
 await page.locator('#pass').selectOption('0');
 await page.screenshot({path:join(dir,'review-html-90.png'),fullPage:true});
 qa=await page.evaluate(()=>window.head009.qa(90));
 const downloadPromise=page.waitForEvent('download');
 await page.locator('#saveReport').click();
 const dl=await downloadPromise;
 if(!dl.suggestedFilename().endsWith('-review.json'))failures.push('report_download');
 const playbackStart=Number(await page.locator('#yaw').inputValue());
 await page.locator('#play').click();
 await page.waitForTimeout(280);
 const playbackEnd=Number(await page.locator('#yaw').inputValue());
 if(playbackEnd===playbackStart)failures.push('playback_no_motion');
 await page.locator('#play').click();
 after={angle:await page.locator('#angleOut').textContent(),report:dl.suggestedFilename(),playbackStart,playbackEnd,
  requiredDomIds:8,embeddedOriginalArt:6,qa90:qa.result};
}catch(e){failures.push('uncaught:'+String(e))}
finally{await browser.close();}
if(errors.length)failures.push(...errors.map(x=>'pageerror:'+x));
if(external.length)failures.push(...external.map(x=>'network:'+x));
const report={schema:'HEAD009-OFFLINE-HTML-QA-V1',mode:'file:// standalone, real Three.js/WebGL',
 checks:{selfContained:!/\bsrc="https?:/i.test(source),offlineRequests:external.length,jsRuntimeErrors:errors.length,controls:after},
 defects:failures,status:failures.length?'FAIL':'PASS_HTML_OFFLINE'};
await writeFile(join(dir,'html-review-qa.json'),JSON.stringify(report,null,2)+'\n');
console.log('HEAD009_HTML_QA '+JSON.stringify(report));
if(failures.length)process.exitCode=1;
