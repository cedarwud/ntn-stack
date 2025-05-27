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
from typing import Dict, List, Optional

import structlog
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
from .models.requests import SliceSwitchRequest
from .models.ueransim_models import UERANSIMConfigRequest, UERANSIMConfigResponse
from .models.responses import (
    HealthResponse,
    UEInfoResponse,
    UEStatsResponse,
    SliceSwitchResponse,
    ErrorResponse,
)


# 自定義 JSON 編碼器
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


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

    # 初始化服務
    ue_service = UEService(mongo_adapter, redis_adapter)
    slice_service = SliceService(mongo_adapter, open5gs_adapter, redis_adapter)
    health_service = HealthService(mongo_adapter, redis_adapter)
    ueransim_service = UERANSIMConfigService()
    satellite_gnb_service = SatelliteGnbMappingService(
        simworld_api_url=os.getenv("SIMWORLD_API_URL", "http://simworld-backend:8000"),
        redis_client=redis_adapter.client if redis_adapter else None
    )
    
    # 初始化 OneWeb 衛星 gNodeB 服務
    from .services.oneweb_satellite_gnb_service import OneWebSatelliteGnbService
    oneweb_service = OneWebSatelliteGnbService(
        satellite_mapping_service=satellite_gnb_service,
        simworld_api_url=os.getenv("SIMWORLD_API_URL", "http://simworld-backend:8000"),
        ueransim_config_dir=os.getenv("UERANSIM_CONFIG_DIR", "/tmp/ueransim_configs")
    )

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

    # 連接外部服務
    await mongo_adapter.connect()
    await redis_adapter.connect()

    logger.info("✅ NetStack API 啟動完成")

    yield

    # 清理資源
    logger.info("🛑 NetStack API 關閉中...")
    
    # 關閉 OneWeb 服務
    if hasattr(app.state, 'oneweb_service'):
        await app.state.oneweb_service.shutdown()
    
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


@app.get("/metrics", tags=["監控"])
async def get_metrics():
    """
    Prometheus 指標端點

    回傳系統運行指標，供 Prometheus 收集
    """
    return Response(
        content=generate_latest(prometheus_registry), media_type="text/plain"
    )


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
    bandwidth: Optional[int] = 20
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
        if all(param is not None for param in [uav_latitude, uav_longitude, uav_altitude]):
            from .models.ueransim_models import UAVPosition
            uav_position = UAVPosition(
                id="mapping-request-uav",
                latitude=uav_latitude,
                longitude=uav_longitude,
                altitude=uav_altitude
            )
        
        # 構建網絡參數
        from .models.ueransim_models import NetworkParameters
        network_params = NetworkParameters(
            frequency=frequency,
            bandwidth=bandwidth
        )
        
        # 執行衛星位置轉換
        mapping_result = await satellite_gnb_service.convert_satellite_to_gnb_config(
            satellite_id=satellite_id,
            uav_position=uav_position,
            network_params=network_params
        )
        
        return CustomJSONResponse(
            content={
                "success": True,
                "message": f"衛星 {satellite_id} 位置轉換完成",
                "data": mapping_result,
                "conversion_info": {
                    "skyfield_integration": "已整合 simworld Skyfield 計算",
                    "coordinate_conversion": "ECEF/ENU 坐標轉換完成",
                    "gnb_mapping": "gNodeB 參數映射完成"
                }
            }
        )
        
    except Exception as e:
        logger.error("衛星位置轉換失敗", satellite_id=satellite_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"衛星位置轉換失敗: {str(e)}"
        )


@app.get("/api/v1/satellite-gnb/batch-mapping", tags=["衛星-gNodeB 映射"])
async def batch_convert_satellites_to_gnb(
    satellite_ids: str,  # 逗號分隔的衛星 ID
    uav_latitude: Optional[float] = None,
    uav_longitude: Optional[float] = None,
    uav_altitude: Optional[float] = None
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
                status_code=400,
                detail="無效的衛星 ID 格式，請使用逗號分隔的整數"
            )
        
        if len(sat_ids) > 20:  # 限制批量處理數量
            raise HTTPException(
                status_code=400,
                detail="批量處理衛星數量不能超過 20 個"
            )
        
        # 構建 UAV 位置對象（如果提供了參數）
        uav_position = None
        if all(param is not None for param in [uav_latitude, uav_longitude, uav_altitude]):
            from .models.ueransim_models import UAVPosition
            uav_position = UAVPosition(
                id="batch-mapping-uav",
                latitude=uav_latitude,
                longitude=uav_longitude,
                altitude=uav_altitude
            )
        
        # 執行批量轉換
        batch_results = await satellite_gnb_service.get_multiple_satellite_configs(
            satellite_ids=sat_ids,
            uav_position=uav_position
        )
        
        # 統計成功和失敗的數量
        successful_count = sum(1 for result in batch_results.values() if result.get("success"))
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
                    "success_rate": f"{(successful_count / len(sat_ids) * 100):.1f}%"
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("批量衛星位置轉換失敗", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"批量衛星位置轉換失敗: {str(e)}"
        )


@app.post("/api/v1/satellite-gnb/start-tracking", tags=["衛星-gNodeB 映射"])
async def start_continuous_tracking(
    satellite_ids: str,
    update_interval: int = 30
):
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
                status_code=400,
                detail="無效的衛星 ID 格式，請使用逗號分隔的整數"
            )
        
        if update_interval < 10:
            raise HTTPException(
                status_code=400,
                detail="更新間隔不能少於 10 秒"
            )
        
        # 在背景啟動持續追蹤任務
        task = asyncio.create_task(
            satellite_gnb_service.update_gnb_positions_continuously(
                satellite_ids=sat_ids,
                update_interval=update_interval
            )
        )
        
        # 將任務存儲到應用狀態中（可選，用於管理）
        if not hasattr(app.state, 'tracking_tasks'):
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
                    "estimated_updates_per_hour": 3600 // update_interval
                },
                "note": "追蹤將在背景持續進行，配置更新將通過 Redis 事件發布"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("啟動衛星追蹤失敗", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"啟動衛星追蹤失敗: {str(e)}"
        )


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
                    "使用 /api/v1/oneweb/ueransim/deploy 部署 UERANSIM 配置"
                ]
            }
        )
        
    except Exception as e:
        logger.error("OneWeb 星座初始化失敗", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"OneWeb 星座初始化失敗: {str(e)}"
        )


@app.post("/api/v1/oneweb/orbital-tracking/start", tags=["OneWeb 衛星 gNodeB"])
async def start_oneweb_orbital_tracking(
    satellite_ids: Optional[str] = None,
    update_interval: int = 30
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
                    status_code=400,
                    detail="無效的衛星 ID 格式，請使用逗號分隔的整數"
                )
        
        if update_interval < 10:
            raise HTTPException(
                status_code=400,
                detail="更新間隔不能少於 10 秒"
            )
        
        # 啟動軌道追蹤
        tracking_result = await oneweb_service.start_orbital_tracking(
            satellite_ids=sat_ids,
            update_interval_seconds=update_interval
        )
        
        return CustomJSONResponse(
            content={
                "success": True,
                "message": "OneWeb 軌道追蹤已啟動",
                "tracking_result": tracking_result,
                "monitoring": {
                    "status_endpoint": "/api/v1/oneweb/constellation/status",
                    "stop_endpoint": f"/api/v1/oneweb/orbital-tracking/stop/{tracking_result['task_id']}"
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("啟動 OneWeb 軌道追蹤失敗", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"啟動軌道追蹤失敗: {str(e)}"
        )


@app.delete("/api/v1/oneweb/orbital-tracking/stop/{task_id}", tags=["OneWeb 衛星 gNodeB"])
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
                content={
                    "success": True,
                    "message": f"軌道追蹤任務 {task_id} 已停止"
                }
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"追蹤任務 {task_id} 不存在"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("停止軌道追蹤失敗", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"停止軌道追蹤失敗: {str(e)}"
        )


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
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error("獲取 OneWeb 星座狀態失敗", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"獲取星座狀態失敗: {str(e)}"
        )


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
            raise HTTPException(
                status_code=400,
                detail="沒有活躍的 OneWeb 衛星可部署"
            )
        
        deployment_results = []
        for satellite in active_satellites:
            satellite_id = satellite["satellite_id"]
            
            try:
                # 為每個衛星重新生成配置
                await oneweb_service._regenerate_ueransim_config(satellite_id)
                
                deployment_results.append({
                    "satellite_id": satellite_id,
                    "satellite_name": satellite["name"],
                    "status": "deployed",
                    "config_file": f"/tmp/ueransim_configs/gnb-oneweb-{satellite_id}.yaml"
                })
                
            except Exception as e:
                deployment_results.append({
                    "satellite_id": satellite_id,
                    "satellite_name": satellite["name"],
                    "status": "failed",
                    "error": str(e)
                })
        
        successful_deployments = sum(1 for result in deployment_results if result["status"] == "deployed")
        
        return CustomJSONResponse(
            content={
                "success": True,
                "message": f"UERANSIM 配置部署完成，成功 {successful_deployments} 個",
                "deployment_results": deployment_results,
                "summary": {
                    "total_satellites": len(active_satellites),
                    "successful_deployments": successful_deployments,
                    "failed_deployments": len(deployment_results) - successful_deployments
                },
                "config_directory": "/tmp/ueransim_configs"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("部署 OneWeb UERANSIM 配置失敗", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"部署 UERANSIM 配置失敗: {str(e)}"
        )


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True, log_level="info")
