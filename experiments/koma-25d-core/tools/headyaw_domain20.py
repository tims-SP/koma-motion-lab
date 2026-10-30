#!/usr/bin/env python3
"""Correct Aka Inox2D HeadYaw authoring input to normalized-grid mapping.

The real input range is [-1,+1]^2; original axis_points is [0,1].
Original input .5 becomes normalized .75, NOT .5. This pure helper handles
scalar and array-valued param samples without introducing new UV or artwork.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
AXIS_X=[0.,.125,.25,.375,.5,.625,.75,.875,1.]
AXIS_Y=[0.,.5,1.]
INPUT_MIN=[-1.,-1.]
INPUT_MAX=[1.,1.]

def normalize_input(raw_xy,minimum=INPUT_MIN,maximum=INPUT_MAX):
    assert len(raw_xy)==len(minimum)==len(maximum)==2
    return [min(1.,max(0.,(float(v)-lo)/(hi-lo)))
            for v,lo,hi in zip(raw_xy,minimum,maximum)]

def interval(grid,x):
    assert all(grid[i]<grid[i+1] for i in range(len(grid)-1))
    for i in range(len(grid)-1):
        if x<=grid[i+1]:
            return i,(x-grid[i])/(grid[i+1]-grid[i])
    return len(grid)-2,1.

def lerp(a,b,f):
    if isinstance(a,list):
        assert isinstance(b,list) and len(a)==len(b)
        return [lerp(x,y,f) for x,y in zip(a,b)]
    return a*(1-f)+b*f

def sample_bilinear(binding_values,raw_xy):
    ux,uy=normalize_input(raw_xy)
    i,u=interval(AXIS_X,ux)
    j,v=interval(AXIS_Y,uy)
    left=lerp(binding_values[i][j],binding_values[i+1][j],u)
    right=lerp(binding_values[i][j+1],binding_values[i+1][j+1],u)
    return lerp(left,right,v)

def test():
    assert normalize_input([0.,0.])==[.5,.5]
    assert normalize_input([.5,.5])==[.75,.75]
    assert normalize_input([1.,.5])==[1.,.75]
    assert normalize_input([-1.,-1.])==[0.,0.]
    grid=[[x+y for y in AXIS_Y] for x in AXIS_X]
    assert abs(sample_bilinear(grid,[.5,.5])-1.5)<1e-9
    assert abs(sample_bilinear(grid,[1.,.5])-1.75)<1e-9
    vectors=[[[x,y] for y in AXIS_Y] for x in AXIS_X]
    assert sample_bilinear(vectors,[.5,.5])==[.75,.75]
    print("CORE020_ORIGINAL_PARAM_INPUT_TO_GRID_TEST_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--source-domain",type=Path)
    a=p.parse_args()
    test()
    if a.source_domain:
        d=json.loads(a.source_domain.read_text())
        assert d["raw_source_min"]==INPUT_MIN and d["raw_source_max"]==INPUT_MAX
        assert d["raw_axis_points"]==[AXIS_X,AXIS_Y]
        assert d["original_headYaw_bindings_count"]==114
        print("CORE020_REAL_PINNED_INX_DOMAIN_VERIFIED")
