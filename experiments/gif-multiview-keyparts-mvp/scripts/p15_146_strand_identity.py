#!/usr/bin/env python3
"""Candidate strand identity labels and conservative source-owned ArtMesh yaw.

This separates hair into three persistent semantic *region candidates*. It
does not assert strand-level identity without individually authored layers.
"""
import json
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
from p15_140_contour_yaw_mesh import contour_mesh,interpolate_mesh,load_roles
from p15_139_hair_artmesh import warp_triangles,area
from p15_129_ahoge_ownership import ANGLES,KEYS,keyframes
from p15_128_keyart_registration import jumps
from p15_134_underpaint_probe import P,rgba,compose,background_rgb
from p15_142_face_ownership import protect_mask
from p15_131_semantic_landmarks import POINTS
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-146-strand-identities'
E=ROOT/'evidence/p15-146-strand-identities-qa.json'
LABELS=('crown','fringe','nape')
PALETTE={'crown':(243,199,63),'fringe':(91,217,231),'nape':(179,120,242)}

def view_parts(angle):
    source,_,_,raw_hair=load_roles(angle)
    # Region identity is based on stable visible head-space measurements,
    # not pixel colors or inherited extracted eye ink.
    face=protect_mask(angle,strength=1.25)
    mask=raw_hair & ~face
    ys,xs=np.where(mask)
    assert xs.size>10000
    left,right=float(xs.min()),float(xs.max())
    top,bottom=float(ys.min()),float(ys.max())
    xn=(np.arange(443,dtype=np.float32)[None,:]-left)/max(right-left,1)
    yn=(np.arange(443,dtype=np.float32)[:,None]-top)/max(bottom-top,1)
    # Near face is on image right for all the present three references.
    # Nape ends are below .68 of source hair height.
    nape=mask&(yn>=.69)&(xn<.80)
    fringe=mask&~nape&(xn>=.70)&(yn>=.25)
    crown=mask&~nape&~fringe
    partitions={'crown':crown,'fringe':fringe,'nape':nape}
    total=np.zeros_like(mask,dtype=np.int32)
    for m in partitions.values():total+=m
    assert np.array_equal(total,mask.astype(np.int32))
    pieces={}
    for role,m in partitions.items():
        part=source.copy();part[~m]=0;pieces[role]=part
    remaining=source.copy();remaining[mask]=0
    recomposed=remaining.copy()
    for name,m in partitions.items():recomposed[m]=pieces[name][m]
    assert np.array_equal(recomposed,source)
    return source,pieces,remaining,partitions,mask

def render_variant(weight=.35):
    parts={a:view_parts(a) for a in KEYS}
    meshes={a:contour_mesh(parts[a][4]) for a in KEYS}
    faces=meshes[90.][1]
    assert all(np.array_equal(faces,meshes[a][1]) for a in KEYS)
    points={a:meshes[a][0] for a in KEYS}
    images=[]
    areas={}
    for a in ANGLES:
        if a in KEYS:
            images.append(parts[a][0].copy());continue
        start,end=(90.,112.5) if a<112.5 else (112.5,135.)
        t=(a-start)/(end-start)
        # At midpoint of interval use owner switching but gate the movement
        # of independent labeled strands to a small fraction of mesh displacement.
        owner=start if t<=.5 else end
        target=interpolate_mesh(points,start,end,t)
        conservative=points[owner]+weight*(target-points[owner])
        areas[str(a)]={'minimumTriangleArea':round(min(area(conservative[tri]) for tri in faces),5),
                       'folds':sum(area(conservative[tri])<=0 for tri in faces)}
        result=parts[owner][2].copy()
        # Preserve source alpha and per-part painter order. Pixels are only
        # assigned to one strand role; use premultiplied alpha composite.
        for label in ('nape','crown','fringe'):
            moved=warp_triangles(parts[owner][1][label],points[owner],conservative,faces)
            result=compose(result,moved)
        images.append(result)
    return images,areas,parts

def metric(images):
    return {'adjacentRGBMAE':jumps(images),'maxAdjacentRGBMAE':max(jumps(images))}

def audit(save=True):
    candidates={}
    grids={}
    for name,strength in [('source_owned_000',0),('strand_mesh_025',.25),('strand_mesh_050',.5)]:
        images,areas,parts=render_variant(strength)
        grids[name]=images
        scores=metric(images)
        scores.update({'meshGeometry':areas,'nativeKeysPixelExact':all(np.array_equal(images[ANGLES.index(a)],parts[a][0]) for a in KEYS)})
        candidates[name]=scores
    reference=[rgba(P/'exports/p15-145-fringe-source-transfer/transfer_050'/(f'yaw{a:06.2f}'.replace('.','p')+'.png')) for a in ANGLES]
    q={'schema':'KOMA_P15_146_SOURCE_STRAND_REGIONS_V1','characterId':'p0_character_001',
      'sourceAngles':list(KEYS),'samples':list(ANGLES),'candidateLabels':list(LABELS),
      'definition':'mutually exclusive crown, near-face fringe and lower nape regions of existing hair candidate mask',
      'referenceP15_145':metric(reference),'methods':candidates,
      'sourceCoverage':{},'sourceArtPreserved':True,
      'pixelPerfectSourceReassembly':True,'eyeProtectMaskEnabled':True,
      'trueAnatomicalRootTipCorrespondenceVerified':False,
      'artistApprovedStrandLabels':False,'underpaintAcrossViewsValidated':False,
      'fullYawVisualAccepted':False,
      'review':'private-assets/exports/p15-146-strand-identities/index.html',
      'next':'Source-paint identifiable strands in 90/112.5/135 and validate root/tip relations; then deform owner-matched ArtMesh with per-view face/neck underpaint.'}
    parts={a:view_parts(a) for a in KEYS}
    for a,(_,individual,rest,masks,combined) in parts.items():
        q['sourceCoverage'][f'{a:g}']={'hairPixelCount':int(combined.sum()),
                                      'labels':{k:int(v.sum()) for k,v in masks.items()},
                                      'protectedFacePixelCount':int(protect_mask(a,strength=1.25).sum()),
                                      'recompositionExact':True}
    q['motionCandidateGate']={
        'thresholdMaxAdjacentRGBMAE':q['referenceP15_145']['maxAdjacentRGBMAE'],
        'passes':any(x['maxAdjacentRGBMAE']<=q['referenceP15_145']['maxAdjacentRGBMAE'] for x in candidates.values()),
        'selectedForProduction':False,
        'reason':'Source region labels have no verified material identity, and middle-angle renderings show line tears and owner switching.'
    }
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(315*5,355*4),(35,41,54));draw=ImageDraw.Draw(board)
        rows=[('P15-145',reference)]+list(grids.items())
        for row,(name,images) in enumerate(rows):
            for i,(angle,frame) in enumerate(zip(ANGLES,images)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                board.paste(tile.convert('RGB').resize((309,309),Image.Resampling.LANCZOS),(315*i,row*355+30))
                draw.text((315*i+6,row*355+7),f'{name} {angle:g}',fill='white')
                if row:
                    folder=OUT/name;folder.mkdir(exist_ok=True)
                    Image.fromarray(frame,'RGBA').save(folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
        board.save(OUT/'comparison.jpg',quality=94)
        annotations=Image.new('RGB',(443*3,490),(36,42,54));d=ImageDraw.Draw(annotations)
        for i,angle in enumerate(KEYS):
            source,individual,rest,masks,_=parts[angle]
            backdrop=Image.new('RGBA',(443,443),(49,61,78,255))
            backdrop.alpha_composite(Image.fromarray(source,'RGBA'))
            over=np.zeros((443,443,4),dtype=np.uint8)
            for name,mask in masks.items():over[mask]=[*PALETTE[name],115]
            backdrop.alpha_composite(Image.fromarray(over,'RGBA'))
            annotations.paste(backdrop.convert('RGB'),(i*443,28))
            d.text((i*443+7,5),f'{angle:g}° source candidate identities',fill='white')
        d.text((10,475),'Gold=crown, cyan=fringe, violet=nape. Provisional labels; root/tip physical identity not proven.',fill='white')
        annotations.save(OUT/'identity-map.jpg',quality=94)
        for angle in KEYS:
            folder=OUT/('source-'+f'{angle:g}'.replace('.','p'));folder.mkdir(exist_ok=True)
            for label,arr in parts[angle][1].items():Image.fromarray(arr,'RGBA').save(folder/(label+'.png'))
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 hair part identities</title><style>body{background:#202733;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>P0 90–135° candidate strand identities</h2><p>Source-conserving strand regions and independently warped mesh trials compared with P15-145. Labels follow view-space geometry, not confirmed individual strands.</p><img src="identity-map.jpg"><h2>Five-angle comparison</h2><img src="comparison.jpg">')
        E.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
    return q
if __name__=='__main__':
    q=audit()
    print(json.dumps({'sourceCounts':q['sourceCoverage'],'reference':q['referenceP15_145'],'methods':q['methods']},indent=2))
