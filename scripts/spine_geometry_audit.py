#!/usr/bin/env python3
"""Independent Spine runtime vs Python converter setup geometry and UV audit.

Never export original vertices/UVs or art: output numerical error statistics only.
"""
from __future__ import annotations
import json,math,sys,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import spine_textured_rive as src
from spine_atlas_uv import parse_atlas, convert_mesh_uvs

def main(source_path:Path,atlas_path:Path,official_path:Path):
    doc=json.loads(source_path.read_text())
    official=json.loads(official_path.read_text())
    atlas=parse_atlas(atlas_path.read_text())
    bones=doc["bones"]
    world=src.world_transform(bones)
    skins=doc["skins"]
    entries=skins[0].get("attachments",{}) if isinstance(skins,list) else skins.get("default",{})
    summary={"status":"NOT_TESTED",
             "source_bones":len(bones),"official_bones":official["bones"],
             "source_slots":len(doc["slots"]),"official_slots":official["slots"],
             "official_active_mesh_slots":len(official["mesh"]),
             "official_active_region_slots":len(official["regions"]),
             "official_active_other_slots":len(official["other"]),
             "converter_supported_mesh_slots":0,
             "mesh_world_position_max_abs_error":0.0,
             "mesh_uv_max_abs_error":0.0,
             "total_mesh_vertices":0,
             "total_mesh_vertex_coordinates":0,
             "total_mesh_uv_coordinates":0,
             "mesh_geometry_error_rms":0.0,
             "mesh_uv_error_rms":0.0,
             "unsupported_slots":[],
             "top_geometry_discrepancies":[],
             "max_influences_per_vertex":0,
             "vertices_over_four_influences":0}
    geom_sq=uv_sq=0.; top=[]
    for slot in doc["slots"]:
        sn=slot["name"]
        reference=official["mesh"].get(sn)
        if not reference:continue
        attached=slot.get("attachment")
        a=entries.get(sn,{}).get(attached) if attached else None
        if not isinstance(a,dict) or a.get("type","region")!="mesh":
            summary["unsupported_slots"].append({"slot":sn,"reason":"linked/alternative/unavailable mesh"})
            continue
        local=src.parse_attachment(a,bones,world,slot["bone"])
        if not local:
            summary["unsupported_slots"].append({"slot":sn,"reason":"unsupported mesh encoding"})
            continue
        normalized,region=convert_mesh_uvs(local["uv"],atlas=atlas,
                attachment=a,attachment_name=attached,expected_page="300401_hongnujian.png")
        if region.name!=reference["region"]:
            summary["unsupported_slots"].append({"slot":sn,"reason":"official region name mismatch"})
            continue
        candidate_vertices=[coord for x,y,_ in local["vertex"] for coord in (x,y)]
        official_vertices=reference["vertices"]
        candidate_uv=[coord for uv in normalized for coord in uv]
        official_uv=reference["uvs"]
        if len(candidate_vertices)!=len(official_vertices) or len(candidate_uv)!=len(official_uv):
            summary["unsupported_slots"].append({"slot":sn,"reason":"world/UV coordinate count mismatch"})
            continue
        summary["converter_supported_mesh_slots"]+=1
        summary["total_mesh_vertices"]+=len(local["vertex"])
        for x,y,inf in local["vertex"]:
            summary["max_influences_per_vertex"]=max(summary["max_influences_per_vertex"],len(inf))
            if len(inf)>4:summary["vertices_over_four_influences"]+=1
        errors=[abs(c-o) for c,o in zip(candidate_vertices,official_vertices)]
        uv_errors=[abs(c-o) for c,o in zip(candidate_uv,official_uv)]
        geom_sq+=sum(e*e for e in errors);uv_sq+=sum(e*e for e in uv_errors)
        summary["total_mesh_vertex_coordinates"]+=len(errors)
        summary["total_mesh_uv_coordinates"]+=len(uv_errors)
        summary["mesh_world_position_max_abs_error"]=max(summary["mesh_world_position_max_abs_error"],max(errors,default=0))
        summary["mesh_uv_max_abs_error"]=max(summary["mesh_uv_max_abs_error"],max(uv_errors,default=0))
        top.append({"slot":sn,"max_world_error":max(errors,default=0),
                    "rms_world_error":math.sqrt(sum(e*e for e in errors)/len(errors)) if errors else 0,
                    "max_uv_error":max(uv_errors,default=0)})
    summary["top_geometry_discrepancies"]=sorted(top,key=lambda x:x["max_world_error"],reverse=True)[:12]
    summary["mesh_geometry_error_rms"]=math.sqrt(geom_sq/max(1,summary["total_mesh_vertex_coordinates"]))
    summary["mesh_uv_error_rms"]=math.sqrt(uv_sq/max(1,summary["total_mesh_uv_coordinates"]))
    # Do not conceal missing artwork: a source region slot should not simply disappear.
    summary["source_render_attachment_coverage"]=round(
        summary["converter_supported_mesh_slots"]/
        max(1,summary["official_active_mesh_slots"]+summary["official_active_region_slots"]),4)
    blockers=[]
    if summary["converter_supported_mesh_slots"]!=summary["official_active_mesh_slots"]:
        blockers.append("MISSING_ACTIVE_MESH_SLOTS")
    if summary["official_active_region_slots"]!=0:
        blockers.append("MISSING_REGION_ATTACHMENTS")
    if summary["mesh_world_position_max_abs_error"]>0.02:
        blockers.append("SETUP_WORLD_TRANSFORM_MISMATCH")
    if summary["mesh_uv_max_abs_error"]>1e-5:
        blockers.append("ATLAS_UV_MISMATCH")
    if summary["vertices_over_four_influences"]>0:
        blockers.append("SKIN_WEIGHTS_TRUNCATED_TO_FOUR")
    summary["blockers"]=blockers
    summary["status"]="FAIL_RIG_FIDELITY" if blockers else "PASS_SETUP_GEOMETRY"
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0 if summary["status"]=="PASS_SETUP_GEOMETRY" else 1

if __name__=="__main__":
    raise SystemExit(main(*[Path(x) for x in sys.argv[1:4]]))
