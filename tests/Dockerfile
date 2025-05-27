# NTN Stack 測試容器
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    docker.io \
    bash \
    && rm -rf /var/lib/apt/lists/*

# 複製需求文件
COPY requirements.txt /app/
COPY test_ntn_stack.py /app/
COPY tests/ /app/tests/

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 安裝額外的測試依賴
RUN pip install --no-cache-dir \
    pytest>=7.4.0 \
    pytest-asyncio>=0.21.0 \
    pytest-html>=3.2.0 \
    pytest-cov>=4.1.0 \
    requests>=2.31.0 \
    aiofiles>=23.2.0

# 創建報告目錄
RUN mkdir -p /app/test-reports

# 設置環境變數
ENV PYTHONPATH=/app
ENV PYTEST_ADDOPTS="--tb=short --strict-markers"

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 預設命令
CMD ["python", "-m", "pytest", "tests/", "-v"] 