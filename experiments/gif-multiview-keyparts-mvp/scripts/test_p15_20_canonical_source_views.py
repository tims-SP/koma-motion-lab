import hashlib,json,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parent.parent
P=R/'private-assets';D=P/'p15-20-canonical-source-views'
Q=json.loads((D/'qa.json').read_text())
class CanonicalSourceViews(unittest.TestCase):
 def test_character_and_13_slots_each(self):
  self.assertEqual(Q['characterId'],'p0_character_001')
  self.assertEqual(Q['viewCount'],3);self.assertEqual(Q['partCount'],39)
  self.assertEqual(len(Q['semanticSlots']),13)
  for v in Q['views']:self.assertEqual(len(v['parts']),13)
 def test_every_part_is_byte_exact_to_source(self):
  for v in Q['views']:
   for p in v['parts']:
    src=P/p['sourcePath'];dst=P/p['path']
    self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),p['sha256'])
    if p['sourceManifestRecordedSHA256']:
     self.assertEqual(p['sourceManifestRecordedSHA256'],p['sha256'])
    self.assertEqual(hashlib.sha256(dst.read_bytes()).hexdigest(),p['sha256'])
    with Image.open(dst) as im:self.assertEqual((im.size,im.mode),((1024,1024),'RGBA'))
 def test_front_side_ahoge_clip_are_not_missing(self):
  v=Q['views'][0];parts={x['semanticId']:x for x in v['parts']}
  for name in ['hair.side','hair.ahoge','hair.clip.cross_gold']:
   self.assertGreater(parts[name]['alphaPixelsGt16'],1000)
 def test_yaw45_side_hair_and_ahoge_exist(self):
  v=Q['views'][1];parts={x['semanticId']:x for x in v['parts']}
  for name in ['hair.side','hair.ahoge','hair.clip.cross_gold','eye.far']:
   self.assertGreater(parts[name]['alphaPixelsGt16'],1000)
 def test_yaw90_hidden_parts_match_manifest(self):
  v=Q['views'][2];parts={x['semanticId']:x for x in v['parts']}
  for name in ['eye.far','ear.far','hair.clip.cross_gold']:
   self.assertEqual(parts[name]['visibility'],'hidden')
   self.assertEqual(parts[name]['alphaPixelsGt16'],0)
  for name in ['hair.side','hair.ahoge','hair.back']:
   self.assertGreater(parts[name]['alphaPixelsGt16'],1000)
 def test_not_misrepresented_as_new_paint(self):
  self.assertFalse(Q['newPaintingCreated'])
  self.assertFalse(Q['mirroringOrGeometricTransformation'])
  self.assertFalse(Q['artisticAcceptance'])
if __name__=='__main__':unittest.main()
