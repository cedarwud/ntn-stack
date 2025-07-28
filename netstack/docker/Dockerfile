# NetStack API Dockerfile - Phase 0 增強版
# 支援本地收集 TLE 數據的 Docker 建置

FROM python:3.11-slim AS builder

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製需求檔案
COPY netstack/requirements.txt ./requirements.txt

# 建立虛擬環境並安裝 Python 依賴
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 升級 pip 並配置超時設定
RUN pip install --upgrade pip && \
    pip config set global.timeout 600 && \
    pip config set global.retries 5

# 安裝所有依賴 - 統一完整安裝
RUN pip install --no-cache-dir --default-timeout=600 -r requirements.txt

# Phase 0 增強：複製手動收集的 TLE 數據
COPY tle_data/ /app/tle_data/

# 複製 Phase 0 預處理腳本
COPY netstack/docker/build_with_phase0_data.py /app/build_with_phase0_data.py

# Phase 0 預處理：掃描並處理收集的數據
RUN python3 /app/build_with_phase0_data.py \
    --tle-data-dir /app/tle_data \
    --output-dir /app/data

# 生產階段
FROM python:3.11-slim AS production

# 建立非 root 用戶
RUN groupadd -r netstack && useradd -r -g netstack netstack

# 安裝運行時依賴
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# 複製虛擬環境
COPY --from=builder /opt/venv /opt/venv

# Phase 0 增強：複製預處理後的數據
COPY --from=builder /app/tle_data /app/tle_data
COPY --from=builder /app/data /app/data

# 設定環境變數
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# 修復 matplotlib 權限問題
ENV MPLCONFIGDIR="/tmp/matplotlib"

# Phase 0 環境變數：從建置時生成的配置加載
RUN if [ -f /app/data/phase0.env ]; then \
        while IFS='=' read -r key value; do \
            if [ -n "$key" ] && [ -n "$value" ]; then \
                echo "export $key=\"$value\"" >> /etc/environment; \
            fi; \
        done < /app/data/phase0.env; \
    fi

# 設定工作目錄
WORKDIR /app

# 複製應用程式源碼
COPY netstack/src/ ./src/
COPY netstack/netstack_api/ ./netstack_api/
# 複製 UPF 擴展模組
COPY netstack/docker/upf-extension/ ./docker/upf-extension/
# 複製 RL 訓練腳本
COPY netstack/scripts/ ./scripts/

# 建立目錄
RUN mkdir -p /var/log/netstack /app/models /app/results /tmp/matplotlib

# Phase 0 增強：驗證預計算數據完整性
RUN ls -lh /app/data/ && echo "Phase 0 precomputed data validation passed"

# 設定目錄權限
RUN chown -R netstack:netstack /var/log/netstack /app/models /app/results /app/data /app/tle_data /tmp/matplotlib

# 建立健康檢查腳本和啟動腳本
COPY netstack/docker/healthcheck.sh /usr/local/bin/healthcheck.sh
COPY netstack/docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/healthcheck.sh /usr/local/bin/docker-entrypoint.sh

# 換手到非 root 用戶
USER netstack

# 暴露埠號
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# 設定啟動腳本
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# 啟動命令
CMD ["uvicorn", "netstack_api.main:app", "--host", "0.0.0.0", "--port", "8080"]

# Phase 0 標籤
LABEL phase0.version="1.0.1"
LABEL phase0.data_source="local_manual_collection" 
LABEL phase0.build_date="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LABEL phase0.computation_method="sgp4_orbit_precomputation"
LABEL phase0.description="NetStack with Phase 0 SGP4 orbit precomputation support"

# 開發階段
FROM builder AS development

# 設定工作目錄
WORKDIR /app

# 安裝除錯工具
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    strace \
    jq \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 建立非 root 用戶
RUN groupadd -r netstack && useradd -r -g netstack netstack

# 複製應用程式源碼
COPY netstack/src/ ./src/
COPY netstack/netstack_api/ ./netstack_api/
# 複製 UPF 擴展模組
COPY netstack/docker/upf-extension/ ./docker/upf-extension/
# 複製 RL 訓練腳本
COPY netstack/scripts/ ./scripts/

# Phase 0 增強：複製數據和配置
COPY --from=builder /app/tle_data /app/tle_data
COPY --from=builder /app/data /app/data

# 建立日誌、測試目錄、模型目錄、結果目錄和 matplotlib 緩存目錄
RUN mkdir -p /var/log/netstack /app/test-reports /app/models /app/results /tmp/matplotlib && \
    chown -R netstack:netstack /var/log/netstack /app/test-reports /app/models /app/results /app/data /app/tle_data /tmp/matplotlib

# 建立健康檢查腳本和啟動腳本
COPY netstack/docker/healthcheck.sh /usr/local/bin/healthcheck.sh
COPY netstack/docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/healthcheck.sh && chmod +x /usr/local/bin/docker-entrypoint.sh

# 設定開發環境變數
ENV ENVIRONMENT=development
ENV LOG_LEVEL=DEBUG
# 修復 matplotlib 權限問題
ENV MPLCONFIGDIR="/tmp/matplotlib"
# Phase 0 開發模式
ENV PHASE0_DEV_MODE=true

# 換手回應用程式用戶
USER netstack

# 暴露埠號
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# 開發模式啟動命令
CMD ["uvicorn", "netstack_api.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]