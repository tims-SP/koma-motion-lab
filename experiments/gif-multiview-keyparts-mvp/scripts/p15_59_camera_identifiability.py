#!/usr/bin/env python3
"""Audit whether P15-12 orthographic proxy identifies physical camera yaw."""
import json, math, hashlib
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'private-assets/exports/p15-59-camera-identifiability'
OUT.mkdir(parents=True,exist_ok=True)
cam_path=ROOT/'evidence/p15-12-camera-proxy-qa.json'
landmark_path=ROOT/'evidence/p15-54-edge-landmark-qa.json'
cam=json.loads(cam_path.read_text())
raw_registry=ROOT/'private-assets/p5-see-through/mv-candidate/landmark-qa.json'
registry=json.loads(raw_registry.read_text())
manual=json.loads(landmark_path.read_text())
cal=cam['calibration']
modes={}
for key,v in cal.items():modes.setdefault(v['mode'],[]).append(key)
assert len(cal)==12
# Gauge symmetry: rotating all proxy (X,Z) points by delta and changing
# the assumed camera angle by +delta yields the identical image projection.
def project(v,angle):
    angle=math.radians(angle)
    return v['c']+v['X']*math.cos(angle)+v['Z']*math.sin(angle)
def transform(v,delta):
    theta=math.radians(delta)
    x=v['X']*math.cos(theta)-v['Z']*math.sin(theta)
    z=v['X']*math.sin(theta)+v['Z']*math.cos(theta)
    return {'c':v['c'],'X':x,'Z':z}
three={key:val for key,val in cal.items() if val['mode']=='three_view_orthographic_proxy'}
angles=[45,55,65,90]
gauge=[]
for delta in [-30,-20,0,20,30]:
    worst=max(abs(project(v,a)-project(transform(v,delta),a+delta))
              for v in three.values() for a in angles)
    gauge.append({'gaugeRotationDeg':delta,'maxProjectionDifferencePx':round(worst,12)})
assert max(x['maxProjectionDifferencePx'] for x in gauge)<1e-9
# Proxy-only "fit" against manually estimated points is diagnostic,
# because P15-54 annotations were placed near projected anchors.
expected=next(f for f in cam['frames'] if f['yaw']==65)['anchors']
matched=[]
for p in manual['landmarks']:
    raw={'near_eye_iris':'eye.near.iris','far_eye_iris':'eye.far.iris',
         'nose_tip':'nose','mouth_center':'mouth','chin':'face.chin',
         'gold_clip_center':'hair.clip.center'}[p['name']]
    dx=p['measured'][0]-expected[raw]['xy'][0]
    dy=p['measured'][1]-expected[raw]['xy'][1]
    matched.append({'semantic':raw,'pointSource':p['source'],
                    'model':cal[raw]['mode'],
                    'distanceFromProxyPx':round((dx*dx+dy*dy)**.5,2),
                    'independentlyDetected':False})
provenance=json.loads((ROOT/'evidence/p15-58-provenance-pose-qa.json').read_text())
candidate=ROOT/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(candidate)==provenance['candidate']['selectedP1556SHA256']
report={
 'schema':'KOMA-P15-59-CAMERA-IDENTIFIABILITY-V1',
 'characterId':'p0_character_001',
  'sourceCameraProxySHA256':sha(cam_path),
 'underlyingLandmarkRegistrySHA256':sha(raw_registry),
 'sampleObservationOrigins':registry['landmarks']['eye.near.iris'],
 'fittedUsingNominalAnglesNotCalibratedCameras':True,
 'sourceManualLandmarksSHA256':sha(landmark_path),
 'candidateSHA256':sha(candidate),
 'orthographicModel':cam['model'],
 'proxySourceAngles':[0,45,90],
 'modelCounts':{key:len(v) for key,v in modes.items()},
 'threeViewProxyKeys':sorted(three.keys()),
 'linearlyExtrapolatedKeys':sorted(modes.get('two_view_linear_extrapolation',[])),
 'cameraIntrinsicsAvailable':False,
 'independentMeasuredWorldPointsAvailable':False,
 'physicalDepthScaleCalibrated':False,
 'independentAbsoluteCameraReferenceAvailable':False,
 'gaugeSymmetryExperiment':gauge,
 'gaugeInterpretation':'A +20deg global relabeling of camera yaw and equivalent rotation of unknown reconstructed X/Z proxy points leaves every projection exactly unchanged. The reconstruction contains no world-fixed orientation reference, so absolute yaw is not identifiable.',
 'landmarkDiagnostics':matched,
 'landmarkWarning':'P15-54 manual estimates were visually chosen near P15-12 proxies and are not independent annotations. Small reprojection residuals are circular validation, not physical yaw measurements.',
 'relativeCommandDeg':provenance['candidate']['cameraCommandRelativeDegrees'],
 'relativeCommandVerifiedAsPhysicalRotation':False,
 'absoluteYaw65Identifiable':False,
 'absoluteYaw65Verified':False,
 'candidateStatus':'RIGHT_FACING_RELATIVE_CAMERA_EDIT_ONLY',
 'formalArtMeshModified':False,
 'formalKeyframeAccepted':False,
 'minimumMissingEvidence':'A world-fixed 3D landmark reference with known depth/orientation plus independently marked corresponding 2D features and camera projection convention, or validated external camera-pose ground truth.',
 'next':'Prioritize acquiring/calibrating real 3D reference constraints; do not count proxy reprojection, LoRA command or 2D interpolation as independent yaw evidence.'
}
(ROOT/'evidence/p15-59-camera-identifiability-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
# Diagnostic illustration: same x-projected landmarks under two yaw/geometry gauges.
W,H=1150,490
img=Image.new('RGB',(W,H),'#172331')
d=ImageDraw.Draw(img)
panels=[(45,0,'Proxy gauge A: nominal 45 deg'),(65,20,'Proxy gauge B: relabeled +20 deg')]
keys=['eye.near.iris','nose','mouth','face.chin','ear.near']
for i,(yaw,delta,label) in enumerate(panels):
    x0=i*575
    d.rectangle((x0+18,50,x0+555,460),fill='#2b3d50')
    d.text((x0+36,22),label,fill='white')
    for key in keys:
        a=project(three[key],45)
        b=project(transform(three[key],delta),yaw)
        assert abs(a-b)<1e-9
        xx=x0+30+(a-380)*1.35
        yy=115+keys.index(key)*60
        d.ellipse((xx-7,yy-7,xx+7,yy+7),fill='#61d7f6')
        d.text((x0+35,yy+14),key,fill='white')
    d.text((x0+35,420),'Same projected X coordinates',fill='#a6e3ae')
img.save(OUT/'gauge-equivalence.png')
for label,source in [('canonical45.png',ROOT/'private-assets/p2-views/whole/yaw045.png'),
                     ('candidate-relative20.png',candidate)]:
    Image.open(source).convert('RGBA').save(OUT/label)
print(json.dumps({'modes':report['modelCounts'],'gauge':gauge,'physicalYawVerified':False}))
