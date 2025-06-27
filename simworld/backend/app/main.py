import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from contextlib import asynccontextmanager

# Import lifespan manager and API router from their new locations
from app.db.lifespan import lifespan
from app.api.v1.router import api_router
from app.core.config import OUTPUT_DIR  # 導入設定的圖片目錄路徑
from app.domains.satellite.services.cqrs_satellite_service import CQRSSatelliteService

# 添加缺失的導入
from app.db.database import database
from app.domains.satellite.services.orbit_service import OrbitService

logger = logging.getLogger(__name__)

# Create FastAPI app instance using the lifespan manager
app = FastAPI(
    title="Sionna RT Simulation API",
    description="API for running Sionna RT simulations and managing devices.",
    version="0.1.0",
    lifespan=lifespan,  # Use the imported lifespan context manager
)

# --- Static Files Mount ---
# 確保靜態文件目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)
logger.info(f"Static files directory set to: {OUTPUT_DIR}")

# 掛載靜態文件目錄到 /rendered_images URL 路徑 (保持與前端組件兼容的 URL)
app.mount("/rendered_images", StaticFiles(directory=OUTPUT_DIR), name="rendered_images")
logger.info(f"Mounted static files directory '{OUTPUT_DIR}' at '/rendered_images'.")

# 掛載 static 目錄
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
logger.info(f"Mounted static directory '{STATIC_DIR}' at '/static'.")

# --- CORS Middleware ---
# 允許特定域名的跨域請求，包括生產環境中的IP地址
# 從環境變數獲取外部 IP，預設為本地環境 IP (安全考量)
EXTERNAL_IP = os.getenv("EXTERNAL_IP", "127.0.0.1")

origins = [
    "http://localhost",
    "http://localhost:5173",  # 本地開發環境
    "http://127.0.0.1:5173",
    f"http://{EXTERNAL_IP}",
    f"http://{EXTERNAL_IP}:5173",  # 外部環境 IP 地址
    # 添加任何其他需要的域名
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 使用明確的域名列表而不是 ["*"]
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有方法
    allow_headers=["*"],  # 允許所有頭部
)
logger.info("CORS middleware added with specific origins.")


# --- Test Endpoint (Before API v1 Router) ---
@app.get("/ping", tags=["Test"])
async def ping():
    return {"message": "pong"}


# --- Include API Routers ---
# Include the router for API version 1
app.include_router(api_router, prefix="/api/v1")  # Add a /api/v1 prefix
logger.info("Included API router v1 at /api/v1.")

# Include algorithm performance router
from app.api.routes.algorithm_performance import router as algorithm_performance_router

app.include_router(algorithm_performance_router)
logger.info("Included algorithm performance router.")


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """Provides a basic welcome message."""
    logger.info("--- Root endpoint '/' requested ---")
    return {"message": "Welcome to the Sionna RT Simulation API"}


# --- Health Check Endpoint ---
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        # Check if database connection is available
        db_status = "healthy" if database.is_connected else "unhealthy"

        return {
            "status": "healthy",
            "timestamp": "2025-06-27T03:00:00Z",
            "service": "simworld-backend",
            "database": db_status,
            "version": "1.0.0",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-06-27T03:00:00Z",
            "service": "simworld-backend",
        }


# --- Uvicorn Entry Point (for direct run, if needed) ---
# Note: Running directly might skip lifespan events unless using uvicorn programmatically
if __name__ == "__main__":
    import uvicorn

    logger.info(
        "Starting Uvicorn server directly (use 'docker compose up' for full setup)..."
    )
    # This won't properly run the lifespan events like DB init unless configured differently.
    # Recommended to run via Docker Compose or `uvicorn app.main:app --reload` from the backend directory.
    uvicorn.run(app, host="0.0.0.0", port=8000)

logger.info(
    "FastAPI application setup complete. Ready for Uvicorn via external command."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理 - CQRS 版本"""

    # 啟動應用
    logger.info("🚀 SimWorld Backend 啟動中...")

    # 初始化資料庫
    await database.connect()
    logger.info("✅ 資料庫連線建立")

    # 初始化現有服務
    orbit_service = OrbitService()

    # 初始化新的 CQRS 衛星服務
    cqrs_satellite_service = CQRSSatelliteService(orbit_service)
    await cqrs_satellite_service.start()
    logger.info("✅ CQRS 衛星服務已啟動")

    # 將服務存儲到 app state
    app.state.orbit_service = orbit_service
    app.state.cqrs_satellite_service = cqrs_satellite_service

    logger.info("✅ SimWorld Backend 啟動完成")

    yield

    # 應用關閉
    logger.info("🛑 SimWorld Backend 關閉中...")

    # 停止 CQRS 衛星服務
    if hasattr(app.state, "cqrs_satellite_service"):
        await app.state.cqrs_satellite_service.stop()
        logger.info("✅ CQRS 衛星服務已停止")

    # 關閉資料庫連線
    await database.disconnect()
    logger.info("✅ 資料庫連線已關閉")
