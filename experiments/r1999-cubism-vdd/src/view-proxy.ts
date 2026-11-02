/** Runtime semantic depth estimates for a Cubism front-view diagnostic proxy. */
export interface ProxyLayer { depth:number; influence:number; semantic:string; }
const MAP:ReadonlyArray<readonly [RegExp,ProxyLayer]>=[
 [/HAIR_FRONT/i,{depth:0.30,influence:1,semantic:'hair.front'}],
 [/HAIR_SIDE/i,{depth:0.18,influence:1,semantic:'hair.side'}],
 [/HAIR_BACK|Hair_B_/i,{depth:-0.30,influence:1,semantic:'hair.back'}],
 [/Hair_M_/i,{depth:0.09,influence:1,semantic:'hair.middle'}],
 [/EYE|BROW/i,{depth:0.2,influence:1,semantic:'eyes'}],
 [/NOSE/i,{depth:0.26,influence:1,semantic:'nose'}],
 [/MOUTH/i,{depth:0.14,influence:1,semantic:'mouth'}],
 [/EAR/i,{depth:-0.05,influence:1,semantic:'ears'}],
 [/FACE/i,{depth:0,influence:1,semantic:'face'}],
 [/NECK/i,{depth:-0.10,influence:0.15,semantic:'neck'}]
];
export function proxyLayerForPart(partId:string,drawableId=''):ProxyLayer {
 // Cubism root drawables have parentPartIndex -1; current model has face artwork.
 const key=partId==='__UNPARENTED_DRAWABLES__'?drawableId:partId;
 for(const [test,layer] of MAP)if(test.test(key))return layer;
 return {depth:0,influence:0,semantic:'body'};
}
export function runtimeFacePivot(model:any):readonly [number,number]{
 let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
 for(let i=0;i<model.getDrawableCount();i++){
  const parent=model.getDrawableParentPartIndex(i);
  const id=parent<0?'__UNPARENTED_DRAWABLES__':model.getPartId(parent).getString().s;
  const drawableId=model.getDrawableId(i).getString().s;
  if(proxyLayerForPart(id,drawableId).semantic!=='face')continue;
  const vertices=model.getDrawableVertexPositions(i);
  for(let j=0;j<vertices.length;j+=2){
   const x=vertices[j],y=vertices[j+1];if(!Number.isFinite(x)||!Number.isFinite(y))continue;
   minX=Math.min(minX,x);maxX=Math.max(maxX,x);
   minY=Math.min(minY,y);maxY=Math.max(maxY,y);
  }
 }
 if(!Number.isFinite(minX))throw Error('No face drawable positions for proxy pivot');
 return [(minX+maxX)/2,(minY+maxY)/2];
}
export function createProxyControls(getYaw:()=>number,setYaw:(angle:number)=>void):void{
 const panel=document.createElement('aside');
 panel.id='r1999-view-proxy';
 panel.setAttribute('aria-label','View-proxy diagnostic controls');
 panel.innerHTML=`<div class="r1999-proxy-title">3D Anchor · View Proxy</div>
 <label for="r1999-yaw">相机水平角度 <strong id="r1999-yaw-value">0°</strong></label>
 <input id="r1999-yaw" type="range" min="0" max="90" step="5" value="0">
 <p id="r1999-view-provenance">0° · Cubism 原画</p>
 <p class="r1999-explanation">几何重投影诊断。独立 45° / 90° 原画待登记；此画面不作为侧脸质量真值。</p>`;
 const css=document.createElement('style');
 css.textContent=`#r1999-view-proxy{position:fixed;z-index:31;left:405px;top:705px;width:400px;
 border:1px solid #425265;border-radius:12px;background:#111925;color:#edf2fa;
 box-sizing:border-box;padding:12px;font:13px/1.45 system-ui}
 #r1999-view-proxy .r1999-proxy-title{font-weight:700;margin-bottom:8px}
 #r1999-view-proxy input{display:block;width:100%;margin:9px 0}
 #r1999-view-proxy strong{float:right}
 #r1999-view-proxy p{margin:5px 0}
 #r1999-view-proxy .r1999-explanation{font-size:11px;color:#aebbd0}
 @media(max-width:750px){#r1999-view-proxy{left:8px;top:6px;width:calc(100vw - 16px)}}`;
 document.head.appendChild(css);document.body.appendChild(panel);
 const slider=panel.querySelector<HTMLInputElement>('#r1999-yaw')!;
 const label=panel.querySelector<HTMLElement>('#r1999-yaw-value')!;
 const provenance=panel.querySelector<HTMLElement>('#r1999-view-provenance')!;
 const sync=()=>{
  label.textContent=`${getYaw()}°`;
  provenance.textContent=getYaw()===0?'0° · Cubism 原画基线':
    `${getYaw()}° · 估算几何代理 / 独立原画待补`;
 };
 slider.addEventListener('input',()=>{setYaw(Number(slider.value));sync()});
 sync();
}
