#!/usr/bin/env python3
"""Bundle private Cubism Part + PMX reference + semantic proxy into one offline HTML.

The resulting self-contained document contains third-party image pixels; keep
the generated HTML in the user's private workspace, not public source control.
"""
import argparse,base64,hashlib,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--html',type=Path,required=True)
 p.add_argument('--javascript',type=Path,required=True)
 p.add_argument('--native-front',type=Path,required=True)
 p.add_argument('--geometry-reference',type=Path,required=True)
 p.add_argument('--semantic-proxy',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args()
 root=a.native_front.resolve()
 native=json.loads((root/'front-layer-manifest.json').read_text())
 geom=a.geometry_reference.resolve()
 geometry=json.loads((geom/'turnaround-qa.json').read_text())
 proxy_dir=a.semantic_proxy.resolve()
 proxy=json.loads((proxy_dir/'proxy-semantic-manifest.json').read_text())
 proxy_qa=json.loads((proxy_dir/'semantic-proxy-qa.json').read_text())
 if geometry.get('status')!='PASS_3D_REFERENCE_RENDER':
  raise ValueError('Structural source failed verification')
 if proxy_qa.get('status')!='PASS_3D_SEMANTIC_PROXY' or proxy.get('independentArtCoverage')!=0:
  raise ValueError('Semantic proxy provenance failed')
 if len(proxy['layers'])!=16 or len(native.get('entries',[]))!=40:
  raise ValueError('Unexpected source file coverage')
 resources={}
 def embed(prefix,file,expected=None):
  path=Path(file)
  raw=path.read_bytes()
  h=hashlib.sha256(raw).hexdigest()
  if expected and h!=expected:raise ValueError('Source integrity mismatch '+str(path))
  key=prefix+'/'+path.name
  resources[key]=base64.b64encode(raw).decode('ascii')
 for entry in native['entries']:
  embed('./private-view-assets',root/entry['filename'],entry['sha256'])
 embed('./private-view-assets',root/'front-layer-manifest.json')
 for key in ('yaw045_three_quarter.png','yaw090_profile.png'):
  match=next(x for x in geometry['renderedImages'] if x['filename']==key)
  embed('./private-geometry-view',geom/key,match['sha256'])
 for entry in proxy['layers']:
  embed('./private-proxy-layers',proxy_dir/entry['path'],entry['sha256'])
 embed('./private-proxy-layers',proxy_dir/'proxy-semantic-manifest.json')
 js=a.javascript.read_text(encoding='utf-8')
 from_native="image.src='./private-view-assets/'+encodeURIComponent(entry.filename);"
 to_native="image.src=window.__R1999_INLINE_URI('./private-view-assets/'+encodeURIComponent(entry.filename));"
 if js.count(from_native)!=1:raise ValueError('Native source image binding changed')
 js=js.replace(from_native,to_native)
 from_geom="img.src='./private-geometry-view/'+encodeURIComponent(file);"
 to_geom="img.src=window.__R1999_INLINE_URI('./private-geometry-view/'+encodeURIComponent(file));"
 if js.count(from_geom)!=1:raise ValueError('Geometry source image binding changed')
 js=js.replace(from_geom,to_geom)
 h=a.html.read_text(encoding='utf-8')
 marker='<script src="./view-layer-lab.js" defer></script>'
 if h.count(marker)!=1:raise ValueError('HTML entrypoint changed')
 boot="""<script>
(() => {
  const resources=__RESOURCES__;
  const uri=key=>'data:'+(key.endsWith('.png')?'image/png':'application/json')+
   ';base64,'+(resources[key]||(()=>{throw new Error('Missing '+key);})());
  window.__R1999_INLINE_URI=uri;
  window.fetch=async(resource)=>{
   const key=String(resource);
   if(!Object.hasOwn(resources,key))throw Error('Resource unavailable in offline package: '+key);
   const payload=Uint8Array.from(atob(resources[key]),c=>c.charCodeAt(0));
   return new Response(payload,{status:200,
    headers:{'Content-Type':key.endsWith('.png')?'image/png':'application/json'}});
  };
})();
</script>
<script>
__JS__
setTimeout(()=>document.getElementById('proxy').click(),120);
</script>"""
 boot=boot.replace('__RESOURCES__',json.dumps(resources,separators=(',',':')))
 boot=boot.replace('__JS__',js.replace('</script','<\\/script'))
 h=h.replace(marker,boot)
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(h,encoding='utf-8')
 report={'schema':'R1999-C06-OFFLINE-SEMANTIC-VDD-PACKAGE-V1',
  'file':a.output.name,
  'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),
  'bytes':a.output.stat().st_size,
  'resourceCount':len(resources),'sourcePartCount':40,
  'geometrySourceCount':2,'pmxProxyCount':16,'independentPaintedArtCount':0,
  'sourceRoles':['Cubism_native_ref','PMX_3D_structure','third_party_3d_proxy'],
  'usage':'private personal review HTML with embedded licensed imagery'}
 a.output.with_suffix('.manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
