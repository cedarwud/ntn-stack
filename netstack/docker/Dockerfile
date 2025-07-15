# NetStack API Dockerfile
# 基於 Python 3.11 的多階段建置

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
COPY ../requirements.txt ./requirements.txt

# 建立虛擬環境並安裝 Python 依賴
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 升級 pip 並配置超時設定
RUN pip install --upgrade pip && \
    pip config set global.timeout 600 && \
    pip config set global.retries 5

# 安裝所有依賴 - 統一完整安裝
RUN pip install --no-cache-dir --default-timeout=600 -r requirements.txt

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

# 設定環境變數
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# 修復 matplotlib 權限問題
ENV MPLCONFIGDIR="/tmp/matplotlib"

# 設定工作目錄
WORKDIR /app

# 複製應用程式源碼
COPY netstack_api/ ./netstack_api/
# 複製 UPF 擴展模組
COPY docker/upf-extension/ ./docker/upf-extension/
# 複製 RL 訓練腳本
COPY scripts/ ./scripts/

# 建立日誌目錄、模型目錄、結果目錄和 matplotlib 緩存目錄
RUN mkdir -p /var/log/netstack /app/models /app/results /tmp/matplotlib && \
    chown -R netstack:netstack /var/log/netstack /app/models /app/results /tmp/matplotlib

# 建立健康檢查腳本
COPY docker/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# 換手到非 root 用戶
USER netstack

# 暴露埠號
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# 啟動命令
CMD ["uvicorn", "netstack_api.main:app", "--host", "0.0.0.0", "--port", "8080"]

# 開發階段
FROM builder AS development

# 設定工作目錄
WORKDIR /app

# 安裝所有依賴 - 開發環境使用完整 requirements.txt
COPY ../requirements.txt ./requirements.txt
RUN pip config set global.timeout 600 && \
    pip config set global.retries 5 && \
    pip install --no-cache-dir --default-timeout=600 -r requirements.txt

# 安裝除錯工具
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    strace \
    jq \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 建立非 root 用戶
RUN groupadd -r netstack && useradd -r -g netstack netstack

# 複製應用程式源碼
COPY netstack_api/ ./netstack_api/
# 複製 UPF 擴展模組
COPY docker/upf-extension/ ./docker/upf-extension/
# 複製 RL 訓練腳本
COPY scripts/ ./scripts/

# 建立日誌、測試目錄、模型目錄、結果目錄和 matplotlib 緩存目錄
RUN mkdir -p /var/log/netstack /app/test-reports /app/models /app/results /tmp/matplotlib && \
    chown -R netstack:netstack /var/log/netstack /app/test-reports /app/models /app/results /tmp/matplotlib

# 建立健康檢查腳本
COPY docker/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# 設定開發環境變數
ENV ENVIRONMENT=development
ENV LOG_LEVEL=DEBUG
# 修復 matplotlib 權限問題
ENV MPLCONFIGDIR="/tmp/matplotlib"

# 換手回應用程式用戶
USER netstack

# 暴露埠號
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# 開發模式啟動命令
CMD ["uvicorn", "netstack_api.main:app", "--host", "0.0.0.0", "--port", "8080"] 