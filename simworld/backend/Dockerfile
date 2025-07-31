# backend/Dockerfile

# 1. 使用官方 Python 鏡像 (與您的環境匹配, e.g., 3.11)
FROM python:3.11-slim

# 2. 設定工作目錄
WORKDIR /app

# 3. 設定環境變量
# ENV CUDA_VISIBLE_DEVICES="-1" 強制使用 CPU (根據您的情況調整或移除)
# 防止 Python 寫入 .pyc 文件
ENV PYTHONDONTWRITEBYTECODE=1
# 強制 stdout/stderr 不緩存，方便看日誌
ENV PYTHONUNBUFFERED=1
# 減少 TensorFlow 日誌
ENV TF_CPP_MIN_LOG_LEVEL="3"
# 讓 Dr.Jit 能找到 LLVM shared lib
ENV DRJIT_LIBLLVM_PATH=/usr/lib/x86_64-linux-gnu/libLLVM-14.so.1
# 設定 PyOpenGL 默認使用 EGL (可通過環境變數覆蓋)
ENV PYOPENGL_PLATFORM=egl

# 4. 安裝系統依賴
#    - 渲染相關：更完整的 OpenGL/EGL/OSMesa 支持
#    - 資料庫相關：PostgreSQL, GDAL, PostGIS
RUN apt update && apt install -y --no-install-recommends \
    libgl1-mesa-glx \
    libegl1-mesa \
    libosmesa6 \
    libopengl0 \
    libglfw3 \
    xvfb \
    llvm-dev \
    libllvm14 \
    build-essential \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    postgresql-client \
    curl \
    && apt clean && rm -rf /var/lib/apt/lists/*


# 5. 複製依賴文件並安裝 Python 依賴
# 先複製 requirements.txt 可以利用 Docker 的層緩存
COPY requirements.txt .

# 升級 pip 並配置超時設定
RUN pip install --no-cache-dir --upgrade pip && \
    pip config set global.timeout 600 && \
    pip config set global.retries 5

# 安裝 Python 依賴，使用更長的超時時間
RUN pip install --no-cache-dir --default-timeout=600 -r requirements.txt

# 6. 複製應用程式碼到工作目錄
COPY . .

# 7. Docker 建置階段：執行 120 分鐘數據預處理
RUN echo "🚀 執行 120 分鐘數據預處理..." && \
    python preprocess_120min_timeseries.py || echo "⚠️ 預處理未能完成，將使用運行時動態載入"

# 8. 創建數據目錄並設置權限
RUN mkdir -p /app/data /app/netstack/tle_data && \
    chmod 755 /app/data /app/netstack/tle_data

# 9. 暴露 Uvicorn 運行的端口
EXPOSE 8000

# 10. 容器啟動時運行的命令
# 注意：這裡不加 --reload，因為開發時會用 volume 掛載 + compose 控制
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]