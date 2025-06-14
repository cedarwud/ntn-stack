"""
NetStack API - Open5GS + UERANSIM 雙 Slice 管理 API

基於 Hexagonal Architecture 的 FastAPI 應用程式，
提供 5G 核心網 UE 管理和 Slice 切換功能。
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.encoders import jsonable_encoder
from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry
from prometheus_client.exposition import generate_latest
from fastapi import Response

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
from .metrics.prometheus_exporter import metrics_exporter
from .services.mesh_bridge_service import MeshBridgeService
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
from .services.uav_mesh_failover_service import (
    UAVMeshFailoverService,
    NetworkMode,
    FailoverTriggerReason,
)

# 添加統一路由器導入
from .routers.unified_api_router import unified_router

# 添加 AI 決策路由器導入
from .routers.ai_decision_router import router as ai_decision_router, initialize_ai_services, shutdown_ai_services

# 添加核心同步路由器導入
from .routers.core_sync_router import router as core_sync_router

# 添加智能回退路由器導入
from .routers.intelligent_fallback_router import router as intelligent_fallback_router

# 添加場景測試路由器導入
from .routers.scenario_test_router import router as scenario_test_router

# 添加衛星 TLE 橋接路由器導入
from .routers.satellite_tle_router import router as satellite_tle_router

# 添加事件驅動服務導入
from .services.event_bus_service import (
    EventBusService,
    get_event_bus,
    shutdown_event_bus,
)


# 自定義 JSON 編碼器
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

    def iterencode(self, o, _one_shot=False):
        """修改迭代編碼以處理特殊浮點值"""

        def _clean_float(value):
            if isinstance(value, float):
                if value == float("inf"):
                    return None
                elif value == float("-inf"):
                    return None
                elif value != value:  # NaN check
                    return None
            elif isinstance(value, dict):
                return {k: _clean_float(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_clean_float(item) for item in value]
            return value

        cleaned_obj = _clean_float(o)
        return super().iterencode(cleaned_obj, _one_shot)


# 自定義 JSONResponse 類
class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=CustomJSONEncoder,
        ).encode("utf-8")


# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Prometheus 指標
# 使用自定義 Registry 而非默認的全局 Registry
from prometheus_client import Counter, Histogram, CollectorRegistry

# 建立自定義 Registry
prometheus_registry = CollectorRegistry()

# 在自定義 Registry 中註冊指標
REQUEST_COUNT = Counter(
    "netstack_api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status"],
    registry=prometheus_registry,
)

REQUEST_DURATION = Histogram(
    "netstack_api_request_duration_seconds",
    "Time spent processing API requests",
    ["method", "endpoint"],
    registry=prometheus_registry,
)

SLICE_SWITCH_COUNT = Counter(
    "netstack_slice_switch_total",
    "Total number of slice switches",
    ["from_slice", "to_slice", "status"],
    registry=prometheus_registry,
)

UE_ATTACH_COUNT = Counter(
    "netstack_ue_attach_total",
    "Total number of UE attachments",
    ["slice_type", "status"],
    registry=prometheus_registry,
)

RTT_HISTOGRAM = Histogram(
    "netstack_slice_rtt_seconds",
    "RTT latency by slice type",
    ["slice_type"],
    registry=prometheus_registry,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    logger.info("🚀 NetStack API 啟動中...")

    # 初始化適配器
    mongo_adapter = MongoAdapter(
        connection_string=os.getenv("DATABASE_URL", "mongodb://mongo:27017/open5gs")
    )
    redis_adapter = RedisAdapter(
        connection_string=os.getenv("REDIS_URL", "redis://redis:6379")
    )
    open5gs_adapter = Open5GSAdapter(mongo_host=os.getenv("MONGO_HOST", "mongo"))

    # 啟動事件總線
    event_bus = await get_event_bus()
    logger.info("✅ 事件總線已啟動")

    # 初始化服務
    ue_service = UEService(mongo_adapter, redis_adapter)
    slice_service = SliceService(mongo_adapter, open5gs_adapter, redis_adapter)
    health_service = HealthService(mongo_adapter, redis_adapter)
    ueransim_service = UERANSIMConfigService()
    satellite_gnb_service = SatelliteGnbMappingService(
        simworld_api_url=os.getenv("SIMWORLD_API_URL", "http://simworld-backend:8000"),
        redis_client=redis_adapter.client if redis_adapter else None,
    )

    # 初始化新的事件驅動干擾控制服務
    interference_service = InterferenceControlService(
        simworld_api_url=os.getenv("SIMWORLD_API_URL", "http://simworld-backend:8000"),
        event_bus=event_bus,
        auto_mitigation=True,
        update_interval_sec=0.1,  # 100ms 實時檢測
    )

    # 啟動干擾控制服務
    await interference_service.start()
    logger.info("✅ 事件驅動干擾控制服務已啟動")

    # 初始化 OneWeb 衛星 gNodeB 服務
    from .services.oneweb_satellite_gnb_service import OneWebSatelliteGnbService

    oneweb_service = OneWebSatelliteGnbService(
        satellite_mapping_service=satellite_gnb_service,
        simworld_api_url=os.getenv("SIMWORLD_API_URL", "http://simworld-backend:8000"),
        ueransim_config_dir=os.getenv("UERANSIM_CONFIG_DIR", "/tmp/ueransim_configs"),
    )

    # 初始化 Sionna 整合服務
    sionna_service = SionnaIntegrationService(
        simworld_api_url=os.getenv("SIMWORLD_API_URL", "http://simworld-backend:8000"),
        update_interval_sec=int(os.getenv("SIONNA_UPDATE_INTERVAL", "30")),
        ueransim_config_dir=os.getenv("UERANSIM_CONFIG_DIR", "/tmp/ueransim_configs"),
    )

    # 初始化 UAV UE 服務
    from .services.uav_ue_service import UAVUEService

    uav_ue_service = UAVUEService(
        mongo_adapter=mongo_adapter,
        redis_adapter=redis_adapter,
        ueransim_config_dir=os.getenv("UERANSIM_CONFIG_DIR", "/tmp/ueransim_configs"),
        simworld_api_url=os.getenv("SIMWORLD_API_URL", "http://simworld-backend:8000"),
        update_interval_sec=float(os.getenv("UAV_UPDATE_INTERVAL", "5.0")),
    )

    # 初始化 UAV-衛星連接質量評估服務
    connection_quality_service = ConnectionQualityService(mongo_adapter)

    # 初始化 Mesh 橋接服務
    mesh_bridge_service = MeshBridgeService(
        mongo_adapter=mongo_adapter,
        redis_adapter=redis_adapter,
        open5gs_adapter=open5gs_adapter,
        upf_ip=os.getenv("UPF_IP", "172.20.0.30"),
        upf_port=int(os.getenv("UPF_PORT", "2152")),
    )

    # 初始化 UAV Mesh 備援服務
    uav_mesh_failover_service = UAVMeshFailoverService(
        mongo_adapter=mongo_adapter,
        redis_adapter=redis_adapter,
        connection_quality_service=connection_quality_service,
        mesh_bridge_service=mesh_bridge_service,
        ueransim_config_dir=os.getenv("UERANSIM_CONFIG_DIR", "/tmp/ueransim_configs"),
    )

    # 設置服務之間的依賴關係
    uav_ue_service.set_connection_quality_service(connection_quality_service)

    # 儲存到應用程式狀態
    app.state.mongo_adapter = mongo_adapter
    app.state.redis_adapter = redis_adapter
    app.state.open5gs_adapter = open5gs_adapter
    app.state.ue_service = ue_service
    app.state.slice_service = slice_service
    app.state.health_service = health_service
    app.state.ueransim_service = ueransim_service
    app.state.satellite_gnb_service = satellite_gnb_service
    app.state.oneweb_service = oneweb_service
    app.state.sionna_service = sionna_service
    app.state.interference_service = interference_service
    app.state.uav_ue_service = uav_ue_service
    app.state.connection_quality_service = connection_quality_service
    app.state.mesh_bridge_service = mesh_bridge_service
    app.state.uav_mesh_failover_service = uav_mesh_failover_service
    app.state.event_bus = event_bus

    # 將服務傳遞給全局變量供端點使用
    globals()["connection_quality_service"] = connection_quality_service
    globals()["uav_ue_service"] = uav_ue_service
    globals()["mesh_bridge_service"] = mesh_bridge_service
    globals()["uav_mesh_failover_service"] = uav_mesh_failover_service

    # 連接外部服務
    await mongo_adapter.connect()
    if redis_adapter:
        await redis_adapter.connect()

    # 啟動 Mesh 橋接服務
    await mesh_bridge_service.start_service()

    # 啟動 Sionna 整合服務
    await sionna_service.start()

    # 初始化 AI 智慧決策服務
    try:
        await initialize_ai_services(redis_adapter)
        logger.info("✅ AI 智慧決策服務已初始化")
    except Exception as e:
        logger.error("AI 智慧決策服務初始化失敗", error=str(e))
        # 不阻塞應用啟動，但記錄錯誤

    logger.info("✅ NetStack API 啟動完成")

    yield

    # 清理資源
    logger.info("🛑 NetStack API 正在關閉...")

    # 停止干擾控制服務
    if hasattr(app.state, "interference_service"):
        await app.state.interference_service.stop()
        logger.info("✅ 干擾控制服務已停止")

    # 關閉事件總線
    await shutdown_event_bus()
    logger.info("✅ 事件總線已關閉")

    # 停止 Mesh 橋接服務
    if mesh_bridge_service:
        await mesh_bridge_service.stop_service()

    # 關閉 OneWeb 服務
    if hasattr(app.state, "oneweb_service"):
        await app.state.oneweb_service.shutdown()

    # 關閉 Sionna 整合服務
    if hasattr(app.state, "sionna_service"):
        await app.state.sionna_service.stop()

    # 關閉 UAV UE 服務
    if hasattr(app.state, "uav_ue_service"):
        await app.state.uav_ue_service.shutdown()

    # 停止 UAV Mesh 備援服務
    if hasattr(app.state, "uav_mesh_failover_service"):
        await app.state.uav_mesh_failover_service.stop_service()

    # 關閉 AI 智慧決策服務
    try:
        await shutdown_ai_services()
        logger.info("✅ AI 智慧決策服務已關閉")
    except Exception as e:
        logger.error("AI 智慧決策服務關閉失敗", error=str(e))

    await mongo_adapter.disconnect()
    await redis_adapter.disconnect()
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

# 註冊統一 API 路由器
app.include_router(unified_router, tags=["統一 API"])

# 註冊 AI 決策 API 路由器
app.include_router(ai_decision_router, tags=["AI 智慧決策"])

# 註冊核心同步 API 路由器
app.include_router(core_sync_router, tags=["核心同步機制"])

# 註冊智能回退 API 路由器
app.include_router(intelligent_fallback_router, tags=["智能回退機制"])

# 註冊場景測試 API 路由器
app.include_router(scenario_test_router, tags=["場景測試驗證"])

# 註冊衛星 TLE 橋接 API 路由器
app.include_router(satellite_tle_router, tags=["衛星 TLE 橋接"])


@app.middleware("http")
async def metrics_middleware(request, call_next):
    """請求指標中介軟體"""
    method = request.method
    endpoint = request.url.path

    with REQUEST_DURATION.labels(method=method, endpoint=endpoint).time():
        response = await call_next(request)

    REQUEST_COUNT.labels(
        method=method, endpoint=endpoint, status=response.status_code
    ).inc()

    return response


# ===== 健康檢查端點 =====


@app.get("/health", response_model=HealthResponse, tags=["健康檢查"])
async def health_check():
    """
    檢查 NetStack 系統健康狀態

    回傳各核心服務的健康狀態，包括：
    - MongoDB 連線狀態
    - Redis 連線狀態
    - Open5GS 核心網服務狀態
    """
    try:
        health_service = app.state.health_service
        health_status = await health_service.check_system_health()

        if health_status["overall_status"] == "healthy":
            return HealthResponse(**health_status)
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health_status
            )
    except Exception as e:
        logger.error("健康檢查失敗", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "健康檢查失敗", "message": str(e)},
        )


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus 指標端點"""
    return metrics_exporter.get_metrics()


# ===== UE 管理端點 =====


@app.get("/api/v1/ue/{imsi}", tags=["UE 管理"])
async def get_ue_info(imsi: str):
    """
    取得指定 IMSI 的 UE 資訊

    Args:
        imsi: UE 的 IMSI 號碼 (例如: 999700000000001)

    Returns:
        UE 的詳細資訊，包括目前 Slice、APN 設定等
    """
    try:
        ue_service = app.state.ue_service
        ue_info = await ue_service.get_ue_info(imsi)

        if not ue_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到 IMSI {imsi} 的 UE",
            )

        return CustomJSONResponse(content=ue_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("取得 UE 資訊失敗", imsi=imsi, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "取得 UE 資訊失敗", "message": str(e)},
        )


@app.get("/api/v1/ue/{imsi}/stats", response_model=UEStatsResponse, tags=["UE 管理"])
async def get_ue_stats(imsi: str):
    """
    取得指定 UE 的統計資訊

    Args:
        imsi: UE 的 IMSI 號碼

    Returns:
        UE 的統計資訊，包括連線時間、流量統計、RTT 等
    """
    try:
        ue_service = app.state.ue_service
        stats = await ue_service.get_ue_stats(imsi)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到 IMSI {imsi} 的統計資料",
            )

        return UEStatsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("取得 UE 統計失敗", imsi=imsi, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "取得 UE 統計失敗", "message": str(e)},
        )


@app.get("/api/v1/ue", tags=["UE 管理"])
async def list_ues():
    """
    列出所有已註冊的 UE

    Returns:
        所有 UE 的資訊列表
    """
    try:
        ue_service = app.state.ue_service
        ues = await ue_service.list_all_ues()

        return CustomJSONResponse(content=ues)

    except Exception as e:
        logger.error("列出 UE 失敗", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "列出 UE 失敗", "message": str(e)},
        )


# ===== Slice 管理端點 =====


@app.post(
    "/api/v1/slice/switch", response_model=SliceSwitchResponse, tags=["Slice 管理"]
)
async def switch_slice(request: SliceSwitchRequest):
    """
    切換 UE 的 Network Slice

    Args:
        request: Slice 切換請求，包含 IMSI 和目標 Slice

    Returns:
        切換結果和新的 Slice 資訊
    """
    try:
        slice_service = app.state.slice_service

        # 記錄切換請求
        logger.info(
            "收到 Slice 切換請求", imsi=request.imsi, target_slice=request.target_slice
        )

        # 將字串轉換為 SliceType 枚舉
        try:
            target_slice_enum = SliceType(request.target_slice)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支援的 Slice 類型: {request.target_slice}",
            )

        # 執行切換
        result = await slice_service.switch_slice(
            imsi=request.imsi, target_slice=target_slice_enum
        )

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Slice 切換失敗"),
            )

        # 更新指標
        SLICE_SWITCH_COUNT.labels(
            from_slice=result.get("previous_slice", "unknown"),
            to_slice=request.target_slice,
            status="success",
        ).inc()

        logger.info(
            "Slice 切換成功", imsi=request.imsi, target_slice=request.target_slice
        )

        # 構建回應
        from .models.responses import SliceInfo

        previous_slice = result.get("previous_slice") or "unknown"
        current_slice = result.get("current_slice") or "unknown"

        previous_slice_info = SliceInfo(
            sst=1 if previous_slice == "eMBB" else 2,
            sd="0x111111" if previous_slice == "eMBB" else "0x222222",
            slice_type=previous_slice,
        )

        new_slice_info = SliceInfo(
            sst=1 if current_slice == "eMBB" else 2,
            sd="0x111111" if current_slice == "eMBB" else "0x222222",
            slice_type=current_slice,
        )

        response_data = {
            "imsi": request.imsi,
            "previous_slice": {
                "sst": previous_slice_info.sst,
                "sd": previous_slice_info.sd,
                "slice_type": previous_slice_info.slice_type,
            },
            "new_slice": {
                "sst": new_slice_info.sst,
                "sd": new_slice_info.sd,
                "slice_type": new_slice_info.slice_type,
            },
            "switch_time": datetime.now().isoformat(),
            "success": True,
            "message": result.get("message", "Slice 切換成功"),
        }

        return CustomJSONResponse(content=response_data)

    except HTTPException:
        # 更新失敗指標
        SLICE_SWITCH_COUNT.labels(
            from_slice="unknown", to_slice=request.target_slice, status="error"
        ).inc()
        raise
    except Exception as e:
        logger.error(
            "Slice 切換失敗",
            imsi=request.imsi,
            target_slice=request.target_slice,
            error=str(e),
        )

        # 更新失敗指標
        SLICE_SWITCH_COUNT.labels(
            from_slice="unknown", to_slice=request.target_slice, status="error"
        ).inc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Slice 切換失敗", "message": str(e)},
        )


@app.get("/api/v1/slice/types", tags=["Slice 管理"])
async def get_slice_types():
    """
    取得可用的 Slice 類型

    Returns:
        支援的 Slice 類型列表及其配置
    """
    try:
        slice_service = app.state.slice_service
        slice_info = await slice_service.get_slice_types()

        return slice_info

    except Exception as e:
        logger.error("取得 Slice 類型失敗", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "取得 Slice 類型失敗", "message": str(e)},
        )


# ===== UERANSIM 動態配置端點 =====


@app.post(
    "/api/v1/ueransim/config/generate",
    response_model=UERANSIMConfigResponse,
    tags=["UERANSIM 配置"],
)
async def generate_ueransim_config(request: UERANSIMConfigRequest):
    """
    動態生成UERANSIM配置

    根據衛星和UAV位置信息，動態生成適合的UERANSIM配置文件。
    支援多種場景：LEO衛星過境、UAV編隊飛行、衛星間切換等。

    Args:
        request: UERANSIM配置生成請求

    Returns:
        生成的UERANSIM配置和相關信息
    """
    try:
        ueransim_service = app.state.ueransim_service

        logger.info(
            "收到UERANSIM配置生成請求",
            scenario=request.scenario.value,
            satellite_id=request.satellite.id if request.satellite else None,
            uav_id=request.uav.id if request.uav else None,
        )

        # 生成配置
        result = await ueransim_service.generate_config(request)

        if result.success:
            logger.info(
                "UERANSIM配置生成成功",
                scenario=result.scenario_type,
                message=result.message,
            )
        else:
            logger.warning(
                "UERANSIM配置生成失敗",
                scenario=result.scenario_type,
                message=result.message,
            )

        return result

    except Exception as e:
        logger.error(
            "UERANSIM配置生成異常", scenario=request.scenario.value, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "配置生成失敗", "message": str(e)},
        )


@app.get("/api/v1/ueransim/templates", tags=["UERANSIM 配置"])
async def get_ueransim_templates():
    """
    取得可用的UERANSIM配置模板

    Returns:
        可用的配置模板列表
    """
    try:
        ueransim_service = app.state.ueransim_service
        templates = await ueransim_service.get_available_templates()

        return {"success": True, "templates": templates, "total_count": len(templates)}

    except Exception as e:
        logger.error("取得UERANSIM模板失敗", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "取得模板失敗", "message": str(e)},
        )


@app.get("/api/v1/ueransim/scenarios", tags=["UERANSIM 配置"])
async def get_supported_scenarios():
    """
    取得支援的場景類型

    Returns:
        支援的場景類型列表
    """
    from .models.ueransim_models import ScenarioType

    scenarios = [
        {
            "type": ScenarioType.LEO_SATELLITE_PASS.value,
            "name": "LEO衛星過境",
            "description": "低軌衛星過境通信場景",
            "required_params": ["satellite", "uav", "network_params"],
        },
        {
            "type": ScenarioType.UAV_FORMATION_FLIGHT.value,
            "name": "UAV編隊飛行",
            "description": "多UAV協調編隊通信場景",
            "required_params": ["satellite", "uav_formation", "network_params"],
        },
        {
            "type": ScenarioType.HANDOVER_BETWEEN_SATELLITES.value,
            "name": "衛星間切換",
            "description": "UAV在不同衛星間的切換場景",
            "required_params": [
                "source_satellite",
                "target_satellite",
                "uav",
                "handover_params",
            ],
        },
        {
            "type": ScenarioType.POSITION_UPDATE.value,
            "name": "位置更新",
            "description": "衛星或UAV位置變更的配置更新",
            "required_params": ["satellite", "uav"],
        },
    ]

    return {"success": True, "scenarios": scenarios, "total_count": len(scenarios)}


# ===== 衛星-gNodeB 映射端點 =====


@app.post("/api/v1/satellite-gnb/mapping", tags=["衛星-gNodeB 映射"])
async def convert_satellite_to_gnb(
    satellite_id: int,
    uav_latitude: Optional[float] = None,
    uav_longitude: Optional[float] = None,
    uav_altitude: Optional[float] = None,
    frequency: Optional[int] = 2100,
    bandwidth: Optional[int] = 20,
):
    """
    將衛星位置轉換為 gNodeB 參數

    **實現 TODO 項目 4：衛星位置轉換為 gNodeB 參數**

    此端點整合 simworld 的 Skyfield 計算結果，將衛星 ECEF/ENU 坐標
    轉換為 UERANSIM gNodeB 配置參數，實現衛星作為 5G 基站的模擬。

    Args:
        satellite_id: 衛星 ID
        uav_latitude: UAV 緯度（可選，用於相對計算）
        uav_longitude: UAV 經度（可選，用於相對計算）
        uav_altitude: UAV 高度（可選，用於相對計算）
        frequency: 工作頻率 (MHz)
        bandwidth: 頻寬 (MHz)

    Returns:
        包含衛星信息、ECEF 坐標、無線參數和 gNodeB 配置的完整映射結果
    """
    try:
        satellite_gnb_service = app.state.satellite_gnb_service

        # 構建 UAV 位置對象（如果提供了參數）
        uav_position = None
        if all(
            param is not None for param in [uav_latitude, uav_longitude, uav_altitude]
        ):
            from .models.ueransim_models import UAVPosition

            uav_position = UAVPosition(
                id="mapping-request-uav",
                latitude=uav_latitude,
                longitude=uav_longitude,
                altitude=uav_altitude,
            )

        # 構建網路參數
        from .models.ueransim_models import NetworkParameters

        network_params = NetworkParameters(frequency=frequency, bandwidth=bandwidth)

        # 執行衛星位置轉換
        mapping_result = await satellite_gnb_service.convert_satellite_to_gnb_config(
            satellite_id=satellite_id,
            uav_position=uav_position,
            network_params=network_params,
        )

        return CustomJSONResponse(
            content={
                "success": True,
                "message": f"衛星 {satellite_id} 位置轉換完成",
                "data": mapping_result,
                "conversion_info": {
                    "skyfield_integration": "已整合 simworld Skyfield 計算",
                    "coordinate_conversion": "ECEF/ENU 坐標轉換完成",
                    "gnb_mapping": "gNodeB 參數映射完成",
                },
            }
        )

    except Exception as e:
        logger.error("衛星位置轉換失敗", satellite_id=satellite_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"衛星位置轉換失敗: {str(e)}")


@app.get("/api/v1/satellite-gnb/batch-mapping", tags=["衛星-gNodeB 映射"])
async def batch_convert_satellites_to_gnb(
    satellite_ids: str,  # 逗號分隔的衛星 ID
    uav_latitude: Optional[float] = None,
    uav_longitude: Optional[float] = None,
    uav_altitude: Optional[float] = None,
):
    """
    批量將多個衛星位置轉換為 gNodeB 參數

    支援同時處理多個衛星的位置轉換，提高效率

    Args:
        satellite_ids: 逗號分隔的衛星 ID 列表 (例如: "1,2,3")
        uav_latitude: UAV 緯度（可選）
        uav_longitude: UAV 經度（可選）
        uav_altitude: UAV 高度（可選）

    Returns:
        所有衛星的映射結果字典
    """
    try:
        satellite_gnb_service = app.state.satellite_gnb_service

        # 解析衛星 ID 列表
        try:
            sat_ids = [int(sid.strip()) for sid in satellite_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400, detail="無效的衛星 ID 格式，請使用逗號分隔的整數"
            )

        if len(sat_ids) > 20:  # 限制批量處理數量
            raise HTTPException(
                status_code=400, detail="批量處理衛星數量不能超過 20 個"
            )

        # 構建 UAV 位置對象（如果提供了參數）
        uav_position = None
        if all(
            param is not None for param in [uav_latitude, uav_longitude, uav_altitude]
        ):
            from .models.ueransim_models import UAVPosition

            uav_position = UAVPosition(
                id="batch-mapping-uav",
                latitude=uav_latitude,
                longitude=uav_longitude,
                altitude=uav_altitude,
            )

        # 執行批量轉換
        batch_results = await satellite_gnb_service.get_multiple_satellite_configs(
            satellite_ids=sat_ids, uav_position=uav_position
        )

        # 統計成功和失敗的數量
        successful_count = sum(
            1 for result in batch_results.values() if result.get("success")
        )
        failed_count = len(batch_results) - successful_count

        return CustomJSONResponse(
            content={
                "success": True,
                "message": f"批量轉換完成，成功 {successful_count} 個，失敗 {failed_count} 個",
                "satellite_configs": batch_results,
                "summary": {
                    "total_satellites": len(sat_ids),
                    "successful_conversions": successful_count,
                    "failed_conversions": failed_count,
                    "success_rate": f"{(successful_count / len(sat_ids) * 100):.1f}%",
                },
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("批量衛星位置轉換失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"批量衛星位置轉換失敗: {str(e)}")


@app.post("/api/v1/satellite-gnb/start-tracking", tags=["衛星-gNodeB 映射"])
async def start_continuous_tracking(satellite_ids: str, update_interval: int = 30):
    """
    開始持續追蹤衛星位置並更新 gNodeB 配置

    實現事件驅動的配置更新機制，確保 gNodeB 配置能實時跟隨衛星移動

    Args:
        satellite_ids: 逗號分隔的衛星 ID 列表
        update_interval: 更新間隔（秒），默認 30 秒

    Returns:
        追蹤任務啟動狀態
    """
    try:
        satellite_gnb_service = app.state.satellite_gnb_service

        # 解析衛星 ID 列表
        try:
            sat_ids = [int(sid.strip()) for sid in satellite_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400, detail="無效的衛星 ID 格式，請使用逗號分隔的整數"
            )

        if update_interval < 10:
            raise HTTPException(status_code=400, detail="更新間隔不能少於 10 秒")

        # 在背景啟動持續追蹤任務
        task = asyncio.create_task(
            satellite_gnb_service.update_gnb_positions_continuously(
                satellite_ids=sat_ids, update_interval=update_interval
            )
        )

        # 將任務存儲到應用狀態中（可選，用於管理）
        if not hasattr(app.state, "tracking_tasks"):
            app.state.tracking_tasks = {}

        task_id = f"track_{'-'.join(map(str, sat_ids))}_{update_interval}"
        app.state.tracking_tasks[task_id] = task

        return CustomJSONResponse(
            content={
                "success": True,
                "message": "衛星位置持續追蹤已啟動",
                "tracking_info": {
                    "task_id": task_id,
                    "satellite_ids": sat_ids,
                    "update_interval_seconds": update_interval,
                    "estimated_updates_per_hour": 3600 // update_interval,
                },
                "note": "追蹤將在背景持續進行，配置更新將通過 Redis 事件發布",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("啟動衛星追蹤失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"啟動衛星追蹤失敗: {str(e)}")


# ===== OneWeb 衛星 gNodeB 管理 =====


@app.post("/api/v1/oneweb/constellation/initialize", tags=["OneWeb 衛星 gNodeB"])
async def initialize_oneweb_constellation():
    """
    初始化 OneWeb 衛星群作為 gNodeB 節點

    建立 OneWeb LEO 衛星群的 5G NTN gNodeB 配置，包括軌道追蹤和動態配置管理

    Returns:
        OneWeb 星座初始化結果
    """
    try:
        oneweb_service = app.state.oneweb_service

        result = await oneweb_service.initialize_oneweb_constellation()

        return CustomJSONResponse(
            content={
                "success": True,
                "message": "OneWeb 衛星群初始化成功",
                "initialization_result": result,
                "next_steps": [
                    "使用 /api/v1/oneweb/orbital-tracking/start 啟動軌道追蹤",
                    "使用 /api/v1/oneweb/constellation/status 查看星座狀態",
                    "使用 /api/v1/oneweb/ueransim/deploy 部署 UERANSIM 配置",
                ],
            }
        )

    except Exception as e:
        logger.error("OneWeb 星座初始化失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"OneWeb 星座初始化失敗: {str(e)}")


@app.post("/api/v1/oneweb/orbital-tracking/start", tags=["OneWeb 衛星 gNodeB"])
async def start_oneweb_orbital_tracking(
    satellite_ids: Optional[str] = None, update_interval: int = 30
):
    """
    啟動 OneWeb 衛星軌道追蹤

    實現實時軌道數據同步和動態 gNodeB 配置更新

    Args:
        satellite_ids: 要追蹤的衛星 ID 列表（逗號分隔），None 表示追蹤所有
        update_interval: 軌道更新間隔（秒）

    Returns:
        軌道追蹤啟動狀態
    """
    try:
        oneweb_service = app.state.oneweb_service

        # 解析衛星 ID 列表
        sat_ids = None
        if satellite_ids:
            try:
                sat_ids = [int(sid.strip()) for sid in satellite_ids.split(",")]
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="無效的衛星 ID 格式，請使用逗號分隔的整數"
                )

        if update_interval < 10:
            raise HTTPException(status_code=400, detail="更新間隔不能少於 10 秒")

        # 啟動軌道追蹤
        tracking_result = await oneweb_service.start_orbital_tracking(
            satellite_ids=sat_ids, update_interval_seconds=update_interval
        )

        return CustomJSONResponse(
            content={
                "success": True,
                "message": "OneWeb 軌道追蹤已啟動",
                "tracking_result": tracking_result,
                "monitoring": {
                    "status_endpoint": "/api/v1/oneweb/constellation/status",
                    "stop_endpoint": f"/api/v1/oneweb/orbital-tracking/stop/{tracking_result['task_id']}",
                },
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("啟動 OneWeb 軌道追蹤失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"啟動軌道追蹤失敗: {str(e)}")


@app.delete(
    "/api/v1/oneweb/orbital-tracking/stop/{task_id}", tags=["OneWeb 衛星 gNodeB"]
)
async def stop_oneweb_orbital_tracking(task_id: str):
    """
    停止 OneWeb 軌道追蹤任務

    Args:
        task_id: 追蹤任務 ID

    Returns:
        停止結果
    """
    try:
        oneweb_service = app.state.oneweb_service

        success = await oneweb_service.stop_orbital_tracking(task_id)

        if success:
            return CustomJSONResponse(
                content={"success": True, "message": f"軌道追蹤任務 {task_id} 已停止"}
            )
        else:
            raise HTTPException(status_code=404, detail=f"追蹤任務 {task_id} 不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("停止軌道追蹤失敗", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"停止軌道追蹤失敗: {str(e)}")


@app.get("/api/v1/oneweb/constellation/status", tags=["OneWeb 衛星 gNodeB"])
async def get_oneweb_constellation_status():
    """
    獲取 OneWeb 星座狀態

    Returns:
        OneWeb 星座的詳細狀態信息
    """
    try:
        oneweb_service = app.state.oneweb_service

        status = await oneweb_service.get_constellation_status()

        return CustomJSONResponse(
            content={
                "success": True,
                "constellation_status": status,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error("獲取 OneWeb 星座狀態失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"獲取星座狀態失敗: {str(e)}")


@app.post("/api/v1/oneweb/ueransim/deploy", tags=["OneWeb 衛星 gNodeB"])
async def deploy_oneweb_ueransim_configs():
    """
    部署 OneWeb 衛星的 UERANSIM gNodeB 配置

    為所有活躍的 OneWeb 衛星生成並部署 UERANSIM 配置文件

    Returns:
        部署結果
    """
    try:
        oneweb_service = app.state.oneweb_service

        # 獲取所有活躍衛星
        constellation_status = await oneweb_service.get_constellation_status()
        active_satellites = constellation_status["satellite_status"]

        if not active_satellites:
            raise HTTPException(status_code=400, detail="沒有活躍的 OneWeb 衛星可部署")

        deployment_results = []
        for satellite in active_satellites:
            satellite_id = satellite["satellite_id"]

            try:
                # 為每個衛星重新生成配置
                await oneweb_service._regenerate_ueransim_config(satellite_id)

                deployment_results.append(
                    {
                        "satellite_id": satellite_id,
                        "satellite_name": satellite["name"],
                        "status": "deployed",
                        "config_file": f"/tmp/ueransim_configs/gnb-oneweb-{satellite_id}.yaml",
                    }
                )

            except Exception as e:
                deployment_results.append(
                    {
                        "satellite_id": satellite_id,
                        "satellite_name": satellite["name"],
                        "status": "failed",
                        "error": str(e),
                    }
                )

        successful_deployments = sum(
            1 for result in deployment_results if result["status"] == "deployed"
        )

        return CustomJSONResponse(
            content={
                "success": True,
                "message": f"UERANSIM 配置部署完成，成功 {successful_deployments} 個",
                "deployment_results": deployment_results,
                "summary": {
                    "total_satellites": len(active_satellites),
                    "successful_deployments": successful_deployments,
                    "failed_deployments": len(deployment_results)
                    - successful_deployments,
                },
                "config_directory": "/tmp/ueransim_configs",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("部署 OneWeb UERANSIM 配置失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"部署 UERANSIM 配置失敗: {str(e)}")


# ===== Sionna 整合 API 端點 =====


@app.post("/api/v1/sionna/channel-simulation", tags=["Sionna 整合"])
async def request_sionna_channel_simulation(
    ue_positions: List[Dict[str, Any]],
    gnb_positions: List[Dict[str, Any]],
    environment_type: str = "urban",
    frequency_ghz: float = 2.1,
    bandwidth_mhz: float = 20,
):
    """請求 Sionna 通道模擬"""
    try:
        sionna_service = app.state.sionna_service

        result = await sionna_service.quick_channel_simulation_and_apply(
            ue_positions=ue_positions,
            gnb_positions=gnb_positions,
            environment_type=environment_type,
            frequency_ghz=frequency_ghz,
            bandwidth_mhz=bandwidth_mhz,
        )

        return CustomJSONResponse(content=result)

    except Exception as e:
        logger.error(f"Sionna 通道模擬失敗: {e}")
        raise HTTPException(status_code=500, detail=f"通道模擬失敗: {str(e)}")


@app.get("/api/v1/sionna/active-models", tags=["Sionna 整合"])
async def get_active_channel_models():
    """獲取活躍的通道模型"""
    try:
        sionna_service = app.state.sionna_service
        models = await sionna_service.get_active_channel_models()

        result = {
            "active_models": models,
            "count": len(models),
            "timestamp": datetime.utcnow().isoformat(),
        }

        return CustomJSONResponse(content=result)

    except Exception as e:
        logger.error(f"獲取活躍通道模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


@app.get("/api/v1/sionna/status", tags=["Sionna 整合"])
async def get_sionna_service_status():
    """獲取 Sionna 整合服務狀態"""
    try:
        sionna_service = app.state.sionna_service
        status = sionna_service.get_service_status()

        return CustomJSONResponse(content=status)

    except Exception as e:
        logger.error(f"獲取 Sionna 服務狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"狀態查詢失敗: {str(e)}")


@app.post("/api/v1/sionna/quick-test", tags=["Sionna 整合"])
async def sionna_quick_test():
    """Sionna 整合快速測試"""
    try:
        # 預設測試配置
        ue_positions = [
            {"position": [100, 0, 1.5]},
            {"position": [500, 200, 1.5]},
            {"position": [800, -100, 1.5]},
        ]

        gnb_positions = [{"position": [0, 0, 30]}, {"position": [1000, 0, 30]}]

        sionna_service = app.state.sionna_service

        result = await sionna_service.quick_channel_simulation_and_apply(
            ue_positions=ue_positions,
            gnb_positions=gnb_positions,
            environment_type="urban",
            frequency_ghz=2.1,
            bandwidth_mhz=20,
        )

        test_result = {
            "test_completed": True,
            "test_config": {
                "ue_count": len(ue_positions),
                "gnb_count": len(gnb_positions),
                "environment": "urban",
                "frequency_ghz": 2.1,
                "bandwidth_mhz": 20,
            },
            "result": result,
        }

        return CustomJSONResponse(content=test_result)

    except Exception as e:
        logger.error(f"Sionna 快速測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"測試失敗: {str(e)}")


# ===== 干擾控制與 AI-RAN 端點 =====


@app.post("/api/v1/interference/jammer-scenario", tags=["干擾控制"])
async def create_jammer_scenario(
    scenario_name: str,
    jammer_configs: List[Dict[str, Any]],
    victim_positions: List[List[float]],
    victim_frequency_mhz: float = 2150.0,
    victim_bandwidth_mhz: float = 20.0,
):
    """創建干擾場景 - 使用事件驅動架構"""
    try:
        # 使用新的事件驅動干擾控制服務
        interference_service = app.state.interference_service

        result = await interference_service.create_jammer_scenario(
            scenario_name=scenario_name,
            jammer_configs=jammer_configs,
            victim_positions=victim_positions,
            victim_frequency_mhz=victim_frequency_mhz,
            victim_bandwidth_mhz=victim_bandwidth_mhz,
        )

        return CustomJSONResponse(content=result)

    except Exception as e:
        logger.error(f"創建干擾場景失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建干擾場景失敗: {str(e)}")


@app.get("/api/v1/interference/status", tags=["干擾控制"])
async def get_interference_control_status():
    """獲取干擾控制服務狀態 - 事件驅動版本"""
    try:
        # 使用新的事件驅動干擾控制服務
        interference_service = app.state.interference_service
        event_bus = app.state.event_bus

        # 獲取服務狀態
        service_status = interference_service.get_service_status()

        # 獲取事件總線指標
        event_metrics = await event_bus.get_metrics()

        # 獲取詳細指標
        detailed_metrics = await interference_service.get_metrics()

        return CustomJSONResponse(
            content={
                "status": "active",
                "architecture": "event_driven",
                "service_info": service_status,
                "event_bus_metrics": event_metrics,
                "performance_metrics": detailed_metrics,
                "features": {
                    "real_time_detection": True,
                    "detection_interval_ms": interference_service.update_interval_sec
                    * 1000,
                    "ai_ran_integration": True,
                    "auto_mitigation": interference_service.auto_mitigation,
                    "event_driven": True,
                    "async_processing": True,
                },
            }
        )

    except Exception as e:
        logger.error(f"獲取干擾控制狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")


@app.post("/api/v1/interference/stop-scenario/{scenario_id}", tags=["干擾控制"])
async def stop_interference_scenario(scenario_id: str):
    """停止干擾場景"""
    try:
        interference_service = app.state.interference_service

        result = await interference_service.stop_scenario(scenario_id)

        return CustomJSONResponse(content=result)

    except Exception as e:
        logger.error(f"停止干擾場景失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止場景失敗: {str(e)}")


@app.get("/api/v1/interference/events/{scenario_id}", tags=["干擾控制"])
async def get_interference_events(scenario_id: str, limit: int = 50):
    """獲取干擾場景的事件歷史"""
    try:
        event_bus = app.state.event_bus

        # 獲取事件歷史（這裡需要實現事件查詢接口）
        # 暫時返回服務指標
        metrics = await event_bus.get_metrics()

        return CustomJSONResponse(
            content={
                "scenario_id": scenario_id,
                "events": [],  # 需要實現事件查詢
                "total_events": metrics.get("events_published", 0),
                "message": "事件歷史查詢功能開發中",
            }
        )

    except Exception as e:
        logger.error(f"獲取干擾事件失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取事件失敗: {str(e)}")


# 保留原有的 AI-RAN 決策端點（但改為事件驅動）
@app.post("/api/v1/interference/ai-ran-decision", tags=["干擾控制"])
async def request_ai_ran_decision(
    interference_detections: List[Dict[str, Any]],
    available_frequencies: List[float],
    scenario_description: str = "UERANSIM 抗干擾決策請求",
):
    """請求 AI-RAN 抗干擾決策 - 事件驅動版本"""
    try:
        # 發布 AI 決策請求事件
        event_bus = app.state.event_bus

        await event_bus.publish(
            event_type="ai_ran.decision_requested",
            data={
                "interference_detections": interference_detections,
                "available_frequencies": available_frequencies,
                "scenario_description": scenario_description,
                "request_source": "api_endpoint",
            },
            source="interference_api",
            priority=event_bus.EventPriority.HIGH,
        )

        return CustomJSONResponse(
            content={
                "status": "request_submitted",
                "message": "AI-RAN 決策請求已提交到事件總線",
                "architecture": "event_driven",
                "detections_count": len(interference_detections),
                "available_frequencies": available_frequencies,
            }
        )

    except Exception as e:
        logger.error(f"AI-RAN 決策請求失敗: {e}")
        raise HTTPException(status_code=500, detail=f"決策請求失敗: {str(e)}")


# 更新快速演示端點
@app.post("/api/v1/interference/quick-demo", tags=["干擾控制"])
async def interference_quick_demo():
    """干擾控制快速演示 - 事件驅動版本"""
    try:
        interference_service = app.state.interference_service

        # 創建演示場景
        demo_result = await interference_service.create_jammer_scenario(
            scenario_name="EventDriven_QuickDemo",
            jammer_configs=[
                {
                    "jammer_type": "constant",
                    "power_dbm": 20,
                    "frequency_mhz": 2150.0,
                    "bandwidth_mhz": 20.0,
                    "position": [25.0331, 121.5654, 10.0],
                }
            ],
            victim_positions=[[25.0321, 121.5644, 1.5]],
            victim_frequency_mhz=2150.0,
            victim_bandwidth_mhz=20.0,
        )

        # 等待一些事件處理
        await asyncio.sleep(2.0)

        # 獲取服務指標
        metrics = await interference_service.get_metrics()

        return CustomJSONResponse(
            content={
                "demo_status": "completed",
                "architecture": "event_driven",
                "scenario_result": demo_result,
                "performance_metrics": metrics,
                "features_demonstrated": [
                    "實時干擾檢測 (<100ms)",
                    "事件驅動架構",
                    "異步處理",
                    "AI-RAN 自動決策",
                    "事件溯源",
                ],
            }
        )

    except Exception as e:
        logger.error(f"干擾控制演示失敗: {e}")
        raise HTTPException(status_code=500, detail=f"演示失敗: {str(e)}")


@app.post("/api/v1/interference/apply-strategy", tags=["干擾控制"])
async def apply_anti_jamming_strategy(
    ai_decision: Dict[str, Any],
    ue_config_path: Optional[str] = None,
    gnb_config_path: Optional[str] = None,
):
    """應用抗干擾策略 - 事件驅動版本"""
    try:
        event_bus = app.state.event_bus

        # 發布策略應用事件
        await event_bus.publish(
            event_type="mitigation.strategy_applied",
            data={
                "ai_decision": ai_decision,
                "ue_config_path": ue_config_path,
                "gnb_config_path": gnb_config_path,
                "apply_time": datetime.utcnow().isoformat(),
            },
            source="interference_api",
            priority=event_bus.EventPriority.HIGH,
        )

        return CustomJSONResponse(
            content={
                "status": "strategy_applied",
                "message": "抗干擾策略已通過事件總線應用",
                "ai_decision": ai_decision,
                "architecture": "event_driven",
            }
        )

    except Exception as e:
        logger.error(f"應用抗干擾策略失敗: {e}")
        raise HTTPException(status_code=500, detail=f"策略應用失敗: {str(e)}")


# ===== UAV UE 管理端點 =====


@app.post("/api/v1/uav/trajectory", tags=["UAV UE 管理"])
async def create_trajectory(request: TrajectoryCreateRequest):
    """
    創建 UAV 飛行軌跡

    Args:
        request: 軌跡創建請求，包含軌跡名稱、描述、任務類型和軌跡點列表

    Returns:
        創建的軌跡詳情，包含計算的總距離和預估飛行時間
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        result = await uav_ue_service.create_trajectory(request)
        return CustomJSONResponse(content=result.dict())
    except Exception as e:
        logger.error(f"創建軌跡失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建軌跡失敗: {str(e)}")


@app.get("/api/v1/uav/trajectory/{trajectory_id}", tags=["UAV UE 管理"])
async def get_trajectory(trajectory_id: str):
    """
    獲取指定軌跡詳情

    Args:
        trajectory_id: 軌跡 ID

    Returns:
        軌跡詳情，包含統計信息
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        result = await uav_ue_service.get_trajectory(trajectory_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"找不到軌跡: {trajectory_id}")

        return CustomJSONResponse(content=result.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取軌跡失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取軌跡失敗: {str(e)}")


@app.get("/api/v1/uav/trajectory", tags=["UAV UE 管理"])
async def list_trajectories(limit: int = 100, offset: int = 0):
    """
    列出所有軌跡

    Args:
        limit: 每頁項目數量（預設 100）
        offset: 偏移量（預設 0）

    Returns:
        軌跡列表和總數
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        result = await uav_ue_service.list_trajectories(limit=limit, offset=offset)
        return CustomJSONResponse(content=result.dict())
    except Exception as e:
        logger.error(f"列出軌跡失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出軌跡失敗: {str(e)}")


@app.put("/api/v1/uav/trajectory/{trajectory_id}", tags=["UAV UE 管理"])
async def update_trajectory(trajectory_id: str, request: TrajectoryUpdateRequest):
    """
    更新軌跡

    Args:
        trajectory_id: 軌跡 ID
        request: 軌跡更新請求

    Returns:
        更新後的軌跡詳情
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        result = await uav_ue_service.update_trajectory(trajectory_id, request)

        if not result:
            raise HTTPException(status_code=404, detail=f"找不到軌跡: {trajectory_id}")

        return CustomJSONResponse(content=result.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新軌跡失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新軌跡失敗: {str(e)}")


@app.delete("/api/v1/uav/trajectory/{trajectory_id}", tags=["UAV UE 管理"])
async def delete_trajectory(trajectory_id: str):
    """
    刪除軌跡

    Args:
        trajectory_id: 軌跡 ID

    Returns:
        刪除結果
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        success = await uav_ue_service.delete_trajectory(trajectory_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"找不到軌跡: {trajectory_id}")

        return CustomJSONResponse(content={"success": True, "message": "軌跡刪除成功"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除軌跡失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除軌跡失敗: {str(e)}")


@app.post("/api/v1/uav", tags=["UAV UE 管理"])
async def create_uav(request: UAVCreateRequest):
    """
    創建新 UAV

    Args:
        request: UAV 創建請求，包含名稱、UE 配置和初始位置

    Returns:
        創建的 UAV 狀態
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        result = await uav_ue_service.create_uav(request)
        return CustomJSONResponse(content=result.dict())
    except Exception as e:
        logger.error(f"創建 UAV 失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建 UAV 失敗: {str(e)}")


@app.get("/api/v1/uav/{uav_id}", tags=["UAV UE 管理"])
async def get_uav_status(uav_id: str):
    """
    獲取 UAV 狀態

    Args:
        uav_id: UAV ID

    Returns:
        UAV 詳細狀態，包含位置、信號質量、任務進度等
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        result = await uav_ue_service.get_uav_status(uav_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"找不到 UAV: {uav_id}")

        return CustomJSONResponse(content=result.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取 UAV 狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取 UAV 狀態失敗: {str(e)}")


@app.get("/api/v1/uav", tags=["UAV UE 管理"])
async def list_uavs(limit: int = 100, offset: int = 0):
    """
    列出所有 UAV

    Args:
        limit: 每頁項目數量（預設 100）
        offset: 偏移量（預設 0）

    Returns:
        UAV 列表和總數
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        result = await uav_ue_service.list_uavs(limit=limit, offset=offset)
        return CustomJSONResponse(content=result.dict())
    except Exception as e:
        logger.error(f"列出 UAV 失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出 UAV 失敗: {str(e)}")


@app.post("/api/v1/uav/{uav_id}/mission/start", tags=["UAV UE 管理"])
async def start_uav_mission(uav_id: str, request: UAVMissionStartRequest):
    """
    開始 UAV 任務

    Args:
        uav_id: UAV ID
        request: 任務開始請求，包含軌跡 ID、開始時間和速度倍數

    Returns:
        更新後的 UAV 狀態
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        result = await uav_ue_service.start_mission(uav_id, request)

        if not result:
            raise HTTPException(status_code=404, detail=f"找不到 UAV: {uav_id}")

        return CustomJSONResponse(content=result.dict())
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"開始 UAV 任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"開始任務失敗: {str(e)}")


@app.post("/api/v1/uav/{uav_id}/mission/stop", tags=["UAV UE 管理"])
async def stop_uav_mission(uav_id: str):
    """
    停止 UAV 任務

    Args:
        uav_id: UAV ID

    Returns:
        更新後的 UAV 狀態
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        result = await uav_ue_service.stop_mission(uav_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"找不到 UAV: {uav_id}")

        return CustomJSONResponse(content=result.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止 UAV 任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止任務失敗: {str(e)}")


@app.put("/api/v1/uav/{uav_id}/position", tags=["UAV UE 管理"])
async def update_uav_position(uav_id: str, request: UAVPositionUpdateRequest):
    """
    更新 UAV 位置

    Args:
        uav_id: UAV ID
        request: 位置更新請求，包含新位置和可選的信號質量

    Returns:
        更新後的 UAV 狀態
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        result = await uav_ue_service.update_uav_position(uav_id, request)

        if not result:
            raise HTTPException(status_code=404, detail=f"找不到 UAV: {uav_id}")

        return CustomJSONResponse(content=result.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新 UAV 位置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新位置失敗: {str(e)}")


@app.delete("/api/v1/uav/{uav_id}", tags=["UAV UE 管理"])
async def delete_uav(uav_id: str):
    """
    刪除 UAV

    Args:
        uav_id: UAV ID

    Returns:
        刪除結果
    """
    try:
        uav_ue_service = app.state.uav_ue_service
        success = await uav_ue_service.delete_uav(uav_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"找不到 UAV: {uav_id}")

        return CustomJSONResponse(content={"success": True, "message": "UAV 刪除成功"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除 UAV 失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除 UAV 失敗: {str(e)}")


@app.post("/api/v1/uav/demo/quick-test", tags=["UAV UE 管理"])
async def uav_quick_demo():
    """
    UAV UE 快速演示

    創建示例軌跡和 UAV，展示完整的 UAV UE 模擬流程

    Returns:
        演示結果和創建的資源 ID
    """
    try:
        uav_ue_service = app.state.uav_ue_service

        # 1. 創建示例軌跡
        from datetime import datetime, timedelta

        base_time = datetime.utcnow()
        demo_points = [
            TrajectoryPoint(
                timestamp=base_time,
                latitude=24.7881,
                longitude=120.9971,
                altitude=100,
                speed=20.0,
                heading=45.0,
            ),
            TrajectoryPoint(
                timestamp=base_time + timedelta(minutes=5),
                latitude=24.8000,
                longitude=121.0100,
                altitude=120,
                speed=25.0,
                heading=90.0,
            ),
            TrajectoryPoint(
                timestamp=base_time + timedelta(minutes=10),
                latitude=24.8200,
                longitude=121.0300,
                altitude=150,
                speed=30.0,
                heading=135.0,
            ),
            TrajectoryPoint(
                timestamp=base_time + timedelta(minutes=15),
                latitude=24.8100,
                longitude=121.0500,
                altitude=100,
                speed=15.0,
                heading=180.0,
            ),
        ]

        trajectory_request = TrajectoryCreateRequest(
            name="演示軌跡_偵察任務",
            description="UAV UE 快速演示軌跡，模擬偵察任務",
            mission_type="reconnaissance",
            points=demo_points,
        )

        trajectory = await uav_ue_service.create_trajectory(trajectory_request)

        # 2. 創建示例 UAV
        demo_ue_config = UAVUEConfig(
            imsi="999700000000001",
            key="465B5CE8B199B49FAA5F0A2EE238A6BC",
            opc="E8ED289DEBA952E4283B54E88E6183CA",
            plmn="99970",
            apn="internet",
            slice_nssai={"sst": 1, "sd": "000001"},
            gnb_ip="172.20.0.40",
            gnb_port=38412,
            power_dbm=23.0,
            frequency_mhz=2150.0,
            bandwidth_mhz=20.0,
        )

        demo_position = UAVPosition(
            latitude=demo_points[0].latitude,
            longitude=demo_points[0].longitude,
            altitude=demo_points[0].altitude,
            speed=demo_points[0].speed,
            heading=demo_points[0].heading,
        )

        uav_request = UAVCreateRequest(
            name="演示UAV_偵察機",
            ue_config=demo_ue_config,
            initial_position=demo_position,
        )

        uav = await uav_ue_service.create_uav(uav_request)

        # 3. 開始演示任務
        mission_request = UAVMissionStartRequest(
            trajectory_id=trajectory.trajectory_id, speed_factor=2.0  # 加速演示
        )

        mission_status = await uav_ue_service.start_mission(uav.uav_id, mission_request)

        demo_result = {
            "success": True,
            "message": "UAV UE 快速演示啟動成功",
            "demo_resources": {
                "trajectory": {
                    "id": trajectory.trajectory_id,
                    "name": trajectory.name,
                    "total_distance_km": trajectory.total_distance_km,
                    "estimated_duration_minutes": trajectory.estimated_duration_minutes,
                },
                "uav": {
                    "id": uav.uav_id,
                    "name": uav.name,
                    "flight_status": mission_status.flight_status,
                    "ue_connection_status": mission_status.ue_connection_status,
                },
            },
            "demo_instructions": [
                f"1. 追蹤 UAV 狀態: GET /api/v1/uav/{uav.uav_id}",
                f"2. 查看軌跡詳情: GET /api/v1/uav/trajectory/{trajectory.trajectory_id}",
                f"3. 停止任務: POST /api/v1/uav/{uav.uav_id}/mission/stop",
                f"4. 清理資源: DELETE /api/v1/uav/{uav.uav_id}, DELETE /api/v1/uav/trajectory/{trajectory.trajectory_id}",
            ],
            "estimated_demo_duration_minutes": 7.5,  # 15分鐘軌跡 ÷ 2倍速
            "monitoring_endpoints": {
                "uav_status": f"/api/v1/uav/{uav.uav_id}",
                "trajectory_info": f"/api/v1/uav/trajectory/{trajectory.trajectory_id}",
                "all_uavs": "/api/v1/uav",
                "all_trajectories": "/api/v1/uav/trajectory",
            },
        }

        return CustomJSONResponse(content=demo_result)

    except Exception as e:
        logger.error(f"UAV 快速演示失敗: {e}")
        raise HTTPException(status_code=500, detail=f"演示失敗: {str(e)}")


# ===== 錯誤處理 =====


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 異常處理器"""
    error_data = {
        "error": "HTTP Error",
        "message": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat(),
    }
    return CustomJSONResponse(
        status_code=exc.status_code,
        content=error_data,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """一般異常處理器"""
    logger.error("未處理的異常", error=str(exc), path=request.url.path)
    error_data = {
        "error": "Internal Server Error",
        "message": "系統內部錯誤",
        "status_code": 500,
        "timestamp": datetime.now().isoformat(),
    }
    return CustomJSONResponse(
        status_code=500,
        content=error_data,
    )


# ===== 根路徑 =====


@app.get("/", tags=["基本資訊"])
async def root():
    """API 根路徑，回傳基本資訊"""
    return {
        "name": "NetStack API",
        "version": "1.0.0",
        "description": "Open5GS + UERANSIM 雙 Slice 核心網管理 API",
        "docs_url": "/docs",
        "health_url": "/health",
        "metrics_url": "/metrics",
        "github": "https://github.com/yourorg/netstack",
    }


# ===== UAV-衛星連接質量評估端點 =====


@app.post(
    "/api/v1/uav-satellite/connection-quality/start-monitoring/{uav_id}",
    response_model=Dict[str, Any],
    summary="開始 UAV 連接質量監控",
    description="為指定 UAV 開始連續的連接質量監控和評估",
)
async def start_connection_quality_monitoring(
    uav_id: str,
    assessment_interval: int = Query(
        default=30, ge=10, le=300, description="評估間隔（秒）"
    ),
):
    """開始 UAV 連接質量監控"""
    try:
        await connection_quality_service.start_monitoring(uav_id, assessment_interval)

        logger.info(
            "開始 UAV 連接質量監控", uav_id=uav_id, interval=assessment_interval
        )

        return {
            "success": True,
            "message": f"已開始 UAV {uav_id} 的連接質量監控",
            "uav_id": uav_id,
            "assessment_interval_seconds": assessment_interval,
            "monitoring_endpoints": {
                "current_quality": f"/api/v1/uav-satellite/connection-quality/{uav_id}",
                "quality_history": f"/api/v1/uav-satellite/connection-quality/{uav_id}/history",
                "anomalies": f"/api/v1/uav-satellite/connection-quality/{uav_id}/anomalies",
            },
        }
    except Exception as e:
        logger.error("開始連接質量監控失敗", uav_id=uav_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"監控啟動失敗: {e}")


@app.post(
    "/api/v1/uav-satellite/connection-quality/stop-monitoring/{uav_id}",
    response_model=Dict[str, Any],
    summary="停止 UAV 連接質量監控",
    description="停止指定 UAV 的連接質量監控",
)
async def stop_connection_quality_monitoring(uav_id: str):
    """停止 UAV 連接質量監控"""
    try:
        await connection_quality_service.stop_monitoring(uav_id)

        logger.info("停止 UAV 連接質量監控", uav_id=uav_id)

        return {
            "success": True,
            "message": f"已停止 UAV {uav_id} 的連接質量監控",
            "uav_id": uav_id,
        }
    except Exception as e:
        logger.error("停止連接質量監控失敗", uav_id=uav_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"監控停止失敗: {e}")


@app.get(
    "/api/v1/uav-satellite/connection-quality/overview",
    response_model=Dict[str, Any],
    summary="獲取連接質量系統概覽",
    description="獲取所有監控中 UAV 的連接質量概覽",
)
async def get_connection_quality_overview():
    """獲取連接質量系統概覽"""
    try:
        # 直接呼叫服務的 get_system_overview 方法
        overview = await connection_quality_service.get_system_overview()

        logger.debug("獲取連接質量系統概覽")
        return overview

    except Exception as e:
        logger.error("獲取連接質量概覽失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"概覽獲取失敗: {e}")


@app.put(
    "/api/v1/uav-satellite/connection-quality/thresholds",
    response_model=Dict[str, Any],
    summary="更新連接質量評估閾值",
    description="更新連接質量評估的閾值配置",
)
async def update_connection_quality_thresholds(thresholds: ConnectionQualityThresholds):
    """更新連接質量評估閾值"""
    try:
        await connection_quality_service.update_thresholds(thresholds)

        logger.info("更新連接質量評估閾值")

        return {
            "success": True,
            "message": "連接質量評估閾值已更新",
            "updated_thresholds": thresholds.dict(),
        }

    except Exception as e:
        logger.error("更新連接質量閾值失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"閾值更新失敗: {e}")


@app.get(
    "/api/v1/uav-satellite/connection-quality/thresholds",
    response_model=ConnectionQualityThresholds,
    summary="獲取連接質量評估閾值",
    description="獲取當前的連接質量評估閾值配置",
)
async def get_connection_quality_thresholds():
    """獲取連接質量評估閾值"""
    try:
        return connection_quality_service.thresholds
    except Exception as e:
        logger.error("獲取連接質量閾值失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"閾值獲取失敗: {e}")


@app.get(
    "/api/v1/uav-satellite/connection-quality/{uav_id}",
    response_model=ConnectionQualityAssessment,
    summary="獲取 UAV 連接質量評估",
    description="獲取指定 UAV 的當前連接質量評估結果",
)
async def get_connection_quality_assessment(
    uav_id: str,
    time_window_minutes: int = Query(
        default=5, ge=1, le=60, description="評估時間窗口（分鐘）"
    ),
):
    """獲取 UAV 連接質量評估"""
    try:
        assessment = await connection_quality_service.assess_connection_quality(
            uav_id, time_window_minutes
        )

        logger.debug("獲取連接質量評估", uav_id=uav_id, grade=assessment.quality_grade)
        return assessment

    except ValueError as e:
        logger.warning("獲取連接質量評估失敗", uav_id=uav_id, error=str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("連接質量評估錯誤", uav_id=uav_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"評估失敗: {e}")


@app.get(
    "/api/v1/uav-satellite/connection-quality/{uav_id}/history",
    response_model=ConnectionQualityHistoricalData,
    summary="獲取 UAV 連接質量歷史",
    description="獲取指定 UAV 的連接質量歷史數據和趨勢分析",
)
async def get_connection_quality_history(
    uav_id: str,
    hours: int = Query(
        default=24, ge=1, le=168, description="歷史數據時間範圍（小時）"
    ),
):
    """獲取 UAV 連接質量歷史"""
    try:
        history = await connection_quality_service.get_quality_history(uav_id, hours)

        logger.debug(
            "獲取連接質量歷史",
            uav_id=uav_id,
            hours=hours,
            sample_count=history.sample_count,
        )
        return history

    except Exception as e:
        logger.error("獲取連接質量歷史失敗", uav_id=uav_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"歷史數據獲取失敗: {e}")


@app.get(
    "/api/v1/uav-satellite/connection-quality/{uav_id}/anomalies",
    response_model=List[Dict[str, Any]],
    summary="檢測 UAV 連接質量異常",
    description="檢測指定 UAV 的連接質量異常事件",
)
async def detect_connection_quality_anomalies(uav_id: str):
    """檢測 UAV 連接質量異常"""
    try:
        anomalies = await connection_quality_service.detect_anomalies(uav_id)

        logger.debug("檢測連接質量異常", uav_id=uav_id, anomaly_count=len(anomalies))

        return anomalies

    except Exception as e:
        logger.error("連接質量異常檢測失敗", uav_id=uav_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"異常檢測失敗: {e}")


@app.post(
    "/api/v1/uav-satellite/connection-quality/{uav_id}/update-signal",
    response_model=UAVConnectionQualityMetrics,
    summary="更新 UAV 信號質量數據",
    description="更新指定 UAV 的信號質量數據並計算連接質量指標",
)
async def update_uav_signal_quality_for_assessment(
    uav_id: str, signal_quality: UAVSignalQuality
):
    """更新 UAV 信號質量數據用於連接質量評估"""
    try:
        # 獲取 UAV 當前位置
        uav_status = await uav_ue_service.get_uav_status(uav_id)
        position = uav_status.current_position if uav_status else None

        # 更新連接質量服務的信號質量數據
        quality_metrics = await connection_quality_service.update_signal_quality(
            uav_id, signal_quality, position
        )

        logger.debug("更新 UAV 信號質量數據", uav_id=uav_id)
        return quality_metrics

    except Exception as e:
        logger.error("更新 UAV 信號質量失敗", uav_id=uav_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"信號質量更新失敗: {e}")


# ===== Mesh 橋接管理 =====


@app.post("/api/v1/mesh/nodes", response_model=MeshNode, tags=["Mesh 橋接"])
async def create_mesh_node(request: MeshNodeCreateRequest):
    """創建 Mesh 網路節點"""
    try:
        mesh_service = app.state.mesh_bridge_service

        node_data = {
            "name": request.name,
            "node_type": request.node_type.value,
            "ip_address": request.ip_address,
            "mac_address": request.mac_address,
            "frequency_mhz": request.frequency_mhz,
            "power_dbm": request.power_dbm,
            "protocol_type": request.protocol_type.value,
        }

        if request.position:
            node_data["position"] = request.position.dict()

        mesh_node = await mesh_service.create_mesh_node(node_data)

        if mesh_node:
            return CustomJSONResponse(
                content=jsonable_encoder(mesh_node.dict()), status_code=201
            )
        else:
            raise HTTPException(status_code=500, detail="創建 Mesh 節點失敗")

    except Exception as e:
        logger.error(f"創建 Mesh 節點 API 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


@app.get("/api/v1/mesh/nodes", tags=["Mesh 橋接"])
async def list_mesh_nodes():
    """列出所有 Mesh 網路節點"""
    try:
        mesh_service = app.state.mesh_bridge_service
        nodes = list(mesh_service.mesh_nodes.values())

        return CustomJSONResponse(
            content={
                "nodes": jsonable_encoder([node.dict() for node in nodes]),
                "total_count": len(nodes),
            }
        )

    except Exception as e:
        logger.error(f"列出 Mesh 節點 API 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


@app.get("/api/v1/mesh/nodes/{node_id}", response_model=MeshNode, tags=["Mesh 橋接"])
async def get_mesh_node(node_id: str):
    """獲取指定 Mesh 節點詳情"""
    try:
        mesh_service = app.state.mesh_bridge_service

        if node_id not in mesh_service.mesh_nodes:
            raise HTTPException(status_code=404, detail=f"Mesh 節點 {node_id} 不存在")

        mesh_node = mesh_service.mesh_nodes[node_id]
        return CustomJSONResponse(content=jsonable_encoder(mesh_node.dict()))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取 Mesh 節點 API 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


@app.put("/api/v1/mesh/nodes/{node_id}", response_model=MeshNode, tags=["Mesh 橋接"])
async def update_mesh_node(node_id: str, request: MeshNodeUpdateRequest):
    """更新 Mesh 節點配置"""
    try:
        mesh_service = app.state.mesh_bridge_service

        if node_id not in mesh_service.mesh_nodes:
            raise HTTPException(status_code=404, detail=f"Mesh 節點 {node_id} 不存在")

        mesh_node = mesh_service.mesh_nodes[node_id]

        # 更新節點屬性
        if request.name is not None:
            mesh_node.name = request.name
        if request.status is not None:
            mesh_node.status = request.status
        if request.position is not None:
            mesh_node.position = request.position
        if request.power_dbm is not None:
            mesh_node.power_dbm = request.power_dbm

        mesh_node.updated_at = datetime.utcnow()

        # 更新資料庫
        await app.state.mongo_adapter.update_one(
            "mesh_nodes", {"node_id": node_id}, mesh_node.dict()
        )

        return CustomJSONResponse(content=jsonable_encoder(mesh_node.dict()))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新 Mesh 節點 API 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


@app.delete("/api/v1/mesh/nodes/{node_id}", tags=["Mesh 橋接"])
async def delete_mesh_node(node_id: str):
    """刪除 Mesh 節點"""
    try:
        mesh_service = app.state.mesh_bridge_service

        if node_id not in mesh_service.mesh_nodes:
            raise HTTPException(status_code=404, detail=f"Mesh 節點 {node_id} 不存在")

        # 從記憶體中移除
        del mesh_service.mesh_nodes[node_id]

        # 從資料庫中刪除
        await app.state.mongo_adapter.delete_one("mesh_nodes", {"node_id": node_id})

        return CustomJSONResponse(content={"message": f"Mesh 節點 {node_id} 已刪除"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除 Mesh 節點 API 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


@app.post(
    "/api/v1/mesh/gateways", response_model=Bridge5GMeshGateway, tags=["Mesh 橋接"]
)
async def create_bridge_gateway(request: BridgeGatewayCreateRequest):
    """創建 5G-Mesh 橋接網關"""
    try:
        mesh_service = app.state.mesh_bridge_service

        gateway_data = {
            "name": request.name,
            "upf_ip": request.upf_ip,
            "upf_port": request.upf_port,
            "mesh_node_id": request.mesh_node_id,
            "mesh_interface": request.mesh_interface,
        }

        if request.slice_info:
            gateway_data["slice_info"] = request.slice_info

        bridge_gateway = await mesh_service.create_bridge_gateway(gateway_data)

        if bridge_gateway:
            return CustomJSONResponse(
                content=jsonable_encoder(bridge_gateway.dict()), status_code=201
            )
        else:
            raise HTTPException(status_code=500, detail="創建橋接網關失敗")

    except Exception as e:
        logger.error(f"創建橋接網關 API 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


@app.get("/api/v1/mesh/gateways", tags=["Mesh 橋接"])
async def list_bridge_gateways():
    """列出所有橋接網關"""
    try:
        mesh_service = app.state.mesh_bridge_service
        gateways = list(mesh_service.bridge_gateways.values())

        return CustomJSONResponse(
            content={
                "gateways": jsonable_encoder([gateway.dict() for gateway in gateways]),
                "total_count": len(gateways),
            }
        )

    except Exception as e:
        logger.error(f"列出橋接網關 API 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


@app.get(
    "/api/v1/mesh/gateways/{gateway_id}",
    response_model=Bridge5GMeshGateway,
    tags=["Mesh 橋接"],
)
async def get_bridge_gateway(gateway_id: str):
    """獲取指定橋接網關詳情"""
    try:
        mesh_service = app.state.mesh_bridge_service

        if gateway_id not in mesh_service.bridge_gateways:
            raise HTTPException(status_code=404, detail=f"橋接網關 {gateway_id} 不存在")

        bridge_gateway = mesh_service.bridge_gateways[gateway_id]
        return CustomJSONResponse(content=jsonable_encoder(bridge_gateway.dict()))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取橋接網關 API 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


@app.get(
    "/api/v1/mesh/topology", response_model=NetworkTopologyResponse, tags=["Mesh 橋接"]
)
async def get_network_topology():
    """獲取 Mesh 網路拓撲"""
    try:
        mesh_service = app.state.mesh_bridge_service

        topology = await mesh_service.get_network_topology()
        if not topology:
            raise HTTPException(status_code=500, detail="無法獲取網路拓撲")

        # 計算網路健康指標
        health_score = 0.9  # 簡化計算
        connectivity_ratio = 0.85
        average_link_quality = 0.8

        response = NetworkTopologyResponse(
            topology=topology,
            health_score=health_score,
            connectivity_ratio=connectivity_ratio,
            average_link_quality=average_link_quality,
        )

        return CustomJSONResponse(content=jsonable_encoder(response.dict()))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取網路拓撲 API 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


@app.get(
    "/api/v1/mesh/nodes/{node_id}/metrics",
    response_model=MeshPerformanceMetrics,
    tags=["Mesh 橋接"],
)
async def get_mesh_node_metrics(node_id: str):
    """獲取 Mesh 節點性能指標"""
    try:
        mesh_service = app.state.mesh_bridge_service

        metrics = await mesh_service.get_performance_metrics(node_id)
        if not metrics:
            raise HTTPException(
                status_code=404, detail=f"節點 {node_id} 不存在或無性能數據"
            )

        return CustomJSONResponse(content=jsonable_encoder(metrics.dict()))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取節點性能指標 API 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


@app.post("/api/v1/mesh/routing/optimize", tags=["Mesh 橋接"])
async def optimize_mesh_routing(target_node_id: Optional[str] = None):
    """觸發 Mesh 路由優化"""
    try:
        mesh_service = app.state.mesh_bridge_service

        success = await mesh_service.trigger_route_optimization(target_node_id)

        if success:
            return CustomJSONResponse(
                content={
                    "message": "路由優化已觸發",
                    "target_node": target_node_id or "all_nodes",
                }
            )
        else:
            raise HTTPException(status_code=500, detail="路由優化失敗")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"路由優化 API 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


@app.post("/api/v1/mesh/demo/quick-test", tags=["Mesh 橋接"])
async def mesh_bridge_quick_demo():
    """Mesh 橋接快速演示"""
    try:
        mesh_service = app.state.mesh_bridge_service

        # 創建示例 Mesh 節點
        demo_node_data = {
            "name": "Demo_UAV_Mesh_Node",
            "node_type": "uav_relay",
            "ip_address": "192.168.100.10",
            "mac_address": "00:11:22:33:44:55",
            "frequency_mhz": 900.0,
            "power_dbm": 20.0,
            "position": {"latitude": 25.0330, "longitude": 121.5654, "altitude": 100.0},
        }

        demo_node = await mesh_service.create_mesh_node(demo_node_data)

        if not demo_node:
            raise HTTPException(status_code=500, detail="創建示例節點失敗")

        # 創建示例橋接網關
        demo_gateway_data = {
            "name": "Demo_Bridge_Gateway",
            "upf_ip": "172.20.0.30",
            "upf_port": 2152,
            "mesh_node_id": demo_node.node_id,
            "mesh_interface": "mesh0",
            "slice_info": {
                "supported_slices": [
                    {"sst": 1, "sd": "0x111111"},
                    {"sst": 2, "sd": "0x222222"},
                ]
            },
        }

        demo_gateway = await mesh_service.create_bridge_gateway(demo_gateway_data)

        if not demo_gateway:
            raise HTTPException(status_code=500, detail="創建示例網關失敗")

        # 模擬封包轉發測試
        test_packet = b"Hello Mesh Bridge"
        forward_success = await mesh_service.forward_packet_5g_to_mesh(
            demo_gateway.gateway_id, test_packet, demo_node.node_id
        )

        # 獲取網路拓撲
        topology = await mesh_service.get_network_topology()

        return CustomJSONResponse(
            content={
                "message": "Mesh 橋接演示完成",
                "demo_results": {
                    "node_created": demo_node.dict(),
                    "gateway_created": demo_gateway.dict(),
                    "packet_forwarding_test": forward_success,
                    "network_topology": topology.dict() if topology else None,
                },
                "test_timestamp": datetime.utcnow().isoformat(),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mesh 橋接演示錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")


# ===== UAV Mesh 備援機制端點 =====


@app.post("/api/v1/uav-mesh-failover/register/{uav_id}", tags=["UAV Mesh 備援"])
async def register_uav_for_failover_monitoring(uav_id: str):
    """
    註冊 UAV 進行備援監控

    Args:
        uav_id: UAV ID

    Returns:
        註冊結果
    """
    try:
        failover_service = app.state.uav_mesh_failover_service
        success = await failover_service.register_uav_for_monitoring(uav_id)

        if success:
            return CustomJSONResponse(
                content={
                    "success": True,
                    "message": f"UAV {uav_id} 已註冊備援監控",
                    "uav_id": uav_id,
                    "monitoring_capabilities": [
                        "連接質量監控",
                        "自動故障切換",
                        "Mesh 網路備援",
                        "衛星連接恢復",
                    ],
                }
            )
        else:
            raise HTTPException(status_code=500, detail="註冊備援監控失敗")

    except Exception as e:
        logger.error(f"註冊 UAV 備援監控失敗: {e}")
        raise HTTPException(status_code=500, detail=f"註冊失敗: {str(e)}")


@app.delete("/api/v1/uav-mesh-failover/unregister/{uav_id}", tags=["UAV Mesh 備援"])
async def unregister_uav_failover_monitoring(uav_id: str):
    """
    取消 UAV 備援監控

    Args:
        uav_id: UAV ID

    Returns:
        取消結果
    """
    try:
        failover_service = app.state.uav_mesh_failover_service
        success = await failover_service.unregister_uav_monitoring(uav_id)

        if success:
            return CustomJSONResponse(
                content={
                    "success": True,
                    "message": f"UAV {uav_id} 已取消備援監控",
                    "uav_id": uav_id,
                }
            )
        else:
            raise HTTPException(status_code=404, detail=f"UAV {uav_id} 未在監控中")

    except Exception as e:
        logger.error(f"取消 UAV 備援監控失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取消失敗: {str(e)}")


@app.post("/api/v1/uav-mesh-failover/trigger/{uav_id}", tags=["UAV Mesh 備援"])
async def trigger_manual_uav_failover(uav_id: str, target_mode: NetworkMode):
    """
    手動觸發 UAV 網路切換

    Args:
        uav_id: UAV ID
        target_mode: 目標網路模式

    Returns:
        切換結果
    """
    try:
        failover_service = app.state.uav_mesh_failover_service
        result = await failover_service.trigger_manual_failover(uav_id, target_mode)

        return CustomJSONResponse(content=result)

    except Exception as e:
        logger.error(f"手動觸發 UAV 網路切換失敗: {e}")
        raise HTTPException(status_code=500, detail=f"切換失敗: {str(e)}")


@app.get("/api/v1/uav-mesh-failover/status/{uav_id}", tags=["UAV Mesh 備援"])
async def get_uav_failover_status(uav_id: str):
    """
    獲取 UAV 備援狀態

    Args:
        uav_id: UAV ID

    Returns:
        UAV 網路狀態和備援信息
    """
    try:
        failover_service = app.state.uav_mesh_failover_service
        status = await failover_service.get_uav_network_status(uav_id)

        return CustomJSONResponse(content=status)

    except Exception as e:
        logger.error(f"獲取 UAV 備援狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"狀態查詢失敗: {str(e)}")


@app.get("/api/v1/uav-mesh-failover/stats", tags=["UAV Mesh 備援"])
async def get_uav_failover_service_stats():
    """
    獲取 UAV 備援服務統計

    Returns:
        服務統計信息，包括監控數量、切換統計等
    """
    try:
        failover_service = app.state.uav_mesh_failover_service
        stats = await failover_service.get_service_stats()

        # 確保數據 JSON 兼容
        def clean_data(obj):
            if isinstance(obj, float):
                if (
                    obj == float("inf") or obj == float("-inf") or obj != obj
                ):  # NaN check
                    return None
                return obj
            elif isinstance(obj, dict):
                return {k: clean_data(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_data(item) for item in obj]
            return obj

        cleaned_stats = clean_data(stats)
        return CustomJSONResponse(content=cleaned_stats)

    except Exception as e:
        logger.error(f"獲取備援服務統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"統計查詢失敗: {str(e)}")


@app.post("/api/v1/uav-mesh-failover/demo/quick-test", tags=["UAV Mesh 備援"])
async def uav_mesh_failover_quick_demo():
    """
    UAV Mesh 備援機制快速演示

    創建示例 UAV，演示完整的失聯檢測和備援切換流程

    Returns:
        演示結果和性能指標
    """
    try:
        # 創建測試 UAV
        from datetime import datetime

        demo_ue_config = UAVUEConfig(
            imsi="999700000000002",
            key="465B5CE8B199B49FAA5F0A2EE238A6BC",
            opc="E8ED289DEBA952E4283B54E88E6183CA",
            plmn="99970",
            apn="internet",
            slice_nssai={"sst": 1, "sd": "000001"},
            gnb_ip="172.20.0.40",
            gnb_port=38412,
            power_dbm=23.0,
            frequency_mhz=2150.0,
            bandwidth_mhz=20.0,
        )

        demo_position = UAVPosition(
            latitude=25.0330,
            longitude=121.5654,
            altitude=150.0,
            speed=25.0,
            heading=90.0,
        )

        uav_request = UAVCreateRequest(
            name="演示UAV_備援測試",
            ue_config=demo_ue_config,
            initial_position=demo_position,
        )

        # 創建 UAV
        uav_ue_service = app.state.uav_ue_service
        uav = await uav_ue_service.create_uav(uav_request)

        # 註冊備援監控
        failover_service = app.state.uav_mesh_failover_service
        await failover_service.register_uav_for_monitoring(uav.uav_id)

        # 模擬信號質量下降
        poor_signal = UAVSignalQuality(
            rsrp_dbm=-115.0,  # 很差的信號
            rsrq_db=-15.0,
            sinr_db=-8.0,  # 低於閾值
            cqi=2,
            throughput_mbps=2.0,
            latency_ms=200.0,
            packet_loss_rate=0.15,  # 高丟包率
            jitter_ms=20.0,
            link_budget_margin_db=-5.0,
            doppler_shift_hz=1000.0,
            beam_alignment_score=0.3,
            interference_level_db=-80.0,
            measurement_confidence=0.8,
            timestamp=datetime.now(),
        )

        # 更新信號質量觸發切換
        await uav_ue_service.update_uav_position(
            uav.uav_id,
            UAVPositionUpdateRequest(
                position=demo_position, signal_quality=poor_signal
            ),
        )

        # 等待切換完成
        await asyncio.sleep(3)

        # 檢查切換結果
        failover_status = await failover_service.get_uav_network_status(uav.uav_id)

        # 手動觸發切回衛星
        recovery_result = await failover_service.trigger_manual_failover(
            uav.uav_id, NetworkMode.SATELLITE_NTN
        )

        # 獲取服務統計
        service_stats = await failover_service.get_service_stats()

        demo_result = {
            "success": True,
            "message": "UAV Mesh 備援機制演示完成",
            "demo_scenario": {
                "created_uav": {
                    "id": uav.uav_id,
                    "name": uav.name,
                    "initial_position": demo_position.dict(),
                },
                "simulated_degradation": {
                    "rsrp_dbm": poor_signal.rsrp_dbm,
                    "sinr_db": poor_signal.sinr_db,
                    "packet_loss_rate": poor_signal.packet_loss_rate,
                },
                "failover_result": failover_status,
                "recovery_result": recovery_result,
            },
            "service_statistics": service_stats,
            "demonstrated_capabilities": [
                "實時連接質量監控",
                "自動故障檢測",
                "快速 Mesh 網路切換",
                "智能恢復機制",
                "性能統計追蹤",
            ],
            "performance_targets": {
                "failover_time_target_ms": 2000,
                "actual_failover_time_ms": recovery_result.get("duration_ms", 0),
                "meets_requirement": recovery_result.get("duration_ms", 0) < 2000,
            },
            "cleanup_info": {
                "uav_id": uav.uav_id,
                "cleanup_endpoints": [
                    f"DELETE /api/v1/uav/{uav.uav_id}",
                    f"DELETE /api/v1/uav-mesh-failover/unregister/{uav.uav_id}",
                ],
            },
        }

        return CustomJSONResponse(content=demo_result)

    except Exception as e:
        logger.error(f"UAV Mesh 備援演示失敗: {e}")
        raise HTTPException(status_code=500, detail=f"演示失敗: {str(e)}")


# ===== Stage 4: Sionna 無線通道與 AI-RAN 抗干擾整合 API 端點 =====

@app.post("/api/sionna/channel-simulation", tags=["Sionna Integration"])
async def sionna_channel_simulation(request: dict):
    """Sionna 無線通道模擬端點"""
    try:
        sionna_service = app.state.sionna_integration_service
        result = await sionna_service.run_channel_simulation(
            ue_positions=request.get("ue_positions", []),
            gnb_positions=request.get("gnb_positions", []),
            frequency_ghz=request.get("frequency_ghz", 2.1)
        )
        return {"success": True, "simulation_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/airan/quick-decision", tags=["AI-RAN"])
async def airan_quick_decision(request: dict):
    """AI-RAN 快速決策端點"""
    try:
        airan_service = app.state.ai_ran_service
        decision = await airan_service.make_quick_decision(
            interference_level=request.get("interference_level", 0.5),
            context=request.get("context", {})
        )
        return {"success": True, "decision": decision}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics/summary", tags=["Metrics"])
async def get_metrics_summary():
    """取得指標摘要"""
    try:
        metrics_collector = app.state.unified_metrics_collector
        summary = await metrics_collector.get_metrics_summary()
        return {"success": True, "metrics": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/interference/detect", tags=["Interference Control"])
async def detect_interference(request: dict):
    """干擾檢測端點"""
    try:
        interference_service = app.state.interference_control_service
        detection_result = await interference_service.detect_interference(
            source_type=request.get("source_type", "unknown"),
            target_ue=request.get("target_ue", ""),
            interference_level=request.get("interference_level", 0.0)
        )
        return {"success": True, "detection": detection_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/frontend/sinr-viewer/config", tags=["Frontend API"])
async def get_sinr_viewer_config():
    """SINR Viewer 配置端點"""
    return {
        "success": True,
        "config": {
            "visualization_type": "heatmap",
            "color_scale": "viridis",
            "update_interval_ms": 1000
        }
    }


@app.get("/api/frontend/interference-visualization/data", tags=["Frontend API"])
async def get_interference_visualization_data():
    """干擾視覺化數據端點"""
    return {
        "success": True,
        "data": {
            "interference_sources": [],
            "affected_areas": [],
            "mitigation_status": "active"
        }
    }


@app.get("/api/frontend/spectrum-visualization/data", tags=["Frontend API"])
async def get_spectrum_visualization_data():
    """頻譜視覺化數據端點"""
    return {
        "success": True,
        "data": {
            "frequency_range": [2100, 2200],
            "power_spectral_density": [],
            "occupied_bands": []
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
