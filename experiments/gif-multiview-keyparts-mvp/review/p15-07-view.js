"use strict";
(() => {
  const q = id => document.getElementById(id);
  const range = q("angle");
  const note = q("reference-note");
  const ids = ["p8","semantic","whole","reference"];
  const views = Object.fromEntries(ids.map(id => [id,q("view-"+id)]));
  const metas = Object.fromEntries(ids.map(id => [id,q("meta-"+id)]));
  const sourceRoot = "../private-assets/";
  const holdouts = Object.freeze({
    "65": {path:"p15-independent-candidates/yaw065-source-rgba.png",
           role:"P15 关键原画候选 · 已用于新渲染输入"},
    "77p5":{path:"p15-independent-candidates/yaw077p5-source-rgba.png",
           role:"P15 关键原画候选 · 已用于新渲染输入"},
    "67p5":{path:"p14-authored-candidates/yaw067p5-artmesh/yaw067p5-painted-semantic-composite.png",
           role:"P14 绘制候选 · 可用于 P15 留出角比较"},
    "72p5":{path:"p14-authored-candidates/yaw072p5-artmesh/yaw072p5-p0-source-mapped-artmesh.png",
           role:"P14 绘制候选 · 可用于 P15 留出角比较"}
  });
  const status = {angle:67.5,ready:false,loaded:[],errors:[],referenceRole:null};
  const token = {value:0};
  function key(yaw) {
    return Number.isInteger(yaw) ? String(yaw) : String(yaw).replace(".","p");
  }
  function load(id,path,displayLabel) {
    const image=views[id];
    image.hidden = !path;
    image.style.display = path ? "block" : "none";
    metas[id].textContent=displayLabel||"无单独参考帧";
    if(!path){image.removeAttribute("src");return Promise.resolve(null)}
    image.src = sourceRoot+path;
    return image.decode().then(() => {
      if(!image.naturalWidth || !image.naturalHeight)throw new Error("Invalid image: "+path);
      return {id,path,width:image.naturalWidth,height:image.naturalHeight};
    });
  }
  async function choose(angle) {
    const v=Number(angle);
    if(!(v>=0 && v<=90) || Math.round(v*2.0)!==v*2.0)throw new Error("2.5 degree source-grid only");
    const request=++token.value;
    status.angle=v;status.ready=false;status.loaded=[];status.errors=[];
    const k=key(v);
    range.value=String(v);
    q("angle-value").textContent=v+"°";
    const ref=holdouts[k]||null;
    status.referenceRole=ref?.role||null;
    const loaders=[
      load("p8","p8-semantic-occlusion/selective-sequence/yaw"+k+".png",
           "已登记 P8 历史基线"),
      load("semantic","p15-07-semantic-preview/yaw"+k+".png",
           (v===45||v===65||v===77.5||v===90)?"原画关键帧精确读取":"13 个语义部件独立形变"),
      load("whole","p15-07-wholekey-preview/yaw"+k+".png",
           "整图光流与轮廓场诊断"),
      load("reference",ref?.path||null,ref?.role||"此角度没有独立绘制对照")
    ];
    const results=await Promise.allSettled(loaders);
    if(request!==token.value)return inspect();
    for(const result of results){
      if(result.status==="fulfilled" && result.value)status.loaded.push(result.value);
      if(result.status==="rejected")status.errors.push(String(result.reason));
    }
    status.ready=status.errors.length===0 && status.loaded.length===(ref?4:3);
    note.textContent=ref ? ref.role+"；图层输入和独立留出角的角色必须分别登记。"
                         : "当前角度只有程序插值，需结合独立绘制原画进行最终质量签收。";
    return inspect();
  }
  function inspect() {
    return {
      angle:status.angle,
      ready:status.ready,
      loaded:status.loaded.map(v=>({...v})),
      errors:[...status.errors],
      referenceRole:status.referenceRole
    };
  }
  q("previous").addEventListener("click",()=>void choose(Math.max(0,status.angle-2.5)));
  q("next").addEventListener("click",()=>void choose(Math.min(90,status.angle+2.5)));
  range.addEventListener("input",()=>void choose(Number(range.value)));
  window.__KOMA_P15_07={setAngle:choose,inspect};
  void choose(67.5);
})();
