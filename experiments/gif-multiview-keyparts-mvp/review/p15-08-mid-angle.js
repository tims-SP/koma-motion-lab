"use strict";
(() => {
  const base="../private-assets/";
  const refs={
    "img45":"p2-views/whole/yaw045.png",
    "img65":"p15-independent-candidates/yaw065-source-rgba.png",
    "img90":"p2-views/whole/yaw090.png"
  };
  const states={
    "imgv1":{
      alpha:"p15-08-yaw055/yaw055-rgba-v1.png",
      source:"p15-08-yaw055/yaw055-qwen2511-v1.png"
    },
    "imgv2":{
      alpha:"p15-08-yaw055/yaw055-rgba-v2.png",
      source:"p15-08-yaw055/yaw055-qwen2511-v2.png"
    }
  };
  const errors=[];
  async function render(){
    const isAlpha=document.getElementById("alpha").checked;
    const lookups={...refs};
    for(const [key,value] of Object.entries(states))lookups[key]=isAlpha?value.alpha:value.source;
    const images=Object.entries(lookups);
    const jobs=images.map(async ([key,src])=>{
      const el=document.getElementById(key);
      el.src=base+src;
      await el.decode();
      if(!el.naturalWidth||!el.naturalHeight)throw Error("image has no decoded pixels: "+src);
      return {key,path:src,width:el.naturalWidth,height:el.naturalHeight};
    });
    const results=await Promise.allSettled(jobs);
    errors.length=0;
    const loaded=[];
    for(const x of results){
      if(x.status==="fulfilled")loaded.push(x.value);
      else errors.push(String(x.reason));
    }
    window.__KOMA_P15_08={ready:errors.length===0&&loaded.length===5,
      alpha:isAlpha,loaded,errors:[...errors]};
    return window.__KOMA_P15_08;
  }
  document.getElementById("alpha").addEventListener("change",()=>{void render()});
  void render();
})();
