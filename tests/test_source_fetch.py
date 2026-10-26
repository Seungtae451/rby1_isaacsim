import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceFetchTests(unittest.TestCase):
    def test_new_clone_at_pinned_head_has_working_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / 'origin'; source.mkdir()
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            subprocess.run(['git', '-C', str(source), 'config', 'user.name', 'Test'], check=True)
            subprocess.run(['git', '-C', str(source), 'config', 'user.email', 'test@example.invalid'], check=True)
            (source / 'LICENSE').write_text('fixture')
            subprocess.run(['git', '-C', str(source), 'add', 'LICENSE'], check=True)
            subprocess.run(['git', '-C', str(source), 'commit', '-qm', 'fixture'], check=True)
            commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
            project = base / 'project'; (project / 'scripts').mkdir(parents=True)
            script = project / 'scripts/fetch_sources.py'
            script.write_bytes((ROOT / 'scripts/fetch_sources.py').read_bytes())
            (project / 'external.lock.json').write_text(json.dumps({
                'fixture': {'url': str(source), 'commit': commit}}))
            result = subprocess.run([sys.executable, str(script)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project / 'external/fixture/LICENSE').is_file(), 'Pinned clone was not checked out')


if __name__ == '__main__':
    unittest.main()
