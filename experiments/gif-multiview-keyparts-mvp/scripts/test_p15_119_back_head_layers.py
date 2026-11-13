import importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('p15_119_back_head_layers.py')
s=importlib.util.spec_from_file_location('p15_119_back_head_layers',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestBackLayers(unittest.TestCase):
    def test_exact_recomposition(self):
        for angle in (135,180):
            result=m.split(angle,save=False)
            self.assertTrue(result['pixelRecompositionExact'])
            self.assertEqual(result['partOverlapPixels'],0)
            self.assertGreater(result['pinkClassifiedPixelCount'],1000)
            self.assertGreater(result['remainingVisiblePixelCount'],1000)
    def test_source_is_available(self):
        self.assertTrue((m.P/'extracted/whole/yaw135.png').exists())
        self.assertTrue((m.P/'extracted/whole/yaw180.png').exists())
if __name__=='__main__':unittest.main()
