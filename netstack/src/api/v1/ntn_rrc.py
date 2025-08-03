"""
Phase 3.1.1: NTN RRC API 端點

提供 3GPP NTN-specific RRC procedures 的 RESTful API 接口，包括：
- RRC Connection Management
- Measurement Report Processing  
- Timing Advance Updates
- Connection Status Monitoring
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from src.protocols.rrc.ntn_procedures import (
    NTNRRCProcessor, 
    RRCMessage,
    RRCMessageType,
    create_ntn_rrc_processor,
    create_test_rrc_setup_request
)

logger = logging.getLogger(__name__)

# 全局 RRC 處理器實例
rrc_processor: Optional[NTNRRCProcessor] = None

# Pydantic 模型定義
class RRCSetupRequest(BaseModel):
    """RRC Setup Request 模型"""
    ue_identity: str = Field(..., description="UE 身份標識")
    establishment_cause: str = Field(default="mo_data", description="建立原因")
    selected_plmn_identity: str = Field(default="46692", description="選擇的 PLMN")

class RRCReconfigurationRequest(BaseModel):
    """RRC Reconfiguration Request 模型"""
    ue_identity: str = Field(..., description="UE 身份標識")
    target_satellite_id: Optional[str] = Field(None, description="目標衛星ID")
    measurement_config: Optional[Dict[str, Any]] = Field(None, description="測量配置")
    neighbor_satellites: Optional[List[str]] = Field(None, description="鄰近衛星列表")

class RRCReleaseRequest(BaseModel):
    """RRC Release Request 模型"""
    ue_identity: str = Field(..., description="UE 身份標識")
    cause: str = Field(default="normal", description="釋放原因")

class MeasurementReportRequest(BaseModel):
    """測量報告模型"""
    ue_identity: str = Field(..., description="UE 身份標識")
    measurements: List[Dict[str, Any]] = Field(..., description="測量數據")

class TimingAdvanceUpdateRequest(BaseModel):
    """時間提前量更新請求模型"""
    ue_identity: str = Field(..., description="UE 身份標識")

# API Router
router = APIRouter(prefix="/api/v1/ntn-rrc", tags=["NTN RRC Procedures"])

@router.on_event("startup")
async def initialize_rrc_processor():
    """初始化 RRC 處理器"""
    global rrc_processor
    try:
        rrc_processor = await create_ntn_rrc_processor()
        logger.info("✅ NTN RRC 處理器初始化成功")
    except Exception as e:
        logger.error(f"❌ NTN RRC 處理器初始化失敗: {e}")
        raise

async def get_rrc_processor() -> NTNRRCProcessor:
    """獲取 RRC 處理器實例"""
    global rrc_processor
    if rrc_processor is None:
        rrc_processor = await create_ntn_rrc_processor()
    return rrc_processor

@router.post("/setup", summary="RRC Connection Setup")
async def rrc_setup(request: RRCSetupRequest) -> JSONResponse:
    """
    處理 RRC Setup Request
    
    實現符合 3GPP TS 38.331 的 NTN-specific RRC 連接建立流程
    """
    try:
        processor = await get_rrc_processor()
        
        # 創建 RRC Setup Request 消息
        setup_message = RRCMessage(
            message_type=RRCMessageType.RRC_SETUP_REQUEST,
            message_id=f"api_setup_{int(datetime.now().timestamp() * 1000)}",
            payload={
                "ue_identity": request.ue_identity,
                "establishment_cause": request.establishment_cause,
                "selected_plmn_identity": request.selected_plmn_identity
            }
        )
        
        # 處理 RRC Setup Request
        response = await processor.process_rrc_setup_request(setup_message)
        
        logger.info(f"📱 RRC Setup 處理完成 - UE: {request.ue_identity}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message_type": response.message_type.value,
                "ue_identity": response.ue_identity,
                "serving_satellite_id": response.payload.get("serving_satellite_id"),
                "timing_advance": response.payload.get("timing_advance"),
                "doppler_compensation": response.payload.get("doppler_compensation"),
                "measurement_config": response.payload.get("measurement_config"),
                "timestamp": response.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ RRC Setup 處理失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reconfiguration", summary="RRC Reconfiguration")
async def rrc_reconfiguration(request: RRCReconfigurationRequest) -> JSONResponse:
    """
    處理 RRC Reconfiguration
    
    用於衛星切換、測量配置更新等 RRC 重配置操作
    """
    try:
        processor = await get_rrc_processor()
        
        # 準備重配置請求數據
        reconfig_data = {
            "ue_identity": request.ue_identity
        }
        
        if request.target_satellite_id:
            reconfig_data["target_satellite_id"] = request.target_satellite_id
        
        if request.measurement_config:
            reconfig_data["measurement_config"] = request.measurement_config
            
        if request.neighbor_satellites:
            reconfig_data["neighbor_satellites"] = request.neighbor_satellites
        
        # 處理重配置
        response = await processor.process_rrc_reconfiguration(reconfig_data)
        
        logger.info(f"🔄 RRC Reconfiguration 處理完成 - UE: {request.ue_identity}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message_type": response.message_type.value,
                "ue_identity": response.ue_identity,
                "reconfiguration_complete": response.payload.get("reconfiguration_complete"),
                "serving_satellite_id": response.payload.get("serving_satellite_id"),
                "updated_measurement_config": response.payload.get("updated_measurement_config"),
                "neighbor_satellites": response.payload.get("neighbor_satellites"),
                "timestamp": response.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ RRC Reconfiguration 處理失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/release", summary="RRC Connection Release")
async def rrc_release(request: RRCReleaseRequest) -> JSONResponse:
    """
    處理 RRC Release
    
    釋放 RRC 連接並清理相關資源
    """
    try:
        processor = await get_rrc_processor()
        
        # 準備釋放請求數據
        release_data = {
            "ue_identity": request.ue_identity,
            "cause": request.cause
        }
        
        # 處理連接釋放
        response = await processor.process_rrc_release(release_data)
        
        logger.info(f"🔚 RRC Release 處理完成 - UE: {request.ue_identity}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message_type": response.message_type.value,
                "ue_identity": response.ue_identity,
                "connection_released": response.payload.get("connection_released"),
                "release_cause": response.payload.get("release_cause"),
                "timestamp": response.timestamp.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ RRC Release 處理失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/measurement-report", summary="Process Measurement Report")
async def process_measurement_report(request: MeasurementReportRequest) -> JSONResponse:
    """
    處理測量報告
    
    分析測量數據並可能觸發衛星切換等 RRC 程序
    """
    try:
        processor = await get_rrc_processor()
        
        # 準備測量報告數據
        measurement_data = {
            "ue_identity": request.ue_identity,
            "measurements": request.measurements,
            "report_timestamp": datetime.now().isoformat()
        }
        
        # 處理測量報告
        response = await processor.process_measurement_report(measurement_data)
        
        result = {
            "success": True,
            "ue_identity": request.ue_identity,
            "measurements_processed": len(request.measurements),
            "handover_triggered": response is not None
        }
        
        if response:
            # 測量報告觸發了切換
            result.update({
                "handover_command": {
                    "message_type": response.message_type.value,
                    "target_satellite_id": response.payload.get("mobility_control_info", {}).get("target_satellite_id"),
                    "handover_reason": response.payload.get("mobility_control_info", {}).get("handover_reason")
                }
            })
            logger.info(f"🛰️ 測量報告觸發衛星切換 - UE: {request.ue_identity}")
        else:
            logger.debug(f"📊 測量報告處理完成，無切換需求 - UE: {request.ue_identity}")
        
        return JSONResponse(status_code=200, content=result)
        
    except Exception as e:
        logger.error(f"❌ 測量報告處理失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timing-advance/update", summary="Update Timing Advance")
async def update_timing_advance(request: TimingAdvanceUpdateRequest) -> JSONResponse:
    """
    更新時間提前量
    
    NTN 特定的時間提前量更新機制
    """
    try:
        processor = await get_rrc_processor()
        
        # 更新時間提前量
        response = await processor.update_timing_advance(request.ue_identity)
        
        if response:
            # 時間提前量已更新
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "ue_identity": request.ue_identity,
                    "timing_advance_updated": True,
                    "message_type": response.message_type.value,
                    "timing_advance": response.payload.get("timing_advance"),
                    "timestamp": response.timestamp.isoformat()
                }
            )
        else:
            # 時間提前量仍有效，無需更新
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "ue_identity": request.ue_identity,
                    "timing_advance_updated": False,
                    "reason": "Timing advance still valid"
                }
            )
            
    except Exception as e:
        logger.error(f"❌ 時間提前量更新失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections", summary="Get Active Connections")
async def get_active_connections() -> JSONResponse:
    """
    獲取所有活動的 RRC 連接狀態
    """
    try:
        processor = await get_rrc_processor()
        connections = processor.get_active_connections()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "total_connections": len(connections),
                "connections": connections
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取活動連接失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections/{ue_identity}", summary="Get Connection Status")
async def get_connection_status(ue_identity: str) -> JSONResponse:
    """
    獲取特定 UE 的連接狀態
    """
    try:
        processor = await get_rrc_processor()
        connections = processor.get_active_connections()
        
        if ue_identity not in connections:
            raise HTTPException(status_code=404, detail=f"Connection not found for UE: {ue_identity}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "ue_identity": ue_identity,
                "connection_status": connections[ue_identity]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 獲取連接狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics", summary="Get Connection Statistics")
async def get_connection_statistics() -> JSONResponse:
    """
    獲取 RRC 連接統計信息
    """
    try:
        processor = await get_rrc_processor()
        stats = processor.get_connection_statistics()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "statistics": stats,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取連接統計失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", summary="RRC Processor Health Check")
async def health_check() -> JSONResponse:
    """
    RRC 處理器健康檢查
    """
    try:
        processor = await get_rrc_processor()
        stats = processor.get_connection_statistics()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "processor_active": True,
                "active_connections": stats["total_active_connections"],
                "satellites_in_use": stats["unique_satellites_in_use"],
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ RRC 處理器健康檢查失敗: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# 測試端點
@router.post("/test/setup", summary="Test RRC Setup (Development Only)")
async def test_rrc_setup(ue_identity: str = "TEST-UE-001") -> JSONResponse:
    """
    測試用的 RRC Setup 端點 (僅開發環境)
    """
    try:
        request = RRCSetupRequest(ue_identity=ue_identity)
        return await rrc_setup(request)
        
    except Exception as e:
        logger.error(f"❌ 測試 RRC Setup 失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 添加到主 app 的函數
def include_ntn_rrc_router(app):
    """將 NTN RRC router 添加到主應用"""
    app.include_router(router)
    logger.info("✅ NTN RRC API 路由已添加")