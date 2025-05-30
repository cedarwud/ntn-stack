# NetStack API Dockerfile
# 基於 Python 3.11 的多階段建置

FROM python:3.11-slim as builder

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製需求檔案
COPY requirements.txt requirements-dev.txt ./
COPY ../requirements.txt ../requirements.txt

# 建立虛擬環境並安裝 Python 依賴
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 升級 pip 並安裝依賴
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 生產階段
FROM python:3.11-slim as production

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

# 設定工作目錄
WORKDIR /app

# 複製應用程式源碼
COPY netstack_api/ ./netstack_api/

# 建立日誌目錄
RUN mkdir -p /var/log/netstack && \
    chown -R netstack:netstack /var/log/netstack

# 建立健康檢查腳本
COPY docker/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# 切換到非 root 用戶
USER netstack

# 暴露埠號
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# 啟動命令
CMD ["uvicorn", "netstack_api.main:app", "--host", "0.0.0.0", "--port", "8080"]

# 開發階段
FROM builder as development

# 設定工作目錄
WORKDIR /app

# 安裝開發和測試依賴
RUN pip install --no-cache-dir -r requirements-dev.txt && \
    pip install --no-cache-dir -r ../requirements.txt

# 確保關鍵測試依賴安裝
RUN pip install --no-cache-dir \
    pytest>=7.4.0 \
    pytest-asyncio>=0.21.0 \
    pytest-html>=3.2.0 \
    pytest-cov>=4.1.0 \
    httpx>=0.25.2 \
    structlog>=23.2.0

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

# 建立日誌和測試目錄
RUN mkdir -p /var/log/netstack /app/test-reports && \
    chown -R netstack:netstack /var/log/netstack /app/test-reports

# 建立健康檢查腳本
COPY docker/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# 設定開發環境變數
ENV ENVIRONMENT=development
ENV LOG_LEVEL=DEBUG

# 切換回應用程式用戶
USER netstack

# 暴露埠號
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# 開發模式啟動命令
CMD ["uvicorn", "netstack_api.main:app", "--host", "0.0.0.0", "--port", "8080"] 