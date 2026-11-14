#!/usr/bin/env python3
"""P0 three-view painted root artwork acceptance and five-angle comparison.

The generated RGBA files remain separate from original canonical keys. This
gate tests provenance, placement, transparency and root attachment before
allowing experimental yaw compositing. Visual approval is independent.
"""
import hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS,top_components
from p15_128_keyart_registration import frame_interp,jumps
from p15_134_underpaint_probe import P,compose
from p15_158_loop_correspondence import similarity,anchors,warp
ROOT=Path(__file__).resolve().parent.parent
ASSETS=P/'p15-162-root-layers'
OUT=P/'exports/p15-162-root-layers'
E=ROOT/'evidence/p15-162-root-layers-qa.json'
def tag(yaw):return {90.:'yaw090',112.5:'yaw112p5',135.:'yaw135'}[yaw]
def path(yaw):
    current=ASSETS/tag(yaw)/'loop-root-native.png'
    if current.exists():return current
    if yaw==135.:
        return P/'p15-150-ahoge/yaw135/ahoge-native.png'
    return current
def source(yaw):
    file=path(yaw)
    rawmeta=(file.parent/'provenance.json')
    if rawmeta.exists():
        meta=json.loads(rawmeta.read_text())
    else:
        prior=json.loads((file.parent/'generation-result.json').read_text())
        meta={'tool':prior['actual_tool'],'sha256':prior['sha256'],
              'dimensions':[prior['canvas_dimensions']['width'],prior['canvas_dimensions']['height']],
              'asset_origin':'P15-150 verified source reuse','source_output_path':prior['source_path']}
    assert file.is_file() and file.stat().st_size>40000
    sha=hashlib.sha256(file.read_bytes()).hexdigest()
    assert meta['sha256']==sha and meta['tool']=='image_gen.imagegen'
    with Image.open(file) as image:
        assert image.mode=='RGBA'
        assert image.size[0]==image.size[1] and image.size[0]>=1024
        raw=np.asarray(image.resize((443,443),Image.Resampling.LANCZOS)).copy()
    return raw,meta
def inspect(part,original):
    alpha=part[...,3]
    yy,xx=np.indices((443,443))
    expected=(yy<110)&(xx>=135)&(xx<=365)
    root_region=(yy>=54)&(yy<=90)&(xx>=160)&(xx<=345)
    significant=alpha>128
    mask=(alpha>64)&root_region
    canonical=(original[...,3]>96)&(yy<95)&(xx>=135)&(xx<=365)
    visible_in_top=(alpha>96)&(yy<95)&(xx>=135)&(xx<=365)
    overlap=int((canonical&visible_in_top).sum())
    union=int((canonical|visible_in_top).sum())
    n,labels,stats,_=cv2.connectedComponentsWithStats((alpha>64).astype('uint8'),8)
    ranked=sorted((int(stats[i,cv2.CC_STAT_AREA]) for i in range(1,n) if stats[i,cv2.CC_STAT_AREA]>15),reverse=True)
    ys,xs=np.where(significant)
    if not len(xs):raise ValueError('empty generated layer')
    return {'opaquePixels':int(significant.sum()),
        'bboxXYXY':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],
        'visibleOutsideTarget':int((significant&~expected).sum()),
        'lowAlphaOutsideTarget':int(((alpha>0)&~expected).sum()),
        'opaqueFaceBodyPixels':int(significant[130:].sum()),
        'rootRegionPixels':int(mask.sum()),
        'sourceTopAlphaIoU':round(overlap/max(1,union),5),
        'rootAtY75':bool(((alpha[75]>64)&(xx[75]>=160)&(xx[75]<=345)).any()),
        'rootRows55to85':[int(((alpha[y]>64)&(xx[y]>=160)&(xx[y]<=345)).sum()) for y in (55,65,75,85)],
        'largeComponents':ranked,
        'outsideNativeSilhouette':int((significant&(original[...,3]<64)).sum())}
def prepare(save=True):
    keys=keyframes()
    items={};notes={};missing=[]
    for yaw in KEYS:
        try:
            layer,meta=source(yaw)
            items[yaw]=layer
            notes[f'{yaw:g}']={'provenanceSHA256':meta['sha256'],'nativeDimensions':meta['dimensions'],
                              'assetOrigin':meta.get('asset_origin','P15-162 source generation'),
                              'diagnostics':inspect(layer,keys[yaw])}
        except Exception as ex:
            missing.append({'yaw':yaw,'issue':str(ex)[:240]})
    result={'schema':'KOMA_P15_162_THREE_VIEW_ROOT_ART_V1',
            'characterId':'p0_character_001','sourceAngles':list(KEYS),
            'producedSources':notes,'unavailableSources':missing,
            'currentGenerationSourceCount':sum(1 for v in notes.values() if v['assetOrigin']=='P15-162 source generation'),
            'nativeKeyArtworkPreserved':True,
            'fullVisualAccepted':False,'sourceUnderpaintArtistApproved':False,
            'rootCorrespondenceVerified':False,'productionAdmitted':False}
    if len(items)==len(KEYS):
        frames=frame_interp(keys[90.],keys[112.5],keys[135.])
        experimental=[]
        for index,angle in enumerate(ANGLES):
            if angle in KEYS:
                experimental.append(keys[angle].copy());continue
            a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
            t=(angle-a)/(b-a);owner=a if t<=.5 else b
            target=anchors(a)*(1-t)+anchors(b)*t
            moved=warp(items[owner],similarity(anchors(owner),target))
            base=frames[index].copy()
            # A diagnostic source-owner replacement of the free loop above
            # y54; original crown and other original pixels stay unmodified.
            base[:54]=0
            experimental.append(compose(base,moved))
        result['yaw']={'angles':list(ANGLES),
            'baselineMaxAdjacentRGBMAE':max(jumps(frames)),
            'candidateMaxAdjacentRGBMAE':max(jumps(experimental)),
            'baselineTopComponents':[top_components(f) for f in frames],
            'candidateTopComponents':[top_components(f) for f in experimental],
            'nativeKeyviewsPixelExact':all(np.array_equal(experimental[ANGLES.index(a)],keys[a]) for a in KEYS)}
        if save:
            OUT.mkdir(parents=True,exist_ok=True)
            board=Image.new('RGB',(310*5,355*2),(34,42,54));d=ImageDraw.Draw(board)
            for j,(name,seq) in enumerate([('reference',frames),('candidate',experimental)]):
                for i,(angle,frame) in enumerate(zip(ANGLES,seq)):
                    tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                    board.paste(tile.crop((135,0,360,120)).resize((305,310),Image.Resampling.NEAREST).convert('RGB'),(i*310,j*355+30))
                    d.text((i*310+5,j*355+8),f'{name} {angle:g}',fill='white')
            board.save(OUT/'yaw-root-comparison.jpg',quality=94)
    result['gate']={
       'allViewsAvailable':len(items)==len(KEYS),
       'allViewsNewlyGenerated':len(items)==len(KEYS) and result['currentGenerationSourceCount']==3,
       'alphaDomainValid':len(items)==len(KEYS) and all(n['diagnostics']['visibleOutsideTarget']<50 and n['diagnostics']['opaqueFaceBodyPixels']==0 for n in notes.values()),
       'sufficientRootPixels':len(items)==len(KEYS) and all(n['diagnostics']['rootRegionPixels']>=150 for n in notes.values()),
       'allRootsReachY75':len(items)==len(KEYS) and all(n['diagnostics']['rootAtY75'] for n in notes.values()),
       'sourceTopRegistration':len(items)==len(KEYS) and all(n['diagnostics']['sourceTopAlphaIoU']>=.45 for n in notes.values()),
       'visualAndGeometryApproved':False,'passes':False}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(350*3,420),(34,42,54));d=ImageDraw.Draw(board)
        for i,a in enumerate(KEYS):
            if a not in items:continue
            frame=items[a]
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
            board.paste(tile.convert('RGB').resize((343,343),Image.Resampling.LANCZOS),(i*350,38))
            d.text((i*350+6,8),f'{a:g}° native part',fill='white')
            Image.fromarray(frame,'RGBA').save(OUT/(tag(a)+'-scaled.png'))
        board.save(OUT/'root-art-source-review.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 root art QA</title><style>body{background:#202833;color:white;font:16px system-ui}img{max-width:100%}</style><h2>Three source-view isolated loop root art</h2><p>Native art and alpha/provenance QA, with source-owner yaw probe when all three sources are available. Root geometry and underpaint require independent visual acceptance.</p><img src="root-art-source-review.jpg"><img src="yaw-root-comparison.jpg">')
        result['review']='private-assets/exports/p15-162-root-layers/index.html'
        E.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
if __name__=='__main__':
 print(json.dumps(prepare(),ensure_ascii=False,indent=2))
