# NetStack API Dockerfile - 簡化單階段設計
# 永久性解決多階段構建的代碼覆蓋問題
# 統一的構建環境，根據參數控制生產/開發差異

FROM python:3.11-slim

# 構建參數
ARG BUILD_ENV=production
ARG INSTALL_DEV_TOOLS=false

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴 (基礎 + 開發工具)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    git \
    netcat-traditional \
    bc \
    && if [ "$INSTALL_DEV_TOOLS" = "true" ]; then \
        apt-get install -y vim htop strace jq netcat-openbsd; \
    fi \
    && rm -rf /var/lib/apt/lists/*

# 創建非root用戶
RUN groupadd -r netstack && useradd -r -g netstack netstack

# 複製需求檔案並安裝Python依賴
COPY requirements.txt ./requirements.txt

# 建立虛擬環境並安裝所有依賴
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 升級pip並安裝依賴
RUN pip install --upgrade pip && \
    pip config set global.timeout 600 && \
    pip config set global.retries 5 && \
    pip install --no-cache-dir --default-timeout=600 -r requirements.txt

# 複製所有應用程式代碼 (一次性複製，避免覆蓋問題)
COPY . .

# Phase 0 預計算：在代碼複製後立即執行，確保修改不被覆蓋
COPY docker/build_with_phase0_data_refactored.py /app/build_with_phase0_data.py

# 創建必要目錄
RUN mkdir -p /app/data /app/tle_data /app/logs /var/log/netstack \
             /app/models /app/results /tmp/matplotlib

# 設定環境變數
ENV PYTHONPATH="/app:/app/src"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MPLCONFIGDIR="/tmp/matplotlib"
ENV PRECOMPUTED_DATA_ENABLED=true
ENV ORBIT_CACHE_PRELOAD=true

# Phase 0 混合模式：建構時預計算基礎數據
RUN echo "🚀 Phase 0 單階段模式：執行預計算..." && \
    python build_with_phase0_data.py || echo "⚠️ 建構時預計算未完成，將在運行時處理" && \
    if [ -f /app/data/phase0_precomputed_orbits.json ]; then \
        echo "$(date -Iseconds)" > /app/data/.build_timestamp && \
        echo "✅ 建構時預計算完成，數據已就緒"; \
    else \
        echo "ℹ️ 建構時預計算跳過，將使用運行時計算"; \
    fi

# Phase 0 環境變數：從建置時生成的配置加載
RUN if [ -f /app/data/phase0.env ]; then \
        while IFS='=' read -r key value; do \
            if [ -n "$key" ] && [ -n "$value" ]; then \
                echo "export $key=\"$value\"" >> /etc/environment; \
            fi; \
        done < /app/data/phase0.env; \
    fi

# 設定目錄權限
RUN chown -R netstack:netstack /var/log/netstack /app/models /app/results \
                               /app/data /app/tle_data /tmp/matplotlib

# 複製並設定啟動腳本權限
COPY docker/healthcheck.sh /usr/local/bin/healthcheck.sh
COPY docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY docker/smart-entrypoint.sh /usr/local/bin/smart-entrypoint.sh
COPY docker/simple-entrypoint.sh /usr/local/bin/simple-entrypoint.sh

RUN chmod +x /usr/local/bin/healthcheck.sh \
             /usr/local/bin/docker-entrypoint.sh \
             /usr/local/bin/smart-entrypoint.sh \
             /usr/local/bin/simple-entrypoint.sh

# 切換到非root用戶
USER netstack

# 暴露埠號
EXPOSE 8080

# 健康檢查 (根據環境調整)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD if [ "$BUILD_ENV" = "development" ]; then \
            curl -f http://localhost:8080/api/v1/satellites/health/precomputed || /usr/local/bin/healthcheck.sh; \
        else \
            /usr/local/bin/healthcheck.sh; \
        fi

# 設定預設啟動腳本
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# 啟動命令 (根據環境調整)
CMD if [ "$BUILD_ENV" = "development" ]; then \
        uvicorn netstack_api.main:app --host 0.0.0.0 --port 8080 --reload; \
    else \
        uvicorn netstack_api.main:app --host 0.0.0.0 --port 8080; \
    fi

# Phase 0 標籤
LABEL phase0.version="2.0.0"
LABEL phase0.architecture="single-stage-unified"
LABEL phase0.data_source="local_manual_collection" 
LABEL phase0.build_date="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LABEL phase0.computation_method="sgp4_orbit_precomputation"
LABEL phase0.description="NetStack unified single-stage build eliminating code overwrite issues"