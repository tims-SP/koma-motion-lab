#!/usr/bin/env bash
# P0.1 — Actual authored 2-bone, weighted vector arm fixture in RML.
# Derived from 'rive docs rigging' in Rive CLI 1.8.0, not a fake generated skeleton overlay.
set -u
set -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${EVIDENCE_DIR:-$ROOT/out/rive-rig-001}"
mkdir -p "$OUT/weighted-arm" "$OUT/screenshots" "$OUT/logs"
cd "$OUT/weighted-arm"

python3 - <<'PY'
from pathlib import Path
from html import escape
for degrees in (0, 45, 90, 135):
    project=Path(f'arm_{degrees:03d}')
    project.mkdir(parents=True,exist_ok=True)
    (project/'rive.yaml').write_text(f'name: arm_{degrees:03d}\n')
    import math
    r=math.radians(degrees)
    # Node groups skeleton and skinned path under the same local transform.
    # Weight value 32640/indices 513 is a 128:127 blend per official Rive rigging docs.
    xml=f'''<Artboard width="480" height="320" name="WeightedArm">
  <Node x="125" y="130" name="RigLocal">
    <RootBone x="0" y="0" length="85" rotation="0" name="UpperArm" id="0:40">
      <Bone length="85" rotation="{r:.8f}" name="Forearm" id="0:41"/>
    </RootBone>
    <Shape name="Arm" id="0:50">
      <PointsPath name="Path" id="0:51">
        <StraightVertex x="0" y="-18"><Weight values="255" indices="1"/></StraightVertex>
        <StraightVertex x="85" y="-18"><Weight values="32640" indices="513"/></StraightVertex>
        <StraightVertex x="170" y="-14"><Weight values="255" indices="2"/></StraightVertex>
        <StraightVertex x="170" y="14"><Weight values="255" indices="2"/></StraightVertex>
        <StraightVertex x="85" y="18"><Weight values="32640" indices="513"/></StraightVertex>
        <StraightVertex x="0" y="18"><Weight values="255" indices="1"/></StraightVertex>
        <Skin tx="0" ty="0" name="Skin">
          <Tendon boneId="0:40" tx="0" ty="0" name="Upper"/>
          <Tendon boneId="0:41" tx="85" ty="0" name="Fore"/>
        </Skin>
      </PointsPath>
      <Fill name="Fill"><SolidColor colorValue="FF7DB9D9" name="ArmPaint"/></Fill>
    </Shape>
  </Node>
</Artboard>
'''
    (project/'scene.rml').write_text(xml)
PY

probe() {
  local name="$1"; shift
  "$@" > "$OUT/logs/${name}.log" 2>&1
  local rc=$?
  echo "$rc" > "$OUT/logs/${name}.exit"
  echo "== $name ($rc) =="
  sed -n '1,48p' "$OUT/logs/${name}.log"
}

for degrees in 000 045 090 135; do
  project="arm_$degrees"
  probe "weighted_verify_$degrees" rive "$project" --verify
  probe "weighted_build_$degrees" rive "$project" --once
  probe "weighted_inspect_$degrees" rive inspect "$project" --summary
  probe "weighted_screenshot_$degrees" rive "$project" --screenshot="$OUT/screenshots/weighted_arm_$degrees.png" --viewport=480x320 --advance=0s
done

python3 - "$OUT" <<'PY'
import json,sys
from pathlib import Path
d=Path(sys.argv[1]); statuses={}
for degree in ('000','045','090','135'):
    statuses[degree]={}
    for stage in ('verify','build','inspect','screenshot'):
        p=d/'logs'/f'weighted_{stage}_{degree}.exit'
        rc=int(p.read_text().strip()) if p.exists() else 999
        statuses[degree][stage]={'exit_code':rc,'status':'PASS' if rc==0 else 'FAIL'}
    file=d/'screenshots'/f'weighted_arm_{degree}.png'
    statuses[degree]['screenshot_exists']=file.exists()
result={'experiment':'RIVE-RIG-001','stage':'authored-weighted-vector-rig','poses':statuses,'manual_editor_used':False,
 'claim':'An RML-defined weighted bone rig, not image-to-rig automation.',
 'auto_skinning_from_layered_image':'NOT_TESTED'}
(d/'weighted-arm-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,indent=2))
PY

for degrees in 000 045 090 135; do
  for stage in verify build inspect screenshot; do
    [ "$(cat "$OUT/logs/weighted_${stage}_${degrees}.exit")" = 0 ] || exit 1
  done
done
