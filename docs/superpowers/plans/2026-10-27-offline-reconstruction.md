# Offline Reconstruction Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver Git-ready source and a locally built, offline-transferable Docker image that converts a video into a NuRec USDZ for host Isaac Sim.

**Architecture:** A standard-library Python CLI runs ffmpeg, COLMAP and pinned NVIDIA 3DGRUT in sequence. A Docker launcher enforces network isolation and narrowly scoped mounts. Source is versioned in Git; an image archive and checksum travel separately.

**Tech Stack:** Python unittest, Docker, CUDA 12.8, COLMAP, 3DGUT/NuRec.

**Spec:** `docs/superpowers/specs/2026-10-26-local-nurec-rby1-design.md`

## Global Constraints

- Docker only performs video reconstruction; no Isaac Sim application, RBY1, Quest, LeRobot or robot policy training in the image.
- Runtime `network=none`; source video read-only; existing output never overwritten.
- User videos, derived frames, reconstructions, datasets, certificates and image archives are never committed or uploaded.
- Host simulation/teleoperation/data collection remain the subsequent project milestone, not claimed implemented by this delivery.
- Existing sibling projects and running GPU processes are untouched.

## Review Focus

- Offline runtime needs metric weights cached before video is mounted.
- GPU feature extraction must work without an X server; Ubuntu's prebuilt COLMAP may lack CUDA.
- Partial or multiple COLMAP models must not silently train the wrong model.
- Docker runtime and host GPU may differ at the company; export sufficient provenance and clearly report compatibility limits.
- Build context and Git staging must exclude local data and credentials by construction.

### Task 1: Safe reconstruction CLI

**Files:** `rby1_local/reconstruct.py`, `tests/test_reconstruct.py`, `pyproject.toml`.

**Interfaces:** `commands(video, job, grut, python, iterations=30000)` returns argv lists; `select_model(job)` validates/selects largest model; CLI produces `scene.usdz`, manifest and pipeline log.

- [x] Add failing tests for model selection without model 0, corrupt COLMAP text, zero-byte/malformed USDZ, preservation of existing jobs and Hydra path metacharacters.
- [x] Run `python3 -m unittest discover -s tests -v`, observe expected failures.
- [x] Implement validation and orchestration, preserving inputs and failed jobs.
- [x] Run the suite; commit tested CLI.

### Task 2: Reconstruction-only image and isolated launcher

**Files:** `docker/Dockerfile`, `.dockerignore`, `scripts/reconstruct.py`, `scripts/build_image.sh`, `tests/test_launcher.py`.

**Interfaces:** host launcher takes `--video`, `--output`, optional image/GPU selection and `--dry-run`; mounts only one video and output parent. Build script produces `rby1-nurec:local` without access to private input directories.

- [x] Write failing launcher tests that inspect emitted argv for network none, read-only input and safe handling of paths, and reject invalid inputs/existing output.
- [x] Implement launcher with no shell interpolation; apply network none, cap-drop and no-new-privileges.
- [ ] Build pinned CUDA/COLMAP/3DGRUT image and precache VGG/LPIPS weights at build time. Verify actual GPU feature extraction and imports without networking.
- [ ] Use a generated synthetic video for an offline reconstruction integration check where practical. Log exact success/failure; do not claim a real room was tested.

### Task 3: Transfer and Git delivery

**Files:** `scripts/export_image.sh`, `README.md`, `docs/verification.md`, `.gitignore`, `AGENTS.md`.

**Interfaces:** exporter writes image tar, sha256 checksum and source bundle under ignored `outputs/transfer/`; README gives build, save/load, isolated run and host Isaac Sim import commands.

- [ ] Verify archive roundtrip with Docker load/inspect and checksum; test Git ignore behavior with local canary files.
- [ ] Record tested environment and all unresolved hardware/scene limitations.
- [ ] Initialize repository on a feature branch, stage explicit code/docs only, inspect staged file list and commit.
- [ ] Obtain a fresh whole-change review, address important findings with regressions and rerun checks.
- [ ] Push only if an explicitly identified remote is available; otherwise deliver local commit and bundle with exact push instructions.

## Execution ledger

- 2026-10-27: User directed preparation/build/Git delivery following the corrected Docker scope. Execute in this project directory, on a new feature branch; no separate worktree is needed for this previously empty project. Native execution selected to minimize setup and shared context; final review will use a fresh reviewer.
- Scope: this plan delivers the user's first-priority reconstruction and transfer milestone. The full RBY1/Quest/LeRobot host milestone remains pending and will be reported explicitly.
- Verification: context audit initially detected Python bytecode included through directory re-inclusion. Reproduced with a real Docker COPY build; tightened directory exclusions; second audit contains exactly the four allowed source/config files.
- Final review: fixed the Important writable-input alias finding; added `test_input_cannot_be_inside_writable_output_mount`, observed RED then GREEN; whole suite 10/10.
