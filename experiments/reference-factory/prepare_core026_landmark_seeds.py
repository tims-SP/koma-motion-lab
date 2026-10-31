#!/usr/bin/env python3
"""Project supervisor-reviewed source image fiducials into the actual native default view."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
def main():
    seeds=json.loads((ROOT/'config/core026-landmark-seeds.json').read_text())
    c=json.loads((ROOT/'config/core025-layer-contract.json').read_text())
    reg=json.loads((ROOT/'out/core026/default-registration.json').read_text())
    assert reg['status']=='PASS_DEFAULT_SOURCE_COORDINATES'
    by={r['psd_order']:r for r in reg['entries']}
    assert len(seeds['records'])==19
    for row in seeds['records']:
        xy=row['source_xy']
        if xy is None: continue
        layer=c['layers'][row['psd_order']-1];tex=ROOT/layer['raw_source_texture']['file']
        assert hashlib.sha256(tex.read_bytes()).hexdigest()==layer['raw_source_texture']['sha256']
        a=np.asarray(Image.open(tex).convert('RGBA'))
        x=int(np.floor(xy[0]))-layer['bounds'][0];y=int(np.floor(xy[1]))-layer['bounds'][1]
        row['source_alpha_at_seed']=int(a[y,x,3]);assert row['source_alpha_at_seed']>0
        rr=by[row['psd_order']];src=np.array(rr['source_xy']);world=np.array(rr['default_world_xy'])
        coefficient=np.linalg.lstsq(np.c_[src,np.ones(len(src))],world,rcond=None)[0]
        w=np.array([*xy,1.])@coefficient
        row['predicted_native_default_xy']=((w+[82,1773])*.4+[360,440]-np.array([34,114])).tolist()
    out=ROOT/'out/core026/landmark-seeds-projected.json'
    out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n')
    print('CORE026_SEED_SLOTS',len(seeds['records']),sum(r['source_xy'] is not None for r in seeds['records']))
if __name__=='__main__':main()
