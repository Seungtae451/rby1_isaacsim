FROM nvidia/cuda:12.8.1-devel-ubuntu24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG COLMAP_VERSION=3.11.1
ARG GRUT_COMMIT=e6f4552b408af020a96de09ab5757f9b57430aaa
ARG BUILD_JOBS=4
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics \
    QT_QPA_PLATFORM=offscreen \
    PATH=/opt/venv/bin:/usr/local/cuda/bin:${PATH} \
    TORCH_HOME=/opt/torch-cache \
    MAX_JOBS=${BUILD_JOBS} \
    TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0;12.0+PTX"

# Public dependencies only; the allowlisted build context contains no videos or robot assets.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git cmake ninja-build build-essential python3 python3-dev python3-venv \
    ffmpeg libboost-program-options-dev libboost-graph-dev libboost-system-dev \
    libeigen3-dev libflann-dev libfreeimage-dev libmetis-dev libgoogle-glog-dev \
    libgtest-dev libsqlite3-dev libglew-dev libcgal-dev libceres-dev libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Ubuntu's COLMAP binary can lack CUDA SIFT. Build headless CUDA explicitly.
RUN git clone --depth 1 --branch ${COLMAP_VERSION} https://github.com/colmap/colmap.git /opt/colmap \
    && cmake -S /opt/colmap -B /opt/colmap/build -GNinja \
       -DCMAKE_BUILD_TYPE=Release -DGUI_ENABLED=OFF -DCUDA_ENABLED=ON \
       -DCMAKE_CUDA_ARCHITECTURES="80;86;89;90;120" \
    && cmake --build /opt/colmap/build -j ${BUILD_JOBS} \
    && cmake --install /opt/colmap/build \
    && rm -rf /opt/colmap

RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cu128
RUN git clone https://github.com/nv-tlabs/3dgrut.git /opt/3dgrut \
    && git -C /opt/3dgrut checkout --detach ${GRUT_COMMIT} \
    && git -C /opt/3dgrut submodule update --init --recursive \
    && pip install --no-cache-dir -e /opt/3dgrut \
    && cd /opt/3dgrut && pip install --no-cache-dir --no-build-isolation -r requirements_extra.txt

RUN apt-get update && apt-get install -y --no-install-recommends wget \
    && rm -rf /var/lib/apt/lists/* \
    && UV_PROJECT_ENVIRONMENT=/opt/venv bash /opt/3dgrut/scripts/install_slangc.sh \
    && chmod -R a+rwX /opt/3dgrut/threedgut_tracer/include

COPY docker/precache.py /opt/precache.py
RUN python /opt/precache.py \
    && pip freeze > /opt/python-packages.txt \
    && git -C /opt/3dgrut rev-parse HEAD > /opt/grut-commit.txt

ENV WANDB_MODE=disabled HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 \
    DO_NOT_TRACK=1 PYTHONPATH=/opt/app
COPY rby1_local /opt/app/rby1_local
WORKDIR /opt/3dgrut
ENTRYPOINT ["python", "-m", "rby1_local.reconstruct"]
