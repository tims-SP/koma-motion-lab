#!/usr/bin/env python3
"""Codex M1 aggregate: finite native image references, never physical 3D recovery."""
import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = ['nose_tip','pupilL','pupilR']
LOWER_FACE = ['chin','face_edgeL','face_edgeR']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def evaluate(review):
    """Visibility gate after independent source/provenance/structure checks."""
    records={r['id']:r for r in review['records']}
    yaws=[f['raw_yaw'] for f in records['nose_tip']['frames']]
    reviewed=sum(f['review_method']=='VISUAL_NATIVE' for r in records.values() for f in r['frames'])
    usable=[]; coverage=[]
    for i,yaw in enumerate(yaws):
        fiducials=[]
        for name in REQUIRED:
            r=records[name];f=r['frames'][i]
            if (not r['is_proxy'] and r['source_xy'] is not None and
                f['state']=='VERIFIED_IMAGE_FIDUCIAL' and f['review_method']=='VISUAL_NATIVE' and
                f['confidence'] in ('HIGH','MEDIUM') and f['eligible_for_fitting'] is True and f['xy'] is not None):
                fiducials.append(name)
        contours=[]
        for name in LOWER_FACE:
            f=records[name]['frames'][i]
            if (f['state']=='BOUNDARY_PROXY_ONLY' and f['review_method']=='VISUAL_NATIVE' and
                f['confidence'] in ('HIGH','MEDIUM') and f['xy'] is not None and f['eligible_for_fitting'] is False):
                contours.append(name)
        accepted=len(fiducials)==3 and bool(contours)
        coverage.append({'raw_yaw':yaw,'image_fiducials':fiducials,'lower_face_contour_observations':contours,
                         'usable_for_limited_comparison':accepted})
        if accepted:usable.append(yaw)
    blockers=[]
    if reviewed!=171:blockers.append('NOT_ALL_171_CELLS_VISUALLY_REVIEWED')
    if 0 not in usable:blockers.append('DEFAULT_POSE_LACKS_REQUIRED_IMAGE_FEATURES_AND_CONTOUR')
    if not any(x<0 for x in usable):blockers.append('NEGATIVE_OBLIQUE_LACKS_REQUIRED_IMAGE_FEATURES_AND_CONTOUR')
    if not any(x>0 for x in usable):blockers.append('POSITIVE_OBLIQUE_LACKS_REQUIRED_IMAGE_FEATURES_AND_CONTOUR')
    return {'status':'BLOCKED_REFERENCE_FOR_DEPTH_FIT' if blockers else 'PASS_REFERENCE_LIMITED',
            'blockers':blockers,'reviewed_cells':reviewed,'usable_raw_yaws':usable,'pose_coverage':coverage,
            'state_counts':dict(Counter(f['state'] for r in records.values() for f in r['frames'])),
            'fit_eligible_image_features':sum(f['eligible_for_fitting'] for r in records.values() for f in r['frames']),
            'source_unknown_slots':[name for name,r in records.items() if r['source_xy'] is None]}

def inside(path):
    result=path.resolve()
    if not result.is_relative_to(ROOT):raise ValueError('Path must stay inside reference-factory')
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--review',type=Path,default=ROOT/'config/core026-landmark-review.json')
    ap.add_argument('--report',type=Path,default=ROOT/'out/core026/m1-acceptance.json')
    args=ap.parse_args();review_path=inside(args.review);report_path=inside(args.report)
    commands=[['audit_core026.py','--verify-source'],['verify_core026_supervisor.py'],
              ['verify_core026_m1c1_supervisor.py'],['extract_core026_constraints.py','--verify'],
              ['prepare_core026_landmark_review.py','--verify','--output',str(review_path)]]
    prerequisites=[]
    for command in commands:
        result=subprocess.run([sys.executable,*command],cwd=ROOT,capture_output=True,text=True)
        prerequisites.append({'command':['python',*command],'exit_code':result.returncode,
                              'stdout_tail':result.stdout[-3500:],'stderr_tail':result.stderr[-1500:]})
        if result.returncode:break
    failed=any(r['exit_code'] for r in prerequisites)
    result={'status':'FAIL_SOURCE_OR_REFERENCE','blockers':['PREREQUISITE_FAILED']} if failed else evaluate(json.loads(review_path.read_bytes()))
    accepted=result['status']=='PASS_REFERENCE_LIMITED'
    registration=json.loads((ROOT/'out/core026/default-registration.json').read_bytes())
    manifest_path=ROOT/'out/core026/reference/reference-manifest.json'
    manifest=json.loads(manifest_path.read_bytes())
    report={'schema':'core026-m1-aggregate/1','author_executor':'Codex explicit local fallback',
            **result,'prerequisites':prerequisites,
            'inputs':{'review_sha256':sha(review_path),'constraints_sha256':sha(ROOT/'config/core026-constraints.json'),
                      'reference_manifest_sha256':sha(manifest_path),'source_inx_sha256':sha(ROOT/'out/source/Aka.inx'),
                      'contract_sha256':sha(ROOT/'config/core025-layer-contract.json')},
            'reference':{'native_head_sha256':[p['head_sha256'] for p in manifest['poses']],
                         'camera_scale':manifest['capture']['camera_scale'],'camera_position':manifest['capture']['camera_position'],
                         'head_roi':manifest['roi']['head'],'raw_yaw_is_physical_degrees':False,
                         'per_pose_registration':'FORBIDDEN; same camera/ROI and source mapping for all poses'},
            'registration':{'unique_texture_max_residual_source_px':registration['raster_unique_max_residual_source_px'],
                            'unique_texture_median_residual_source_px':registration['raster_unique_median_residual_source_px'],
                            'selected_unique_uuids':len({r['selected_uuid'] for r in registration['entries']})},
            'comparison_metrics':{'reference_image_observations':'AVAILABLE_AT_USABLE_RAW_YAWS_ONLY',
                                  'candidate_absolute_landmark_error_px':'BLOCKED_NO_CORE026_CANDIDATE_RENDERER',
                                  'candidate_face_silhouette_IoU':'BLOCKED_NO_CORE026_CANDIDATE_RENDERER',
                                  'attachment_gap_px':'BLOCKED_UNKNOWN_ATTACHMENT_ROOTS_AND_NO_CANDIDATE',
                                  'raw_yaw_to_physical_angle':'BLOCKED_NOT_CALIBRATED',
                                  'reference_admission_is_candidate_fit_acceptance':False},
            'scope':{'M1':'PASS_REFERENCE_LIMITED' if accepted else 'NOT_ACCEPTED',
                     'M2_permission':'LOCAL_RECEIVER_COMPOSITOR_PROTOTYPE_ONLY' if accepted else 'BLOCKED',
                     'interpolation_and_extrapolation':'NOT_VALIDATED','physical_depth':'NOT_RECOVERED',
                     'physical_yaw_degrees':'UNKNOWN','anatomical_landmarks':'NOT_ESTABLISHED',
                     'contours_are_fixed_material_points':False,'runtime_receiver_compositor':'NOT_IMPLEMENTED',
                     'corrected_natural_3d_turn':'NOT_ACCEPTED','360_degree_assets':'INCOMPLETE'},
            'M2_first_gate':'Preserve original 0-yaw art before any oblique comparison. No blind Z fitting or global depth inference.'}
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('CORE026_M1',json.dumps({'status':result['status'],'blockers':result['blockers'],
          'reviewed_cells':result.get('reviewed_cells'),'usable_raw_yaws':result.get('usable_raw_yaws'),
          'M2_permission':report['scope']['M2_permission'],'physical_depth':'NOT_RECOVERED'}))
    return 11 if failed else 0 if accepted else 12

if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,TypeError,KeyError) as error:
        print('CORE026_M1_FAIL:',error,file=sys.stderr);sys.exit(11)
