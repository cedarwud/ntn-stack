# LEO衛星換手決策RL系統 - Dockerfile
# Phase 1: PostgreSQL真實數據儲存

# 使用官方的 Python 3.10 slim 映像檔作為基礎
FROM python:3.10-slim

# 設置工作目錄
WORKDIR /app

# 將依賴文件複製到容器中
COPY netstack/rl_system/requirements.txt .

# 安裝 Python 依賴
# --no-cache-dir: 不緩存下載的包，以減小映像檔大小
# --upgrade pip: 升級 pip 到最新版本
RUN pip install --no-cache-dir -r requirements.txt

# 將應用程式的其餘代碼複製到工作目錄中
COPY . .

# 開放 FastAPI 應用程式運行的端口
EXPOSE 8001

# 設置啟動命令
# 執行 Python 腳本來啟動應用，而不是直接調用 Uvicorn
# -u: 使用無緩衝的 stdout 和 stderr
CMD ["python", "netstack/rl_system/start_system.py"] 