"""Validate actual map semantics, coverage, hashes, repeat stability and MP4 decode.

Use --baseline manifest.json to verify a separate renderer-process repeat.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(baseline=None):
    out=ROOT/'out';folder=out/'structure';m=json.loads((folder/'manifest.json').read_text());contract=json.loads((ROOT/'contract.json').read_text())
    assert m['contractSha256']==digest(ROOT/'contract.json')
    assert m['sourceSha256']==digest(out/'source/reference.vrm')
    assert [v['yaw_deg'] for v in m['views']]==contract['world']['angles_deg']
    rows=['beauty','silhouette','depth','normal','part_id'];metrics=[]
    board=Image.new('RGB',(9*170,5*190),(30,32,40));draw=ImageDraw.Draw(board)
    for x,v in enumerate(m['views']):
        arrays={}
        for y,k in enumerate(rows):
            entry=v['passes'][k];p=folder/entry['file'];assert digest(p)==entry['sha256'] and entry['repeatIdentical']
            im=Image.open(p).convert('RGB');assert im.size==(512,512)
            a=np.array(im);arrays[k]=a;im.thumbnail((170,170));board.paste(im,(x*170,y*190+20));draw.text((x*170+3,y*190+3),f"{v['yaw_deg']} {k}",fill='white')
        silhouette=arrays['silhouette'];assert np.all((silhouette==0)|(silhouette==255)), 'Silhouette must be binary; source paint leaked'
        assert np.all(silhouette[:,:,0]==silhouette[:,:,1]) and np.all(silhouette[:,:,1]==silhouette[:,:,2])
        mask=silhouette[:,:,0]>0;area=float(mask.mean());assert .04<area<.85
        ids=arrays['part_id'];allowed={(0,0,0),(0,255,0),(0,0,255)}
        assert set(map(tuple,np.unique(ids.reshape(-1,3),axis=0)))<=allowed,'Part IDs must be exact colors'
        assert np.array_equal(mask,ids.max(axis=2)>0),'Part map/silhouette coverage mismatch'
        d=arrays['depth'];assert np.all(d[:,:,0]==d[:,:,1]) and np.all(d[:,:,1]==d[:,:,2])
        assert np.array_equal(mask,d.max(axis=2)>0),'Depth coverage mismatch'
        assert len(np.unique(d[mask,0]))>3,'Depth missing geometric variation'
        normal=arrays['normal'];normalmask=normal.max(axis=2)>0
        assert np.array_equal(mask,normalmask),'Normal coverage mismatch'
        length=np.linalg.norm(normal[mask]/255*2-1,axis=1)
        assert float(np.quantile(np.abs(length-1),.99))<.025,'Normals are not normalized data'
        yy,xx=np.where(mask);assert yy.min()>5 and xx.min()>5 and xx.max()<506,'Head clipped at top or side'
        metrics.append({'yaw_deg':v['yaw_deg'],'foreground_fraction':area,'bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'depth_levels':len(np.unique(d[mask,0]))})
    assert len({v['passes']['silhouette']['sha256'] for v in m['views']})==9,'Static yaw outputs'
    separate='NOT_TESTED'
    if baseline:
        b=json.loads(Path(baseline).read_text());assert b['contractSha256']==m['contractSha256'] and b['sourceSha256']==m['sourceSha256']
        assert [(v['yaw_deg'],v['passes']) for v in b['views']]==[(v['yaw_deg'],v['passes']) for v in m['views']]
        separate='PASS_45_IDENTICAL_PNG_HASHES'
    board.save(folder/'contact.jpg',quality=92)
    frames=out/'video_frames';frames.mkdir(exist_ok=True)
    # Anchor-only structural demonstration, explicitly not continuous animation.
    for i,v in enumerate(m['views']):
        canvas=Image.new('RGB',(1024,560),(25,28,36));draw=ImageDraw.Draw(canvas)
        draw.text((16,14),f"CORE-022 | generic pixiv VRM | yaw {v['yaw_deg']} deg | held anchors, NOT Aka animation",fill='white')
        for j,k in enumerate(['beauty','normal']):canvas.paste(Image.open(folder/v['passes'][k]['file']).convert('RGB'),(j*512,40))
        canvas.save(frames/f'{i:03d}.png')
    movie=out/'reference_factory_anchors.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','2','-i',str(frames/'%03d.png'),'-vf','fps=24','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(movie)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,width,height,r_frame_rate','-of','json',str(movie)]))
    assert int(probe['streams'][0]['nb_read_frames'])==108
    decoded=out/'decoded';decoded.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(movie),'-vf',"select=eq(n\\,0)+eq(n\\,48)+eq(n\\,96)",'-vsync','0',str(decoded/'%02d.png')],check=True)
    sheet=Image.new('RGB',(1024,3*560))
    for i,p in enumerate(sorted(decoded.glob('*.png'))):sheet.paste(Image.open(p).convert('RGB'),(0,i*560))
    sheet.save(out/'decoded_contact.jpg',quality=92)
    report={'status':'PASS_STRUCTURAL_FACTORY_ONLY','views':9,'maps':45,'same_process_repeat':'PASS','separate_process_repeat':separate,
      'metrics':metrics,'video':{'sha256':digest(movie),'probe':probe,'content':'nine actual rendered anchors held 12 frames each; no continuous in-between motion'},
      'open_gates':{'VRM_aka_registration':'NOT_TESTED','fox_ear_structure':'MISSING_FROM_GENERIC_VRM','aka_decomposition_benchmark':'NOT_TESTED','ABCD_candidates':'NOT_TESTED','human_approved_90':'NOT_TESTED','full_front_native_runtime_parity':'NOT_TESTED','continuous_360_aka':'NOT_BUILT'}}
    (out/'qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path);a=p.parse_args();main(a.baseline)
