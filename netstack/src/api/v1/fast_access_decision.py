"""
Phase 3.2.2.2: 快速接入決策引擎 API

提供快速接入決策引擎的 RESTful API 接口，包括：
1. 接入請求提交和管理
2. 決策引擎控制和監控
3. 候選衛星評估和選擇
4. 系統性能和統計信息
5. 配置管理和調整
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from enum import Enum
import logging

from ...algorithms.access.fast_access_decision import (
    FastAccessDecisionEngine,
    AccessRequest,
    AccessCandidate,
    AccessPlan,
    AccessDecisionType,
    ServiceClass,
    AccessTrigger,
    create_fast_access_decision_engine,
    create_test_access_request
)

logger = logging.getLogger(__name__)

# 全局接入決策引擎實例
_access_engine: Optional[FastAccessDecisionEngine] = None

router = APIRouter(prefix="/fast-access-decision", tags=["fast-access-decision"])


# === Pydantic 模型定義 ===

class AccessTriggerType(str, Enum):
    """接入觸發類型"""
    INITIAL_ATTACH = "initial_attach"
    HANDOVER = "handover"
    SERVICE_REQUEST = "service_request"
    EMERGENCY_CALL = "emergency_call"
    PERIODIC_UPDATE = "periodic_update"


class ServiceClassType(str, Enum):
    """服務類別"""
    EMERGENCY = "emergency"
    VOICE = "voice"
    VIDEO = "video"
    DATA = "data"
    IOT = "iot"
    BACKGROUND = "background"


class AccessRequestModel(BaseModel):
    """接入請求模型"""
    user_id: str = Field(..., description="用戶ID")
    device_id: str = Field(..., description="設備ID")
    trigger_type: AccessTriggerType = Field(..., description="觸發類型")
    service_class: ServiceClassType = Field(..., description="服務類別")
    
    # 位置信息
    user_latitude: float = Field(..., description="用戶緯度")
    user_longitude: float = Field(..., description="用戶經度")
    user_altitude_m: float = Field(0.0, description="用戶高度(米)")
    
    # 服務需求
    required_bandwidth_mbps: float = Field(1.0, ge=0.1, description="所需帶寬(Mbps)")
    max_acceptable_latency_ms: float = Field(1000.0, ge=10, description="最大可接受延遲(ms)")
    min_acceptable_reliability: float = Field(0.95, ge=0.5, le=1.0, description="最小可接受可靠性")
    max_acceptable_jitter_ms: float = Field(100.0, ge=0, description="最大可接受抖動(ms)")
    
    # 優先級和期限
    priority: int = Field(5, ge=1, le=10, description="優先級 (1-10)")
    deadline_ms: Optional[int] = Field(None, description="期限(毫秒)")
    max_waiting_time_ms: int = Field(30000, description="最大等待時間(毫秒)")
    
    # 當前狀態
    current_satellite_id: Optional[str] = Field(None, description="當前衛星ID")
    current_signal_strength_dbm: Optional[float] = Field(None, description="當前信號強度(dBm)")
    battery_level_percent: Optional[float] = Field(None, description="電池電量百分比")
    
    # 設備能力
    device_capabilities: Dict[str, Any] = Field(default_factory=dict, description="設備能力")
    additional_info: Dict[str, Any] = Field(default_factory=dict, description="額外信息")


class AccessRequestResponse(BaseModel):
    """接入請求響應"""
    request_id: str = Field(..., description="請求ID")
    status: str = Field(..., description="提交狀態")
    message: str = Field(..., description="響應消息")
    estimated_processing_time_ms: int = Field(..., description="預估處理時間(ms)")


class AccessCandidateModel(BaseModel):
    """接入候選模型"""
    satellite_id: str = Field(..., description="衛星ID")
    beam_id: str = Field(..., description="波束ID")
    frequency_band: str = Field(..., description="頻段")
    
    # 覆蓋信息
    elevation_angle: float = Field(..., description="仰角(度)")
    azimuth_angle: float = Field(..., description="方位角(度)")
    distance_km: float = Field(..., description="距離(公里)")
    signal_strength_dbm: float = Field(..., description="信號強度(dBm)")
    path_loss_db: float = Field(..., description="路徑損耗(dB)")
    doppler_shift_hz: float = Field(..., description="都卜勒頻移(Hz)")
    
    # 容量信息
    total_capacity_mbps: float = Field(..., description="總容量(Mbps)")
    available_capacity_mbps: float = Field(..., description="可用容量(Mbps)")
    current_load_percent: float = Field(..., description="當前負載百分比")
    active_users: int = Field(..., description="活躍用戶數")
    max_users: int = Field(..., description="最大用戶數")
    
    # 服務質量預測
    predicted_throughput_mbps: float = Field(..., description="預測吞吐量(Mbps)")
    predicted_latency_ms: float = Field(..., description="預測延遲(ms)")
    predicted_packet_loss_rate: float = Field(..., description="預測丟包率")
    predicted_availability_duration_s: float = Field(..., description="預測可用時間(秒)")
    
    # 接入成本
    setup_time_ms: float = Field(..., description="建立時間(ms)")
    signaling_overhead_kb: float = Field(..., description="信令開銷(KB)")
    power_consumption_mw: float = Field(..., description="功耗(mW)")
    interference_level_db: float = Field(..., description="干擾水平(dB)")
    
    # 評分結果
    composite_score: float = Field(..., description="綜合評分")
    ranking: int = Field(..., description="排名")


class AccessPlanModel(BaseModel):
    """接入計劃模型"""
    plan_id: str = Field(..., description="計劃ID")
    request_id: str = Field(..., description="對應的請求ID")
    selected_satellite_id: str = Field(..., description="選定的衛星ID")
    decision: str = Field(..., description="決策結果")
    execution_time: datetime = Field(..., description="執行時間")
    
    # 時序信息
    preparation_phase_duration_ms: int = Field(..., description="準備階段時長(ms)")
    execution_phase_duration_ms: int = Field(..., description="執行階段時長(ms)")
    completion_phase_duration_ms: int = Field(..., description="完成階段時長(ms)")
    total_duration_ms: int = Field(..., description="總時長(ms)")
    
    # 資源預留
    reserved_bandwidth_mbps: float = Field(..., description="預留帶寬(Mbps)")
    reserved_beam_capacity_percent: float = Field(..., description="預留波束容量百分比")
    allocated_frequency_khz: float = Field(..., description="分配頻率(kHz)")
    
    # 服務質量保證
    guaranteed_throughput_mbps: float = Field(..., description="保證吞吐量(Mbps)")
    guaranteed_max_latency_ms: float = Field(..., description="保證最大延遲(ms)")
    guaranteed_reliability: float = Field(..., description="保證可靠性")
    
    # 條件和約束
    conditions: List[str] = Field(..., description="條件列表")
    fallback_options: List[str] = Field(..., description="備用選項")
    status: str = Field(..., description="執行狀態")


class EngineStatusModel(BaseModel):
    """引擎狀態模型"""
    engine_id: str = Field(..., description="引擎ID")
    is_running: bool = Field(..., description="是否運行中")
    pending_requests: int = Field(..., description="待處理請求數")
    active_plans: int = Field(..., description="活動計劃數")
    completed_accesses: int = Field(..., description="已完成接入數")
    
    # 資源狀態
    satellite_loads: Dict[str, float] = Field(..., description="衛星負載狀態")
    
    # 統計信息
    statistics: Dict[str, Union[int, float]] = Field(..., description="統計信息")
    
    # 配置信息
    configuration: Dict[str, Any] = Field(..., description="配置信息")


class ConfigUpdateModel(BaseModel):
    """配置更新模型"""
    decision_config: Optional[Dict[str, Any]] = Field(None, description="決策配置")
    evaluation_weights: Optional[Dict[str, float]] = Field(None, description="評估權重")
    service_configs: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="服務配置")


class CandidateQueryModel(BaseModel):
    """候選查詢模型"""
    user_latitude: float = Field(..., description="用戶緯度")
    user_longitude: float = Field(..., description="用戶經度")
    service_class: Optional[ServiceClassType] = Field(None, description="服務類別")
    min_elevation_angle: float = Field(10.0, description="最小仰角(度)")
    max_candidates: int = Field(10, ge=1, le=50, description="最大候選數")


# === 依賴注入 ===

async def get_access_engine() -> FastAccessDecisionEngine:
    """獲取接入決策引擎實例"""
    global _access_engine
    if _access_engine is None:
        _access_engine = create_fast_access_decision_engine("api_engine")
        await _access_engine.start_engine()
    return _access_engine


# === API 端點實現 ===

@router.post("/requests", response_model=AccessRequestResponse)
async def submit_access_request(
    request_data: AccessRequestModel,
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
):
    """提交接入請求"""
    try:
        # 創建接入請求
        access_request = AccessRequest(
            request_id=f"api_req_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            user_id=request_data.user_id,
            device_id=request_data.device_id,
            trigger_type=AccessTrigger(request_data.trigger_type.value),
            service_class=ServiceClass(request_data.service_class.value),
            timestamp=datetime.now(timezone.utc),
            user_latitude=request_data.user_latitude,
            user_longitude=request_data.user_longitude,
            user_altitude_m=request_data.user_altitude_m,
            required_bandwidth_mbps=request_data.required_bandwidth_mbps,
            max_acceptable_latency_ms=request_data.max_acceptable_latency_ms,
            min_acceptable_reliability=request_data.min_acceptable_reliability,
            max_acceptable_jitter_ms=request_data.max_acceptable_jitter_ms,
            priority=request_data.priority,
            deadline_ms=request_data.deadline_ms,
            max_waiting_time_ms=request_data.max_waiting_time_ms,
            current_satellite_id=request_data.current_satellite_id,
            current_signal_strength_dbm=request_data.current_signal_strength_dbm,
            battery_level_percent=request_data.battery_level_percent,
            device_capabilities=request_data.device_capabilities,
            payload=request_data.additional_info
        )
        
        # 提交請求
        request_id = await engine.submit_access_request(access_request)
        
        # 估算處理時間
        estimated_time = engine.decision_config['evaluation_interval_ms']
        if access_request.service_class == ServiceClass.EMERGENCY:
            estimated_time = 50  # 緊急請求快速處理
        
        return AccessRequestResponse(
            request_id=request_id,
            status="submitted",
            message="接入請求已成功提交",
            estimated_processing_time_ms=estimated_time
        )
        
    except Exception as e:
        logger.error(f"提交接入請求失敗: {e}")
        raise HTTPException(status_code=500, detail=f"提交接入請求失敗: {str(e)}")


@router.get("/requests/{request_id}")
async def get_access_request_status(
    request_id: str,
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
):
    """獲取接入請求狀態"""
    try:
        # 檢查待處理請求
        if request_id in engine.pending_requests:
            request = engine.pending_requests[request_id]
            return {
                "request_id": request_id,
                "status": "pending",
                "user_id": request.user_id,
                "service_class": request.service_class.value,
                "priority": request.priority,
                "submitted_at": request.timestamp.isoformat(),
                "estimated_remaining_time_ms": engine.decision_config['evaluation_interval_ms']
            }
        
        # 檢查活動計劃
        for plan in engine.active_plans.values():
            if plan.request.request_id == request_id:
                return {
                    "request_id": request_id,
                    "status": "planned",
                    "plan_id": plan.plan_id,
                    "selected_satellite_id": plan.selected_candidate.satellite_id,
                    "decision": plan.decision.value,
                    "execution_time": plan.execution_time.isoformat(),
                    "total_duration_ms": plan.get_total_duration_ms(),
                    "reserved_bandwidth_mbps": plan.reserved_bandwidth_mbps,
                    "guaranteed_throughput_mbps": plan.guaranteed_throughput_mbps
                }
        
        # 檢查已完成的接入
        for completed_plan in list(engine.completed_accesses):
            if hasattr(completed_plan, 'request') and completed_plan.request.request_id == request_id:
                return {
                    "request_id": request_id,
                    "status": "completed",
                    "plan_id": completed_plan.plan_id,
                    "selected_satellite_id": completed_plan.selected_candidate.satellite_id,
                    "decision": completed_plan.decision.value,
                    "success": completed_plan.status == "completed",
                    "execution_time_ms": completed_plan.get_total_duration_ms()
                }
        
        raise HTTPException(status_code=404, detail="接入請求未找到")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取接入請求狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")


@router.delete("/requests/{request_id}")
async def cancel_access_request(
    request_id: str,
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
):
    """取消接入請求"""
    try:
        cancelled = await engine.cancel_access_request(request_id)
        
        if cancelled:
            return {
                "request_id": request_id,
                "status": "cancelled",
                "message": "接入請求已成功取消"
            }
        else:
            raise HTTPException(status_code=404, detail="接入請求未找到或無法取消")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消接入請求失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取消請求失敗: {str(e)}")


@router.get("/plans")
async def get_active_access_plans(
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
):
    """獲取活動接入計劃列表"""
    try:
        plans = []
        for plan in engine.active_plans.values():
            plans.append(AccessPlanModel(
                plan_id=plan.plan_id,
                request_id=plan.request.request_id,
                selected_satellite_id=plan.selected_candidate.satellite_id,
                decision=plan.decision.value,
                execution_time=plan.execution_time,
                preparation_phase_duration_ms=plan.preparation_phase_duration_ms,
                execution_phase_duration_ms=plan.execution_phase_duration_ms,
                completion_phase_duration_ms=plan.completion_phase_duration_ms,
                total_duration_ms=plan.get_total_duration_ms(),
                reserved_bandwidth_mbps=plan.reserved_bandwidth_mbps,
                reserved_beam_capacity_percent=plan.reserved_beam_capacity_percent,
                allocated_frequency_khz=plan.allocated_frequency_khz,
                guaranteed_throughput_mbps=plan.guaranteed_throughput_mbps,
                guaranteed_max_latency_ms=plan.guaranteed_max_latency_ms,
                guaranteed_reliability=plan.guaranteed_reliability,
                conditions=plan.conditions,
                fallback_options=[c.satellite_id for c in plan.fallback_options],
                status=plan.status
            ))
        
        return {
            "active_plans_count": len(plans),
            "plans": plans
        }
        
    except Exception as e:
        logger.error(f"獲取活動接入計劃失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取計劃失敗: {str(e)}")


@router.get("/candidates")
async def get_access_candidates(
    query: CandidateQueryModel = Depends(),
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
):
    """獲取接入候選衛星"""
    try:
        # 創建臨時請求用於獲取候選
        temp_request = AccessRequest(
            request_id="temp_candidate_query",
            user_id="temp_user",
            device_id="temp_device",
            trigger_type=AccessTrigger.SERVICE_REQUEST,
            service_class=ServiceClass(query.service_class.value) if query.service_class else ServiceClass.DATA,
            timestamp=datetime.now(timezone.utc),
            user_latitude=query.user_latitude,
            user_longitude=query.user_longitude
        )
        
        # 獲取候選衛星
        candidates = await engine._get_access_candidates(temp_request)
        
        # 評估候選衛星
        evaluated_candidates = await engine._evaluate_candidates(temp_request, candidates)
        
        # 限制返回數量
        limited_candidates = evaluated_candidates[:query.max_candidates]
        
        # 轉換為API模型
        candidate_models = []
        for candidate in limited_candidates:
            if candidate.elevation_angle >= query.min_elevation_angle:
                candidate_models.append(AccessCandidateModel(
                    satellite_id=candidate.satellite_id,
                    beam_id=candidate.beam_id,
                    frequency_band=candidate.frequency_band,
                    elevation_angle=candidate.elevation_angle or 0.0,
                    azimuth_angle=candidate.azimuth_angle or 0.0,
                    distance_km=candidate.distance_km or 0.0,
                    signal_strength_dbm=candidate.signal_strength_dbm or -100.0,
                    path_loss_db=candidate.path_loss_db or 180.0,
                    doppler_shift_hz=candidate.doppler_shift_hz or 0.0,
                    total_capacity_mbps=candidate.total_capacity_mbps,
                    available_capacity_mbps=candidate.available_capacity_mbps,
                    current_load_percent=candidate.current_load_percent,
                    active_users=candidate.active_users,
                    max_users=candidate.max_users,
                    predicted_throughput_mbps=candidate.predicted_throughput_mbps,
                    predicted_latency_ms=candidate.predicted_latency_ms,
                    predicted_packet_loss_rate=candidate.predicted_packet_loss_rate,
                    predicted_availability_duration_s=candidate.predicted_availability_duration_s,
                    setup_time_ms=candidate.setup_time_ms,
                    signaling_overhead_kb=candidate.signaling_overhead_kb,
                    power_consumption_mw=candidate.power_consumption_mw,
                    interference_level_db=candidate.interference_level_db,
                    composite_score=candidate.composite_score,
                    ranking=candidate.ranking
                ))
        
        return {
            "query_location": {
                "latitude": query.user_latitude,
                "longitude": query.user_longitude
            },
            "candidates_count": len(candidate_models),
            "candidates": candidate_models
        }
        
    except Exception as e:
        logger.error(f"獲取接入候選失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取候選失敗: {str(e)}")


@router.get("/statistics")
async def get_access_statistics(
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
):
    """獲取接入統計信息"""
    try:
        stats = engine.stats.copy()
        
        # 計算成功率
        total_requests = stats['requests_accepted'] + stats['requests_rejected']
        success_rate = (stats['requests_accepted'] / total_requests * 100) if total_requests > 0 else 0
        
        # 添加額外統計
        stats['success_rate_percent'] = round(success_rate, 2)
        stats['pending_requests_count'] = len(engine.pending_requests)
        stats['active_plans_count'] = len(engine.active_plans)
        stats['completed_accesses_count'] = len(engine.completed_accesses)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"獲取接入統計信息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")


@router.get("/status", response_model=EngineStatusModel)
async def get_engine_status(
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
):
    """獲取決策引擎狀態"""
    try:
        status = engine.get_engine_status()
        
        return EngineStatusModel(
            engine_id=status['engine_id'],
            is_running=status['is_running'],
            pending_requests=status['pending_requests'],
            active_plans=status['active_plans'],
            completed_accesses=status['completed_accesses'],
            satellite_loads=status['satellite_loads'],
            statistics=status['statistics'],
            configuration=status['configuration']
        )
        
    except Exception as e:
        logger.error(f"獲取引擎狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")


@router.post("/engine/start")
async def start_engine(
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
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
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
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


@router.put("/config")
async def update_engine_config(
    config_data: ConfigUpdateModel,
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
):
    """更新引擎配置"""
    try:
        config_dict = {}
        
        if config_data.decision_config:
            config_dict['decision_config'] = config_data.decision_config
        
        if config_data.evaluation_weights:
            config_dict['evaluation_weights'] = config_data.evaluation_weights
        
        if config_data.service_configs:
            config_dict['service_configs'] = config_data.service_configs
        
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
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
):
    """獲取引擎配置"""
    try:
        return {
            "decision_config": engine.decision_config,
            "evaluation_weights": engine.evaluation_weights,
            "service_configs": {k.value: v for k, v in engine.service_configs.items()}
        }
        
    except Exception as e:
        logger.error(f"獲取引擎配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取配置失敗: {str(e)}")


@router.get("/health")
async def health_check(
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
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
        if status['pending_requests'] > 50:
            health_score -= 0.2
            issues.append("待處理請求過多")
        
        # 檢查成功率
        stats = status['statistics']
        total_requests = stats['requests_accepted'] + stats['requests_rejected']
        if total_requests > 0:
            success_rate = stats['requests_accepted'] / total_requests
            if success_rate < 0.9:
                health_score -= 0.3
                issues.append(f"接入成功率過低: {success_rate:.2%}")
        
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
                "completed_accesses": status['completed_accesses']
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
async def submit_test_access_request(
    user_id: str = "test_user",
    service_class: ServiceClassType = ServiceClassType.DATA,
    trigger_type: AccessTriggerType = AccessTriggerType.INITIAL_ATTACH,
    priority: int = 5,
    engine: FastAccessDecisionEngine = Depends(get_access_engine)
):
    """提交測試接入請求"""
    try:
        test_request = create_test_access_request(
            user_id, 
            ServiceClass(service_class.value),
            AccessTrigger(trigger_type.value),
            priority
        )
        
        request_id = await engine.submit_access_request(test_request)
        
        return {
            "request_id": request_id,
            "status": "test_submitted",
            "message": "測試接入請求已提交",
            "test_parameters": {
                "user_id": user_id,
                "service_class": service_class.value,
                "trigger_type": trigger_type.value,
                "priority": priority
            }
        }
        
    except Exception as e:
        logger.error(f"提交測試接入請求失敗: {e}")
        raise HTTPException(status_code=500, detail=f"提交測試請求失敗: {str(e)}")


# 路由包含函數
def include_fast_access_decision_router(app):
    """包含快速接入決策路由到應用"""
    app.include_router(router)
    logger.info("✅ 快速接入決策引擎 API 路由已註冊")