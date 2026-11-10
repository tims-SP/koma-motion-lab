"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const angles = [55, 57.5, 60, 62.5, 65];
  const frameName = n => "yaw" + (Number.isInteger(n) ? n : String(n).replace(".", "p"));
  let changeId = 0;
  const status = {angle:60, part:"eye.far", ready:false, sources:[], errors:[]};

  function snapshot() {
    return {angle:status.angle,part:status.part,ready:status.ready,
      sources:status.sources.map(x=>({...x})),errors:[...status.errors]};
  }
  async function setView(angle, part) {
    angle = Number(angle);
    if (!angles.includes(angle)) throw Error("P15-10 angle must match 2.5-degree grid");
    if (!Array.from($("part").options).some(x => x.value === part)) {
      throw Error("Unrecognized P0 semantic role");
    }
    const requestId = ++changeId;
    $("yaw").value = String(angle);
    $("part").value = part;
    $("yaw-label").textContent = angle + "°";
    $("part-name").textContent = part;
    status.angle = angle; status.part = part;
    status.ready = false; status.sources = []; status.errors = [];
    const f = frameName(angle);
    const urls = {
      baseline: "../private-assets/p15-07-wholekey-preview/" + f + ".png",
      anchor: "../private-assets/p15-09-midarc/" + f + ".png",
      semantic: "../private-assets/p15-10-semantic-pose/arc/" + f + ".png",
      layer: "../private-assets/p15-10-semantic-pose/arc/" + f + "/parts/" + part + ".png"
    };
    const results = await Promise.allSettled(Object.entries(urls).map(async ([id, src]) => {
      const target = $(id);
      target.src = src;
      await target.decode();
      if (!target.naturalWidth || !target.naturalHeight) throw Error("Missing image: " + src);
      return {id,src,width:target.naturalWidth,height:target.naturalHeight};
    }));
    if (requestId !== changeId) return snapshot();
    for (const r of results) {
      if (r.status === "fulfilled") status.sources.push(r.value);
      else status.errors.push(String(r.reason));
    }
    status.ready = status.sources.length === 4 && status.errors.length === 0;
    return snapshot();
  }
  $("prev").addEventListener("click",()=>void setView(Math.max(55,status.angle-2.5),status.part));
  $("next").addEventListener("click",()=>void setView(Math.min(65,status.angle+2.5),status.part));
  $("yaw").addEventListener("input",()=>void setView(Number($("yaw").value),status.part));
  $("part").addEventListener("change",()=>void setView(status.angle,$("part").value));
  window.__KOMA_P15_10={setView,snapshot,angles};
  void setView(60,"eye.far");
})();
