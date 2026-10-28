#!/usr/bin/env bash
# RIVE-RIG-001: evidence-first, no-editor CLI probe. Intentionally does not claim auto-rig success.
set -u
set -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="${EVIDENCE_DIR:-$ROOT/out/rive-rig-001}"
mkdir -p "$EVIDENCE_DIR/logs" "$EVIDENCE_DIR/work" "$EVIDENCE_DIR/screenshots"
cd "$EVIDENCE_DIR/work"

capture() {
  local name="$1"; shift
  echo "== $name : $* =="
  "$@" > "$EVIDENCE_DIR/logs/${name}.log" 2>&1
  local rc=$?
  printf '%s\n' "$rc" > "$EVIDENCE_DIR/logs/${name}.exit"
  sed -n '1,30p' "$EVIDENCE_DIR/logs/${name}.log"
  echo "[exit: $rc]"
  return 0
}

capture cli_version rive --version
capture cli_help rive --help
capture cli_doctor rive doctor
capture cli_docs_help rive docs --help
capture cli_schema_help rive schema --help
capture cli_docs_rigging rive docs --search rigging
capture cli_schema_bone rive schema --search bone
capture cli_schema_mesh rive schema --search mesh
capture cli_schema_weight rive schema --search weight
capture cli_schema_ik rive schema --search ik
# Capture the actual 1.8.0 rigging model, not inferred legacy editor syntax.
capture cli_docs_rigging_full rive docs rigging
capture cli_schema_RootBone rive schema RootBone
capture cli_schema_Bone rive schema Bone
capture cli_schema_Mesh rive schema Mesh
capture cli_schema_MeshVertex rive schema MeshVertex
capture cli_schema_Weight rive schema Weight
capture cli_schema_IKConstraint rive schema IKConstraint
capture cli_samples_help rive samples --help
capture cli_samples_list rive samples
capture cli_samples_path rive samples --path
capture cli_inspect_help rive inspect --help

capture scaffold rive create arm_probe

if [ -d arm_probe ]; then
  capture compile rive arm_probe --once
  capture verify rive arm_probe --verify
  capture screenshot rive arm_probe --screenshot="$EVIDENCE_DIR/screenshots/scaffold.png" --viewport=640x360 --advance=0.5s
  find arm_probe -maxdepth 3 -type f -print | sort > "$EVIDENCE_DIR/scaffold-files.txt"
else
  printf 'Scaffold directory not created\n' > "$EVIDENCE_DIR/scaffold-files.txt"
fi

# Probe Rive CLI support only. Bone/mesh/weight implementation is NOT tested here:
python3 - "$EVIDENCE_DIR" <<'PY'
from pathlib import Path
import sys, json
out=Path(sys.argv[1])
statuses={}
for exit_file in sorted((out/'logs').glob('*.exit')):
    name=exit_file.stem
    code=int(exit_file.read_text().strip())
    statuses[name]={"exit_code":code,"status":"PASS" if code==0 else "FAIL"}
has_rig=bool(list((out/'work').glob('**/*rig*.rml')))
report={
 "experiment":"RIVE-RIG-001",
 "stage":"P0 environment/CLI discovery",
 "cli_probe":statuses,
 "assertions":{
   "no_editor_used":True,
   "bone_hierarchy_created":"NOT_TESTED",
   "skinned_mesh_created":"NOT_TESTED",
   "vertex_weights_created":"NOT_TESTED",
   "ik_pose_rendered":"NOT_TESTED",
   "auto_rig_from_images":"NOT_TESTED",
   "headless_screenshot":"PASS" if (out/'screenshots'/'scaffold.png').exists() else "FAIL",
 },
 "notes":[
  "The scaffold is a Rive API smoke test only; rigging is not demonstrated.",
  "Inspect official schema/docs captured in logs to implement a real weighted arm fixture in the next commit.",
  "Do not confuse successful compilation with acceptable deformation or automatic skinning.",
 ]
}
(out/'result.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
summary=['# RIVE-RIG-001 CLI Probe','',
         'Environment/CLI discovery (NOT an auto-rig pass).','',
         '| Probe | Status |','|---|---|']
summary += [f'| {k} | {v["status"]} (exit {v["exit_code"]}) |' for k,v in statuses.items()]
summary += ['','## Hard gates','']
summary += [f'- {k}: **{v}**' for k,v in report['assertions'].items()]
summary += ['','Rigging requires a subsequent test that emits real bones, mesh weights and rendered bent poses.']
(out/'summary.md').write_text('\n'.join(summary)+'\n')
print((out/'summary.md').read_text())
PY

# Fail the job only when the CLI installation or basic scaffold itself failed.
[ "$(cat "$EVIDENCE_DIR/logs/cli_version.exit")" = "0" ] &&
[ "$(cat "$EVIDENCE_DIR/logs/scaffold.exit")" = "0" ]
