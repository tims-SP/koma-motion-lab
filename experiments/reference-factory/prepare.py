"""Pinned source fetch, genuine Aka identity preparation and inspectable M0 freeze.

No runtime parity or approved hidden-design claim is made by this preparer.
"""
from pathlib import Path
import hashlib, importlib.util, json, struct, subprocess, uuid
import numpy as np

ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    lock=json.loads((ROOT/'sources.lock.json').read_text())
    source=ROOT/'out/source';source.mkdir(parents=True,exist_ok=True)
    for item in lock['sources']:
        p=source/item['file']
        if not p.exists():
            subprocess.run(['curl','-fsSL','--retry','2','--max-time','180',item['url'],'-o',str(p)],check=True)
        if sha(p)!=item['sha256']:raise ValueError('Pinned source mismatch: '+item['file'])
    spec=importlib.util.spec_from_file_location('prepare_aka8',ROOT.parent/'koma-25d-core/tools/prepare_aka8.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    identity=ROOT/'out/identity';module.main(source/'tutorial-aka.psd',identity)
    m=json.loads((identity/'reference_manifest.json').read_text())
    # Record the exact rounded resize and integer paste used by the source preparer.
    l,t,r,b=m['original_psd_subject_bbox'];ratio=min(1024/(r-l),1024/(b-t))
    w,h=round((r-l)*ratio),round((b-t)*ratio);sx,sy=w/(r-l),h/(b-t)
    px,py=(1024-w)//2,(1024-h)//2
    matrix=np.array([[sx,0,px-l*sx],[0,sy,py-t*sy],[0,0,1]],float)
    points=np.array([[l,t,1],[r,b,1],[(l+r)/2,(t+b)/2,1]],float).T
    inverse=np.linalg.inv(matrix)
    error=float(np.abs(inverse@matrix@points-points).max())
    assert error<1e-9
    bdata=(source/'Aka.inx').read_bytes();n=struct.unpack('>I',bdata[8:12])[0]
    model=json.loads(bdata[12:12+n]);nodes=[]
    def visit(node,parent=None):
        mesh=node.get('mesh')
        record={'source_node_uuid':node.get('uuid'),'parent_uuid':parent,'name':node.get('name'),'type':node.get('type')}
        if mesh:
            raw=json.dumps(mesh,sort_keys=True,separators=(',',':')).encode()
            record.update(topology_and_uv_sha256=hashlib.sha256(raw).hexdigest(),texture_ids=node.get('textures'),vertex_count=len(mesh['verts']),index_count=len(mesh['indices']))
        nodes.append(record)
        for child in node.get('children',[]) or []:visit(child,node.get('uuid'))
    visit(model['nodes'])
    vrm=(source/'reference.vrm').read_bytes();vn=struct.unpack_from('<I',vrm,12)[0];vj=json.loads(vrm[20:20+vn])
    vmeta=vj['extensions']['VRMC_vrm']['meta']
    assert vmeta['allowRedistribution'] and vmeta['modification']=='allowModificationRedistribution'
    # PSD tile identities are independent of INX node identity until correspondence is validated.
    for part in m['parts']:
        part['semantic_uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'koma:Aka:PSD:'+part['part_id']))
        part['inx_correspondence']='NOT_VALIDATED'
    m['view_direction']='FRONT_SOURCE; positive target yaw must point nose to image right'
    m['approval_state']='REVIEWED_SOURCE_REFERENCE'
    dump(identity/'reference_manifest.json',m)
    freeze={'schema':'koma-source-freeze/1','character':'Aka','scope':'HEAD_ONLY',
      'source_lock_sha256':sha(ROOT/'sources.lock.json'),'contract_sha256':sha(ROOT/'contract.json'),
      'identity_file':'identity/source_A_aka_front.png','identity_sha256':sha(identity/'source_A_aka_front.png'),
      'source_pose':'PSD stored default composition; open mouth, not neutral expression',
      'source_runtime_pose':{'HeadYaw_raw':[0,0],'full_front_parity':'NOT_TESTED'},
      'canonicalization':{'coordinate_domain':'continuous pixel EDGE coordinates, centers at i+0.5','crop_source_xyxy':[l,t,r,b],'resized_wh':[w,h],'paste_xy':[px,py],
        'source_to_canonical':matrix.tolist(),'canonical_to_source':inverse.tolist(),'roundtrip_error_px':error,
        'reversibility':'coordinate mapping only; crop/resampling lose pixels; immutable original PSD retained'},
      'character_facts':['orange bob hair','two tall fox ears with light inner fur','red/pink leaf ornament near crown','pink/red eyes with gold highlights','dark neck band','source mouth open; do not label neutral'],
      'source_node_count':len(nodes),'source_artmesh_count':sum('topology_and_uv_sha256' in x for x in nodes),
      'vrm_embedded_license':vmeta,'artifacts':[{'id':p['file'],'sha256':p['sha256'],'retrieval_uri':p['url'],'retention':'pinned upstream plus local workspace cache; independent owner-controlled archive NOT_TESTED','state':'SOURCE_TRUTH'} for p in lock['sources']],
      'gates':{'M0_source_freeze':'PASS_WITH_OPEN_FULL_FRONT_GATE','M1_source_bank':'PARTIAL_ONE_VRM_SAMPLE','M3_decomposition_benchmark':'NOT_TESTED','M4_ABCD':'NOT_TESTED','GOLDEN_90':'BLOCKED_HUMAN_REVIEW','FULL_FRONT_SOURCE_PARITY':'NOT_TESTED'}}
    dump(ROOT/'out/source_freeze.json',freeze);dump(ROOT/'out/native_topology_index.json',nodes)
    print(json.dumps({'source_sha_check':'PASS','coordinate_roundtrip_error_px':error,'native_artmeshes':freeze['source_artmesh_count']}))
if __name__=='__main__':main()
