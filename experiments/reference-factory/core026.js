// Default compositor design/initial application: Codex/mcode. Eye control: Codex.
// Raw RGBA is decoded losslessly. Multiply is resolved live against preceding
// artwork, then GPU-rasterized as source operations on19 shared receiver meshes.
// No old baked layers/whole-head image, no fitted depth or nonzero yaw support.
import * as THREE from 'three';
const N=1630,C=815;
const raw=new Map(),shifts=new Map(),textures=new Map(),materials=new Map(),meshes=[];
const hash=async b=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('');
const load=async p=>{const r=await fetch(p);if(!r.ok)throw Error(p+': '+r.status);return r;};
const json=async p=>(await load(p)).json();

// Lossless PNG RGBA8 decoder: avoids Canvas2D premultiply/unpremultiply loss.
async function rgbaPNG(url,expected){
  const b=await (await load(url)).arrayBuffer();if(await hash(b)!==expected)throw Error('Source PNG SHA '+url);
  const bytes=new Uint8Array(b),v=new DataView(b),idat=[];let w,h;
  for(let p=8;p<bytes.length;){const len=v.getUint32(p),type=String.fromCharCode(...bytes.subarray(p+4,p+8));
    if(type==='IHDR'){w=v.getUint32(p+8);h=v.getUint32(p+12);if(bytes[p+16]!==8||bytes[p+17]!==6||bytes[p+20]!==0)throw Error('Expected noninterlaced RGBA8 PNG');}
    if(type==='IDAT')idat.push(bytes.slice(p+8,p+8+len));p+=12+len;if(type==='IEND')break;}
  const scan=new Uint8Array(await new Response(new Blob(idat).stream().pipeThrough(new DecompressionStream('deflate'))).arrayBuffer());
  const stride=w*4,out=new Uint8Array(stride*h);if(scan.length!==(stride+1)*h)throw Error('PNG scan length');
  const paeth=(a,b,c)=>{const p=a+b-c,pa=Math.abs(p-a),pb=Math.abs(p-b),pc=Math.abs(p-c);return pa<=pb&&pa<=pc?a:pb<=pc?b:c;};
  let s=0;for(let y=0;y<h;y++){const f=scan[s++];if(f>4)throw Error('PNG filter');
    for(let x=0;x<stride;x++){const i=y*stride+x,a=x>=4?out[i-4]:0,b=y?out[i-stride]:0,c=y&&x>=4?out[i-stride-4]:0;
      out[i]=scan[s++]+(f===0?0:f===1?a:f===2?b:f===3?Math.floor((a+b)/2):paeth(a,b,c));}}
  return {w,h,data:out};
}

const contract=await json('/config/core025-layer-contract.json');
const proposal=await json('/config/core026-compositor-contract.json');
const cfg=await json('/config/core025-render.json');
const eyePolicy=await json('/config/core026-eye-policy.json');
if(eyePolicy.schema!=='core026-eye-policy/1'||eyePolicy.selected_policy!=='artist_override_source_paint_domain'||
   eyePolicy.runtime_mask_policy!=='source_paint_domain'||eyePolicy.control.integer_min!==-8||eyePolicy.control.integer_max!==8||eyePolicy.coupled_gaze_horizontal_radius!==8)
  throw Error('Unrecognized explicit artist eye override');
for(const [side,orders] of [['left',[27,28,29]],['right',[37,38,39]]]){
  const e=eyePolicy.eyes[side];if(!e||[e.white_order,e.pupil_order,e.highlight_order].some((n,i)=>n!==orders[i]))throw Error('Eye source identity');
}
const eyeControls={left:0,right:0};
const gazeEnvelopes={left:false,right:false};
if(proposal.painter_schedule.length!==62||proposal.proposed_passes.length!==25)throw Error('M2A contract');
for(const layer of contract.layers){
  const im=await rgbaPNG('/'+layer.raw_source_texture.file,layer.raw_source_texture.sha256);
  if(im.w!==layer.bounds[2]-layer.bounds[0]||im.h!==layer.bounds[3]-layer.bounds[1])throw Error('Source bounds');
  raw.set(layer.order,{...im,layer});
}
const alphaAt=(n,x,y)=>{const r=raw.get(n),[l,t]=r.layer.bounds,xx=x-l,yy=y-t;return xx>=0&&xx<r.w&&yy>=0&&yy<r.h?r.data[(yy*r.w+xx)*4+3]:0;};
const shadow=new Map(proposal.default_shadow_clips.map(c=>[c.shadow_order,c.base_order]));
const nativeClip=new Map(Object.values(eyePolicy.eyes).flatMap(e=>[[e.pupil_order,e.white_order],[e.highlight_order,e.white_order]]));
const eyeSideByBase=new Map(Object.entries(eyePolicy.eyes).map(([side,e])=>[e.white_order,side]));
function eyePaintAlpha(base,x,y){
  let domain=0;const radius=gazeEnvelopes[eyeSideByBase.get(base)]?eyePolicy.coupled_gaze_horizontal_radius:0;
  for(let d=-radius;d<=radius;d++)domain=Math.max(domain,alphaAt(base,x+d,y),alphaAt(base+1,x+d,y),alphaAt(base+2,x+d,y));
  return domain;
}
const clipAudits=[];

THREE.ColorManagement.enabled=false;
const renderer=new THREE.WebGLRenderer({canvas:document.getElementById('stage'),antialias:false,alpha:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setSize(N,N,false);renderer.toneMapping=THREE.NoToneMapping;renderer.outputColorSpace=THREE.LinearSRGBColorSpace;
const scene=new THREE.Scene(),camera=new THREE.OrthographicCamera(-1,1,1,-1,.1,20);
camera.position.set(0,0,5);camera.lookAt(0,0,0);camera.updateMatrixWorld(true);
const geoBySurface=new Map();
function axis(a,b){const v=[];for(let n=a;n<b;n+=12)v.push(n);v.push(b);return v;}
for(const group of proposal.surface_groups){
  const ls=group.members.map(n=>raw.get(n).layer.bounds);
  const box=[Math.min(...ls.map(b=>b[0])),Math.min(...ls.map(b=>b[1])),Math.max(...ls.map(b=>b[2])),Math.max(...ls.map(b=>b[3]))];
  const xs=axis(box[0],box[2]),ys=axis(box[1],box[3]),pos=[],source=[],idx=[];
  for(const sy of ys)for(const sx of xs){const X=(sx-C)/C,Y=(C-sy)/C,d=cfg.depth;
    const z=d.a1*Math.exp(-((X/d.sx1)**2)-(((Y+d.yoffset1)/d.sy1)**2))+d.a2*Math.exp(-((X/d.sx2)**2)-(((Y+d.yoffset2)/d.sy2)**2));
    pos.push(X,Y,z);source.push(sx,sy);}
  for(let y=0;y<ys.length-1;y++)for(let x=0;x<xs.length-1;x++){const a=y*xs.length+x,b=a+1,c=a+xs.length,d=c+1;idx.push(a,c,b,b,c,d);}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('sourceXY',new THREE.Float32BufferAttribute(source,2));g.setIndex(idx);
  geoBySurface.set(group.surface_order,g);
}
const VERT=`precision highp float;uniform mat4 projectionMatrix;uniform mat4 modelViewMatrix;attribute vec3 position;attribute vec2 sourceXY;varying vec2 vSource;void main(){vSource=sourceXY;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`;
const FRAG=`precision highp float;uniform sampler2D uMap;uniform vec4 uRect;uniform float uMode;uniform vec3 uId;varying vec2 vSource;void main(){vec2 uv=(vSource-uRect.xy)/uRect.zw;if(uv.x<0.0||uv.y<0.0||uv.x>=1.0||uv.y>=1.0)discard;vec4 t=texture2D(uMap,uv);if(t.a<=0.0)discard;gl_FragColor=vec4((uMode>0.5?uId:t.rgb)*t.a,t.a);}`;
for(const op of proposal.painter_schedule){
  const r=raw.get(op.psd_order),t=new THREE.DataTexture(new Float32Array(r.w*r.h*4),r.w,r.h,THREE.RGBAFormat,THREE.FloatType);
  t.colorSpace=THREE.NoColorSpace;t.minFilter=t.magFilter=THREE.NearestFilter;t.generateMipmaps=false;t.flipY=false;
  const n=op.psd_order,m=new THREE.RawShaderMaterial({vertexShader:VERT,fragmentShader:FRAG,
    uniforms:{uMap:{value:t},uRect:{value:new THREE.Vector4(r.layer.bounds[0],r.layer.bounds[1],r.w,r.h)},uMode:{value:0},uId:{value:new THREE.Vector3(((n*67)%251+1)/255,((n*137)%251+1)/255,((n*193)%251+1)/255)}},
    transparent:true,depthTest:false,depthWrite:false,blending:THREE.NormalBlending,premultipliedAlpha:true,side:THREE.DoubleSide,forceSinglePass:true});
  const mesh=new THREE.Mesh(geoBySurface.get(op.ultimate_surface_order),m);mesh.renderOrder=n;mesh.frustumCulled=false;
  scene.add(mesh);meshes.push(mesh);textures.set(n,t);materials.set(n,m);
}

let cacheKey=null,maskPolicy='source_paint_domain';
function rebuild(version){
  const key=maskPolicy+version+JSON.stringify([...shifts])+JSON.stringify(gazeEnvelopes);if(key===cacheKey)return;
  const dest=new Float64Array(N*N*4);clipAudits.length=0;
  for(const op of proposal.painter_schedule){
    const n=op.psd_order,r=raw.get(n),[dx,dy]=shifts.get(n)||[0,0],left=r.layer.bounds[0]+dx,top=r.layer.bounds[1]+dy;
    const data=textures.get(n).image.data;let changedNative=0;
    for(let y=0;y<r.h;y++)for(let x=0;x<r.w;x++){
      const j=(y*r.w+x)*4,X=left+x,Y=top+y;let au=r.data[j+3];
      if(version==='clean'&&shadow.has(n))au=Math.round(au*alphaAt(shadow.get(n),X,Y)/255);
      if(nativeClip.has(n)){
        const base=nativeClip.get(n),white=alphaAt(base,X,Y);
        // The PSD iris intentionally extends beyond its raw eye-white PNG.
        // Preserve the original painted domain; native GPU clip parity remains
        // explicitly BLOCKED, not redefined as a proven anatomical eye mask.
        const domain=eyePaintAlpha(base,X,Y);
        const next=maskPolicy==='eye_white_only'?Math.round(au*white/255):Math.min(au,domain);
        if(next!==au)changedNative++;au=next;
      }
      if(X<0||X>=N||Y<0||Y>=N)au=0;
      const A=au/255,i=(Y*N+X)*4,Ab=au?dest[i+3]:0;
      for(let c=0;c<3;c++){
        let effective=r.data[j+c]/255;
        if(op.is_source_multiply&&au)effective*=1-Ab+dest[i+c];
        effective=Math.round(Math.min(1,Math.max(0,effective))*255)/255;
        data[j+c]=effective;if(au)dest[i+c]=A*effective+(1-A)*dest[i+c];
      }
      data[j+3]=A;if(au)dest[i+3]=A+(1-A)*Ab;
    }
    if(nativeClip.has(n))clipAudits.push({order:n,base:nativeClip.get(n),changed_alpha_pixels:changedNative});
    materials.get(n).uniforms.uRect.value.set(left,top,r.w,r.h);textures.get(n).needsUpdate=true;
  }
  cacheKey=key;
}

const rt=new THREE.WebGLRenderTarget(N,N,{depthBuffer:false,stencilBuffer:false});
const alphaTex=new THREE.DataTexture(new Uint8Array(N*N*4),N,N,THREE.RGBAFormat,THREE.UnsignedByteType);
alphaTex.colorSpace=THREE.NoColorSpace;alphaTex.minFilter=alphaTex.magFilter=THREE.NearestFilter;alphaTex.generateMipmaps=false;
const alphaScene=new THREE.Scene(),alphaMat=new THREE.RawShaderMaterial({
  vertexShader:`precision highp float;uniform mat4 projectionMatrix;uniform mat4 modelViewMatrix;attribute vec3 position;attribute vec2 uv;varying vec2 v;void main(){v=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
  fragmentShader:`precision highp float;uniform sampler2D tex;varying vec2 v;void main(){gl_FragColor=texture2D(tex,v);}`,uniforms:{tex:{value:alphaTex}},depthTest:false,depthWrite:false});
alphaScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),alphaMat));
const metadata={schema:'core026-live-compositor/1',source_count:62,receiver_count:19,logical_pass_count:25,gpu_source_draws:62,
  source_color_inputs:contract.layers.map(l=>({order:l.order,file:l.raw_source_texture.file,sha256:l.raw_source_texture.sha256})),
  painter_schedule:proposal.painter_schedule,logical_passes:proposal.proposed_passes,
  blend_implementation:'live original Normal/Multiply against preceding transparent artwork, quantized effective source RGB, then per-source GPU Normal draws',
  geometry:'19 shared receiver grids; unchanged unfitted CORE025 height profile, no per-layer Z offset',
  depth_tested:false,local_eye_uv:'live source-pixel offset with provisional source-painted eye support cap',
  default_mask_policy:'source_paint_domain',native_clip_parity:'BLOCKED_RAW_EYE_WHITE_MASK_FAILS_SOURCE_ART_PARITY',
  eye_policy:eyePolicy,eye_control_scope:'DISCRETE_HORIZONTAL_DEFAULT_POSE_ONLY; artist override, not native clip equivalence',
  mask_note:'Rest/manual use fixed source-paint alpha; coupled gaze activates its fixed horizontal 8px alpha-derived envelope. Artist override, not native GPU ClipToLower equivalence.',
  physical_depth:'NOT_RECOVERED',dynamic_occlusion:'NOT_IMPLEMENTED',natural_3d_turn:'NOT_ACCEPTED',supported_pose:'DEFAULT_ONLY',
  camera:cfg.camera,canvas:[N,N]};
function render(p={}){
  const {version='source',background='white',pass='beauty',size=N}=p;
  if((p.yaw_deg??0)!==0||(p.raw_yaw??0)!==0)throw Error('Nonzero yaw not accepted in M2B0');
  if(!['source','clean'].includes(version)||!['white','black'].includes(background)||!['beauty','alpha','part_id'].includes(pass)||size!==N)throw Error('Unsupported render parameters');
  rebuild(version);for(const m of materials.values())m.uniforms.uMode.value=pass==='part_id'?1:0;
  renderer.setRenderTarget(null);let artworkDraws=0;
  if(pass==='alpha'){
    renderer.setRenderTarget(rt);renderer.setClearColor(0,0);renderer.clear();renderer.render(scene,camera);artworkDraws=renderer.info.render.calls;
    const data=new Uint8Array(N*N*4);renderer.readRenderTargetPixels(rt,0,0,N,N,data);
    const target=alphaTex.image.data;for(let i=0;i<data.length;i+=4){target[i]=target[i+1]=target[i+2]=data[i+3];target[i+3]=255;}
    alphaTex.needsUpdate=true;renderer.setRenderTarget(null);renderer.setClearColor(0,1);renderer.clear();renderer.render(alphaScene,camera);
  }else{renderer.setClearColor(background==='white'?0xffffff:0,1);renderer.clear();renderer.render(scene,camera);artworkDraws=renderer.info.render.calls;}
  return {version,background,pass,size,camera_matrix:Array.from(camera.matrixWorld.elements),projection_matrix:Array.from(camera.projectionMatrix.elements),
    source_count:62,receiver_count:19,logical_pass_count:25,draw_count:renderer.info.render.calls,artwork_draw_count:artworkDraws,uv_offsets:[...shifts],native_clip_alpha_changes:clipAudits.map(x=>({...x})),
    mask_policy:maskPolicy,eye_controls:{...eyeControls},gaze_envelopes:{...gazeEnvelopes},native_clip_parity:'BLOCKED',physical_depth:'NOT_RECOVERED',dynamic_occlusion:'NOT_IMPLEMENTED'};
}
function applyOffset(order,xy){
  if(xy[0]===0&&xy[1]===0)shifts.delete(order);else shifts.set(order,[...xy]);cacheKey=null;}
function setLayerUvOffset(order,xy){if(!raw.has(order)||!Array.isArray(xy)||xy.length!==2||!xy.every(Number.isInteger))throw Error('Expected layer and integer source-pixel offset');
  for(const [side,e] of Object.entries(eyePolicy.eyes))if(order===e.pupil_order||order===e.highlight_order)eyeControls[side]='manual_layer_offsets';
  applyOffset(order,xy);
}
function setEyeGaze(eye,dx){
  if(!['left','right','both'].includes(eye)||!Number.isInteger(dx)||dx< -8||dx>8)throw Error('Expected left/right/both and integer horizontal source offset -8..8');
  for(const side of eye==='both'?['left','right']:[eye]){
    const e=eyePolicy.eyes[side];applyOffset(e.pupil_order,[dx,0]);applyOffset(e.highlight_order,[dx,0]);eyeControls[side]=dx;gazeEnvelopes[side]=dx!==0;
  }
}
window.core026={render,metadata,setLayerUvOffset,setEyeGaze,setEyeMaskPolicy(value){
  if(!['source_paint_domain','eye_white_only'].includes(value))throw Error('Unknown mask policy');maskPolicy=value;cacheKey=null;
},reset(){shifts.clear();eyeControls.left=eyeControls.right=0;gazeEnvelopes.left=gazeEnvelopes.right=false;maskPolicy='source_paint_domain';cacheKey=null;}};
render();window.core026Ready=true;
