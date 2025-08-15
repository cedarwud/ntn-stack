# NetStack API Dockerfile - LEO Restructure Edition
# Phase 0 Implementation: Complete replacement of 6-stage system with leo_restructure
# Unified build environment with new 4-component architecture (F1→F2→F3→A1)

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

# LEO Restructure System: 4-component architecture (F1→F2→F3→A1)
# Note: leo_core is copied from the root directory via COPY . . above

# TLE 數據：複製衛星軌道數據
COPY tle_data /app/tle_data

# 創建必要目錄
RUN mkdir -p /app/data /app/tle_data /app/logs /var/log/netstack \
             /app/models /app/results /tmp/matplotlib

# 設定環境變數
ENV PYTHONPATH="/app:/app/src:/app/netstack:/app/src/leo_core"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MPLCONFIGDIR="/tmp/matplotlib"
ENV PRECOMPUTED_DATA_ENABLED=true
ENV ORBIT_CACHE_PRELOAD=true

# LEO Build Script: Execute LEO restructure system (4-component processing)
# Note: leo_build_script.py is copied from the root directory via COPY . . above
RUN chmod +x /app/leo_build_script.py

# LEO衛星軌道預計算：建構時執行LEO重構系統 (4組件處理)
RUN echo "🗑️ 清理舊數據檔案，確保重新生成..." && \
    rm -f /app/data/sgp4_orbital_dataset*.json \
          /app/data/enhanced_satellite_data.json \
          /app/data/stage*_*.json \
          /app/data/phase1_*.json \
          /app/data/.build_timestamp \
          /app/data/.data_ready && \
    echo "🚀 LEO重構系統：執行4組件預計算 (F1→F2→F3→A1)..." && \
    (cd /app && python leo_build_script.py) || echo "⚠️ 建構時LEO預計算未完成，將在運行時處理" && \
    if [ -f /app/data/phase1_final_report.json ]; then \
        echo "$(date -Iseconds)" > /app/data/.build_timestamp && \
        echo "✅ LEO建構時預計算完成，數據已就緒" && \
        ls -la /app/data/phase1_*.json | head -5; \
    else \
        echo "ℹ️ LEO建構時預計算跳過，將使用運行時計算"; \
    fi

# 衛星數據環境變數：從建置時生成的配置加載
RUN if [ -f /app/data/satellite_data.env ]; then \
        while IFS='=' read -r key value; do \
            if [ -n "$key" ] && [ -n "$value" ]; then \
                echo "export $key=\"$value\"" >> /etc/environment; \
            fi; \
        done < /app/data/satellite_data.env; \
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

# LEO重構系統標籤
LABEL leo_restructure.version="1.0.0"
LABEL leo_restructure.architecture="4-component-unified"  
LABEL leo_restructure.components="F1_TLE_Loader→F2_Satellite_Filter→F3_Signal_Analyzer→A1_Dynamic_Pool_Planner"
LABEL leo_restructure.source="real_tle_data_computation" 
LABEL leo_restructure.build_date="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LABEL leo_restructure.computation_method="leo_phase1_handover_events"
LABEL leo_restructure.description="NetStack LEO重構系統 Phase 0實現"