# NetStack API Dockerfile - Enhanced Six-Stage Edition
# 增強六階段系統：整合 shared_core + simulated_annealing + 統一主流程控制器
# 完整六階段架構：TLE載入→智能篩選→信號分析→時間序列→數據整合→動態池規劃

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
    gzip \
    jq \
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

# Enhanced Six-Stage System: 六階段增強系統 + shared_core + simulated_annealing
# 主流程控制器：scripts/run_six_stages.py

# TLE 數據：複製衛星軌道數據
COPY tle_data /app/tle_data

# 創建必要目錄
RUN mkdir -p /app/data /app/tle_data /app/logs /var/log/netstack \
             /app/models /app/results /tmp/matplotlib

# 設定環境變數
ENV PYTHONPATH="/app:/app/src:/app/netstack"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MPLCONFIGDIR="/tmp/matplotlib"
ENV PRECOMPUTED_DATA_ENABLED=true
ENV ORBIT_CACHE_PRELOAD=true

# 🏗️ 建構時預處理：執行六階段數據處理（無壓縮，高效能版）
RUN echo "🏗️ 開始建構時六階段數據預處理..." && \
    echo "📊 Stage 1-6: 完整六階段處理" && \
    echo "⚡ 策略: 直接包含900MB數據，最高性能" && \
    echo "🎯 目標: < 5秒啟動時間（無解壓縮）" && \
    # 設定Python環境路徑（確保建構時能找到模組）
    export PYTHONPATH="/app:/app/src:/app/netstack" && \
    export PYTHONUNBUFFERED=1 && \
    export PYTHONDONTWRITEBYTECODE=1 && \
    # 檢查必要模組是否可導入
    cd /app && \
    python3 -c 'import sys; sys.path.insert(0, "/app"); sys.path.insert(0, "/app/src"); import aiofiles; print("✅ aiofiles module OK"); from shared_core import data_models; print("✅ shared_core module OK"); print("🔧 模組檢查通過，開始六階段處理...")' && \
    # 執行完整六階段預處理（縮短超時時間，增強錯誤處理）
    timeout 1800 python scripts/run_six_stages.py --data-dir /app/data > /tmp/six_stage_build.log 2>&1; \
    BUILD_EXIT_CODE=$?; \
    if [ $BUILD_EXIT_CODE -eq 0 ]; then \
        echo "✅ 建構時六階段處理成功完成"; \
        cat /tmp/six_stage_build.log | tail -10; \
    elif [ $BUILD_EXIT_CODE -eq 124 ]; then \
        echo "⏰ 建構時處理超時(30分鐘)，標記為運行時處理"; \
        echo "RUNTIME_PROCESSING_REQUIRED=true" > /app/data/.build_status; \
    else \
        echo "⚠️ 建構時處理失敗(退出碼:$BUILD_EXIT_CODE)，標記為運行時處理"; \
        echo "BUILD_FAILED=true" > /app/data/.build_status; \
        echo "最後10行日誌:"; \
        cat /tmp/six_stage_build.log | tail -10; \
    fi && \
    # 🎯 簡化策略：只移除超大檔案（2.3GB），其餘直接保留
    if [ -d "/app/data" ] && [ "$BUILD_EXIT_CODE" -eq 0 ]; then \
        echo "📊 移除超大TLE檔案，保留其餘900MB預處理數據..."; \
        # 只刪除超大的TLE軌道文件（2.3GB），運行時重新生成
        find /app/data -name "*tle_orbital_calculation_output.json" -type f -size +100M -delete 2>/dev/null || true; \
        echo "✅ 建構時數據準備完成 (保留~900MB預處理數據)"; \
        du -sh /app/data/ 2>/dev/null || echo "Data size check completed"; \
        # 創建建構時預處理標記
        echo "BUILD_TIME_PREPROCESSED=true" > /app/data/.build_mode; \
        echo "NO_COMPRESSION_FAST_STARTUP=true" > /app/data/.fast_startup; \
    else \
        echo "📋 創建運行時處理標記"; \
        mkdir -p /app/data; \
        echo "RUNTIME_PROCESSING_REQUIRED=true" > /app/data/.build_mode; \
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

# 複製並設定啟動腳本權限 (包含新的無壓縮直接啟動腳本和回退腳本)
COPY docker/healthcheck.sh /usr/local/bin/healthcheck.sh
COPY docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY docker/smart-entrypoint.sh /usr/local/bin/smart-entrypoint.sh
COPY docker/simple-entrypoint.sh /usr/local/bin/simple-entrypoint.sh
COPY docker/build-time-entrypoint.sh /usr/local/bin/build-time-entrypoint.sh
COPY docker/runtime-entrypoint.sh /usr/local/bin/runtime-entrypoint.sh
COPY docker/volume-based-entrypoint.sh /usr/local/bin/volume-based-entrypoint.sh
COPY docker/build-time-optimized-entrypoint.sh /usr/local/bin/build-time-optimized-entrypoint.sh
COPY docker/build-time-direct-entrypoint.sh /usr/local/bin/build-time-direct-entrypoint.sh
COPY docker/fallback-entrypoint.sh /usr/local/bin/fallback-entrypoint.sh
COPY docker/smart-startup-selector.sh /usr/local/bin/smart-startup-selector.sh

RUN chmod +x /usr/local/bin/healthcheck.sh \
             /usr/local/bin/docker-entrypoint.sh \
             /usr/local/bin/smart-entrypoint.sh \
             /usr/local/bin/simple-entrypoint.sh \
             /usr/local/bin/build-time-entrypoint.sh \
             /usr/local/bin/runtime-entrypoint.sh \
             /usr/local/bin/volume-based-entrypoint.sh \
             /usr/local/bin/build-time-optimized-entrypoint.sh \
             /usr/local/bin/build-time-direct-entrypoint.sh \
             /usr/local/bin/fallback-entrypoint.sh \
             /usr/local/bin/smart-startup-selector.sh

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

# 設定預設啟動腳本：使用智能選擇器（自動選擇最適模式）
ENTRYPOINT ["/usr/local/bin/smart-startup-selector.sh"]

# 啟動命令 (根據環境調整)
CMD if [ "$BUILD_ENV" = "development" ]; then \
        uvicorn netstack_api.main:app --host 0.0.0.0 --port 8080 --reload; \
    else \
        uvicorn netstack_api.main:app --host 0.0.0.0 --port 8080; \
    fi

# 增強六階段系統標籤
LABEL six_stage_enhanced.version="3.0.0"
LABEL six_stage_enhanced.architecture="enhanced-six-stage-unified"  
LABEL six_stage_enhanced.components="TLE載入→智能篩選→信號分析→時間序列→數據整合→動態池規劃"
LABEL six_stage_enhanced.source="real_tle_data_computation" 
LABEL six_stage_enhanced.build_date="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LABEL six_stage_enhanced.computation_method="six_stage_complete_pipeline"
LABEL six_stage_enhanced.enhancements="shared_core+simulated_annealing+unified_controller"
LABEL six_stage_enhanced.description="NetStack 增強六階段系統 - 整合四階段技術資產"