import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / 'scripts/reconstruct.py'


class LauncherTests(unittest.TestCase):
    def test_dry_run_is_isolated_and_preserves_paths(self):
        self.assertTrue(LAUNCHER.exists(), 'Host Docker launcher is missing')
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            video = base / 'input with spaces;$.mp4'
            video.touch()
            output = base / 'output with spaces'
            result = subprocess.run([sys.executable, str(LAUNCHER), '--video', str(video),
                                     '--output', str(output), '--dry-run'],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            cmd = json.loads(result.stdout)
            self.assertIn('--network=none', cmd)
            self.assertIn('--pull=never', cmd)
            self.assertIn('--cap-drop=ALL', cmd)
            self.assertIn('no-new-privileges', cmd)
            mounts = [cmd[i+1] for i, x in enumerate(cmd) if x == '--mount']
            self.assertEqual(len(mounts), 2)
            self.assertIn(f'type=bind,src={video},dst=/input/video,readonly', mounts)
            self.assertFalse(output.exists())

    def test_existing_output_is_preserved(self):
        self.assertTrue(LAUNCHER.exists())
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            video = base / 'input.mp4'; video.touch()
            output = base / 'job'; output.mkdir()
            sentinel = output / 'keep'; sentinel.write_text('private')
            result = subprocess.run([sys.executable, str(LAUNCHER), '--video', str(video),
                                     '--output', str(output), '--dry-run'], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(), 'private')


if __name__ == '__main__':
    unittest.main()
