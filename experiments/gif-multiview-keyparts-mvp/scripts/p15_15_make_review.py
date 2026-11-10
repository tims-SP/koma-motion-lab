#!/usr/bin/env python3
"""Offline PSD-derived ArtMesh diagnostic, preserves source and not an art signoff."""
import json,hashlib,shutil,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent.parent
P=R/"private-assets"
d=json.loads((R/"evidence/p15-15-role-routing-qa.json").read_text())
out=P/"exports/p15-15-artmesh-review"
(out/"images").mkdir(parents=True,exist_ok=True)
views=[]
for view in d["views"]:
 rows=[]
 for role in view["roles"]:
  src=P/role["path"]
  dst=out/"images"/view["yaw"]/(role["role"]+".png")
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  rows.append({"role":role["role"],"src":str(dst.relative_to(out)),
               "pixels":role["visiblePixels"],"missing":role["missingIndependentArt"]})
 views.append({"name":view["yaw"],"layers":rows,"missing":view["missingOrNonIndependentRoles"]})
template='''<!DOCTYPE html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>P15-15 PSD 分层审查</title><style>
body{margin:0;background:#151922;color:#e9edf3;font:15px system-ui;padding:18px}
main{max-width:1150px;margin:auto}h1{font-size:25px}p{color:#bac2cf}.cols{display:grid;grid-template-columns:minmax(0,768px) 310px;gap:20px}
#stage{width:100%;aspect-ratio:1;position:relative;background:repeating-conic-gradient(#424954 0 25%,#20252d 0 50%) 50%/24px 24px}
#stage img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
aside{max-height:78vh;overflow:auto}label{display:block;padding:7px;border-bottom:1px solid #36404e}
select{padding:8px;background:#263240;color:white;border:1px solid #526070}
.bad{color:#f4bc80}@media(max-width:750px){.cols{grid-template-columns:1fr}aside{max-height:360px}}
</style><main><h1>P15-15 · PSD ArtMesh 角色路由</h1>
<p>逐层开关显示原生 PSD 派生角色。当前是几何拆分参考，未通过独立原画、原生隐藏补绘或连续转头签收。</p>
<label>PSD 角度：<select id="view"></select></label><div class="cols"><div id="stage"></div><aside id="layers"></aside></div>
<p id="missing" class="bad"></p></main><script>
const views=__DATA__;const pick=document.querySelector('#view'),stage=document.querySelector('#stage'),list=document.querySelector('#layers');
for(let i=0;i<views.length;i++){let option=document.createElement('option');option.value=i;option.textContent=views[i].name;pick.appendChild(option);}
function display(){let v=views[Number(pick.value)];stage.replaceChildren();list.replaceChildren();
for(let role of v.layers){let pic=document.createElement('img');pic.src=role.src;pic.alt=role.role;stage.appendChild(pic);
let row=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=true;
check.onchange=()=>pic.hidden=!check.checked;let span=document.createElement('span');
span.textContent=' '+role.role+' · '+role.pixels+' px'+(role.missing?' · 独立原画缺失':'');
row.append(check,span);list.appendChild(row);}
document.querySelector('#missing').textContent='未验收独立部件：'+v.missing.join('、');}
pick.onchange=display;display();
</script></html>'''
# hidden attribute on position: absolute images can be overridden; use display inline style.
template=template.replace("pic.hidden=!check.checked","pic.style.display=check.checked?'block':'none'")
(out/"index.html").write_text(template.replace("__DATA__",json.dumps(views,ensure_ascii=False)))
shutil.copy2(R/"evidence/p15-15-role-routing-qa.json",out/"audit.json")
bundle=P/"exports/p15-15-artmesh-review.zip"
with zipfile.ZipFile(bundle,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(out.rglob("*")):
  if f.is_file():z.write(f,f.relative_to(out))
with zipfile.ZipFile(bundle) as z:
 assert z.testzip() is None
 print(json.dumps({"zipBytes":bundle.stat().st_size,"entries":len(z.namelist()),
 "sha256":hashlib.sha256(bundle.read_bytes()).hexdigest()}))
