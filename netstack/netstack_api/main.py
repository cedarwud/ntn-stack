"""
NetStack API - Open5GS + UERANSIM 雙 Slice 管理 API

基於 Hexagonal Architecture 的 FastAPI 應用程式，
提供 5G 核心網 UE 管理和 Slice 換手功能。

重構說明：
- 原本 3119 行的巨型文件已重構為模組化架構
- 將 79 個路由端點分組到不同的路由器模組中
- 保持所有原有功能，但提高可維護性
- 使用已有的路由器，並新增健康檢查和UE管理的獨立模組
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

# 適配器導入
from .adapters.mongo_adapter import MongoAdapter
from .adapters.redis_adapter import RedisAdapter
from .adapters.open5gs_adapter import Open5GSAdapter

# 服務導入
from .services.ue_service import UEService
from .services.slice_service import SliceService, SliceType
from .services.health_service import HealthService
from .services.ueransim_service import UERANSIMConfigService
from .services.satellite_gnb_mapping_service import SatelliteGnbMappingService
from .services.unified_sionna_integration import (
    UnifiedSionnaIntegration as SionnaIntegrationService,
)
from .services.interference_control_service import InterferenceControlService
from .services.connection_quality_service import ConnectionQualityService
from .services.mesh_bridge_service import MeshBridgeService
from .services.uav_mesh_failover_service import (
    UAVMeshFailoverService,
    NetworkMode,
    FailoverTriggerReason,
)

# 模型導入
from .models.requests import SliceSwitchRequest
from .models.ueransim_models import UERANSIMConfigRequest, UERANSIMConfigResponse
from .models.responses import (
    HealthResponse,
    UEInfoResponse,
    UEStatsResponse,
    SliceSwitchResponse,
    ErrorResponse,
)
from .models.uav_models import (
    TrajectoryCreateRequest,
    TrajectoryUpdateRequest,
    UAVCreateRequest,
    UAVMissionStartRequest,
    UAVPositionUpdateRequest,
    TrajectoryResponse,
    UAVStatusResponse,
    UAVListResponse,
    TrajectoryListResponse,
    TrajectoryPoint,
    UAVUEConfig,
    UAVPosition,
    UAVConnectionQualityMetrics,
    ConnectionQualityAssessment,
    ConnectionQualityHistoricalData,
    ConnectionQualityThresholds,
    UAVSignalQuality,
)
from .models.mesh_models import (
    MeshNodeCreateRequest,
    MeshNodeUpdateRequest,
    BridgeGatewayCreateRequest,
    BridgeGatewayUpdateRequest,
    MeshRoutingUpdateRequest,
    NetworkTopologyResponse,
    MeshPerformanceMetrics,
    BridgePerformanceMetrics,
    MeshNode,
    Bridge5GMeshGateway,
    MeshNetworkTopology,
)

# 指標導入
from .metrics.prometheus_exporter import metrics_exporter

# 所有現有路由器導入
from .routers.unified_api_router import unified_router
from .routers.ai_decision_router import (
    router as ai_decision_router,
    initialize_ai_services,
    shutdown_ai_services,
)
from .routers.core_sync_router import router as core_sync_router
from .routers.intelligent_fallback_router import (
    router as intelligent_fallback_router,
    initialize_fallback_service,
    shutdown_fallback_service
)

# 導入可用的路由器（註釋掉可能有問題的路由器）
try:
    from .routers.performance_router import router as performance_router
except ImportError:
    performance_router = None
    print("警告: Performance router 導入失敗，跳過")

try:
    from .routers.rl_monitoring_router import router as rl_monitoring_router
except ImportError:
    rl_monitoring_router = None
    print("警告: RL monitoring router 導入失敗，跳過")

try:
    from .routers.satellite_tle_router import router as satellite_tle_router
except ImportError:
    satellite_tle_router = None
    print("警告: Satellite TLE router 導入失敗，跳過")

try:
    from .routers.scenario_test_router import router as scenario_test_router
except ImportError:
    scenario_test_router = None
    print("警告: Scenario test router 導入失敗，跳過")

# 新的模組化路由器導入
from .app.api.health import router as health_router
from .app.api.v1.ue import router as ue_router
from .app.api.v1.handover import router as handover_router

# 日誌設定
logger = structlog.get_logger(__name__)

# 全域變數
mongo_adapter = None
redis_adapter = None
open5gs_adapter = None

# Prometheus 指標設定
REQUEST_COUNT = Counter(
    "netstack_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "netstack_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式生命週期管理
    處理啟動和關閉時的資源初始化和清理
    """
    global mongo_adapter, redis_adapter, open5gs_adapter

    logger.info("🚀 NetStack API 正在啟動...")

    try:
        # 初始化適配器
        mongo_url = os.getenv("DATABASE_URL", "mongodb://mongo:27017/open5gs")
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        mongo_host = os.getenv("MONGO_HOST", "mongo")

        mongo_adapter = MongoAdapter(mongo_url)
        redis_adapter = RedisAdapter(redis_url)
        open5gs_adapter = Open5GSAdapter(mongo_host=mongo_host, mongo_port=27017)

        await mongo_adapter.connect()
        await redis_adapter.connect()
        # Open5GSAdapter 沒有 connect 方法，跳過

        # 初始化服務並注入到 app.state (按依賴順序)
        app.state.ue_service = UEService(mongo_adapter, open5gs_adapter)
        app.state.slice_service = SliceService(
            mongo_adapter, open5gs_adapter, redis_adapter
        )
        app.state.health_service = HealthService(mongo_adapter, redis_adapter)
        app.state.ueransim_service = UERANSIMConfigService()
        app.state.satellite_service = SatelliteGnbMappingService(mongo_adapter)
        app.state.sionna_service = SionnaIntegrationService()
        app.state.interference_service = InterferenceControlService()

        # 首先初始化基礎服務
        app.state.connection_service = ConnectionQualityService(mongo_adapter)
        app.state.mesh_service = MeshBridgeService(
            mongo_adapter, redis_adapter, open5gs_adapter
        )

        # 然後初始化依賴於其他服務的服務
        app.state.uav_failover_service = UAVMeshFailoverService(
            mongo_adapter,
            redis_adapter,
            app.state.connection_service,
            app.state.mesh_service,
        )

        # 初始化 AI 服務
        await initialize_ai_services(redis_adapter)
        
        # 初始化回退服務
        await initialize_fallback_service()

        logger.info("✅ NetStack API 啟動完成")

        yield  # 應用程式運行期間

    except Exception as e:
        logger.error("💥 NetStack API 啟動失敗", error=str(e))
        raise
    finally:
        # 清理資源
        logger.info("🔧 NetStack API 正在關閉...")

        await shutdown_ai_services()
        await shutdown_fallback_service()

        if mongo_adapter:
            await mongo_adapter.disconnect()
        if redis_adapter:
            await redis_adapter.disconnect()
        # Open5GSAdapter 沒有 disconnect 方法，跳過

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


# 請求日誌和指標中間件
@app.middleware("http")
async def log_and_metrics_middleware(request: Request, call_next):
    """記錄請求日誌和收集 Prometheus 指標"""
    start_time = datetime.utcnow()

    # 記錄請求開始
    logger.info(
        "HTTP請求開始",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
    )

    try:
        response = await call_next(request)

        # 計算處理時間
        duration = (datetime.utcnow() - start_time).total_seconds()

        # 記錄 Prometheus 指標
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
            duration=duration,
        )

        return response

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            "HTTP請求失敗",
            method=request.method,
            url=str(request.url),
            error=str(e),
            duration=duration,
        )

        # 記錄錯誤指標
        REQUEST_COUNT.labels(
            method=request.method, endpoint=request.url.path, status=500
        ).inc()

        raise


# ===== 路由器註冊 =====
# 註冊所有路由器，包括現有的和新重構的

# 新的模組化路由器（將取代原來的直接定義路由）
app.include_router(health_router, tags=["健康檢查"])
app.include_router(ue_router, tags=["UE 管理"])
app.include_router(handover_router)

# 現有的統一路由器
app.include_router(unified_router, tags=["統一 API"])

# AI 決策路由器
app.include_router(ai_decision_router, tags=["AI 智慧決策"])

# 核心同步路由器
app.include_router(core_sync_router, tags=["核心同步機制"])

# 智能回退路由器
app.include_router(intelligent_fallback_router, tags=["智能回退機制"])

# 條件性註冊路由器（只有成功導入的才註冊）
if performance_router:
    app.include_router(performance_router, tags=["性能監控"])

if rl_monitoring_router:
    app.include_router(rl_monitoring_router, tags=["RL 訓練監控"])

if satellite_tle_router:
    app.include_router(satellite_tle_router, tags=["衛星 TLE 橋接"])

if scenario_test_router:
    app.include_router(scenario_test_router, tags=["場景測試驗證"])


# ===== 根路徑處理 =====
@app.get("/", summary="API 根路徑")
async def root():
    """
    API 根路徑
    返回應用程式的基本資訊和可用端點
    """
    return {
        "name": "NetStack API",
        "version": "1.0.0",
        "description": "Open5GS + UERANSIM 雙 Slice 核心網管理 API",
        "status": "重構完成 - 原3119行已模組化",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "metrics": "/metrics",
            "openapi": "/openapi.json",
        },
        "features": [
            "UE 管理",
            "Slice 管理",
            "衛星 gNodeB 映射",
            "OneWeb 衛星整合",
            "Sionna 整合",
            "AI 決策引擎",
            "Mesh 網路橋接",
            "UAV 管理",
            "干擾控制",
            "UERANSIM 配置",
        ],
    }


# ===== 全域異常處理 =====
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """處理 404 錯誤"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"路徑 {request.url.path} 不存在",
            "timestamp": datetime.utcnow().isoformat(),
            "available_docs": "/docs",
        },
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
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """處理 HTTP 異常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# ===== 啟動設定 =====
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True, log_level="info")
