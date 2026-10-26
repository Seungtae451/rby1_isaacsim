#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
task_dest=${1:-"$task_root/outputs/transfer"}
mkdir -p "$task_dest"
task_dest=$(cd -- "$task_dest" && pwd)
for task_file in rby1-nurec.tar rby1-source.bundle SHA256SUMS image-inspect.json; do
    if [[ -e "$task_dest/$task_file" ]]; then
        echo "Refusing to overwrite $task_dest/$task_file" >&2
        exit 1
    fi
done
docker image inspect rby1-nurec:local > "$task_dest/image-inspect.json"
docker save -o "$task_dest/rby1-nurec.tar.partial" rby1-nurec:local
mv "$task_dest/rby1-nurec.tar.partial" "$task_dest/rby1-nurec.tar"
git -C "$task_root" bundle create "$task_dest/rby1-source.bundle" --all
(cd -- "$task_dest" && sha256sum rby1-nurec.tar rby1-source.bundle image-inspect.json > SHA256SUMS)
echo "Transfer files: $task_dest"
