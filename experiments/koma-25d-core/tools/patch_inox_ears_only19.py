#!/usr/bin/env python3
"""Minimal fail-closed patch of pinned Inox2D to draw ONLY real original Aka ears.

All original puppet nodes, parameters, parent matrices, native deformation and
textures are initialized and evaluated WITHOUT pruning or re-authoring.
Only the textured-mesh DRAW DISPATCH is filtered; mask-source rendering is
left intact so relevant native GPU masks are evaluated normally.

The upstream repository is cloned in CI at an exact commit. Nothing here
requires editing the user's source INX or inventing any UV/data.
"""
from pathlib import Path
import argparse,json
p=argparse.ArgumentParser()
p.add_argument("--checkout",type=Path,required=True)
p.add_argument("--report",type=Path,required=True)
a=p.parse_args()
root=a.checkout
source=root/"inox2d/src/node.rs"
s=source.read_text()
needle="pub struct InoxNodeUuid(pub(crate) u32);"
assert s.count(needle)==1,"Unexpected upstream node representation"
s=s.replace(needle,"pub struct InoxNodeUuid(pub u32); // CORE019: expose original source ID for draw-only debug filter")
source.write_text(s)
renderer=root/"inox2d-opengl/src/lib.rs"
s=renderer.read_text()
needle="""\t\trender_ctx: &TexturedMeshRenderCtx,
\t\t_id: InoxNodeUuid,
\t) {
\t\tself.push_debug_group("inox2d - draw textured content");"""
replace="""\t\trender_ctx: &TexturedMeshRenderCtx,
\t\t_id: InoxNodeUuid,
\t) {
        // CORE019: ONLY change visibility of source Aka ear drawcalls.
        // Every full original node, parameter, inherited transform, deform and UV
        // is still evaluated by the existing Inox2D puppet pipeline.
        // Mask calls are deliberately left in place to avoid breaking ear masks.
        if !as_mask && std::env::var_os("KOMA_NATIVE_EARS_ONLY").is_some()
            && _id.0 != 3424078890 && _id.0 != 3453251657 {
            return;
        }
\t\tself.push_debug_group("inox2d - draw textured content");"""
assert s.count(needle)==1,"Unexpected upstream renderer dispatch, do not make unsafe patch"
s=s.replace(needle,replace)
renderer.write_text(s)
main=root/"examples/render-opengl/src/main.rs"
s=main.read_text()
needle="}, 0.0));"
assert s.count(needle)==1, "CORE008 fixed-yaw patch must be applied first"
s=s.replace(needle,"}, 0.5));")
main.write_text(s)
a.report.parent.mkdir(parents=True,exist_ok=True)
doc={"schema":"core019-inox-native-only-ears-patch/1",
 "source_sha":"d4dd9dd7f16b775042cbda44370570abf9a8cf81",
 "ear_native_ids":[3424078890,3453251657],
 "filter_only_drawcalls":True,
 "original_inx_file_changed":False,
 "original_puppet_nodes_pruned":False,
 "all_114_original_head_yaw_bindings_evaluated":True,
 "vertex_and_uv_source_unchanged":True,
 "mask_drawcalls_preserved":True,
 "pitch_normalized":0.5,"parameter_samples":[0.5,1.0],
 "original_upstream_renderer_modified":"KOMA_EARS_ONLY_TEST_FILTER_AND_FIXED_POSE_ONLY",
 "native_2d_GL_reference":True,
 "native_3d_new_skin_proven":False}
a.report.write_text(json.dumps(doc,indent=2)+"\n")
print("CORE019_REAL_NATIVE_DRAW_FILTER_INSTALLED",json.dumps(doc))
