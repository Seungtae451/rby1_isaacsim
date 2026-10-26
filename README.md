# Local NuRec → Isaac Sim / RBY1 Model A

회사 영상을 외부로 전송하지 않고 **영상 → COLMAP → 3DGUT → NuRec USDZ**로 변환하는 프로젝트입니다.

**현재 구현 범위:** 영상 재구성 전용 Docker와 Git/오프라인 전송 절차입니다. Isaac Sim 실행, RBY1 Model A 배치, Quest 컨트롤러·팔꿈치 retargeting, LeRobot 수집, 로봇 정책 학습은 **호스트 실행 대상으로 설계했으며 아직 구현되지 않았습니다.** 전체 설계는 [설계서](docs/superpowers/specs/2026-10-26-local-nurec-rby1-design.md)에 있습니다.

합성 영상 40프레임의 COLMAP 등록·3DGUT 100회 학습·USDZ 생성, 네트워크 없는 실행, 이미지 save/load를 검증했습니다. 실제 회사 영상과 호스트 Isaac Sim 렌더링은 미검증입니다. 자세한 결과는 [검증 기록](docs/verification.md)을 확인하세요.

## 이동할 파일

Git 저장소에는 소스·Dockerfile·스크립트·설정·문서만 저장합니다. **Git clone만으로 Docker 이미지가 생기지는 않습니다.** 인터넷이 없는 슈퍼컴에서는 여기서 빌드한 이미지 tar도 별도로 가져가야 합니다.

```text
Git:     코드 + Dockerfile + 실행 스크립트 + 문서
별도:    rby1-nurec.tar + SHA256SUMS + image-inspect.json
선택:    rby1-source.bundle (슈퍼컴에서 GitHub에 연결하지 못할 때)
회사 내: 원본 영상과 생성된 USDZ/로그/학습 산출물
```

영상·프레임·USDZ·데이터셋·인증서·모델 체크포인트·이미지 tar는 Git에 올리지 않습니다. 영상은 채팅 첨부 대신 회사 PC의 로컬 경로로 제공합니다.

## 1. 인터넷 가능한 준비 PC: 이미지 빌드

Linux x86_64, Docker, 충분한 디스크 공간이 필요합니다. 빌드 과정은 공개 패키지·소스·metric 모델 가중치를 다운로드합니다. **회사 영상은 빌드하지 않으며 빌드 컨텍스트는 재구성 코드만 허용합니다.**

```bash
git clone https://github.com/Seungtae451/rby1_isaacsim.git
cd rby1_isaacsim
bash scripts/build_image.sh
python3 -m unittest discover -s tests -v
```

CUDA 12.8.1 / PyTorch 2.8.0 / COLMAP 3.11.1 / 고정 commit의 3DGRUT를 사용합니다. COLMAP은 CUDA를 켜고 GUI 없이 빌드합니다. 장면 학습에 필요한 VGG/LPIPS 가중치는 빌드 때 이미지에 캐시합니다. 정확한 Python 패키지는 이미지의 `/opt/python-packages.txt`에 기록됩니다.

이미지에는 Isaac Sim, RBY1 자산, Quest 서버, LeRobot 또는 로봇 정책 학습 실행 환경을 넣지 않습니다. COLMAP/3DGRUT에 필요한 개발 도구는 첫 실행의 CUDA 확장 컴파일을 위해 포함합니다.

## 2. 이미지 전송본 생성

소스가 Git 커밋된 후 실행합니다. 대용량 이미지 파일은 Git 대신 회사가 승인한 저장장치/파일 전송 절차로 옮깁니다.

```bash
bash scripts/export_image.sh
# 기본 출력: outputs/transfer/
```

스크립트는 기존 전송본을 덮어쓰지 않습니다. 다른 출력 경로는 첫 인자로 지정합니다.

## 3. 회사 PC → 슈퍼컴

회사 PC에서 Git으로 소스를 받습니다. 소스 폴더와 전송 파일을 회사 내부 절차로 슈퍼컴에 옮깁니다. 슈퍼컴이 GitHub에 연결할 수 없다면 bundle로 동일한 소스를 복원할 수 있습니다.

```bash
# 인터넷 없는 슈퍼컴: 전달받은 transfer 폴더에서
sha256sum -c SHA256SUMS
docker load -i rby1-nurec.tar
git clone rby1-source.bundle rby1_isaacsim
cd rby1_isaacsim
docker image inspect rby1-nurec:local --format '{{.Id}}'
```

슈퍼컴에도 NVIDIA 드라이버와 NVIDIA Container Toolkit, Docker 사용 권한이 필요합니다. CUDA 12.8/PyTorch 및 해당 GPU가 지원되는 환경이어야 합니다. 이 이미지의 사전 컴파일 대상은 SM80/86/89/90/120입니다. ARM 서버·SM100 GPU·Docker 사용이 금지된 스케줄러 환경은 별도 빌드/운영 검증이 필요합니다. 16GB GPU 두 장은 자동으로 단일 32GB GPU가 되지 않으며 기본 실행은 GPU 한 장입니다.

## 4. 영상 재구성: 네트워크 없이 실행

영상은 주변을 이동하면서 다양한 시점으로 촬영합니다. 회전만 하는 파노라마·심한 흔들림·반사면·움직이는 물체·겹침이 부족한 영상은 실패할 수 있습니다. 처음에는 작은 방의 20–60초 영상으로 검증하세요. 동일한 렌즈와 일관된 초점·노출을 권장합니다.

```bash
python3 scripts/reconstruct.py \
  --video /company/videos/room.mp4 \
  --output /company/reconstruction/room-001 \
  --gpu 0
```

`--output`은 **아직 없는 job 디렉터리**여야 합니다. 부모 디렉터리는 해당 재구성 작업 전용으로 사용하세요. 원본 영상이 출력 부모 디렉터리 아래에 있으면 쓰기 마운트로 원본이 노출되므로 실행을 거절합니다. Docker에는 영상 파일 하나를 읽기 전용으로, 출력 부모 디렉터리만 쓰기 가능하게 마운트합니다. 컨테이너는 `--network=none --pull=never --cap-drop=ALL`로 실행하며 영상 업로드·런타임 패키지 다운로드를 하지 않습니다. 실행할 명령만 확인하려면 `--dry-run`을 추가합니다.

초당 2프레임·최대 폭 1600으로 시작합니다. 최소 30장, 하나의 COLMAP 모델에 80% 이상 등록되어야 학습으로 진행합니다. 기본 학습은 30,000회입니다. `--iterations 100`은 연결 확인용이며 최종 품질 검증을 대신하지 않습니다. 첫 실행은 Slang/CUDA 확장 컴파일로 시간이 더 걸리며 출력 부모의 `.torch_extensions/`에 캐시됩니다.

```text
room-001/
  images/             추출 프레임 (회사 내부 보관)
  database.db         COLMAP 특징·매칭
  sparse/0/           선택된 희소 재구성
  training/           장면 체크포인트·학습 로그
  scene.usdz          Isaac Sim에서 불러올 NuRec 환경
  manifest.json       입력 SHA256·등록 수·소스 commit·미검증 정렬 상태
  pipeline.log        단계별 로컬 로그
```

실패한 job은 보존합니다. `pipeline.log`를 로컬에서 확인하고 새로운 출력 경로로 재시도하세요. 영상·프레임·로그를 외부 이슈에 첨부하지 마세요.

## 5. 로컬 호스트의 Isaac Sim에 로딩

생성된 `scene.usdz`를 회사 내부에서 Isaac Sim PC로 옮겨 **호스트의 Isaac Sim**에서 불러옵니다. NuRec 지원 Isaac Sim과 로컬로 준비된 확장/자산이 필요합니다. 이후 RBY1은 공식 저장소의 **Model A v1.2**를 사용하도록 설계했습니다.

단안 재구성은 실제 길이와 바닥 방향을 보장하지 않습니다. 알려진 실제 길이로 scale을 맞추고 바닥이 Z-up 및 z=0에 놓이도록 정렬해야 합니다. Gaussian 자산에는 자동 충돌체가 없습니다. 바닥·벽·작업대 proxy와 조작할 물체의 물리를 별도로 준비해야 합니다. 영상 하나만 넣으면 물리적으로 완성된 로봇 환경이 즉시 생긴다고 보장하지 않습니다.

Docker 밖의 Isaac Sim/Quest/학습과 Quest OS의 외부 송신 차단은 **회사 호스트 방화벽 및 WAN 차단 AP/VLAN**에서 적용해야 합니다. offline 환경 변수만으로 호스트 전체의 통신을 차단할 수 없습니다.

## 검증 기록과 출처

- [실행 검증 기록](docs/verification.md)
- [이번 전달 작업의 실행 계획](docs/superpowers/plans/2026-10-27-offline-reconstruction.md)
- [NVIDIA 단안 재구성 공식 문서](https://docs.nvidia.com/nurec/robotics/neural_reconstruction_mono.html)
- [NVIDIA 3DGRUT](https://github.com/nv-tlabs/3dgrut) — Apache-2.0, 이미지 내 원본 LICENSE 보존
- [COLMAP](https://github.com/colmap/colmap) — 원본 라이선스 이미지 내 설치/소스 기록 참조
- [RBY1 공식 시뮬레이터](https://github.com/RainbowRobotics/rby1-sim-isaac)
- [RBY1 공식 SDK/URDF](https://github.com/RainbowRobotics/rby1-sdk)

독립적인 재구성 경로만 사용할 때 `scripts/fetch_sources.py`는 필요하지 않습니다. 이 스크립트는 이후 호스트 RBY1 통합에 사용할 공개 소스들을 `external.lock.json`의 버전으로 준비하는 용도입니다.
