FROM python:3.11-slim

# 🚀 Orbit Engine 容器配置
# 設置 Orbit Engine 統一工作目錄
WORKDIR /orbit-engine

# 🛠️ 安裝基礎開發工具（GPU通過nvidia-container-runtime提供）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 複製 Python 依賴定義
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製核心代碼 (通過 volume 掛載在開發時)
# 生產時可以直接 COPY，開發時通過 volume 覆蓋
COPY src/ ./src/
COPY scripts/ ./scripts/

# 🌐 設置 Orbit Engine 環境變量
ENV PYTHONPATH=/orbit-engine/src:/orbit-engine

# 🚀 Orbit Engine 核心路徑配置
ENV ORBIT_ENGINE_NAME=orbit-engine
ENV PROJECT_ROOT_NAME=orbit-engine-system
ENV CONTAINER_ROOT=/orbit-engine

# 📂 Orbit Engine 數據路徑配置
ENV CONTAINER_DATA_ROOT=/orbit-engine/data
ENV CONTAINER_OUTPUTS_ROOT=/orbit-engine/data/outputs
ENV CONTAINER_TLE_DATA=/orbit-engine/data/tle_data
ENV CONTAINER_VALIDATION_SNAPSHOTS=/orbit-engine/data/validation_snapshots
ENV CONTAINER_LOGS=/orbit-engine/data/logs

# 📊 Orbit Engine 階段輸出路徑
ENV CONTAINER_STAGE1_OUTPUT=/orbit-engine/data/outputs/stage1
ENV CONTAINER_STAGE2_OUTPUT=/orbit-engine/data/outputs/stage2
ENV CONTAINER_STAGE3_OUTPUT=/orbit-engine/data/outputs/stage3
ENV CONTAINER_STAGE4_OUTPUT=/orbit-engine/data/outputs/stage4
ENV CONTAINER_STAGE5_OUTPUT=/orbit-engine/data/outputs/stage5
ENV CONTAINER_STAGE6_OUTPUT=/orbit-engine/data/outputs/stage6

# 🔧 應用配置
ENV SATELLITE_ENV=production
ENV VALIDATION_LEVEL=STANDARD
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# 創建 Orbit Engine 必要目錄結構
RUN mkdir -p /orbit-engine/data/tle_data \
             /orbit-engine/data/outputs/stage1 \
             /orbit-engine/data/outputs/stage2 \
             /orbit-engine/data/outputs/stage3 \
             /orbit-engine/data/outputs/stage4 \
             /orbit-engine/data/outputs/stage5 \
             /orbit-engine/data/outputs/stage6 \
             /orbit-engine/data/validation_snapshots \
             /orbit-engine/data/logs \
             /orbit-engine/config \
             /orbit-engine/tests

# 設置權限
RUN chmod +x /orbit-engine/scripts/*.py

# 🔍 Orbit Engine 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python /orbit-engine/scripts/health_check.py || exit 1

# 🏷️ 容器標籤
LABEL orbit-engine.version="2.0" \
      orbit-engine.type="processing-engine" \
      orbit-engine.architecture="six-stage-pipeline" \
      maintainer="orbit-engine-team"

# 🚀 默認命令 - Orbit Engine 六階段處理
CMD ["python", "/orbit-engine/scripts/run_six_stages_with_validation.py", "--validation-level=STANDARD"]