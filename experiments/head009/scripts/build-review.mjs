import {build} from 'vite';
import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import {resolve,join,dirname} from 'node:path';
import {createHash} from 'node:crypto';
const root=process.cwd(),out=resolve(root,'out/head009'),dist=resolve(out,'review-dist');
await mkdir(out,{recursive:true});
await build({root,base:'./',logLevel:'warn',
 build:{outDir:dist,emptyOutDir:true,rollupOptions:{input:resolve(root,'review.html')},minify:'esbuild',cssCodeSplit:false}});
let html=await readFile(join(dist,'review.html'),'utf8');
const script=html.match(/<script\s+type="module"[^>]*src="([^"]+)"[^>]*><\/script>/);
if(!script)throw Error('Vite did not emit a bundled review module');
const js=await readFile(resolve(dist,script[1].replace(/^\.\//,'')),'utf8');
if(/(?:^|\n)\s*import\s+(?!\()/m.test(js))throw Error('Remaining external JS imports');
html=html.replace(script[0],'<script type="module">\n'+js.replace(/<\/script/gi,'<\\/script')+'\n</script>');
for(const tag of html.matchAll(/<link\s+rel="stylesheet"[^>]*href="([^"]+)"[^>]*>/g)){
 const css=await readFile(resolve(dist,tag[1].replace(/^\.\//,'')),'utf8');
 html=html.replace(tag[0],'<style>\n'+css+'\n</style>');
}
const names=['front-000.svg','threequarter-045.svg','profile-right-090.svg','heldout-030.svg','heldout-060.svg','heldout-075.svg'];
const refs=Object.fromEntries(await Promise.all(names.map(async name=>[name,await readFile(resolve(root,'reference',name),'utf8')])));
const landmarks=JSON.parse(await readFile(resolve(root,'reference/organ-landmarks.json'),'utf8'));
const embedded=JSON.stringify(refs).replace(/</g,'\\u003c'),landmarksText=JSON.stringify(landmarks).replace(/</g,'\\u003c');
const injection='<script>window.__HEAD009_REFS='+embedded+';window.__HEAD009_ORGAN='+landmarksText+';</script>';
if(!html.includes('<!--HEAD009_EMBED-->'))throw Error('Missing embedding insertion point');
html=html.replace('<!--HEAD009_EMBED-->',injection);
if(/<script[^>]+\bsrc=|<link[^>]+href=/i.test(html))throw Error('Unbundled external dependency detected');
const file=join(out,'head009-review.html');
await writeFile(file,html);
const sha=createHash('sha256').update(html).digest('hex');
const report={schema:'HEAD009-HTML-PACKAGING-V1',file:'head009-review.html',bytes:(await stat(file)).size,sha256:sha,
 embeddedOriginalArt:names,organLandmarkCount:Object.keys(landmarks.organParts).length,noExternalScripts:true,buildMode:'standalone-vite-threejs'};
await writeFile(join(out,'html-packaging.json'),JSON.stringify(report,null,2)+'\n');
console.log('HEAD009_HTML_PACKAGE '+JSON.stringify(report));
