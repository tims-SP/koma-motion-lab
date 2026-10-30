"""Audit manually generated pilot files; missing arms never count as a benchmark.

Image generation is a manual built-in imagegen step, not a fake local model call.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'out/candidates';entries=[]
    for arm,refs in [('A',['identity/source_A_aka_front.png']),('C',['identity/source_A_aka_front.png','identity/source_B_aka_parts.png','structure/00090_beauty.png','structure/00090_silhouette.png'])]:
        p=folder/f'pilot-{arm}-001.png'
        if not p.exists():continue
        im=Image.open(p).convert('RGB');a=np.array(im)
        # Explicit diagnostic ink threshold; not a semantic mask or alpha extraction.
        mask=a.min(axis=2)<220;yy,xx=np.where(mask)
        if not len(xx):raise ValueError('Blank generated candidate')
        margins=[int(xx.min()),int(yy.min()),int(im.width-xx.max()-1),int(im.height-yy.max()-1)]
        issues=[]
        if im.size!=(1024,1024):issues.append('CAMERA_CROP_ERROR: output canvas differs from 1024x1024 request')
        if min(margins)<48:issues.append('CAMERA_CROP_ERROR: ink threshold margin below 48 px')
        entries.append({'candidate_id':f'pilot-{arm}-001','arm':arm,'file':p.name,'sha256':sha(p),'dimensions':list(im.size),
          'prompt_template':'prompts/pilot-'+arm+'.txt','compiled_prompt_sha256':sha(ROOT/'prompts'/f'pilot-{arm}.txt'),
          'provider':'OpenAI built-in imagegen','model':'NOT_EXPOSED_BY_TOOL','model_version':None,'seed':None,'job_id':None,
          'generation_date':'2026-10-30','generation_parameters_observed':{'transparent_background':False},
          'references':[{'file':r,'sha256':sha(ROOT/'out'/r)} for r in refs],
          'lineage':{'parents':[],'repairs':[],'regional_truth':'visible identity conditioned on source; unseen profile/back structures are GENERATED_CANDIDATE'},
          'lifecycle':'REVIEWED','authority':'GENERATED_CANDIDATE','human_approval':'NOT_REQUESTED_OR_GRANTED',
          'qa':{'ink_threshold_rgb_min':220,'margins_ltrb_px':margins,'hard_gate':'FAIL' if issues else 'MANUAL_REVIEW_REQUIRED','issues':issues,
            'visual_review':'one near eye and right-facing profile visible; orange bob/fox ears/leaf/neckband present; exact angle/camera and hidden anatomy are not calibrated',
            'task_example_contamination':'no obvious brown long hair copied; one sample cannot establish robustness'}})
    manifest={'schema':'koma-generation-pilot/1','experiment':'A_vs_C_feasibility_pilot','N_per_executed_arm':1,'candidate_count':len(entries),
      'B':'NOT_TESTED: MV-Adapter not installed/executed','D':'NOT_TESTED: separate lineart/color-transfer path not executed',
      'full_ABCD_benchmark':'NOT_TESTED','ranking':'NONE_ACCEPTED','production_status':'NOT_ACCEPTED','candidates':entries}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if entries:
        board=Image.new('RGB',(3*420,470),(241,242,246));d=ImageDraw.Draw(board)
        paths=[ROOT/'out/identity/source_A_aka_front.png']+[folder/e['file'] for e in entries]
        labels=['SOURCE PSD (open-mouth expression)']+[e['candidate_id']+' | framing FAIL' for e in entries]
        for i,(p,label) in enumerate(zip(paths,labels)):
            im=Image.open(p).convert('RGB');im.thumbnail((410,410));board.paste(im,(i*420+(420-im.width)//2,45));d.text((i*420+8,14),label,fill=(24,31,45))
        board.save(folder/'pilot_comparison.jpg',quality=94)
    print(json.dumps({'candidate_count':len(entries),'ranking':manifest['ranking'],'full_ABCD_benchmark':'NOT_TESTED'}))
if __name__=='__main__':main()
