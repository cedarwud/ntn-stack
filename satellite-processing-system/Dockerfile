FROM python:3.11-slim

# 設置工作目錄  
WORKDIR /satellite-processing

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 Python 依賴定義
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製核心代碼 (通過 volume 掛載在開發時)
# 生產時可以直接 COPY，開發時通過 volume 覆蓋
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# 設置環境變量
ENV PYTHONPATH=/satellite-processing/src:/satellite-processing
ENV SATELLITE_PROCESSING_HOME=/satellite-processing
ENV TLE_DATA_DIR=/satellite-processing/data/tle_data
ENV OUTPUT_DIR=/satellite-processing/data/outputs
ENV VALIDATION_DIR=/satellite-processing/data/validation_snapshots

# 創建必要目錄
RUN mkdir -p /satellite-processing/data/{tle_data,outputs,validation_snapshots,logs}

# 設置權限
RUN chmod +x /satellite-processing/scripts/*.py

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python /satellite-processing/scripts/health_check.py || exit 1

# 默認命令
CMD ["python", "/satellite-processing/scripts/run_six_stages_with_validation.py", "--validation-level=STANDARD"]