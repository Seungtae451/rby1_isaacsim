# 검증 기록

상태: **영상 재구성 Docker와 오프라인 전송 검증 완료**. 실제 회사 영상 및 호스트 Isaac Sim 렌더링 검증은 아직 하지 않았다.

## 현재 확인한 사항

- Python 표준 라이브러리 테스트 10개 통과. COLMAP 모델 선택·손상된 pose·USDZ 검사·Hydra 경로 인코딩·기존 출력 보존·Docker 실행 인자·고정 소스 checkout을 확인했다. 원본 영상이 쓰기 가능한 출력 부모에 포함되는 경우의 실행 거부도 확인했다.
- `bash -n scripts/build_image.sh scripts/export_image.sh`와 Python compileall 통과.
- 실제 Docker `COPY .` 컨텍스트를 별도 scratch 빌드로 추출해 허용 파일 4개만 포함됨을 확인했다: Dockerfile, precache.py, 패키지 __init__.py, reconstruct.py. 영상 canary, external 자산, 호스트 스크립트, 인증서, Git 폴더는 포함되지 않는다.
- `git check-ignore`로 `data/`, `outputs/`, `external/`이 제외됨을 확인했다.
- `docker run --network none --gpus device=0`에서 RTX 5080과 NVIDIA 드라이버 580.95.05가 확인됐다. 이 확인은 CUDA 재구성 성공을 의미하지 않는다.
- 실제 회사 영상은 제공되거나 처리되지 않았다. 재구성용 합성 장면만 별도로 생성했다.
- 전체 이미지 빌드 완료: `rby1-nurec:local`, Docker image ID `sha256:a383c82178910649f45b7c10ec4306997c5739433540defac13e5ddc25a07fb9`.
- 일반 사용자 UID/GID, `network=none`, GPU 0에서 PyTorch `2.8.0+cu128`, 3DGUT trainer import 및 VGG/LPIPS 생성이 통과했다. 캐시된 metric 가중치를 사용했으며 외부 네트워크 인터페이스가 없음을 확인했다.
- 합성 영상 전체 파이프라인 종료 코드 0: 프레임 40장 중 40장 등록, 3DGUT 100회 학습, 1.6MiB의 `scene.usdz`와 manifest 생성. 학습용 train/val 분할 후 카메라 35개가 export됐다. 100회는 연결 확인용이며 최종 품질을 나타내지 않는다.
- 생성된 USDZ를 네트워크 없는 별도 컨테이너의 OpenUSD로 열었다. prim 7개와 `/World/gauss/gauss` Volume을 확인했다. 이 확인은 Isaac Sim RTX/NuRec 렌더링 검증과 구분한다.
- `docker save`로 약 11GB tar 생성, `sha256sum -c SHA256SUMS` 전체 통과, `docker load` 종료 코드 0. 다시 불러온 image ID가 빌드한 ID와 일치한다. 별도의 깨끗한 슈퍼컴에서 재현한 결과는 아니다.
- 별도 코드 검토에서 확인한 원본 영상의 쓰기 마운트 중복 문제는 실패 재현 테스트를 추가하고 수정했다. 소스는 사용자 지정 Git 원격의 `feat/offline-reconstruction` 브랜치에 저장했다.

## 로컬 증거 파일

아래 파일은 `outputs/`에만 보관하며 Git에 포함하지 않는다.

- `docker-build-resumed.log`: 재시작 후 캐시 재사용 및 최종 빌드 기록
- `offline-preflight.log`: GPU·import·metric 캐시 확인
- `integration/job-001/pipeline.log`, `manifest.json`, `scene.usdz`: 합성 영상 실행 결과
- `usdz-open-check.log`: OpenUSD로 Volume prim 확인
- `docker-load-check.log`: 이미지 archive load 결과
- `transfer/`: image tar, source bundle, image inspect, SHA256SUMS

## 남은 현장 검증과 알려진 한계

- 회사 영상의 재구성 품질, 실측 크기/바닥 정렬, host Isaac Sim NuRec 렌더링과 proxy 충돌.
- RBY1/Quest/LeRobot/로봇 정책 학습은 후속 호스트 구현 대상이며 이번 재구성 컨테이너에 포함되지 않는다.
- 슈퍼컴의 GPU 아키텍처·드라이버·Docker 사용 권한·스케줄러 및 회사 호스트/Quest 네트워크 차단은 현장에서 확인해야 한다.
- 첫 실행 시 CUDA/Slang 확장이 로컬에서 컴파일되며, 컴파일러의 unused-variable 경고와 자동 GPU 아키텍처 선택 안내가 있었다. 사용자 UID로 실행하면 upstream의 Git 소유권 확인 로그가 `Git hash: Unknown`으로 표시되지만 실행은 계속되며, 별도의 `manifest.json`에는 빌드 시 기록한 정확한 고정 commit이 남는다.

## 환경

2026-10-27, Linux x86_64, Docker Engine 29.9.2, Python 3.10.12(host), RTX 5080 16GB ×2, NVIDIA driver 580.95.05. 다른 GPU 작업은 종료하지 않았다.
