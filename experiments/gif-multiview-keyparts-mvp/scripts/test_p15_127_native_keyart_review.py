import importlib.util
import unittest
from pathlib import Path
from PIL import Image

script=Path(__file__).with_name('p15_127_native_keyart_review.py')
spec=importlib.util.spec_from_file_location('p15_127_native_keyart_review',script)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestNativeSource(unittest.TestCase):
    def test_generator_and_provenance(self):
        result=module.audit(save=False)
        self.assertTrue(result['actualNativeToolInvoked'])
        self.assertTrue(result['independentNativeRasterConfirmed'])
        self.assertFalse(result['geometryAndIdentityArtistApproved'])
        self.assertEqual(len(result['nativeSHA256']),64)

    def test_scale_and_native_preservation(self):
        original=module.GEN/'yaw112p5-native.png'
        digest=module.sha(original)
        with Image.open(original) as im:
            self.assertEqual(im.size,(1254,1254))
        self.assertEqual(module.registered().shape,(443,443,4))
        self.assertEqual(module.sha(original),digest)

if __name__=='__main__':unittest.main()
