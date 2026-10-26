"""Host launcher: video reconstruction only, with Docker networking disabled."""
import argparse
import json
import os
import subprocess
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True, help='New job directory; never overwritten')
    p.add_argument('--image', default='rby1-nurec:local')
    p.add_argument('--gpu', default='0', help='One GPU index or UUID')
    p.add_argument('--iterations', type=int, default=30000)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    video, output = args.video.resolve(), args.output.resolve()
    if not video.is_file():
        p.error('Video must be an existing local file')
    if output.exists():
        p.error('Output already exists; choose a new directory')
    if video.is_relative_to(output.parent):
        p.error('Video must be outside the writable output parent; choose a dedicated output folder')
    if any(',' in str(x) or '\n' in str(x) for x in (video, output)):
        p.error('Docker bind mount paths cannot contain commas or newlines')
    if not args.gpu or any(c in args.gpu for c in ',"\n'):
        p.error('Select a single GPU index or UUID')
    if args.iterations < 1:
        p.error('Iterations must be positive')
    cmd = ['docker', 'run', '--rm', '--pull=never', '--network=none', '--cap-drop=ALL',
           '--security-opt', 'no-new-privileges', '--gpus', f'device={args.gpu}',
           '--shm-size=2g', '--user', f'{os.getuid()}:{os.getgid()}',
           '--env', 'HOME=/tmp', '--env', 'XDG_CACHE_HOME=/tmp/.cache',
           '--env', 'TORCH_CUDA_ARCH_LIST=', '--env', 'TORCH_EXTENSIONS_DIR=/output/.torch_extensions',
           '--mount', f'type=bind,src={video},dst=/input/video,readonly',
           '--mount', f'type=bind,src={output.parent},dst=/output',
           args.image, '--video', '/input/video', '--job', f'/output/{output.name}',
           '--iterations', str(args.iterations)]
    if args.dry_run:
        print(json.dumps(cmd, ensure_ascii=False, indent=2)); return
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    main()
