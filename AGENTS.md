# Project instructions

- Apply Superpowers and Ponytail full alongside the user's personal defaults.
- Docker only converts local videos into NuRec USDZ environment assets. Isaac Sim execution, RBY1 Model A, Quest, LeRobot and robot policy training run on the host.
- Never send user videos, frames, datasets or derived scenes to external services or tools. Ask for a local path, not a chat upload. Do not include private inputs in Git or Docker builds.
- Preserve existing jobs and source videos. Reconstruct under `--network=none` with only read-only input and local output mounts.
- Run `python3 -m unittest discover -s tests -v` for the Python suite. Record actual Docker/GPU evidence separately from unit tests.
