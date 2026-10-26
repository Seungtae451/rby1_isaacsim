# 검증 기록

상태: **진행 중**. 이 문서는 검증 완료 주장과 미검증 항목을 구분하며 실제 Docker/GPU 결과로 갱신한다.

## 현재 확인한 사항

- Python 표준 라이브러리 테스트 9개 통과. COLMAP 모델 선택·손상된 pose·USDZ 검사·Hydra 경로 인코딩·기존 출력 보존·Docker 실행 인자·고정 소스 checkout을 확인했다.
- `bash -n scripts/build_image.sh scripts/export_image.sh`와 Python compileall 통과.
- 실제 Docker `COPY .` 컨텍스트를 별도 scratch 빌드로 추출해 허용 파일 4개만 포함됨을 확인했다: Dockerfile, precache.py, 패키지 __init__.py, reconstruct.py. 영상 canary, external 자산, 호스트 스크립트, 인증서, Git 폴더는 포함되지 않는다.
- `git check-ignore`로 `data/`, `outputs/`, `external/`이 제외됨을 확인했다.
- `docker run --network none --gpus device=0`에서 RTX 5080과 NVIDIA 드라이버 580.95.05가 확인됐다. 이 확인은 CUDA 재구성 성공을 의미하지 않는다.
- 실제 회사 영상은 제공되거나 처리되지 않았다. 재구성용 합성 장면만 별도로 생성했다.

## 남은 실행 검증

- 전체 Docker 이미지 빌드와 오프라인 import/metric 가중치 캐시 확인.
- 합성 영상의 CUDA COLMAP → 3DGUT → NuRec USDZ 연결 검증.
- 이미지 tar 저장, checksum 및 Docker load 확인.
- 회사 영상의 품질, 크기/바닥 정렬, host Isaac Sim NuRec 렌더링.
- RBY1/Quest/LeRobot/로봇 정책 학습은 후속 호스트 구현 대상이며 이번 재구성 컨테이너에 포함되지 않는다.

## 환경

2026-10-27, Linux x86_64, Docker Engine 29.9.2, Python 3.10.12(host), RTX 5080 16GB ×2, NVIDIA driver 580.95.05. 다른 GPU 작업은 종료하지 않았다.
