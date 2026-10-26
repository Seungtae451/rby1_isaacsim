import tempfile
import unittest
import zipfile
from pathlib import Path

from rby1_local import reconstruct as r


class ReconstructionTests(unittest.TestCase):
    def test_rejects_corrupt_colmap_pose(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'images.txt'
            path.write_text('# header\n1 nan 0 0 0 0 0 0 1 000001.jpg\n\n')
            with self.assertRaises(ValueError):
                r.registered_images(path)

    def test_counts_images_with_empty_observation_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'images.txt'
            path.write_text('# header\n1 1 0 0 0 0 0 0 1 000001.jpg\n\n'
                            '2 1 0 0 0 0 0 0 1 000002.jpg\n1.5 2.5 -1\n')
            self.assertEqual(r.registered_images(path), 2)

    def test_largest_model_is_promoted_when_zero_is_missing(self):
        self.assertTrue(hasattr(r, 'select_model'), 'Model selection must be callable independently')
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / 'images').mkdir()
            for i in range(40):
                (job / 'images' / f'{i:06d}.jpg').touch()
            for name, count in [('2', 10), ('7', 35)]:
                model = job / 'sparse' / name
                model.mkdir(parents=True)
                (model / 'images.txt').write_text(''.join(
                    f'{i+1} 1 0 0 0 0 0 0 1 {i:06d}.jpg\n\n' for i in range(count)))
                (model / 'points3D.bin').write_bytes(name.encode())
            self.assertEqual(r.select_model(job), (40, 35))
            self.assertEqual((job / 'sparse/0/points3D.bin').read_bytes(), b'7')
            self.assertTrue((job / 'sparse/2').exists())

    def test_low_registration_is_rejected_without_moving_models(self):
        self.assertTrue(hasattr(r, 'select_model'))
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / 'images').mkdir()
            for i in range(40):
                (job / 'images' / f'{i:06d}.jpg').touch()
            model = job / 'sparse/2'
            model.mkdir(parents=True)
            (model / 'images.txt').write_text('1 1 0 0 0 0 0 0 1 000001.jpg\n\n')
            with self.assertRaises(ValueError):
                r.select_model(job)
            self.assertTrue(model.exists())
            self.assertFalse((job / 'sparse/0').exists())

    def test_empty_or_non_usd_zip_is_rejected(self):
        self.assertTrue(hasattr(r, 'validate_usdz'))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'scene.usdz'
            path.touch()
            with self.assertRaises(ValueError):
                r.validate_usdz(path)
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('random.txt', 'not a scene')
            with self.assertRaises(ValueError):
                r.validate_usdz(path)

    def test_hydra_paths_are_quoted_as_literal_values(self):
        cmds = r.commands(Path('/input/video.mp4'), Path('/output/room [1],test'),
                          Path('/opt/3dgrut'), '/opt/venv/bin/python')
        self.assertIn('path="/output/room [1],test"', cmds[-1])


if __name__ == '__main__':
    unittest.main()
