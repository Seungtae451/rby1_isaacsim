#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$task_root"
docker build --progress=plain -f docker/Dockerfile -t rby1-nurec:local "$@" .
