"""
NetStack API - 重構後的主應用程式
將原本 3119 行的 main.py 重構為模組化架構

重構改進：
1. 將健康檢查路由提取到 app/api/health.py
2. 將UE管理路由提取到 app/api/v1/ue.py
3. 保留必要的中間件和生命週期管理
4. 簡化主文件，提高可維護性
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import FastAPI, HTTPException, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.encoders import jsonable_encoder
from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry
from prometheus_client.exposition import generate_latest
from fastapi import Response

# 導入適配器和服務
from .adapters.mongo_adapter import MongoAdapter
from .adapters.redis_adapter import RedisAdapter
from .adapters.open5gs_adapter import Open5GSAdapter
from .services.ue_service import UEService
from .services.slice_service import SliceService, SliceType
from .services.health_service import HealthService
from .services.ueransim_service import UERANSIMConfigService
from .services.satellite_gnb_mapping_service import SatelliteGnbMappingService
from .services.sionna_integration_service import SionnaIntegrationService
from .services.interference_control_service import InterferenceControlService
from .services.connection_quality_service import ConnectionQualityService

# 導入模型
from .models.requests import SliceSwitchRequest
from .models.ueransim_models import UERANSIMConfigRequest, UERANSIMConfigResponse
from .models.responses import (
    HealthResponse,
    UEInfoResponse,
    UEStatsResponse,
    SliceSwitchResponse,
    ErrorResponse,
)

# 導入指標
from .metrics.prometheus_exporter import metrics_exporter

# 導入現有的路由器
from .routers.unified_api_router import unified_router
from .routers.ai_decision_router import (
    router as ai_decision_router,
    initialize_ai_services,
    shutdown_ai_services,
)
from .routers.core_sync_router import router as core_sync_router
from .routers.intelligent_fallback_router import router as intelligent_fallback_router

# 導入新的重構路由器
from .app.api.health import router as health_router
from .app.api.v1.ue import router as ue_router

# 日誌設定
logger = structlog.get_logger(__name__)

# 全域變數
mongo_adapter = None
redis_adapter = None
open5gs_adapter = None


# 生命週期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    global mongo_adapter, redis_adapter, open5gs_adapter
    
    logger.info("🚀 NetStack API 正在啟動...")
    
    try:
        # 初始化適配器
        mongo_adapter = MongoAdapter()
        redis_adapter = RedisAdapter()
        open5gs_adapter = Open5GSAdapter()
        
        await mongo_adapter.connect()
        await redis_adapter.connect()
        await open5gs_adapter.connect()
        
        # 初始化服務並注入到 app.state
        app.state.ue_service = UEService(mongo_adapter, open5gs_adapter)
        app.state.slice_service = SliceService(mongo_adapter, open5gs_adapter)
        app.state.health_service = HealthService(mongo_adapter, redis_adapter, open5gs_adapter)
        app.state.ueransim_service = UERANSIMConfigService()
        app.state.satellite_service = SatelliteGnbMappingService(mongo_adapter)
        app.state.sionna_service = SionnaIntegrationService()
        app.state.interference_service = InterferenceControlService()
        app.state.connection_service = ConnectionQualityService(mongo_adapter)
        
        # 初始化 AI 服務
        await initialize_ai_services()
        
        logger.info("✅ NetStack API 啟動完成")
        
        yield  # 應用程式運行期間
        
    except Exception as e:
        logger.error("💥 NetStack API 啟動失敗", error=str(e))
        raise
    finally:
        # 清理資源
        logger.info("🔧 NetStack API 正在關閉...")
        
        await shutdown_ai_services()
        
        if mongo_adapter:
            await mongo_adapter.disconnect()
        if redis_adapter:
            await redis_adapter.disconnect()
        if open5gs_adapter:
            await open5gs_adapter.disconnect()
            
        logger.info("✅ NetStack API 已關閉")


# 建立 FastAPI 應用程式
app = FastAPI(
    title="NetStack API",
    description="Open5GS + UERANSIM 雙 Slice 核心網管理 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應限制具體域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus 指標
REQUEST_COUNT = Counter(
    "netstack_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "netstack_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"]
)


# 請求日誌和指標中間件
@app.middleware("http")
async def log_and_metrics_middleware(request: Request, call_next):
    """記錄請求日誌和收集指標"""
    start_time = datetime.utcnow()
    
    # 記錄請求開始
    logger.info(
        "HTTP請求開始",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None
    )
    
    try:
        response = await call_next(request)
        
        # 計算處理時間
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # 記錄指標
        method = request.method
        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=method, endpoint=endpoint, status=response.status_code
        ).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        # 記錄請求完成
        logger.info(
            "HTTP請求完成",
            method=method,
            url=endpoint,
            status_code=response.status_code,
            duration=duration
        )
        
        return response
        
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            "HTTP請求失敗",
            method=request.method,
            url=str(request.url),
            error=str(e),
            duration=duration
        )
        
        # 記錄錯誤指標
        REQUEST_COUNT.labels(
            method=request.method, endpoint=request.url.path, status=500
        ).inc()
        
        raise


# 註冊路由器

# 新的重構路由器（優先級較高）
app.include_router(health_router, tags=["健康檢查"])
app.include_router(ue_router, tags=["UE 管理"])

# 現有的統一路由器
app.include_router(unified_router, tags=["統一 API"])
app.include_router(ai_decision_router, tags=["AI 智慧決策"])
app.include_router(core_sync_router, tags=["核心同步機制"])
app.include_router(intelligent_fallback_router, tags=["智能回退機制"])

# 這裡可以繼續添加其他現有的路由器
# app.include_router(scenario_test_router, tags=["場景測試驗證"])
# app.include_router(satellite_tle_router, tags=["衛星 TLE 橋接"])
# app.include_router(rl_monitoring_router, tags=["RL 訓練監控"])


# 根路徑處理
@app.get("/", summary="API 根路徑")
async def root():
    """
    API 根路徑
    返回應用程式的基本資訊
    """
    return {
        "name": "NetStack API",
        "version": "1.0.0",
        "description": "Open5GS + UERANSIM 雙 Slice 核心網管理 API",
        "status": "重構完成",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


# 全域異常處理
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """處理 404 錯誤"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"路徑 {request.url.path} 不存在",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    """處理 500 錯誤"""
    logger.error("內部服務器錯誤", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "服務器內部錯誤",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_refactored:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )