#!/usr/bin/env python3
"""Independent original-RGBA oracle for discrete eye controls; never admits M3."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out/core026/eyes-supervisor'
LIMITS={'rgb_global_mae':.10,'rgb_foreground_union_mae':.50,'rgb_max':4,'rgb_over16_pixels':0}
EYES={'left':(27,28,29),'right':(37,38,39)}
N=1630

def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)
def rgb(p):
    with Image.open(p) as im:
        need(im.size==(N,N),'Wrong screenshot size')
        return np.asarray(im.convert('RGB')).copy()
def metric(actual,reference,foreground):
    d=np.abs(actual.astype(np.int16)-reference.astype(np.int16))
    return {'global_mae':float(d.mean()),'foreground_union_mae':float(d[foreground].mean()),
            'max_channel_error':int(d.max()),'over16_pixels':int(np.count_nonzero(d.max(2)>16))}
def passes(m):
    return m['global_mae']<=.10 and m['foreground_union_mae']<=.50 and m['max_channel_error']<=4 and m['over16_pixels']==0

class SourceOracle:
    """Full canvas source-over, with independent NumPy cropped-array math.

    This is a default/source-coordinate oracle, not a projected-space renderer.
    Effective source RGB has the pre-existing 8-bit quantization contract.
    """
    def __init__(self):
        self.contract=read(ROOT/'config/core025-layer-contract.json')
        self.proposal=read(ROOT/'config/core026-compositor-contract.json')
        self.layers={l['order']:l for l in self.contract['layers']}
        self.images={}
        for n,l in self.layers.items():
            p=ROOT/l['raw_source_texture']['file'];need(sha(p)==l['raw_source_texture']['sha256'],'Source PNG changed')
            with Image.open(p) as im:self.images[n]=np.asarray(im.convert('RGBA')).copy()
        self.shadows={c['shadow_order']:c['base_order'] for c in self.proposal['default_shadow_clips']}
        self.alpha_cache={};self.domains={}
        for side,orders in EYES.items():self.domains[side]=np.maximum.reduce([self.alpha(n) for n in orders])
        self.gaze_domains={side:np.maximum.reduce([np.roll(a,dx,axis=1) for dx in range(-8,9)]) for side,a in self.domains.items()}
        # All eye supports are >8px from canvas edges; np.roll cannot wrap support.
        for a in self.domains.values():need(not a[:,:8].any() and not a[:,-8:].any(),'Eye support touches canvas edge')

    def alpha(self,n):
        if n not in self.alpha_cache:
            a=np.zeros((N,N),np.uint8);l,t,r,b=self.layers[n]['bounds'];a[t:b,l:r]=self.images[n][...,3];self.alpha_cache[n]=a
        return self.alpha_cache[n]

    def compose(self,version,offsets):
        dst=np.zeros((N,N,4),np.float64)
        for op in self.proposal['painter_schedule']:
            n=op['psd_order'];src=self.images[n];dx=offsets.get(n,0)
            l,t,r,b=self.layers[n]['bounds'];l+=dx;r+=dx
            need(0<=l<r<=N and 0<=t<b<=N,'Oracle source outside canvas')
            alpha=src[...,3].copy()
            if version=='clean' and n in self.shadows:
                alpha=np.floor(alpha.astype(float)*self.alpha(self.shadows[n])[t:b,l:r]/255+.5).astype(np.uint8)
            for side,(_,p,h) in EYES.items():
                domain=self.gaze_domains[side] if offsets.get(p,0) or offsets.get(h,0) else self.domains[side]
                if n in (p,h):alpha=np.minimum(alpha,domain[t:b,l:r])
            a=alpha[...,None].astype(float)/255;back=dst[t:b,l:r]
            color=src[...,:3].astype(float)/255
            if op['is_source_multiply']:color*=1-back[...,3:4]+back[...,:3]
            color=np.floor(np.clip(color,0,1)*255+.5)/255
            back[...,:3]=a*color+(1-a)*back[...,:3]
            back[...,3:4]=a+(1-a)*back[...,3:4]
        return dst

def offsets_for(eye,dx):
    return {n:dx for side,(_,p,h) in EYES.items() if eye in (side,'both') for n in (p,h) if dx}
def flatten(premult,background):
    return np.rint(np.clip(premult[...,:3]+(1-premult[...,3:4])*(background=='white'),0,1)*255).astype(np.uint8)

def validate(report):
    m=read(OUT/'manifest.json');need(m['schema']=='core026-eye-captures/1','Capture schema')
    need(not m['blocked_paths'] and not m['page_errors'],'Forbidden inputs or browser errors')
    required={'core026.html','core026.js','config/core026-eye-policy.json','config/core025-layer-contract.json',
        'config/core026-compositor-contract.json','config/core025-render.json','capture_core026_eyes_supervisor.mjs'}
    need(set(m['inputs'])==required,'Missing input provenance')
    for f,digest in m['inputs'].items():need(sha(ROOT/f)==digest,'Stale capture input '+f)
    policy=read(ROOT/'config/core026-eye-policy.json')
    need(policy['selected_policy']=='artist_override_source_paint_domain','Unreviewed eye policy')
    need(policy['native_clip_equivalence'].startswith('BLOCKED_'),'Artist override mislabeled native parity')
    need(policy['coupled_gaze_horizontal_radius']==8,'Unreviewed gaze envelope extent')
    need(policy['control']=={'axis':'horizontal_source_pixels','integer_min':-8,'integer_max':8,'continuous_motion':'NOT_ACCEPTED'},'Control scope changed')
    need(m['metadata']['eye_policy']==policy,'Runtime eye policy differs from pinned input')
    need(m['metadata']['depth_tested'] is False and m['metadata']['natural_3d_turn']=='NOT_ACCEPTED','Subset mislabeled as full runtime')
    oracle=SourceOracle()
    need(set(m['requested_raw_pngs'])=={'/'+l['raw_source_texture']['file'] for l in oracle.layers.values()},'Not exactly62 original color inputs')
    need(len(m['invalid_controls'])==5 and all(c['result']!='ACCEPTED' for c in m['invalid_controls']),'Invalid controls were admitted')
    captures={c['id']:c for c in m['captures']}
    states={'default':('both',0),'reset':('both',0)}
    states.update({eye+('_minus8' if dx<0 else '_plus8'):(eye,dx) for eye in EYES.keys()|{'both'} for dx in (-8,8)})
    positive={f'{state}_{version}_{background}' for state in states for version in ('source','clean') for background in ('white','black')}
    negative={f'negative_{eye}_{kind}_source_white' for eye in EYES for kind in ('highlight_static','fixed_domain')}
    need(len(captures)==36 and set(captures)==positive|negative,'36 actual capture plan differs')
    need(m['invalid_control_state']['sha256']==captures['default_source_white']['sha256'] and
         m['invalid_control_state']['pose']['uv_offsets']==[],'Invalid control mutated actual rendered state')
    world=np.eye(4);world[2,3]=5
    projection=np.eye(4);projection[2,2]=-2/19.9;projection[2,3]=-20.1/19.9
    for c in captures.values():
        need(sha(OUT/c['file'])==c['sha256'],'PNG hash changed')
        need(c['pose']['artwork_draw_count']==62,'Actual source draw count differs')
        need(np.allclose(np.asarray(c['pose']['camera_matrix']).reshape(4,4,order='F'),world,rtol=0,atol=1e-12),'Camera changed')
        need(np.allclose(np.asarray(c['pose']['projection_matrix']).reshape(4,4,order='F'),projection,rtol=0,atol=1e-12),'Projection changed')
        need(c['params']=={'version':c['params']['version'],'background':c['params']['background'],'pass':'beauty','size':N},'Wrong capture parameters')
    default_manifest=read(ROOT/'out/core026/runtime-supervisor/manifest.json')
    defaults={c['id']:c for c in default_manifest['captures']}
    need(read(ROOT/'out/core026/runtime-supervisor/supervisor-qa.json')['default_art_gate']=='PASS','Prerequisite default art gate failed')
    metrics={};locality={};references={};report['metrics']=metrics
    for state,(eye,dx) in sorted(states.items()):
        offsets=offsets_for(eye,dx)
        allowed=np.zeros((N,N),bool)
        for side in EYES:
            if eye in (side,'both'):
                allowed|=np.asarray(Image.fromarray(oracle.gaze_domains[side]).filter(ImageFilter.MaxFilter(3)))>0
        for version in ('source','clean'):
            predicted=oracle.compose(version,offsets)
            for background in ('white','black'):
                key=f'{state}_{version}_{background}';c=captures[key]
                need(c['control']=={'eye':eye,'dx':dx} and c['state']==state,'Wrong control request')
                expected_gaze={side:(dx if eye in (side,'both') else 0) for side in EYES}
                need(c['pose']['eye_controls']==expected_gaze,'Control state differs')
                need(c['pose']['gaze_envelopes']=={side:bool(expected_gaze[side]) for side in EYES},'Active alpha envelope differs')
                need({int(n):xy for n,xy in c['pose']['uv_offsets']}=={n:[x,0] for n,x in offsets.items()},'Pupil/highlight offset accounting differs')
                need(c['pose']['mask_policy']=='source_paint_domain','Wrong active mask policy')
                actual=rgb(OUT/c['file']);reference=flatten(predicted,background)
                foreground=(predicted[...,3]>0)|np.any(actual!=(255 if background=='white' else 0),axis=2)
                metrics[key]=metric(actual,reference,foreground)
                need(passes(metrics[key]),key+': source-RGBA oracle mismatch '+str(metrics[key]))
                base=captures[f'default_{version}_{background}']
                delta=np.any(actual!=rgb(OUT/base['file']),axis=2)
                outside=int(np.count_nonzero(delta&~allowed))
                need(outside==0,key+': changes outside fixed eye paint support')
                if dx:need(int(delta.sum())>0,key+': control changed no actual pixels')
                else:
                    need(c['sha256']==base['sha256']==defaults[f'{version}_{background}']['sha256'],'Default/reset not byte-identical to independent default capture')
                locality[key]={'changed_pixels':int(delta.sum()),'changes_outside_declared_eye_envelope_plus1px':outside}
                if state in ('left_plus8','right_plus8') and version=='source' and background=='white':references[eye]=(reference,foreground)
    negatives={}
    for eye,(_,p,h) in EYES.items():
        c=captures[f'negative_{eye}_highlight_static_source_white'];reference,fg=references[eye]
        bad=rgb(OUT/c['file']);negative_metric=metric(bad,reference,fg)
        need(not passes(negative_metric) and negative_metric['max_channel_error']>4 and negative_metric['over16_pixels']>0,'Static highlight negative not rejected')
        need(c['pose']['eye_controls'][eye]=='manual_layer_offsets','Manual control mislabeled as coupled')
        positive_rgb=rgb(OUT/captures[f'{eye}_plus8_source_white']['file'])
        visible_highlight_delta=int(np.count_nonzero(np.any(positive_rgb!=bad,axis=2)))
        need(visible_highlight_delta>0,'No visible highlight contribution')
        pupil_static=flatten(oracle.compose('source',{h:8}),'white')
        pupil_negative=metric(positive_rgb,pupil_static,fg)
        need(pupil_negative['max_channel_error']>4,'No visible moved pupil contribution')
        fixed=captures[f'negative_{eye}_fixed_domain_source_white']
        fixed_metric=metric(rgb(OUT/fixed['file']),reference,fg)
        need(fixed['pose']['gaze_envelopes']=={'left':False,'right':False},'Wrong fixed-domain counterexample')
        need(not passes(fixed_metric) and fixed_metric['max_channel_error']>4 and fixed_metric['over16_pixels']>0,'Fixed-domain iris-cutting negative not rejected')
        negatives[eye]={'static_highlight_metric':negative_metric,'visible_highlight_contribution_pixels':visible_highlight_delta,
            'static_pupil_oracle_metric':pupil_negative,'fixed_rest_domain_metric':fixed_metric,'status':'BOTH_ACTUAL_NEGATIVES_REJECTED_BY_UNCHANGED_RGB_LIMITS'}
    # Show both eyes at identical scale for all six controls and the shared rest.
    sheet=Image.new('RGB',(2970,1074),'#222');draw=ImageDraw.Draw(sheet)
    for row,eye in enumerate(('left','right','both')):
        for col,(label,state) in enumerate([('-8',eye+'_minus8'),('0','default'),('+8',eye+'_plus8')]):
            im=Image.open(OUT/captures[f'{state}_source_white']['file']).convert('RGB').crop((565,920,1060,1080)).resize((990,320))
            sheet.paste(im,(col*990,row*358));draw.text((col*990+8,row*358+329),eye+' '+label+' source px',fill='white')
    sheet.save(OUT/'eye-review-sheet.png')
    report.update(status='PASS_DISCRETE_EYE_CONTROL_ONLY',numeric_gate='PASS',positive_captures=32,negative_captures=4,
        source_pngs_checked=62,metrics=metrics,locality=locality,negative_controls=negatives,default_and_reset_sha_unchanged=True,
        policy=policy,inputs=m['inputs'],
        limitations={'visual_gate':'PENDING_CODEX_IMAGE_REVIEW','native_clip_parity':policy['native_clip_equivalence'],
            'physical_depth':'NOT_RECOVERED','spatial_compositing':'NOT_IMPLEMENTED','continuous_eye_motion':'NOT_ACCEPTED',
            'natural_3d_turn':'NOT_ACCEPTED','full_M2B':'BLOCKED_SPATIAL_RUNTIME_AND_NATIVE_REGISTRATION',
            'M3_permission':'BLOCKED_PENDING_COMPLETE_M2B'})

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'schema':'core026-eye-supervisor/1','author_executor':'Codex independent source-RGBA oracle',
        'validator_sha256':sha(Path(__file__)),'limits':LIMITS,'status':'FAIL','failures':[]}
    try:validate(report)
    except Exception as error:report['failures'].append(str(error));report['status']='FAIL'
    (OUT/'supervisor-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('CORE026_EYE_SUPERVISOR',json.dumps({k:v for k,v in report.items() if k not in ('metrics','locality','policy','inputs')}))
    return 0 if report['status']=='PASS_DISCRETE_EYE_CONTROL_ONLY' and not report['failures'] else 14

if __name__=='__main__':sys.exit(main())
