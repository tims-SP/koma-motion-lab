#!/usr/bin/env python3
"""Codex-designed patch, applied and executed by mcode; structural review only."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
REF = ROOT / 'out/core026/reference'
EPS = 1e-5  # Native pixels, numerical serialization tolerance, not quality acceptance.
YAWS = [v / 4 for v in range(-4, 5)]
IDENTITIES = [('nose_tip',21),('nose_root',21),('chin',13),('mouth_cornerL',22),
 ('mouth_cornerR',22),('face_edgeL',13),('face_edgeR',13),('eye_innerL',27),
 ('eye_outerL',27),('pupilL',28),('eye_innerR',37),('eye_outerR',37),('pupilR',38),
 ('ear_rootL',1),('ear_rootR',2),('ear_tipL',1),('ear_tipR',2),('neck_connection',11),('leaf_stem',62)]
HARD_UNKNOWN = {'nose_root','mouth_cornerL','mouth_cornerR','ear_rootL','ear_rootR','neck_connection'}
CONTOURS = {'chin','face_edgeL','face_edgeR'}
STATES = {'VERIFIED_IMAGE_FIDUCIAL','BOUNDARY_PROXY_ONLY','NCC_CANDIDATE','OCCLUDED','UNKNOWN'}
CLAIMS = {'overall_M1':'NOT_ACCEPTED','runtime_depth_and_occlusion':'NOT_IMPLEMENTED',
          'scope':'REVIEW_PREPARATION_AND_STRUCTURE_ONLY'}

def need(ok, message):
    if not ok: raise ValueError(message)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_bytes())
def same(a,b): return json.dumps(a,sort_keys=True,allow_nan=False)==json.dumps(b,sort_keys=True,allow_nan=False)

def point(xy):
    return isinstance(xy,list) and len(xy)==2 and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<652 for v in xy)

def close_xy(a,b):
    if a is None or b is None: return a is b
    return point(a) and point(b) and max(abs(x-y) for x,y in zip(a,b))<=EPS

def in_root(path):
    p=path.resolve(); need(p.is_relative_to(ROOT),'Output/input path outside project'); return p

def skeleton():
    seed_path=ROOT/'config/core026-landmark-seeds.json'
    projector=ROOT/'out/core026/landmark-seeds-projected.json'
    manifest_path=REF/'reference-manifest.json'
    seeds=read(seed_path); projected=read(projector); manifest=read(manifest_path)
    tracks=read(ROOT/'out/core026/landmarks/landmarks.json')
    contract_path=ROOT/'config/core025-layer-contract.json'; contract=read(contract_path)
    need(sha(contract_path)=='9f6d4190b597053027403575fa7b37d05bedf878e03d12c83efa46ae01fe9b6d','Frozen contract hash changed')
    need([(r['id'],r['psd_order']) for r in seeds['records']]==IDENTITIES,'19 seed identities/order changed')
    need(len(projected['records'])==19,'Projected seed count changed')
    projections={r['id']:r for r in projected['records']}
    need(len(projections)==19,'Duplicate projected identities')
    need(manifest['status']=='PASS' and manifest['capture']['ffmpeg_draw_mouse'] is False,'Reference not clean/PASS')
    need(manifest['source']['sha256']=='dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f','Wrong source INX')
    need(manifest['capture']['camera_scale']==.4 and manifest['capture']['camera_position']==[82,1773], 'Camera changed')
    need(manifest['roi']['head']==[34,114,686,766],'ROI changed')
    need([p['raw_yaw'] for p in manifest['poses']]==YAWS,'Reference pose grid changed')
    need([p['raw_yaw'] for p in tracks['frames']]==YAWS,'Tracking pose grid changed')
    need(tracks['reference_manifest_sha256']==sha(manifest_path) and tracks['seeds_sha256']==sha(projector),'Stale tracking inputs')
    for pose in manifest['poses']:
        p=REF/'frames'/Path(pose['head_png']).name
        need(sha(p)==pose['head_sha256'],'Native head PNG hash mismatch')
        with Image.open(p) as im: need(im.size==(652,652),'Wrong native head dimensions')
    records=[]; textures={}
    for seed in seeds['records']:
        name=seed['id']; source=seed['source_xy']; projection=projections.get(name)
        need(projection is not None,'Projected seed missing')
        for key in ['psd_order','source_xy','semantic_class','definition']:
            need(same(projection[key],seed[key]),f'{name}: stale projected {key}')
        alpha=None
        if name in HARD_UNKNOWN: need(source is None,f'{name}: hard unknown source was filled')
        else:
            need(isinstance(source,list) and len(source)==2,f'{name}: source coordinate missing')
            layer=contract['layers'][seed['psd_order']-1]
            image_path=in_root(ROOT/layer['raw_source_texture']['file'])
            if image_path not in textures:
                need(sha(image_path)==layer['raw_source_texture']['sha256'],'Source PNG hash changed')
                with Image.open(image_path) as im: textures[image_path]=im.convert('RGBA').copy()
            image=textures[image_path]; x0,y0,x1,y1=layer['bounds']
            need(image.size==(x1-x0,y1-y0),'Raw texture bounds mismatch')
            x,y=math.floor(source[0])-x0,math.floor(source[1])-y0
            need(0<=x<image.width and 0<=y<image.height,'Source point outside texture')
            alpha=image.getpixel((x,y))[3]; need(alpha>0,'Source point has no alpha support')
            need(projection.get('source_alpha_at_seed')==alpha,'Projected source alpha changed')
        proxy=seed['semantic_class']=='PAINTED_BOUNDARY_PROXY' or name in CONTOURS
        frames=[]
        for pose,track in zip(manifest['poses'],tracks['frames']):
            need(set(track['landmarks'])=={n for n,_ in IDENTITIES},'Tracking identities changed')
            xy=track['landmarks'][name]['xy']
            if xy is not None:
                need(point(xy),'Candidate coordinate outside native frame')
                need(source is not None,'Unknown source gained a tracking candidate')
                xy=[round(float(v),6) for v in xy]
            state='UNKNOWN' if xy is None else 'BOUNDARY_PROXY_ONLY' if proxy else 'NCC_CANDIDATE'
            frames.append({'raw_yaw':pose['raw_yaw'],'native_head_sha256':pose['head_sha256'],
             'candidate_xy':xy,'candidate_method':'UNKNOWN' if xy is None else 'SOURCE_PROJECTED_DEFAULT' if pose['raw_yaw']==0 else 'NCC_CANDIDATE',
             'state':state,'xy':None if xy is None else list(xy),'confidence':'UNKNOWN',
             'review_method':'UNREVIEWED','image_feature_evidence':None,'eligible_for_fitting':False})
        records.append({'id':name,'psd_order':seed['psd_order'],'source_xy':source,'source_alpha':alpha,
         'semantic_class':seed['semantic_class'],'definition':seed['definition'],'is_proxy':proxy,'frames':frames})
    for im in textures.values(): im.close()
    return {'schema':'core026-landmark-review/1','inputs':{'source_inx_sha256':manifest['source']['sha256'],
     'reference_manifest_sha256':sha(manifest_path),'seed_config_sha256':sha(seed_path),
     'tracker_program_sha256':sha(ROOT/'verify_core026_reference.py'),
     'projector_program_sha256':sha(ROOT/'prepare_core026_landmark_seeds.py')},
     'candidate_tolerance_native_pixels':EPS,'claims':CLAIMS,'records':records}

def verify(data, base):
    need(isinstance(data,dict),'Review must be an object')
    need(set(data)==set(base),'Top-level review fields differ')
    for key in ['schema','inputs','candidate_tolerance_native_pixels','claims']:
        need(same(data[key],base[key]),f'Immutable {key} changed')
    need(isinstance(data['records'],list) and len(data['records'])==19,'Need exactly19 records')
    counts={'slots':19,'poses':9,'cells':0,'reviewed':0,'fit_eligible':0,'hard_unknown_slots':6}
    immutable={'raw_yaw','native_head_sha256','candidate_method'}
    for actual,expected in zip(data['records'],base['records']):
        need(isinstance(actual,dict) and set(actual)==set(expected),'Landmark record fields changed')
        name=expected['id']
        for key in set(expected)-{'frames'}: need(same(actual[key],expected[key]),f'{name}: immutable {key} changed')
        need(isinstance(actual['frames'],list) and len(actual['frames'])==9,f'{name}: need9 frames')
        for a,e in zip(actual['frames'],expected['frames']):
            counts['cells']+=1; tag=f"{name}/{e['raw_yaw']}"
            need(isinstance(a,dict) and set(a)==set(e),f'{tag}: frame fields changed')
            for key in immutable: need(same(a[key],e[key]),f'{tag}: immutable {key} changed')
            need(close_xy(a['candidate_xy'],e['candidate_xy']),f'{tag}: candidate coordinate changed')
            need(a['state'] in STATES,f'{tag}: invalid state')
            need(a['confidence'] in {'HIGH','MEDIUM','LOW','UNKNOWN'},f'{tag}: invalid confidence')
            need(a['review_method'] in {'UNREVIEWED','VISUAL_NATIVE'},f'{tag}: invalid method')
            need(type(a['eligible_for_fitting']) is bool,f'{tag}: eligibility must be bool')
            need(a['xy'] is None or point(a['xy']),f'{tag}: coordinate invalid')
            if a['review_method']=='UNREVIEWED':
                need(a['state']==e['state'] and close_xy(a['xy'],e['xy']) and a['confidence']=='UNKNOWN' and
                 a['image_feature_evidence'] is None and not a['eligible_for_fitting'],f'{tag}: unreviewed candidate promoted')
            else:
                counts['reviewed']+=1
                need(isinstance(a['image_feature_evidence'],str) and bool(a['image_feature_evidence'].strip()),f'{tag}: visual evidence missing')
            if name in HARD_UNKNOWN:
                need(a['state'] in {'UNKNOWN','OCCLUDED'} and a['xy'] is None and not a['eligible_for_fitting'],f'{tag}: hard unknown was filled')
            if a['state'] in {'UNKNOWN','OCCLUDED'}:
                need(a['xy'] is None and a['confidence']=='UNKNOWN' and not a['eligible_for_fitting'],f'{tag}: unknown/occluded has coordinate')
            else: need(point(a['xy']),f'{tag}: candidate/review coordinate missing')
            if actual['is_proxy']:
                need(a['state']!='VERIFIED_IMAGE_FIDUCIAL' and not a['eligible_for_fitting'],f'{tag}: proxy promoted')
            qualified=(not actual['is_proxy'] and expected['source_xy'] is not None and
             a['state']=='VERIFIED_IMAGE_FIDUCIAL' and a['review_method']=='VISUAL_NATIVE' and
             a['confidence'] in {'HIGH','MEDIUM'} and point(a['xy']) and
             isinstance(a['image_feature_evidence'],str) and bool(a['image_feature_evidence'].strip()))
            if a['state']=='VERIFIED_IMAGE_FIDUCIAL': need(qualified,f'{tag}: unsupported verified fiducial')
            if a['eligible_for_fitting']: need(qualified,f'{tag}: invalid fitting eligibility'); counts['fit_eligible']+=1
    return counts

def main():
    ap=argparse.ArgumentParser(description=__doc__); mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true'); mode.add_argument('--verify',action='store_true')
    ap.add_argument('--output',type=Path,default=ROOT/'config/core026-landmark-review.json'); a=ap.parse_args()
    output=in_root(a.output)
    if a.prepare: need(not output.exists(),'Review already exists; refusing to overwrite it')
    base=skeleton(); data=base if a.prepare else read(output); counts=verify(data,base)
    if a.prepare:
        output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print('CORE026_LANDMARK_REVIEW',json.dumps({'status':'PREPARED_PENDING_REVIEW' if a.prepare else 'STRUCTURE_ONLY_PASS',
     **counts,'overall_M1':'NOT_ACCEPTED_BY_STRUCTURE_CHECK','runtime_depth_and_occlusion':'NOT_IMPLEMENTED'}))
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(f'CORE026_LANDMARK_REVIEW_FAIL: {exc}',file=sys.stderr); sys.exit(11)
