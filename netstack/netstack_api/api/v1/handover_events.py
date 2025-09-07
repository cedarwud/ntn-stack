"""
換手事件API端點

提供完整的A4/A5/D2事件觸發和決策API
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ...services.handover.handover_event_trigger_service import (
    get_handover_trigger_service,
    HandoverEventTriggerService,
    SatelliteMeasurement,
    HandoverDecision,
    HandoverPriority,
    create_test_measurement_scenario
)

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(
    prefix="/api/v1/handover-events",
    tags=["Handover Events"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

# Pydantic 模型
class SatelliteMeasurementModel(BaseModel):
    """衛星測量數據模型"""
    satellite_id: str = Field(..., description="衛星ID")
    rsrp_dbm: float = Field(..., description="RSRP信號強度 (dBm)")
    rsrq_db: float = Field(..., description="RSRQ信號品質 (dB)")
    distance_km: float = Field(..., description="距離 (公里)")
    elevation_deg: float = Field(..., description="仰角 (度)")
    azimuth_deg: float = Field(..., description="方位角 (度)")
    is_visible: bool = Field(True, description="是否可見")
    signal_quality_score: float = Field(0.5, description="信號品質分數 (0-1)")

class HandoverRequestModel(BaseModel):
    """換手請求模型"""
    serving_satellite: SatelliteMeasurementModel
    neighbor_satellites: List[SatelliteMeasurementModel]
    observer_location: Optional[Dict[str, float]] = Field(
        default={"lat": 24.9441667, "lon": 121.3713889, "alt": 0.024},
        description="觀測者位置"
    )
    force_evaluation: bool = Field(False, description="是否強制評估(忽略冷卻期)")

class HandoverDecisionModel(BaseModel):
    """換手決策結果模型"""
    should_handover: bool = Field(..., description="是否應該換手")
    target_satellite_id: Optional[str] = Field(None, description="目標衛星ID")
    handover_reason: str = Field(..., description="換手原因")
    priority: str = Field(..., description="優先級")
    expected_improvement: Dict[str, float] = Field(..., description="預期改善")
    confidence_score: float = Field(..., description="信心分數")
    triggered_events: List[str] = Field(..., description="觸發的事件類型")
    timestamp: str = Field(..., description="決策時間")

class EventStatisticsModel(BaseModel):
    """事件統計模型"""
    total_events: int
    event_breakdown: Dict[str, int]
    total_handovers: int
    last_handover: Optional[Dict[str, Any]]
    monitoring_active: bool

# 輔助函數
def _convert_to_measurement(model: SatelliteMeasurementModel) -> SatelliteMeasurement:
    """轉換模型為內部測量對象"""
    return SatelliteMeasurement(
        satellite_id=model.satellite_id,
        timestamp=datetime.now().timestamp(),
        rsrp_dbm=model.rsrp_dbm,
        rsrq_db=model.rsrq_db,
        distance_km=model.distance_km,
        elevation_deg=model.elevation_deg,
        azimuth_deg=model.azimuth_deg,
        is_visible=model.is_visible,
        signal_quality_score=model.signal_quality_score
    )

def _convert_decision_to_model(decision: HandoverDecision) -> HandoverDecisionModel:
    """轉換決策為API模型"""
    return HandoverDecisionModel(
        should_handover=decision.should_handover,
        target_satellite_id=decision.target_satellite_id,
        handover_reason=decision.handover_reason,
        priority=decision.priority.value,
        expected_improvement=decision.expected_improvement,
        confidence_score=decision.confidence_score,
        triggered_events=decision.triggered_events,
        timestamp=datetime.now().isoformat()
    )

# API端點
@router.post(
    "/evaluate",
    response_model=HandoverDecisionModel,
    summary="評估換手決策",
    description="基於當前衛星測量數據評估是否需要換手，支援A4/A5/D2事件觸發"
)
async def evaluate_handover(
    request: HandoverRequestModel,
    service: HandoverEventTriggerService = Depends(get_handover_trigger_service)
) -> HandoverDecisionModel:
    """評估換手決策的主要端點"""
    try:
        logger.info(
            f"🎯 收到換手評估請求: 服務衛星={request.serving_satellite.satellite_id}, "
            f"鄰居衛星數={len(request.neighbor_satellites)}"
        )
        
        # 轉換輸入數據
        serving_measurement = _convert_to_measurement(request.serving_satellite)
        neighbor_measurements = [
            _convert_to_measurement(neighbor) 
            for neighbor in request.neighbor_satellites
        ]
        
        # 處理換手決策
        decision = await service.process_satellite_measurements(
            serving_measurement,
            neighbor_measurements,
            request.observer_location
        )
        
        # 轉換結果
        result = _convert_decision_to_model(decision)
        
        logger.info(
            f"✅ 換手決策完成: {decision.should_handover}, "
            f"目標: {decision.target_satellite_id}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"換手評估失敗: {e}")
        raise HTTPException(status_code=500, detail=f"換手評估失敗: {str(e)}")

@router.get(
    "/statistics",
    response_model=EventStatisticsModel,
    summary="獲取事件統計",
    description="獲取換手事件觸發統計信息"
)
async def get_event_statistics(
    service: HandoverEventTriggerService = Depends(get_handover_trigger_service)
) -> EventStatisticsModel:
    """獲取事件統計信息"""
    try:
        stats = service.get_event_statistics()
        return EventStatisticsModel(**stats)
    except Exception as e:
        logger.error(f"獲取統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")

@router.post(
    "/start-monitoring",
    summary="啟動事件監控",
    description="啟動自動換手事件監控"
)
async def start_monitoring(
    background_tasks: BackgroundTasks,
    service: HandoverEventTriggerService = Depends(get_handover_trigger_service)
):
    """啟動事件監控"""
    try:
        background_tasks.add_task(service.start_monitoring)
        return {"message": "事件監控已啟動", "status": "success"}
    except Exception as e:
        logger.error(f"啟動監控失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動監控失敗: {str(e)}")

@router.post(
    "/stop-monitoring",
    summary="停止事件監控",
    description="停止自動換手事件監控"
)
async def stop_monitoring(
    service: HandoverEventTriggerService = Depends(get_handover_trigger_service)
):
    """停止事件監控"""
    try:
        await service.stop_monitoring()
        return {"message": "事件監控已停止", "status": "success"}
    except Exception as e:
        logger.error(f"停止監控失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止監控失敗: {str(e)}")

@router.put(
    "/configuration",
    summary="更新配置",
    description="更新換手事件觸發配置參數"
)
async def update_configuration(
    config: Dict[str, Any],
    service: HandoverEventTriggerService = Depends(get_handover_trigger_service)
):
    """更新配置參數"""
    try:
        service.update_configuration(config)
        return {"message": "配置更新成功", "status": "success", "config": config}
    except Exception as e:
        logger.error(f"配置更新失敗: {e}")
        raise HTTPException(status_code=500, detail=f"配置更新失敗: {str(e)}")

@router.post(
    "/test-scenario",
    response_model=HandoverDecisionModel,
    summary="測試換手場景",
    description="使用預定義測試場景測試換手決策功能"
)
async def test_handover_scenario(
    service: HandoverEventTriggerService = Depends(get_handover_trigger_service)
) -> HandoverDecisionModel:
    """測試換手場景"""
    try:
        logger.info("🧪 執行測試換手場景")
        
        # 創建測試場景
        serving, neighbors = await create_test_measurement_scenario()
        
        # 執行換手決策
        decision = await service.process_satellite_measurements(
            serving, neighbors
        )
        
        result = _convert_decision_to_model(decision)
        
        logger.info("✅ 測試場景執行完成")
        return result
        
    except Exception as e:
        logger.error(f"測試場景執行失敗: {e}")
        raise HTTPException(status_code=500, detail=f"測試場景執行失敗: {str(e)}")

@router.get(
    "/event-types",
    summary="獲取支援的事件類型",
    description="獲取所有支援的3GPP換手事件類型"
)
async def get_supported_event_types():
    """獲取支援的事件類型"""
    return {
        "supported_events": {
            "A1": "服務衛星信號強度高於閾值",
            "A2": "服務衛星信號強度低於閾值", 
            "A3": "相鄰衛星信號強度比服務衛星強",
            "A4": "相鄰衛星信號強度高於閾值",
            "A5": "服務衛星信號低於閾值1且相鄰衛星高於閾值2",
            "A6": "相鄰衛星信號強度比服務衛星強且高於偏移量",
            "D2": "基於距離的換手觸發"
        },
        "handover_triggers": ["A4", "A5", "D2"],
        "status": "ready"
    }

@router.get(
    "/health",
    summary="健康檢查",
    description="檢查換手事件服務的健康狀態"
)
async def health_check(
    service: HandoverEventTriggerService = Depends(get_handover_trigger_service)
):
    """健康檢查"""
    try:
        stats = service.get_event_statistics()
        return {
            "healthy": True,
            "service": "handover-events",
            "monitoring_active": stats["monitoring_active"],
            "total_events_processed": stats["total_events"],
            "total_handovers": stats["total_handovers"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        raise HTTPException(status_code=503, detail=f"服務不可用: {str(e)}")

# 路由器包含函數
def include_handover_events_router(app):
    """將換手事件路由器包含到應用中"""
    app.include_router(router)
    logger.info("✅ 換手事件API端點已註冊")