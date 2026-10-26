"""Video -> COLMAP -> local 3DGUT -> NuRec USDZ. Run inside network=none."""
import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import zipfile
from pathlib import Path


def commands(video, job, grut, python, iterations=30000):
    images, sparse = job / 'images', job / 'sparse'
    def value(path):
        if '${' in str(path):
            raise ValueError('Hydra interpolation is not allowed in job paths')
        return json.dumps(str(path), ensure_ascii=False)
    return [
        ['ffmpeg', '-nostdin', '-v', 'error', '-i', str(video), '-vf',
         "fps=2,scale=w='min(1600,iw)':h=-2", '-q:v', '2', str(images / '%06d.jpg')],
        ['colmap', 'feature_extractor', '--database_path', str(job / 'database.db'),
         '--image_path', str(images), '--ImageReader.single_camera', '1',
         '--ImageReader.camera_model', 'PINHOLE', '--SiftExtraction.use_gpu', '1'],
        ['colmap', 'sequential_matcher', '--database_path', str(job / 'database.db'),
         '--SiftMatching.use_gpu', '1'],
        ['colmap', 'mapper', '--database_path', str(job / 'database.db'),
         '--image_path', str(images), '--output_path', str(sparse)],
        [python, str(grut / 'train.py'), '--config-name', 'apps/colmap_3dgut_mcmc.yaml',
         f'path={value(job)}', f'out_dir={value(job / "training")}', 'experiment_name=scene',
         f'n_iterations={iterations}', 'num_workers=4', 'test_last=false',
         'use_wandb=false', 'with_gui=false', 'with_viser_gui=false',
         'export_usd.enabled=true', 'export_usd.format=nurec',
         f'export_usd.path={value(job / "scene.usdz")}',
         'export_usd.apply_normalizing_transform=false'],
    ]


def registered_images(path):
    ids = set()
    pose_line = True
    for line in path.read_text().splitlines():
        if line.startswith('#'):
            continue
        if not pose_line:
            pose_line = True
            continue
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 10:
            raise ValueError(f'Malformed COLMAP pose in {path}')
        image_id, camera_id = int(parts[0]), int(parts[8])
        values = [float(x) for x in parts[1:8]]
        if (image_id <= 0 or camera_id <= 0 or image_id in ids
                or not all(math.isfinite(x) for x in values)
                or abs(sum(x*x for x in values[:4]) - 1) > .01):
            raise ValueError(f'Invalid COLMAP pose in {path}')
        ids.add(image_id)
        pose_line = False
    if not pose_line:
        raise ValueError(f'Missing COLMAP observations line in {path}')
    return len(ids)


def select_model(job):
    models = sorted(p for p in (job / 'sparse').iterdir() if p.is_dir() and p.name.isdigit())
    if not models:
        raise ValueError('COLMAP produced no model; see pipeline.log')
    counts = {p: registered_images(p / 'images.txt') for p in models}
    best = max(counts, key=counts.get)
    registered = counts[best]
    total = len(list((job / 'images').glob('*.jpg')))
    if registered < 30 or registered / max(total, 1) < .8:
        raise ValueError(f'Only {registered}/{total} images registered in one model; recapture')
    if best.name != '0':
        zero = job / 'sparse/0'
        if zero.exists():
            zero.rename(job / 'sparse/rejected-0')
        best.rename(zero)
    return total, registered


def validate_usdz(path):
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if (not entries or Path(entries[0].filename).suffix not in ('.usd', '.usda', '.usdc')
                    or entries[0].file_size == 0 or archive.testzip() is not None):
                raise ValueError('USDZ has no valid root USD layer')
    except (zipfile.BadZipFile, OSError) as exc:
        raise ValueError(f'Invalid USDZ: {path}') from exc


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video', type=Path, required=True)
    p.add_argument('--job', type=Path, required=True)
    p.add_argument('--grut', type=Path, default=Path('/opt/3dgrut'))
    p.add_argument('--python', default='/opt/venv/bin/python')
    p.add_argument('--iterations', type=int, default=30000)
    p.add_argument('--plan', action='store_true', help='Print commands without reading video or writing data')
    args = p.parse_args()
    video, job = args.video.resolve(), args.job.resolve()
    if args.iterations < 1:
        p.error('--iterations must be positive')
    cmds = commands(video, job, args.grut, args.python, args.iterations)
    if args.plan:
        print(json.dumps(cmds, indent=2)); return
    if not video.is_file():
        raise FileNotFoundError(video)
    for exe in ('ffmpeg', 'colmap', args.python):
        if not shutil.which(exe):
            raise RuntimeError(f'Missing executable: {exe}')
    # Existing jobs are retained even on failure; never overwrite original data.
    job.mkdir(parents=True, exist_ok=False)
    (job / 'images').mkdir(); (job / 'sparse').mkdir()
    os.environ.update(QT_QPA_PLATFORM='offscreen', WANDB_MODE='disabled', HF_HUB_OFFLINE='1',
                      HF_DATASETS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
    with (job / 'pipeline.log').open('w') as log:
        for cmd in cmds[:-1]:
            log.write(json.dumps(cmd) + '\n'); log.flush()
            subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
            if cmd[0] == 'ffmpeg' and len(list((job / 'images').glob('*.jpg'))) < 30:
                raise ValueError('Need at least 30 sampled frames (15s); inspect capture quality')
        models = sorted(x for x in (job / 'sparse').iterdir() if x.is_dir() and x.name.isdigit())
        for model in models:
            subprocess.run(['colmap', 'model_converter', '--input_path', str(model),
                            '--output_path', str(model), '--output_type', 'TXT'],
                           check=True, stdout=log, stderr=subprocess.STDOUT)
        total, registered = select_model(job)
        log.write(json.dumps(cmds[-1]) + '\n'); log.flush()
        subprocess.run(cmds[-1], check=True, cwd=args.grut, stdout=log, stderr=subprocess.STDOUT)
    validate_usdz(job / 'scene.usdz')
    digest = hashlib.sha256()
    with video.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    (job / 'manifest.json').write_text(json.dumps({
        'video_sha256': digest.hexdigest(), 'frames': total, 'registered': registered,
        'iterations': args.iterations,
        'grut_commit': Path('/opt/grut-commit.txt').read_text().strip()
        if Path('/opt/grut-commit.txt').is_file() else 'unknown',
        'asset': 'scene.usdz', 'metric_alignment_verified': False,
        'collision_geometry': False,
    }, indent=2) + '\n')
    print(f'Created {job / "scene.usdz"}; verify scale, floor and collisions before teleoperation.')


if __name__ == '__main__':
    main()
