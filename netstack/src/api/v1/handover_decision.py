"""
Phase 3.2.1.2: 精細化切換決策引擎 API

提供精細化切換決策引擎的 RESTful API 接口，包括：
1. 切換請求提交和管理
2. 決策引擎控制和監控
3. 切換計劃執行和追蹤
4. 系統性能和統計信息
5. 配置管理和調整
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from enum import Enum
import logging

from ...algorithms.handover.fine_grained_decision import (
    FineGrainedHandoverDecisionEngine,
    HandoverRequest,
    HandoverTrigger,
    HandoverDecision,
    OptimizationObjective,
    SatelliteCandidate,
    create_fine_grained_handover_engine,
    create_test_handover_request
)

logger = logging.getLogger(__name__)

# 全局決策引擎實例
_handover_engine: Optional[FineGrainedHandoverDecisionEngine] = None

router = APIRouter(prefix="/handover-decision", tags=["handover-decision"])


# === Pydantic 模型定義 ===

class HandoverTriggerType(str, Enum):
    """切換觸發類型"""
    SIGNAL_STRENGTH = "signal_strength"
    LOAD_BALANCING = "load_balancing"
    PREDICTED_OUTAGE = "predicted_outage"
    SERVICE_QUALITY = "service_quality"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    EMERGENCY = "emergency"


class ServiceType(str, Enum):
    """服務類型"""
    VOICE = "voice"
    VIDEO = "video"
    DATA = "data"
    IOT = "iot"


class HandoverRequestModel(BaseModel):
    """切換請求模型"""
    user_id: str = Field(..., description="用戶ID")
    current_satellite_id: str = Field(..., description="當前衛星ID")
    trigger_type: HandoverTriggerType = Field(..., description="觸發類型")
    priority: int = Field(5, ge=1, le=10, description="優先級 (1-10)")
    deadline_ms: Optional[int] = Field(None, description="完成時間限制(毫秒)")
    
    # 服務需求
    service_type: ServiceType = Field(ServiceType.DATA, description="服務類型")
    required_bandwidth_mbps: float = Field(1.0, ge=0.1, description="所需帶寬(Mbps)")
    max_acceptable_latency_ms: float = Field(500.0, ge=10, description="最大可接受延遲(ms)")
    min_acceptable_reliability: float = Field(0.95, ge=0.5, le=1.0, description="最小可接受可靠性")
    
    # 當前狀態
    current_signal_strength_dbm: float = Field(-100.0, description="當前信號強度(dBm)")
    current_throughput_mbps: float = Field(0.0, ge=0, description="當前吞吐量(Mbps)")
    current_latency_ms: float = Field(1000.0, ge=0, description="當前延遲(ms)")
    
    additional_info: Dict[str, Any] = Field(default_factory=dict, description="額外信息")


class HandoverRequestResponse(BaseModel):
    """切換請求響應"""
    request_id: str = Field(..., description="請求ID")
    status: str = Field(..., description="提交狀態")
    message: str = Field(..., description="響應消息")
    estimated_processing_time_ms: int = Field(..., description="預估處理時間(ms)")


class SatelliteCandidateModel(BaseModel):
    """候選衛星模型"""
    satellite_id: str = Field(..., description="衛星ID")
    signal_strength_dbm: float = Field(..., description="信號強度(dBm)")
    elevation_angle: float = Field(..., description="仰角(度)")
    azimuth_angle: float = Field(..., description="方位角(度)")
    distance_km: float = Field(..., description="距離(公里)")
    velocity_kmh: float = Field(..., description="速度(公里/小時)")
    doppler_shift_hz: float = Field(..., description="都卜勒頻移(Hz)")
    
    # 資源狀態
    available_bandwidth_mbps: float = Field(..., description="可用帶寬(Mbps)")
    current_load_percent: float = Field(..., description="當前負載百分比")
    user_count: int = Field(..., description="用戶數量")
    beam_capacity_percent: float = Field(..., description="波束容量百分比")
    
    # 預測指標
    predicted_throughput_mbps: float = Field(..., description="預測吞吐量(Mbps)")
    predicted_latency_ms: float = Field(..., description="預測延遲(ms)")
    predicted_reliability: float = Field(..., description="預測可靠性")
    predicted_availability_duration_s: float = Field(..., description="預測可用時間(秒)")
    
    # 切換成本
    handover_delay_ms: float = Field(..., description="切換延遲(ms)")
    signaling_overhead_kb: float = Field(..., description="信令開銷(KB)")
    resource_preparation_ms: float = Field(..., description="資源準備時間(ms)")


class HandoverPlanModel(BaseModel):
    """切換計劃模型"""
    plan_id: str = Field(..., description="計劃ID")
    request_id: str = Field(..., description="對應的請求ID")
    target_satellite_id: str = Field(..., description="目標衛星ID")
    decision: str = Field(..., description="決策結果")
    execution_time: datetime = Field(..., description="執行時間")
    
    # 時序信息
    preparation_phase_duration_ms: int = Field(..., description="準備階段時長(ms)")
    execution_phase_duration_ms: int = Field(..., description="執行階段時長(ms)")
    completion_phase_duration_ms: int = Field(..., description="完成階段時長(ms)")
    total_duration_ms: int = Field(..., description="總時長(ms)")
    
    # 預期改善
    expected_improvement: Dict[str, float] = Field(..., description="預期改善")
    reserved_resources: Dict[str, Any] = Field(..., description="預留資源")


class EngineStatusModel(BaseModel):
    """引擎狀態模型"""
    engine_id: str = Field(..., description="引擎ID")
    is_running: bool = Field(..., description="是否運行中")
    pending_requests: int = Field(..., description="待處理請求數")
    active_plans: int = Field(..., description="活動計劃數")
    completed_handovers: int = Field(..., description="已完成切換數")
    
    # 統計信息
    statistics: Dict[str, Union[int, float]] = Field(..., description="統計信息")
    
    # 配置信息
    configuration: Dict[str, Any] = Field(..., description="配置信息")


class ConfigUpdateModel(BaseModel):
    """配置更新模型"""
    decision_config: Optional[Dict[str, Any]] = Field(None, description="決策配置")
    optimization_weights: Optional[Dict[str, float]] = Field(None, description="優化權重")
    service_weights: Optional[Dict[str, Dict[str, float]]] = Field(None, description="服務權重")


class HandoverQueryModel(BaseModel):
    """切換查詢模型"""
    user_id: Optional[str] = Field(None, description="用戶ID")
    satellite_id: Optional[str] = Field(None, description="衛星ID")
    trigger_type: Optional[HandoverTriggerType] = Field(None, description="觸發類型")
    priority_min: Optional[int] = Field(None, description="最小優先級")
    priority_max: Optional[int] = Field(None, description="最大優先級")
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    status: Optional[str] = Field(None, description="狀態")
    limit: int = Field(50, ge=1, le=1000, description="返回數量限制")


# === 依賴注入 ===

async def get_handover_engine() -> FineGrainedHandoverDecisionEngine:
    """獲取切換決策引擎實例"""
    global _handover_engine
    if _handover_engine is None:
        _handover_engine = create_fine_grained_handover_engine("api_engine")
        await _handover_engine.start_engine()
    return _handover_engine


# === API 端點實現 ===

@router.post("/requests", response_model=HandoverRequestResponse)
async def submit_handover_request(
    request_data: HandoverRequestModel,
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """提交切換請求"""
    try:
        # 創建切換請求
        handover_request = HandoverRequest(
            request_id=f"api_req_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            user_id=request_data.user_id,
            current_satellite_id=request_data.current_satellite_id,
            trigger_type=HandoverTrigger(request_data.trigger_type.value),
            priority=request_data.priority,
            timestamp=datetime.now(timezone.utc),
            deadline_ms=request_data.deadline_ms,
            service_type=request_data.service_type.value,
            required_bandwidth_mbps=request_data.required_bandwidth_mbps,
            max_acceptable_latency_ms=request_data.max_acceptable_latency_ms,
            min_acceptable_reliability=request_data.min_acceptable_reliability,
            current_signal_strength_dbm=request_data.current_signal_strength_dbm,
            current_throughput_mbps=request_data.current_throughput_mbps,
            current_latency_ms=request_data.current_latency_ms,
            payload=request_data.additional_info
        )
        
        # 提交請求
        request_id = await engine.submit_handover_request(handover_request)
        
        # 估算處理時間
        estimated_time = engine.decision_config['decision_interval_ms']
        if handover_request.priority >= engine.decision_config['emergency_priority_threshold']:
            estimated_time = 50  # 緊急請求快速處理
        
        return HandoverRequestResponse(
            request_id=request_id,
            status="submitted",
            message="切換請求已成功提交",
            estimated_processing_time_ms=estimated_time
        )
        
    except Exception as e:
        logger.error(f"提交切換請求失敗: {e}")
        raise HTTPException(status_code=500, detail=f"提交切換請求失敗: {str(e)}")


@router.get("/requests/{request_id}")
async def get_handover_request_status(
    request_id: str,
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """獲取切換請求狀態"""
    try:
        # 檢查待處理請求
        if request_id in engine.pending_requests:
            request = engine.pending_requests[request_id]
            return {
                "request_id": request_id,
                "status": "pending",
                "priority": request.priority,
                "trigger_type": request.trigger_type.value,
                "submitted_at": request.timestamp.isoformat(),
                "estimated_remaining_time_ms": engine.decision_config['decision_interval_ms']
            }
        
        # 檢查活動計劃
        for plan in engine.active_plans.values():
            if plan.request.request_id == request_id:
                return {
                    "request_id": request_id,
                    "status": "scheduled",
                    "plan_id": plan.plan_id,
                    "target_satellite_id": plan.target_satellite.satellite_id,
                    "execution_time": plan.execution_time.isoformat(),
                    "decision": plan.decision.value,
                    "total_duration_ms": plan.get_total_duration_ms()
                }
        
        # 檢查已完成的切換
        for completed_plan in engine.completed_handovers:
            if completed_plan.request.request_id == request_id:
                return {
                    "request_id": request_id,
                    "status": "completed",
                    "plan_id": completed_plan.plan_id,
                    "target_satellite_id": completed_plan.target_satellite.satellite_id,
                    "success": completed_plan.payload.get("success", False),
                    "execution_time_ms": completed_plan.payload.get("execution_time_ms", 0),
                    "completed_at": completed_plan.payload.get("completed_at", "").isoformat() if completed_plan.payload.get("completed_at") else ""
                }
        
        raise HTTPException(status_code=404, detail="切換請求未找到")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取切換請求狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")


@router.delete("/requests/{request_id}")
async def cancel_handover_request(
    request_id: str,
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """取消切換請求"""
    try:
        cancelled = await engine.cancel_handover_request(request_id)
        
        if cancelled:
            return {
                "request_id": request_id,
                "status": "cancelled",
                "message": "切換請求已成功取消"
            }
        else:
            raise HTTPException(status_code=404, detail="切換請求未找到或無法取消")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消切換請求失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取消請求失敗: {str(e)}")


@router.get("/plans")
async def get_active_handover_plans(
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """獲取活動切換計劃列表"""
    try:
        plans = []
        for plan in engine.active_plans.values():
            plans.append(HandoverPlanModel(
                plan_id=plan.plan_id,
                request_id=plan.request.request_id,
                target_satellite_id=plan.target_satellite.satellite_id,
                decision=plan.decision.value,
                execution_time=plan.execution_time,
                preparation_phase_duration_ms=plan.preparation_phase_duration_ms,
                execution_phase_duration_ms=plan.execution_phase_duration_ms,
                completion_phase_duration_ms=plan.completion_phase_duration_ms,
                total_duration_ms=plan.get_total_duration_ms(),
                expected_improvement=plan.expected_improvement,
                reserved_resources=plan.reserved_resources
            ))
        
        return {
            "active_plans_count": len(plans),
            "plans": plans
        }
        
    except Exception as e:
        logger.error(f"獲取活動切換計劃失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取計劃失敗: {str(e)}")


@router.get("/statistics")
async def get_handover_statistics(
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """獲取切換統計信息"""
    try:
        stats = engine.stats.copy()
        
        # 計算成功率
        total_handovers = stats['handovers_successful'] + stats['handovers_failed']
        success_rate = (stats['handovers_successful'] / total_handovers * 100) if total_handovers > 0 else 0
        
        # 添加額外統計
        stats['success_rate_percent'] = round(success_rate, 2)
        stats['pending_requests_count'] = len(engine.pending_requests)
        stats['active_plans_count'] = len(engine.active_plans)
        stats['completed_handovers_count'] = len(engine.completed_handovers)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"獲取切換統計信息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")


@router.get("/status", response_model=EngineStatusModel)
async def get_engine_status(
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """獲取決策引擎狀態"""
    try:
        status = engine.get_engine_status()
        
        return EngineStatusModel(
            engine_id=status['engine_id'],
            is_running=status['is_running'],
            pending_requests=status['pending_requests'],
            active_plans=status['active_plans'],
            completed_handovers=status['completed_handovers'],
            statistics=status['statistics'],
            configuration=status['configuration']
        )
        
    except Exception as e:
        logger.error(f"獲取引擎狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")


@router.post("/engine/start")
async def start_engine(
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """啟動決策引擎"""
    try:
        if engine.is_running:
            return {
                "status": "already_running",
                "message": "決策引擎已在運行中"
            }
        
        await engine.start_engine()
        
        return {
            "status": "started",
            "message": "決策引擎已成功啟動",
            "engine_id": engine.engine_id
        }
        
    except Exception as e:
        logger.error(f"啟動決策引擎失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動引擎失敗: {str(e)}")


@router.post("/engine/stop")
async def stop_engine(
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """停止決策引擎"""
    try:
        if not engine.is_running:
            return {
                "status": "already_stopped",
                "message": "決策引擎已停止"
            }
        
        await engine.stop_engine()
        
        return {
            "status": "stopped",
            "message": "決策引擎已成功停止",
            "engine_id": engine.engine_id
        }
        
    except Exception as e:
        logger.error(f"停止決策引擎失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止引擎失敗: {str(e)}")


@router.put("/config", response_model=Dict[str, str])
async def update_engine_config(
    config_data: ConfigUpdateModel,
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """更新引擎配置"""
    try:
        config_dict = {}
        
        if config_data.decision_config:
            config_dict['decision_config'] = config_data.decision_config
        
        if config_data.optimization_weights:
            config_dict['optimization_weights'] = config_data.optimization_weights
        
        if config_data.service_weights:
            # 更新服務權重
            for service_type, weights in config_data.service_weights.items():
                if service_type in engine.service_weights:
                    engine.service_weights[service_type].update(weights)
        
        if config_dict:
            engine.update_config(config_dict)
        
        return {
            "status": "updated",
            "message": "引擎配置已成功更新"
        }
        
    except Exception as e:
        logger.error(f"更新引擎配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失敗: {str(e)}")


@router.get("/config")
async def get_engine_config(
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """獲取引擎配置"""
    try:
        return {
            "decision_config": engine.decision_config,
            "optimization_weights": engine.optimization_weights,
            "service_weights": engine.service_weights
        }
        
    except Exception as e:
        logger.error(f"獲取引擎配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取配置失敗: {str(e)}")


@router.get("/candidates/{satellite_id}")
async def get_satellite_candidates(
    satellite_id: str,
    user_id: str,
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """獲取指定衛星的候選衛星列表"""
    try:
        candidates = await engine._get_satellite_candidates(user_id, satellite_id)
        
        candidate_models = []
        for candidate in candidates:
            candidate_models.append(SatelliteCandidateModel(
                satellite_id=candidate.satellite_id,
                signal_strength_dbm=candidate.signal_strength_dbm,
                elevation_angle=candidate.elevation_angle,
                azimuth_angle=candidate.azimuth_angle,
                distance_km=candidate.distance_km,
                velocity_kmh=candidate.velocity_kmh,
                doppler_shift_hz=candidate.doppler_shift_hz,
                available_bandwidth_mbps=candidate.available_bandwidth_mbps,
                current_load_percent=candidate.current_load_percent,
                user_count=candidate.user_count,
                beam_capacity_percent=candidate.beam_capacity_percent,
                predicted_throughput_mbps=candidate.predicted_throughput_mbps,
                predicted_latency_ms=candidate.predicted_latency_ms,
                predicted_reliability=candidate.predicted_reliability,
                predicted_availability_duration_s=candidate.predicted_availability_duration_s,
                handover_delay_ms=candidate.handover_delay_ms,
                signaling_overhead_kb=candidate.signaling_overhead_kb,
                resource_preparation_ms=candidate.resource_preparation_ms
            ))
        
        return {
            "current_satellite_id": satellite_id,
            "user_id": user_id,
            "candidates_count": len(candidate_models),
            "candidates": candidate_models
        }
        
    except Exception as e:
        logger.error(f"獲取候選衛星失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取候選衛星失敗: {str(e)}")


@router.get("/health")
async def health_check(
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """健康檢查"""
    try:
        status = engine.get_engine_status()
        
        # 健康狀態評估
        health_score = 1.0
        issues = []
        
        # 檢查引擎運行狀態
        if not status['is_running']:
            health_score -= 0.5
            issues.append("引擎未運行")
        
        # 檢查待處理請求堆積
        if status['pending_requests'] > 20:
            health_score -= 0.2
            issues.append("待處理請求過多")
        
        # 檢查成功率
        total_handovers = status['statistics']['handovers_successful'] + status['statistics']['handovers_failed']
        if total_handovers > 0:
            success_rate = status['statistics']['handovers_successful'] / total_handovers
            if success_rate < 0.95:
                health_score -= 0.3
                issues.append(f"切換成功率過低: {success_rate:.2%}")
        
        health_status = "healthy" if health_score >= 0.8 else "degraded" if health_score >= 0.5 else "unhealthy"
        
        return {
            "status": health_status,
            "health_score": round(health_score, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine_id": status['engine_id'],
            "is_running": status['is_running'],
            "issues": issues,
            "uptime_info": {
                "pending_requests": status['pending_requests'],
                "active_plans": status['active_plans'],
                "completed_handovers": status['completed_handovers']
            }
        }
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "health_score": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }


# === 測試端點 ===

@router.post("/test/submit-test-request")
async def submit_test_handover_request(
    user_id: str = "test_user",
    current_satellite_id: str = "TEST-SAT-001",
    trigger_type: HandoverTriggerType = HandoverTriggerType.SIGNAL_STRENGTH,
    priority: int = 5,
    engine: FineGrainedHandoverDecisionEngine = Depends(get_handover_engine)
):
    """提交測試切換請求"""
    try:
        test_request = create_test_handover_request(
            user_id, current_satellite_id, 
            HandoverTrigger(trigger_type.value), 
            priority
        )
        
        request_id = await engine.submit_handover_request(test_request)
        
        return {
            "request_id": request_id,
            "status": "test_submitted",
            "message": "測試切換請求已提交",
            "test_parameters": {
                "user_id": user_id,
                "current_satellite_id": current_satellite_id,
                "trigger_type": trigger_type.value,
                "priority": priority
            }
        }
        
    except Exception as e:
        logger.error(f"提交測試切換請求失敗: {e}")
        raise HTTPException(status_code=500, detail=f"提交測試請求失敗: {str(e)}")


# 路由包含函數
def include_handover_decision_router(app):
    """包含切換決策路由到應用"""
    app.include_router(router)
    logger.info("✅ 精細化切換決策引擎 API 路由已註冊")