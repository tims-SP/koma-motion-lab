"use strict";
(() => {
  const q=id=>document.getElementById(id);
  const slider=q("yaw");
  const source="../private-assets/";
  const status={angle:55,ready:false,images:[],errors:[]};
  let current=0;
  const key=ang=>Number.isInteger(ang)?String(ang):String(ang).replace(".","p");
  async function choose(yaw) {
    yaw=Number(yaw);
    if(yaw<45||yaw>65||!Number.isInteger(yaw*2/5))throw Error("P15-09 2.5° grid 45–65");
    const id=++current;
    slider.value=yaw;
    q("angle-value").textContent=yaw+"°";
    status.angle=yaw;status.ready=false;status.images=[];status.errors=[];
    const name="yaw"+key(yaw)+".png";
    const paths={
      p8:"p8-semantic-occlusion/selective-sequence/"+name,
      old:"p15-07-wholekey-preview/"+name,
      new:"p15-09-midarc/"+name
    };
    const entries=Object.entries(paths).map(async ([kind,path])=>{
      const image=q("frame-"+kind);
      image.src=source+path;
      await image.decode();
      if(!image.naturalWidth||!image.naturalHeight)throw Error("image not loaded: "+path);
      return {kind,path,width:image.naturalWidth,height:image.naturalHeight};
    });
    const r=await Promise.allSettled(entries);
    if(id!==current)return inspect();
    for(const entry of r) {
      if(entry.status==="fulfilled")status.images.push(entry.value);
      else status.errors.push(String(entry.reason));
    }
    status.ready=status.images.length===3&&!status.errors.length;
    q("pose-status").textContent=yaw<=55?"P5 锚点引导，双眼与发夹位置连续":"55°→65° 绘制侧脸形变参考";
    return inspect();
  }
  function inspect(){return {angle:status.angle,ready:status.ready,
    images:status.images.map(x=>({...x})),errors:[...status.errors]}}
  q("prev").addEventListener("click",()=>void choose(Math.max(45,status.angle-2.5)));
  q("next").addEventListener("click",()=>void choose(Math.min(65,status.angle+2.5)));
  slider.addEventListener("input",()=>void choose(Number(slider.value)));
  window.__KOMA_P15_09={choose,inspect};
  void choose(55);
})();
