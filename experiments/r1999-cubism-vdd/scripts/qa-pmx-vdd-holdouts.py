#!/usr/bin/env python3
"""Compare predicted VDD frames to withheld orthographic PMX structural views.

Holdouts are model-derived camera renders, not independent painted art.
Their purpose is testing geometric interpolation without training on the view.
"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image

HOLDOUTS=[55,67,82]
THRESHOLDS={'silhouetteIoUMin':0.90,'RGBMAEMax255':20.0,
            'predictionAreaRatioMin':0.92,'predictionAreaRatioMax':1.08}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def analyze(a,b):
 with Image.open(a) as img:pred=img.convert('RGBA')
 with Image.open(b) as img:truth=img.convert('RGBA')
 if pred.size!=(640,640) or truth.size!=(640,640):raise ValueError('Need 640x640 aligned RGBA')
 intersection=union=area_pred=area_true=0
 difference=0.0
 for pixelA,pixelB in zip(pred.getdata(),truth.getdata()):
  pred_alpha=pixelA[3]>40
  true_alpha=pixelB[3]>40
  area_pred+=pred_alpha
  area_true+=true_alpha
  intersection+=pred_alpha and true_alpha
  present=pred_alpha or true_alpha
  union+=present
  if present:
   alphaA=pixelA[3]/255;alphaB=pixelB[3]/255
   difference+=sum(abs((pixelA[c]*alphaA+240*(1-alphaA))-
                       (pixelB[c]*alphaB+240*(1-alphaB))) for c in range(3))
 if union<=0 or area_true<=0:raise ValueError('Empty silhouette')
 metrics={'silhouetteIoU':round(intersection/union,6),
          'RGBMAE255':round(difference/(union*3),4),
          'predictionAlphaPixels':area_pred,'holdoutAlphaPixels':area_true,
          'predictionAreaRatio':round(area_pred/area_true,6)}
 metrics['thresholdChecks']={
  'silhouette':metrics['silhouetteIoU']>=THRESHOLDS['silhouetteIoUMin'],
  'color':metrics['RGBMAE255']<=THRESHOLDS['RGBMAEMax255'],
  'area':THRESHOLDS['predictionAreaRatioMin']<=metrics['predictionAreaRatio']<=THRESHOLDS['predictionAreaRatioMax']}
 return metrics

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--root',type=Path,required=True)
 p.add_argument('--prediction-pattern',default='predicted-yaw{angle:03d}.png')
 p.add_argument('--method',default='canvas_semantic_rect_warp')
 p.add_argument('--output',type=Path,required=True)
 args=p.parse_args()
 root=args.root.resolve()
 candidates=json.loads((root/'predictions-manifest.json').read_text())
 holdouts=json.loads((root/'holdout-manifest.json').read_text())
 if holdouts.get('angles')!=HOLDOUTS or holdouts.get('independent2DArtCoverage')!=0:
  raise RuntimeError('Unexpected holdout reference provenance')
 if candidates.get('independent2DArtCoverage')!=0:
  raise RuntimeError('Prediction provenance incorrectly asserts independent art')
 truth_map={x['yawDeg']:x for x in holdouts['holdoutViews']}
 found={x['yawDeg']:x for x in candidates['frames']}
 checks=[]
 for angle in HOLDOUTS:
  reference=root/truth_map[angle]['file']
  prediction=root/args.prediction_pattern.format(angle=angle)
  if not prediction.is_file():raise FileNotFoundError(prediction)
  if sha(reference)!=truth_map[angle]['sha256']:
   raise RuntimeError('Holdout hash mismatch '+str(angle))
  if args.prediction_pattern=='predicted-yaw{angle:03d}.png':
   if sha(prediction)!=found[angle]['sha256']:
    raise RuntimeError('Prediction hash mismatch '+str(angle))
  metrics=analyze(prediction,reference)
  checks.append({'yawDeg':angle,'predictionSha256':sha(prediction),
     'holdoutSha256':truth_map[angle]['sha256'],**metrics})
 accepted=all(all(row['thresholdChecks'].values()) for row in checks)
 report={'schema':'R1999-PMX-VDD-HOLDOUT-QA-V1','method':args.method,
   'role':'THIRD_PARTY_3D_STRUCTURE_AND_RGB_PROXY',
   'independentPaintedArtCoverage':0,
   'goal':'cartoon_shading_out_of_plane_yaw_with_anatomical_continuity',
   'thresholds':THRESHOLDS,
   'holdoutCount':len(checks),'angles':checks,
   'visualGate':'PASS_STRUCTURAL_HOLDOUT' if accepted else 'NEEDS_VDD_REFINEMENT',
   'engineeringGate':'PASS_MEASURED_PREDICTIONS_AND_HOLDOUTS'}
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'engineeringGate':report['engineeringGate'],'visualGate':report['visualGate'],
                   'angles':[{'yawDeg':row['yawDeg'],'IoU':row['silhouetteIoU'],'MAE':row['RGBMAE255'],
                               'areaRatio':row['predictionAreaRatio']} for row in checks]}))
if __name__=='__main__':main()
