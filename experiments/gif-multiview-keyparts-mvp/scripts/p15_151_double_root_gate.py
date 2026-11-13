#!/usr/bin/env python3
"""Three-view loop-hair double-root continuity and crown attachment QA.

Distinguishes image-generation candidates from source-registered physical roots.
No extrapolated pixels are promoted to authored scalp/ArtMesh material.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from p15_150_three_view_ahoge import SOURCE_KEYS,load_native,fit,keyframes,replace_upper,old_source_loop,P
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-151-double-root-gate'
E=ROOT/'evidence/p15-151-double-root-gate-qa.json'
CHECK_ROWS=(45,50,55,60,65,70,75,80)
ATTACHMENT_Y=75

def row_segments(mask,y,min_pixels=2):
    xs=np.flatnonzero(mask[y])
    if not len(xs):return []
    segments=[];st=last=int(xs[0])
    for value in xs[1:]:
        value=int(value)
        if value>last+1:
            if last-st+1>=min_pixels:segments.append([st,last])
            st=value
        last=value
    if last-st+1>=min_pixels:segments.append([st,last])
    return segments

def root_tracks(image):
    alpha=image[...,3]>128
    tracks=[]
    for y in CHECK_ROWS:
        runs=row_segments(alpha,y)
        # Two greatest runs correspond to root branches only when clearly separated.
        strongest=sorted(runs,key=lambda x:x[1]-x[0],reverse=True)[:2]
        strongest.sort(key=lambda x:x[0])
        tracks.append({'y':y,'intervals':runs,'twoBranchIntervals':strongest if len(strongest)==2 else [],
                       'twoRootsVisible':len(strongest)==2 and strongest[1][0]-strongest[0][1]>=5})
    return tracks

def analyze(save=True):
    keyframes_map=keyframes()
    reports={}
    images={}
    for a in SOURCE_KEYS:
        native,prov=load_native(a)
        registered,reg=fit(native,keyframes_map[a])
        replaced=replace_upper(keyframes_map[a],registered)
        rows=root_tracks(registered)
        below=registered[ATTACHMENT_Y:110,:,3]>128
        # Crown-attachment continuity means two isolated root branches reach
        # the selected y=75 inspection row. This is necessary but not sufficient.
        at_attachment=next(x for x in rows if x['y']==ATTACHMENT_Y)
        active=[x['y'] for x in rows if x['twoRootsVisible']]
        holes=((keyframes_map[a][:100,:,3]>160)&(replaced[:100,:,3]<64))
        reports[f'{a:g}']={'nativeSHA256':prov['nativeSHA256'],'registration':reg,
                           'rows':rows,'lastPairedRowY':max(active) if active else None,
                           'twoRootsReachAttachmentY75':bool(at_attachment['twoRootsVisible']),
                           'opaquePixelsBetweenY75And110':int(below.sum()),
                           'sourceUpperAlphaHolesAfterReplacement':int(holes.sum()),
                           'sourceBelowY130PixelExact':bool(np.array_equal(replaced[130:],keyframes_map[a][130:]))}
        images[a]=(keyframes_map[a],registered,replaced)
    gate=all(x['twoRootsReachAttachmentY75'] for x in reports.values())
    result={'schema':'KOMA_P15_151_DOUBLE_ROOT_ATTACHMENT_AUDIT_V1',
      'characterId':'p0_character_001','keyAngles':list(SOURCE_KEYS),
      'attachmentProbeY':ATTACHMENT_Y,'sampleRows':list(CHECK_ROWS),
      'views':reports,'geometryGate':{'allViewsTwoRootsReachAttachment':gate,
          'physicalCorrespondenceApproved':False,
          'sourcePaintedHiddenScalpAvailable':False,
          'meaning':'Both roots must reach the near-crown attachment row; this does not prove source alignment or physical identity'},
      'selectedForProduction':False,'fullYawVisualAccepted':False,
      'sourceArtworkUnmodified':True,
      'review':'private-assets/exports/p15-151-double-root-gate/index.html',
      'next':'Paint source-registered double-root attachment for yaw90 and match source crown geometry for 112.5/135; validate hidden scalp and displacement before accepting ArtMesh.'}
    if save:
        OUT.mkdir(exist_ok=True,parents=True)
        board=Image.new('RGB',(350*3,400*3),(35,42,53));draw=ImageDraw.Draw(board)
        for col,a in enumerate(SOURCE_KEYS):
            source,part,replaced=images[a]
            for row,(name,image) in enumerate([('Original source',source),('Registered loop',part),('Root replacement',replaced)]):
                canvas=Image.new('RGBA',(443,443),(49,61,78,255));canvas.alpha_composite(Image.fromarray(image,'RGBA'))
                pen=ImageDraw.Draw(canvas)
                for y in CHECK_ROWS:
                    pen.line([(175,y),(355,y)],fill=(0,225,225,100),width=1)
                pen.line([(175,ATTACHMENT_Y),(355,ATTACHMENT_Y)],fill=(251,145,42,220),width=2)
                board.paste(canvas.convert('RGB').resize((344,344),Image.Resampling.LANCZOS),(350*col,400*row+26))
                draw.text((350*col+7,400*row+6),f'{name} {a:g}°',fill='white')
        board.save(OUT/'root-attachment-overview.jpg',quality=94)
        crop=Image.new('RGB',(350*3,340),(35,42,53));p=ImageDraw.Draw(crop)
        for col,a in enumerate(SOURCE_KEYS):
            original,part,_=images[a]
            canvas=Image.new('RGBA',(443,443),(49,61,78,255));canvas.alpha_composite(Image.fromarray(part,'RGBA'))
            mini=canvas.crop((160,0,365,115)).resize((330,280),Image.Resampling.NEAREST)
            crop.paste(mini.convert('RGB'),(350*col,28))
            p.text((350*col+7,8),f'Root detail {a:g}° / last paired y={reports[f"{a:g}"]["lastPairedRowY"]}',fill='white')
            p.line((350*col,28+int(75/115*280),350*col+330,28+int(75/115*280)),fill=(253,169,48),width=2)
        crop.save(OUT/'root-detail.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 double root attachment</title><style>body{background:#202833;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90 / 112.5 / 135° ahoge double-root continuity</h2><p>Source-aligned isolated loop and root junction; orange inspection line y=75. Necessary two-branch reachability gate, not physical-strand proof.</p><img src="root-attachment-overview.jpg"><h2>Enlarged root comparison</h2><img src="root-detail.jpg">')
        E.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    return result
if __name__=='__main__':
    r=analyze()
    print(json.dumps({'gate':r['geometryGate'],'views':{k:{'lastPairedRowY':v['lastPairedRowY'],'reaches':v['twoRootsReachAttachmentY75'],'upperHoles':v['sourceUpperAlphaHolesAfterReplacement']} for k,v in r['views'].items()}},indent=2))
