#!/usr/bin/env python3
"""Independent clean-image/hash checks and candidate NCC tracks; never automatic fit acceptance."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from numpy.lib.stride_tricks import sliding_window_view
ROOT=Path(__file__).resolve().parent
REF=ROOT/'out/core026/reference'
OUT=ROOT/'out/core026/landmarks'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def correlate(previous,current,xy,radius=32,half=5):
    px,py=np.rint(np.asarray(xy)-.5).astype(int);h,w=previous.shape[:2]
    if px<half or py<half or px>=w-half or py>=h-half:raise ValueError('Template outside actual frame')
    t=previous[py-half:py+half+1,px-half:px+half+1].astype(float)
    t-=t.mean(axis=(0,1),keepdims=True);norm=np.linalg.norm(t)
    if norm<1e-6:raise ValueError('Textureless template')
    x0,x1=max(0,px-radius-half),min(w,px+radius+half+1)
    y0,y1=max(0,py-radius-half),min(h,py+radius+half+1)
    region=current[y0:y1,x0:x1].astype(float)
    windows=sliding_window_view(region,t.shape[:2],axis=(0,1)).transpose(0,1,3,4,2)
    numerator=np.einsum('ijxyc,xyc->ij',windows,t);sums=windows.sum(axis=(2,3))
    variance=(windows*windows).sum(axis=(2,3,4))-(sums*sums).sum(axis=2)/t.shape[0]**2
    score=numerator/(np.sqrt(np.maximum(variance,1e-12))*norm)
    iy,ix=np.unravel_index(np.argmax(score),score.shape)
    def offset(a,b,c):
        d=a-2*b+c
        return float(np.clip(.5*(a-c)/d,-.5,.5)) if abs(d)>1e-12 else 0.
    dx=offset(score[iy,ix-1],score[iy,ix],score[iy,ix+1]) if 0<ix<score.shape[1]-1 else 0.
    dy=offset(score[iy-1,ix],score[iy,ix],score[iy+1,ix]) if 0<iy<score.shape[0]-1 else 0.
    centre=np.array([x0+ix+half,y0+iy+half],float)
    return np.asarray(xy)+centre-[px,py]+[dx,dy],float(score[iy,ix])
def main():
    mp=REF/'reference-manifest.json';m=json.loads(mp.read_text())
    assert m['status']=='PASS' and m['capture']['ffmpeg_draw_mouse'] is False
    assert m['capture']['camera_scale']==.4 and m['capture']['camera_position']==[82,1773]
    assert m['roi']['head']==[34,114,686,766]
    poses=m['poses'];assert [p['raw_yaw'] for p in poses]==[i/4 for i in range(-4,5)]
    images=[];top_margins=[]
    for p in poses:
        full=REF/'frames'/Path(p['full_png']).name;head=REF/'frames'/Path(p['head_png']).name
        assert sha(full)==p['full_sha256'] and sha(head)==p['head_sha256']
        cmd=p['capture']['command'];assert cmd[cmd.index('-draw_mouse')+1]=='0' and cmd.index('-draw_mouse')<cmd.index('-i')
        im=Image.open(full).convert('RGB');assert im.size==(720,880)
        a=np.array(Image.open(head).convert('RGB'));assert np.array_equal(np.array(im.crop((34,114,686,766))),a)
        yy,xx=np.nonzero(a.max(2)>16);top_margins.append(int(yy.min()));assert yy.min()>=2
        images.append(a)
    sp=ROOT/'out/core026/landmark-seeds-projected.json';seeds=json.loads(sp.read_text())
    assert len(seeds['records'])==19
    frames=[{'raw_yaw':p['raw_yaw'],'landmarks':{}} for p in poses]
    for seed in seeds['records']:
        name=seed['id']
        for frame in frames:
            frame['landmarks'][name]={'status':'UNKNOWN','xy':None,'reason':seed['definition'],
                'semantic_class':seed['semantic_class'],'eligible_for_fitting':False}
        if seed['source_xy'] is None:continue
        start=np.array(seed['predicted_native_default_xy'],float)
        frames[4]['landmarks'][name].update(status='SOURCE_PROJECTED_SEED_REVIEWED',xy=start.tolist())
        for indices in ([5,6,7,8],[3,2,1,0]):
            old,point=4,start.copy()
            for index in indices:
                try:
                    target,score=correlate(images[old],images[index],point)
                    reverse,rs=correlate(images[index],images[old],target)
                    error=float(np.linalg.norm(reverse-point))
                    if min(score,rs)<.82 or error>1.25:
                        frames[index]['landmarks'][name].update(reason='NCC/forward-backward failure',ncc=score,reverse_ncc=rs,fb_error_px=error)
                        break
                    frames[index]['landmarks'][name].update(status='TRACKED_CANDIDATE_REQUIRES_REVIEW',xy=target.tolist(),ncc=score,reverse_ncc=rs,fb_error_px=error)
                    old,point=index,target
                except ValueError as e:
                    frames[index]['landmarks'][name]['reason']=str(e);break
    OUT.mkdir(parents=True,exist_ok=True);board=Image.new('RGB',(1440,1515),'#111');draw=ImageDraw.Draw(board)
    for index,frame in enumerate(frames):
        im=Image.fromarray(images[index]);dr=ImageDraw.Draw(im)
        for number,seed in enumerate(seeds['records'],1):
            p=frame['landmarks'][seed['id']]
            if p['xy'] is not None:
                x,y=p['xy'];colour='#ff58ed' if p['semantic_class']=='PAINTED_BOUNDARY_PROXY' else '#55ff74'
                dr.ellipse((x-3,y-3,x+3,y+3),outline=colour);dr.text((x+4,y-8),str(number),fill=colour)
        im.save(OUT/('annotated_%02d.png'%index));im.thumbnail((480,480));x,y=index%3*480,index//3*505
        board.paste(im,(x,y+25));draw.text((x+5,y+5),'native raw yaw=%+.2f'%frame['raw_yaw'],fill='white')
    board.save(OUT/'review-contact.png')
    result={'schema':'core026-supervisor-native-track-diagnostic/1','status':'DIAGNOSTIC_COMPLETE_NOT_FIT_ACCEPTANCE',
        'reference_manifest_sha256':sha(mp),'seeds_sha256':sha(sp),
        'method':'Adjacent-pose channel-centred RGB NCC; both scores>=.82; FB<=1.25 native pixels; branch stops on failure.',
        'claims':{'physical_yaw_degrees':'UNKNOWN','visibility_ground_truth':'NOT_ESTABLISHED_BY_NCC','overall_M1':'NOT_ACCEPTED_BY_THIS_CHECK','all_points_fit_eligible':False},
        'top_ink_margin_pixels':top_margins,'frames':frames}
    (OUT/'landmarks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('CORE026_LANDMARK_COUNTS',json.dumps([(p['raw_yaw'],sum(q['xy'] is not None for q in p['landmarks'].values())) for p in frames]))
    print('CORE026_REFERENCE_HASH_QA',json.dumps({'full_sha_verified':9,'crop_sha_verified':9,'top_margins':top_margins,'fit_acceptance':False}))
if __name__=='__main__':main()
