import json,hashlib,unittest
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-32-mesh-vdd-qa.json').read_text())
B=json.loads((R/'evidence/p15-31-native-vdd-qa.json').read_text())
class MeshVdd(unittest.TestCase):
 def test_manifest_and_scope(self):
  self.assertEqual(Q['characterId'],'p0_character_001')
  self.assertEqual(len(Q['angles']),9)
  self.assertEqual(Q['meshRoles'],['eye.far','hair.clip.cross_gold','hair.side'])
  self.assertEqual(Q['meshGrid'],[7,7]);self.assertEqual(Q['trianglesPerRole'],72)
  self.assertTrue(Q['meshRolesAreImageDerived2DNotPhysical3D'])
 def test_keyframes_exact(self):
  for f in Q['angles']:
   if f['kind']!='exact-keyframe':continue
   b=next(x for x in B['frames'] if x['yaw']==f['yaw'])
   name='yaw'+(str(int(f['yaw'])) if float(f['yaw']).is_integer() else str(f['yaw']).replace('.','p'))
   p=P/'p15-32-mesh-vdd'/name/'composite.png'
   self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),hashlib.sha256((P/b['composite']).read_bytes()).hexdigest())
 def test_midpoint_geometry(self):
  mids=[x for x in Q['angles'] if x['kind']=='mesh-deformed-midpoint']
  self.assertEqual([x['yaw'] for x in mids],[56.25,58.75,61.25,63.75])
  for f in mids:
   self.assertEqual(set(f['meshDiagnostics']),set(Q['meshRoles']))
   for d in f['meshDiagnostics'].values():
    self.assertEqual(d['triangles'],72)
    self.assertGreater(d['forward']['meanPx'],0)
    self.assertLess(d['forward']['maxPx'],42)
    self.assertEqual(d['forward']['triangleFlipCount'],0)
    self.assertGreater(d['forward']['minTriangleAreaRatio'],.5)
 def test_parts_dimensions_and_alpha(self):
  for f in Q['angles']:
   name='yaw'+(str(int(f['yaw'])) if float(f['yaw']).is_integer() else str(f['yaw']).replace('.','p'))
   folder=P/'p15-32-mesh-vdd'/name
   self.assertTrue((folder/'composite.png').exists())
   for role in ['eye.far','hair.clip.cross_gold','hair.side']:
    with Image.open(folder/(role+'.png')) as im:
     self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(443,443))
     self.assertGreater(np.asarray(im)[:,:,3].sum(),0)
 def test_nonmesh_roles_unchanged_at_midpoint(self):
  roles=[p['role'] for p in B['frames'][1]['parts'] if p['role'] not in Q['meshRoles']]
  for y in [56.25,58.75,61.25,63.75]:
   f=next(x for x in B['frames'] if x['yaw']==y)
   name='yaw'+str(y).replace('.','p')
   for role in roles:
    a=np.asarray(Image.open(P/'p15-32-mesh-vdd'/name/(role+'.png')).convert('RGBA'))
    b=np.asarray(Image.open(P/next(x['path'] for x in f['parts'] if x['role']==role)).convert('RGBA'))
    self.assertTrue(np.array_equal(a,b),role)
 def test_mesh_changes_vs_previous_interpolation(self):
  for y in [56.25,58.75,61.25,63.75]:
   name='yaw'+str(y).replace('.','p')
   for role in Q['meshRoles']:
    a=np.asarray(Image.open(P/'p15-32-mesh-vdd'/name/(role+'.png')).convert('RGBA'))
    b=np.asarray(Image.open(P/'p15-31-per-role-vdd'/name/(role+'.png')).convert('RGBA'))
    self.assertGreater(np.count_nonzero(np.any(a!=b,axis=2)),10)
 def test_review_archive_integrity(self):
  import zipfile
  with zipfile.ZipFile(P/'exports/p15-32-mesh-vdd-review.zip') as z:
   self.assertIsNone(z.testzip());self.assertIn('index.html',z.namelist())
if __name__=='__main__':unittest.main()
