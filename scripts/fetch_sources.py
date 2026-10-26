"""Online preparation only. Never mounts or reads user data."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for name, source in json.loads((root / 'external.lock.json').read_text()).items():
    dest = root / 'external' / name
    if not dest.exists():
        subprocess.run(['git', 'clone', source['url'], str(dest)], check=True)
    actual = subprocess.check_output(['git', '-C', str(dest), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != source['commit']:
        if subprocess.check_output(['git', '-C', str(dest), 'status', '--porcelain']):
            raise RuntimeError(f'{dest}: local modifications; refusing checkout')
        subprocess.run(['git', '-C', str(dest), 'fetch', 'origin', source['commit']], check=True)
        subprocess.run(['git', '-C', str(dest), 'checkout', '--detach', source['commit']], check=True)
    if name == '3dgrut':
        subprocess.run(['git', '-C', str(dest), 'submodule', 'update', '--init', '--recursive'], check=True)
    print(name, source['commit'])
