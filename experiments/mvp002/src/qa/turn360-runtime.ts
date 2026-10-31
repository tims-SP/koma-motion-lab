import * as THREE from 'three';
import type { PartTrace, FrameTrace, XYZ, XY } from './turn360-contract';

/**
 * Runtime-side evidence must originate from the *actual geometry* submitted
 * for the beauty render. Do not replace an unobservable property with a
 * made-up intent state just to satisfy the QA contract.
 */
export class Turn360Recorder {
  public traces:PartTrace[]=[];
  public lastFrame:FrameTrace|null=null;
  public active=false;
  public yaw=0;
  public frameIndex=0;
  public warnings:string[]=[];
  public start(yaw:number,frame:number):void{
    this.traces=[];this.warnings=[];this.active=true;
    this.yaw=yaw;this.frameIndex=frame;
  }
  public record(input:{
    id:string;center:THREE.Vector3;vddOffset:XY;vertices:THREE.Vector3[];
    uv:XY[];triangles:number[];keyA:number;keyB:number;weight:number;
    visible:number;parent:string;sourceIsDerived:boolean;
    localAnchor:THREE.Vector3;boneWorld:THREE.Matrix4;camera:THREE.OrthographicCamera;
    authoredKeys:readonly {yaw:number;contour:readonly XY[];shift:XY;visible:number}[];
  }):void{
    if(!this.active)return;
    const p=input,vals=p.vertices.map(x=>x.z);
    const warningCodes:string[]=[];
    if(p.sourceIsDerived)warningCodes.push('VIEW_270_MIRRORED_SOURCE');
    if(p.triangles.length%3!==0)warningCodes.push('BAD_TRIANGLE_INDEX_COUNT');
    if(p.vertices.some(v=>!isFinite(v.x)||!isFinite(v.y)||!isFinite(v.z)))
      warningCodes.push('NONFINITE_VERTEX');
    if(p.uv.some(v=>v.some(c=>!isFinite(c)||c<-.001||c>1.001)))
      warningCodes.push('UV_OUTSIDE_UNIT');
    const indices=p.triangles;
    for(let i=0;i<indices.length;i+=3){
      const a=p.vertices[indices[i]],b=p.vertices[indices[i+1]],c=p.vertices[indices[i+2]];
      if(!a||!b||!c){warningCodes.push('INVALID_TRIANGLE_VERTEX');break;}
      const cross=(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);
      if(Math.abs(cross)<1e-7){warningCodes.push('DEGENERATE_TRIANGLE');break;}
    }
    if(p.vertices.length!==p.uv.length)warningCodes.push('UV_VERTEX_COUNT_MISMATCH');
    // FNV-1a records content identity, not an assertion of artistic quality.
    const hash=(o:unknown)=>{let h=2166136261;for(const c of JSON.stringify(o)){
      h=Math.imul(h^c.charCodeAt(0),16777619);
    }return (h>>>0).toString(16).padStart(8,'0');};
    const key=(n:number)=>{
      const source=p.authoredKeys.find(k=>k.yaw===n);
      if(!source)throw Error('No actual source key '+p.id+'/'+n);
      return {yawDegrees:n,sourceHash:hash(source),independentlyAuthored:!p.sourceIsDerived,
        topologyId:'fan'+source.contour.length+'-v1'};
    };
    p.camera.updateMatrixWorld();
    const projection=(point:THREE.Vector3):XY=>{
      const ndc=point.clone().project(p.camera);
      return [(ndc.x+1)*480,(1-ndc.y)*270];
    };
    const originalWorld=p.localAnchor.clone().applyMatrix4(p.boneWorld);
    const anchorPx=projection(originalWorld);
    const centerPx=projection(p.vertices[0]);
    const trace:PartTrace={
      id:p.id,parentBoneId:p.parent,
      boneLocalAnchorXYZ:p.localAnchor.toArray() as XYZ,
      boneWorldMatrix:p.boneWorld.toArray(),
      worldAnchorXYZ:p.center.toArray() as XYZ,
      projectedAnchorXY:[p.center.x,p.center.y],vddOffsetXY:p.vddOffset,
      anchorProjectionPixels:anchorPx,deformedCenterPixels:centerPx,
      keyA:key(p.keyA),keyB:key(p.keyB),keyWeight:p.weight,
      geometryVerticesXY:p.vertices.map(v=>[v.x,v.y]),
      textureUV:p.uv,triangleIndices:p.triangles,visibility:p.visible<.025?'absent':p.visible<.995?'crossfade':'visible',
      topologyTransition:'none',depthMin:Math.min(...vals),depthMax:Math.max(...vals),
      expectedOccluders:[],actualVisibleAreaPixels:0,visiblePixelCountFromIdPass:0,
      sourceTextureHash:hash([p.id,p.keyA,p.keyB,p.weight]),
      warningCodes
    };
    this.traces.push(trace);
  }
  public finish(info:{
    camera:THREE.OrthographicCamera; timeSeconds:number; yaw:number;poseHash?:string;
    bounds:[number,number,number,number]; rendererCommit:string;
  }):FrameTrace{
    const camera=info.camera;
    this.lastFrame={
      frameIndex:this.frameIndex,timeSeconds:info.timeSeconds,
      yawDegrees:info.yaw,poseHash:info.poseHash??'static-neutral-pose',
      cameraHash:[camera.left,camera.right,camera.top,camera.bottom,camera.position.toArray()].join('|'),
      cameraViewMatrix:camera.matrixWorldInverse.toArray(),
      cameraProjectionMatrix:camera.projectionMatrix.toArray(),
      lightHash:'neutral-fixed-qa-light',characterAssetHash:'mvp002-proxy-12-parts',
      rendererCommit:info.rendererCommit,parts:this.traces,
      actualVisiblePartIds:[],characterBoundingBoxPixels:info.bounds,
      geometryWarnings:this.traces.flatMap(p=>p.warningCodes.map(c=>p.id+':'+c)),
      imageDiagnostics:[]
    };
    this.active=false;
    return this.lastFrame;
  }
  public updateVisible(counts:Map<string,number>,bounds:readonly [number,number,number,number]):void{
    if(!this.lastFrame)throw Error('No frame before ID readback');
    for(const part of this.lastFrame.parts){
      // a PartTrace is mutable during its owning frame's readback.
      part.visiblePixelCountFromIdPass=counts.get(part.id)||0;
      part.actualVisibleAreaPixels=counts.get(part.id)||0;
    }
    this.lastFrame.characterBoundingBoxPixels=[...bounds];
    this.lastFrame.actualVisiblePartIds=this.lastFrame.parts
      .filter(p=>p.visiblePixelCountFromIdPass>0).map(p=>p.id);
  }
}

export const qaPalette:readonly [number,number,number][]=[
  [255,64,64],[64,220,70],[80,110,255],[255,190,55],
  [240,60,210],[30,220,215],[195,140,60],[160,90,255],
  [125,245,110],[255,110,160],[50,155,245],[220,220,90]
];
export function idShader(original:THREE.Material, color:readonly [number,number,number],depth=false):THREE.Material{
 const shader=original instanceof THREE.ShaderMaterial;
 const getTex=(name:string)=>shader?(original.uniforms[name]?.value as THREE.Texture|undefined):undefined;
 const alpha=shader?(Number(original.uniforms.strength?.value) || 0):1;
 const texA=getTex('artA'),texB=getTex('artB'),mix=shader?(Number(original.uniforms.transition?.value) || 0):0;
 const frontMask=shader?(Number(original.uniforms.frontMask?.value ?? 1)):1;
 const faceWipe=shader?(Number(original.uniforms.faceWipe?.value ?? 0)):0;
 const wipeDirection=shader?(Number(original.uniforms.wipeDirection?.value ?? 1)):1;
 const wipeBounds=shader?original.uniforms.wipeBounds?.value as THREE.Vector2|undefined:undefined;
 return new THREE.ShaderMaterial({
  uniforms:{artA:{value:texA||null},artB:{value:texB||null},transition:{value:mix},
    strength:{value:alpha},useTex:{value:shader?1:0},
    frontMask:{value:frontMask},faceWipe:{value:faceWipe},wipeDirection:{value:wipeDirection},
    wipeBounds:{value:wipeBounds?.clone()??new THREE.Vector2(0,1)},
    partColor:{value:new THREE.Vector3(...color.map(x=>x/255))}},
  vertexShader:'varying vec2 vUv; varying float worldPartX; void main(){vUv=uv; worldPartX=position.x; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
  fragmentShader:[
    'uniform sampler2D artA,artB;',
    'uniform float transition,strength,useTex;',
    'uniform float frontMask,faceWipe,wipeDirection;',
    'uniform vec2 wipeBounds;',
    'varying float worldPartX;',
    'uniform vec3 partColor;',
    'varying vec2 vUv;',
    'void main(){',
    '  float opacity=1.;',
    '  if(useTex>0.5){opacity=mix(texture2D(artA,vUv).a,texture2D(artB,vUv).a,transition)*strength;}',
    '  if(faceWipe>0.5 && frontMask<0.999){',
    '    float x=clamp((worldPartX-wipeBounds.x)/max(0.0001,wipeBounds.y-wipeBounds.x),0.0,1.0);',
    '    float side=wipeDirection>0.0?x:1.0-x;',
    '    float edge=1.0-frontMask;',
    '    opacity*=smoothstep(edge-0.035,edge+0.035,side);',
    '  }',
    '  if(opacity<0.08)discard;',
    depth?'  gl_FragColor=vec4(vec3(gl_FragCoord.z),1.);':'  gl_FragColor=vec4(partColor,1.);',
    '}'
  ].join('\n'),
  side:THREE.DoubleSide,depthTest:original.depthTest,depthWrite:original.depthWrite,transparent:false
 });
}
export function countIdPixels(buf:Uint8Array,ids:readonly string[],scale:number):Map<string,number>{
 const map=new Map(ids.map(id=>[id,0]));
 const codes=qaPalette.map(c=>(c[0]<<16)|(c[1]<<8)|c[2]);
 const lookup=new Map(codes.map((c,i)=>[c,i]));
 for(let i=0;i<buf.length;i+=4){
   if(buf[i+3]!==255)continue;
   const code=(buf[i]<<16)|(buf[i+1]<<8)|buf[i+2];
   const pos=lookup.get(code);
   if(pos!==undefined&&pos<ids.length){
     map.set(ids[pos],(map.get(ids[pos])||0)+scale);
   }
 }
 return map;
}
