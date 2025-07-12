#!/usr/bin/env python3
"""
LEO衛星換手決策RL系統啟動腳本
"""
import os
import sys
import uvicorn
from fastapi import FastAPI
import logging

# 將專案根目錄添加到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 導入路由器
from netstack.rl_system.api.enhanced_training_routes import router as training_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """創建 FastAPI 應用程式實例。"""
    app = FastAPI(
        title="LEO衛星換手決策RL系統",
        description="Phase 1: 支援 PostgreSQL 真實數據庫的研究級RL系統",
        version="1.0.0",
    )
    app.include_router(training_router, prefix="/api/rl", tags=["RL Training"])
    return app


app = create_app()


def main():
    """系統主入口點"""
    logger.info("🚀 正在啟動 LEO 衛星換手決策 RL 系統...")
    uvicorn.run(
        "netstack.rl_system.start_system:app",
        host="0.0.0.0",
        port=8001,
        reload=True if os.getenv("ENV") == "development" else False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
