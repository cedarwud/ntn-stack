import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import lifespan manager and API router from their new locations
from app.db.lifespan import lifespan
from app.api.v1.router import api_router
from app.core.config import OUTPUT_DIR  # 導入設定的圖片目錄路徑

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
origins = [
    "http://localhost",
    "http://localhost:5173",  # 本地開發環境
    "http://127.0.0.1:5173",
    "http://120.126.151.101",
    "http://120.126.151.101:5173",  # 生產環境 IP 地址
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


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """Provides a basic welcome message."""
    logger.info("--- Root endpoint '/' requested ---")
    return {"message": "Welcome to the Sionna RT Simulation API"}


# --- Uvicorn Entry Point (for direct run, if needed) ---
# Note: Running directly might skip lifespan events unless using uvicorn programmatically
if __name__ == "__main__":
    import uvicorn

    logger.info(
        "Starting Uvicorn server directly (use 'docker-compose up' for full setup)..."
    )
    # This won't properly run the lifespan events like DB init unless configured differently.
    # Recommended to run via Docker Compose or `uvicorn app.main:app --reload` from the backend directory.
    uvicorn.run(app, host="0.0.0.0", port=8000)

logger.info(
    "FastAPI application setup complete. Ready for Uvicorn via external command."
)
