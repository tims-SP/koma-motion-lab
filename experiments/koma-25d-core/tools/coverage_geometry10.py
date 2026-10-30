#!/usr/bin/env python3
"""Synthetic 3D surface-visibility coverage test. No source anime art is loaded.

Two reference cameras 0 and nominal +40 degrees; +40 is an uncalibrated
hypothesis, not a physical measured angle. This script is an optimistic
geometry-only upper bound, NOT a production-quality coverage percentage.
"""
import argparse, json, math
from pathlib import Path
import numpy as np
ANGLES=list(range(0,360,45))
SRC=[0,40]
R=460
RAD=np.array([.88,1.0,.68],float)

def coverage(yaw):
    a=math.radians(yaw)
    view=np.array([math.sin(a),0,math.cos(a)])
    screen_x=np.array([math.cos(a),0,-math.sin(a)])
    grid=np.linspace(-1.02,1.02,R)
    u,v=np.meshgrid(grid,grid)
    px=u*screen_x[0];py=v;pz=u*screen_x[2]
    inv=1/RAD**2
    A=np.sum(view*view*inv)
    B=2*(px*view[0]*inv[0]+pz*view[2]*inv[2])
    C=px*px*inv[0]+py*py*inv[1]+pz*pz*inv[2]-1
    delta=B*B-4*A*C
    visible=delta>=0
    t=(-B+np.sqrt(np.maximum(delta,0)))/(2*A)
    point=np.stack([px+t*view[0],py,pz+t*view[2]],axis=-1)
    n=point*inv
    n/=np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-12)
    possible=np.zeros((R,R),bool)
    for deg in SRC:
        t=math.radians(deg)
        source_axis=np.array([math.sin(t),0,math.cos(t)])
        possible|=(n@source_axis)>0.67
    return dict(yaw_deg=yaw,
        geometry_eligible_pct=round(100*np.count_nonzero(visible&possible)/np.count_nonzero(visible),2),
        missing_geom_projection_pct=round(100*np.count_nonzero(visible&~possible)/np.count_nonzero(visible),2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    d={'status':'GEOMETRIC_SOURCE_VISIBILITY_ONLY',
       'input_art':'NONE_SYNTHETIC_SMOKE',
       'camera_source_angles_assumed_deg':SRC,
       'does_not_use_real_inx_mesh':True,
       'does_not_use_generated_image_alpha':True,
       'physical_angle_calibration':False,
       'results':[coverage(x) for x in ANGLES]}
    assert d['results'][4]['missing_geom_projection_pct']==100, '180 must have no source view coverage'
    assert d['results'][5]['missing_geom_projection_pct']>99.9, '225 has negligible source view coverage'
    assert d['results'][3]['missing_geom_projection_pct']>90, '135 mostly missing'
    assert d['results'][0]['missing_geom_projection_pct']<40, 'front source hemisphere visible'
    a.output.write_text(json.dumps(d,indent=2)+'\n')
    print('CORE010_GEOMETRY_COVERAGE_PASS',json.dumps(d['results']))
if __name__=='__main__':main()
