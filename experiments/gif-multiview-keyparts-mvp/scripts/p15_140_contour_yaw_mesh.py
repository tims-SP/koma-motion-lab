#!/usr/bin/env python3
"""Three-view head-hair contour mesh correspondence and source-owned yaw study.

16 consistent angular contour roles + two inner radial rings. The geometry
comes from mask silhouettes, not verified hair-strand anatomy.
"""
from pathlib import Path
import json,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw
from p15_139_hair_artmesh import warp_triangles,area
from p15_129_ahoge_ownership import keyframes,ANGLES,KEYS
from p15_128_keyart_registration import jumps
from p15_135_closed_hair_mask import closed_mask,split
from p15_134_underpaint_probe import P,rgba,compose
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-140-contour-yaw-mesh';E=ROOT/'evidence/p15-140-contour-yaw-mesh-qa.json'
RAYS=24
ANG=np.linspace(-np.pi,np.pi,RAYS,endpoint=False)
def load_roles(angle):
    whole=keyframes()[angle].copy()
    if angle==112.5:
        mask,_=closed_mask(whole)
    else:
        directory=P/'exports/p15-133-semantic-source'/('yaw'+f'{angle:g}'.replace('.','p'))
        mask=rgba(directory/'hair.visible.png')[...,3]>0
    foreground,remaining=split(whole,mask)
    return whole,foreground,remaining,mask
def contour_mesh(binary):
    yy,xx=np.where(binary)
    assert len(xx)>1000
    cloud=np.column_stack((xx,yy)).astype(np.float32)
    hull=cv2.convexHull(cloud).reshape(-1,2)
    center=np.array([xx.mean(),yy.mean()],dtype=np.float32)
    # Convex hull makes contour correspondence nonfolding; labels follow fixed angles.
    contour=[]
    for theta in ANG:
        direction=np.array([np.cos(theta),np.sin(theta)],dtype=np.float32)
        radii=[]
        for i in range(len(hull)):
            a=hull[i];b=hull[(i+1)%len(hull)]
            edge=b-a
            cross=lambda u,v:float(u[0]*v[1]-u[1]*v[0])
            denom=cross(direction,edge)
            if abs(denom)<1e-6:continue
            delta=a-center
            t=cross(delta,edge)/denom
            u=cross(delta,direction)/denom
            if t>0 and -1e-4<=u<=1.0001:radii.append(t)
        assert radii,'center must be inside hull'
        contour.append(center+max(radii)*direction)
    exterior=np.array(contour,np.float32)
    inner1=center[None,:]+.35*(exterior-center[None,:])
    inner2=center[None,:]+.70*(exterior-center[None,:])
    positions=np.concatenate([center[None,:],inner1,inner2,exterior],axis=0)
    faces=[]
    for i in range(RAYS):
        k=(i+1)%RAYS
        faces.append((0,1+i,1+k))
        for start,next_start in ((1,1+RAYS),(1+RAYS,1+2*RAYS)):
            faces.extend([(start+i,next_start+i,next_start+k),(start+i,next_start+k,start+k)])
    faces=np.asarray(faces,np.int32)
    # Sign is positive in the source image coordinate frame by construction.
    assert all(area(positions[f])>0 for f in faces)
    return positions,faces,center,exterior
def interpolate_mesh(positions,a,b,t):
    return positions[a]*(1-t)+positions[b]*t
def choose_owner(a,b,t):
    return a if t<=.5 else b
def run(save=True):
    roles={a:load_roles(a) for a in KEYS}
    meshes={a:contour_mesh(roles[a][3]) for a in KEYS}
    faces=meshes[90.][1]
    assert all(np.array_equal(faces,meshes[a][1]) for a in KEYS)
    positions={a:meshes[a][0] for a in KEYS}
    render=[]
    owners={}
    min_areas={}
    for angle in ANGLES:
        if angle in roles:
            result=roles[angle][0].copy()
            owners[str(angle)]=angle
        else:
            a,b=(90.,112.5) if angle<112.5 else (112.5,135.)
            t=(angle-a)/(b-a)
            target=interpolate_mesh(positions,a,b,t)
            owner=choose_owner(a,b,t)
            # Foreground mesh can deform separately from intact source body.
            deformation=warp_triangles(roles[owner][1],positions[owner],target,faces)
            result=compose(roles[owner][2],deformation)
            owners[str(angle)]=owner
            min_areas[str(angle)]=round(min(area(target[f]) for f in faces),4)
        render.append(result)
    metrics={'maxAdjacentCompositeRGBMAE':max(jumps(render)),
             'adjacentCompositeRGBMAE':jumps(render),
             'nativeKeysPixelExact':all(np.array_equal(render[ANGLES.index(a)],roles[a][0]) for a in KEYS),
             'allTrianglesPositive':all(v>0 for v in min_areas.values())}
    baseline=[]
    for a in ANGLES:
        p=P/'exports/p15-129-ahoge-owner/nearest_key_owner'/(f'yaw{a:06.2f}'.replace('.','p')+'.png')
        baseline.append(rgba(p))
    metrics['baselineMaxAdjacentCompositeRGBMAE']=max(jumps(baseline))
    report={'schema':'KOMA_P15_140_CONTOUR_VDD_YAW_V1','characterId':'p0_character_001',
        'sourceAngles':list(KEYS),'samples':list(ANGLES),'meshVertexCount':len(positions[90.]),
        'meshTriangleCount':len(faces),'meshRoleDefinition':'24 shared polar outline rays, two inner rings and center; convex-hull shape correspondence',
        'positions':{str(a):positions[a].round(3).tolist() for a in KEYS},
        'sourceOwners':owners,'intermediateMinimumSignedArea':min_areas,'metrics':metrics,
        'sourceArtPreserved':True,'sourceVisibleMaskSemanticValidated':False,
        'paintedUnderlayPerViewAvailable':False,'trueStrandIdentityVerified':False,
        'fullYawVisualAccepted':False,'review':'private-assets/exports/p15-140-contour-yaw-mesh/index.html',
        'next':'Use painter-verified outlines and per-view underpaint to remove owner-switch pop and eye/neck seams; gate full 360 on continuous visual quality.'}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(315*5,349*3),(36,43,53));d=ImageDraw.Draw(board)
        for j,(name,sequence) in enumerate([('P15-129 reference',baseline),('Contour ArtMesh',render)]):
            for i,(angle,arr) in enumerate(zip(ANGLES,sequence)):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(arr,'RGBA'))
                board.paste(tile.convert('RGB').resize((309,309),Image.Resampling.LANCZOS),(315*i,349*j+30))
                d.text((315*i+6,349*j+7),f'{name} {angle:g}',fill='white')
                if j==1:Image.fromarray(arr,'RGBA').save(OUT/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
        for i,a in enumerate(KEYS):
            src=roles[a][0]
            tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(src,'RGBA'))
            draw=ImageDraw.Draw(tile)
            pos=positions[a]
            for f in faces:
                poly=[tuple(map(float,pt)) for pt in pos[f]]
                draw.line(poly+[poly[0]],fill=(0,235,238,155),width=1)
            board.paste(tile.convert('RGB').resize((309,309),Image.Resampling.LANCZOS),(315*i,349*2+30))
            d.text((315*i+5,349*2+6),f'Mesh {a:g}',fill='white')
        board.save(OUT/'comparison.jpg',quality=94)
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 contour ArtMesh yaw</title><style>body{font:16px system-ui;background:#202732;color:#eee}img{max-width:100%}</style><h2>90–112.5–135° common contour ArtMesh</h2><p>Same triangle IDs and polar view-dependent UV coordinates. Upper: prior source ownership; middle: source-owned deformed hair mesh; lower: source meshes. Per-view underpaint and anatomical correspondence pending.</p><img src="comparison.jpg">')
        E.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
if __name__=='__main__':
    q=run()
    print(json.dumps({'vertices':q['meshVertexCount'],'triangles':q['meshTriangleCount'],'minArea':q['intermediateMinimumSignedArea'],'metrics':q['metrics']},indent=2))
