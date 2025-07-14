"""
Phase 2.2 真實換手場景生成 API 端點

提供完整的真實換手場景生成、觸發檢測、候選評分和信號預測功能
整合所有 Phase 2.2 開發的核心組件
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ..scenarios.handover_scenario_generator import (
    RealTimeHandoverScenarioGenerator,
    HandoverScenario,
    ScenarioResult,
    ScenarioComplexity,
    HandoverTriggerType,
)
from ..scenarios.handover_trigger_engine import (
    HandoverTriggerEngine,
    TriggerEvent,
    TriggerCondition,
    TriggerSeverity,
)
from ..scenarios.candidate_scoring_service import (
    EnhancedCandidateScoringService,
    AdvancedCandidateScore,
    ScoringWeights,
)
from ..scenarios.signal_quality_service import (
    EnhancedSignalQualityService,
    SignalQualityMetrics,
    EnvironmentScenario,
)
from ..environments.leo_satellite_environment import LEOSatelliteEnvironment
from ...simworld_tle_bridge_service import SimWorldTLEBridgeService

logger = logging.getLogger(__name__)


# API 模型定義
class ScenarioGenerationRequest(BaseModel):
    scenario_type: str = Field(
        default="urban", description="場景類型：urban, suburban, rural, high_mobility"
    )
    complexity: str = Field(
        default="moderate", description="複雜度：simple, moderate, complex"
    )
    trigger_type: str = Field(default="signal_degradation", description="觸發類型")
    duration_seconds: int = Field(default=300, description="場景持續時間（秒）")
    ue_position: Dict[str, float] = Field(
        default={"lat": 24.786667, "lon": 120.996944, "alt": 100.0},
        description="用戶設備位置",
    )
    custom_constraints: Optional[Dict[str, Any]] = Field(
        default=None, description="自定義約束"
    )


class TriggerMonitoringRequest(BaseModel):
    current_serving_satellite: str = Field(description="當前服務衛星 ID")
    ue_position: Dict[str, float] = Field(description="用戶設備位置")
    candidate_satellites: List[str] = Field(description="候選衛星列表")
    monitoring_duration_s: float = Field(default=60.0, description="監控持續時間（秒）")


class CandidateScoringRequest(BaseModel):
    satellite_ids: List[str] = Field(description="候選衛星 ID 列表")
    ue_position: Dict[str, float] = Field(description="用戶設備位置")
    current_serving_satellite: Optional[str] = Field(
        default=None, description="當前服務衛星"
    )
    scenario_context: Optional[Dict[str, Any]] = Field(
        default=None, description="場景上下文"
    )
    scoring_weights: Optional[Dict[str, float]] = Field(
        default=None, description="評分權重"
    )


class SignalPredictionRequest(BaseModel):
    satellite_id: str = Field(description="衛星 ID")
    ue_position: Dict[str, float] = Field(description="用戶設備位置")
    scenario: str = Field(default="urban", description="環境場景")
    prediction_horizons: Optional[List[int]] = Field(
        default=None, description="預測時間範圍（秒）"
    )


# 響應模型
class ScenarioGenerationResponse(BaseModel):
    scenario_id: str
    scenario_type: str
    complexity: str
    trigger_type: str
    candidate_count: int
    expected_handovers: int
    performance_targets: Dict[str, float]
    created_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TriggerEventResponse(BaseModel):
    event_id: str
    trigger_type: str
    severity: str
    satellite_id: str
    trigger_value: float
    threshold: float
    confidence: float
    recommended_action: str
    alternative_satellites: List[str]
    timestamp: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CandidateScoreResponse(BaseModel):
    satellite_id: str
    overall_score: float
    signal_score: float
    load_score: float
    elevation_score: float
    distance_score: float
    prediction_confidence: float
    stability_score: float
    handover_cost: float
    signal_trend: str
    optimal_handover_time: Optional[datetime]
    risk_level: str
    risk_factors: List[str]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class SignalQualityResponse(BaseModel):
    satellite_id: str
    current_rsrp: float
    current_rsrq: float
    current_sinr: float
    predicted_5s_rsrp: float
    predicted_30s_rsrp: float
    predicted_60s_rsrp: float
    prediction_confidence: float
    signal_trend: str
    improvement_potential: float
    degradation_risk: float
    stability_score: float


# 創建路由器
router = APIRouter(tags=["Phase 2.2 - 真實換手場景生成"])

# 全局服務實例（在實際部署中應該通過依賴注入管理）
_services_initialized = False
_scenario_generator = None
_trigger_engine = None
_scoring_service = None
_signal_service = None


async def get_services():
    """獲取服務實例"""
    global _services_initialized, _scenario_generator, _trigger_engine, _scoring_service, _signal_service

    if not _services_initialized:
        # 初始化基礎服務
        tle_bridge = SimWorldTLEBridgeService()
        leo_env = LEOSatelliteEnvironment(
            {
                "simworld_url": "http://localhost:8888",
                "max_satellites": 6,
                "scenario": "urban",
                "fallback_enabled": True,
            }
        )

        # 初始化 Phase 2.2 服務
        _scenario_generator = RealTimeHandoverScenarioGenerator(
            tle_bridge_service=tle_bridge, leo_environment=leo_env
        )

        _trigger_engine = HandoverTriggerEngine(
            tle_bridge_service=tle_bridge, leo_environment=leo_env
        )

        _scoring_service = EnhancedCandidateScoringService(
            tle_bridge_service=tle_bridge,
            leo_environment=leo_env,
            load_balancer=leo_env.load_balancer,
        )

        _signal_service = EnhancedSignalQualityService(
            tle_bridge_service=tle_bridge, leo_environment=leo_env
        )

        _services_initialized = True
        logger.info("Phase 2.2 服務初始化完成")

    return _scenario_generator, _trigger_engine, _scoring_service, _signal_service


@router.post("/scenarios/generate", response_model=ScenarioGenerationResponse)
async def generate_handover_scenario(request: ScenarioGenerationRequest):
    """
    生成真實換手場景

    基於真實 TLE 數據和軌道動力學，生成複雜的換手決策場景
    """
    try:
        scenario_generator, _, _, _ = await get_services()

        # 轉換輸入參數
        complexity = ScenarioComplexity(request.complexity.lower())
        trigger_type = HandoverTriggerType(request.trigger_type.lower())

        # 生成場景
        scenario = await scenario_generator.generate_handover_scenario(
            scenario_type=request.scenario_type,
            complexity=complexity,
            trigger_type=trigger_type,
            custom_constraints=request.custom_constraints,
        )

        # 構建響應
        response = ScenarioGenerationResponse(
            scenario_id=scenario.scenario_id,
            scenario_type=scenario.scenario_type,
            complexity=scenario.complexity.value,
            trigger_type=scenario.trigger_type.value,
            candidate_count=len(scenario.candidate_satellites),
            expected_handovers=scenario.expected_handovers,
            performance_targets=scenario.performance_targets,
            created_at=scenario.created_at,
        )

        logger.info(f"成功生成換手場景: {scenario.scenario_id}")
        return response

    except Exception as e:
        logger.error(f"生成換手場景失敗: {e}")
        raise HTTPException(status_code=500, detail=f"場景生成失敗: {str(e)}")


@router.post("/triggers/monitor", response_model=List[TriggerEventResponse])
async def monitor_handover_triggers(request: TriggerMonitoringRequest):
    """
    監控換手觸發條件

    實時檢測基於真實軌道數據的換手觸發事件
    """
    try:
        _, trigger_engine, _, _ = await get_services()

        # 監控觸發條件
        trigger_events = await trigger_engine.monitor_handover_triggers(
            current_serving_satellite=request.current_serving_satellite,
            ue_position=request.ue_position,
            candidate_satellites=request.candidate_satellites,
        )

        # 構建響應
        responses = []
        for event in trigger_events:
            response = TriggerEventResponse(
                event_id=event.event_id,
                trigger_type=event.trigger_type.value,
                severity=event.severity.value,
                satellite_id=event.satellite_id,
                trigger_value=event.trigger_value,
                threshold=event.threshold,
                confidence=event.confidence,
                recommended_action=event.recommended_action,
                alternative_satellites=event.alternative_satellites,
                timestamp=event.timestamp,
            )
            responses.append(response)

        logger.info(f"檢測到 {len(trigger_events)} 個觸發事件")
        return responses

    except Exception as e:
        logger.error(f"觸發監控失敗: {e}")
        raise HTTPException(status_code=500, detail=f"觸發監控失敗: {str(e)}")


@router.post("/candidates/score", response_model=List[CandidateScoreResponse])
async def score_candidate_satellites(request: CandidateScoringRequest):
    """
    評分候選衛星

    使用統一的多維度評分系統對候選衛星進行智能評分和排序
    """
    try:
        scenario_generator, _, scoring_service, _ = await get_services()

        # 獲取衛星數據
        leo_env = scoring_service.leo_env
        all_satellites = await leo_env.get_satellite_data()

        # 篩選候選衛星
        candidate_satellites = [
            sat for sat in all_satellites if str(sat.id) in request.satellite_ids
        ]

        if not candidate_satellites:
            raise HTTPException(status_code=404, detail="未找到指定的候選衛星")

        # 更新評分權重（如果提供）
        if request.scoring_weights:
            new_weights = ScoringWeights(**request.scoring_weights)
            scoring_service.update_scoring_weights(new_weights)

        # 評分和排序
        scored_candidates = await scoring_service.score_and_rank_candidates(
            satellites=candidate_satellites,
            ue_position=request.ue_position,
            current_serving_satellite=request.current_serving_satellite,
            scenario_context=request.scenario_context,
        )

        # 構建響應
        responses = []
        for score in scored_candidates:
            response = CandidateScoreResponse(
                satellite_id=str(score.satellite_id),
                overall_score=score.overall_score,
                signal_score=score.signal_score,
                load_score=score.load_score,
                elevation_score=score.elevation_score,
                distance_score=score.distance_score,
                prediction_confidence=score.prediction_confidence,
                stability_score=score.stability_score,
                handover_cost=score.handover_cost,
                signal_trend=score.signal_trend,
                optimal_handover_time=score.optimal_handover_time,
                risk_level=score.handover_risk_level,
                risk_factors=score.risk_factors,
            )
            responses.append(response)

        logger.info(f"成功評分 {len(scored_candidates)} 個候選衛星")
        return responses

    except Exception as e:
        logger.error(f"候選衛星評分失敗: {e}")
        raise HTTPException(status_code=500, detail=f"評分失敗: {str(e)}")


@router.post("/signal/predict", response_model=SignalQualityResponse)
async def predict_signal_quality(request: SignalPredictionRequest):
    """
    預測信號品質

    使用物理傳播模型和機器學習預測 RSRP、RSRQ、SINR 等信號指標
    """
    try:
        scenario_generator, _, _, signal_service = await get_services()

        # 獲取衛星數據
        leo_env = signal_service.leo_env
        all_satellites = await leo_env.get_satellite_data()

        # 找到指定衛星
        target_satellite = None
        for sat in all_satellites:
            if str(sat.id) == request.satellite_id:
                target_satellite = sat
                break

        if not target_satellite:
            raise HTTPException(
                status_code=404, detail=f"未找到衛星: {request.satellite_id}"
            )

        # 轉換場景類型
        scenario = EnvironmentScenario(request.scenario.lower())

        # 預測信號品質
        signal_metrics = await signal_service.predict_signal_quality(
            satellite=target_satellite,
            ue_position=request.ue_position,
            scenario=scenario,
            time_horizons=request.prediction_horizons,
        )

        # 構建響應
        response = SignalQualityResponse(
            satellite_id=request.satellite_id,
            current_rsrp=signal_metrics.current.rsrp_dbm,
            current_rsrq=signal_metrics.current.rsrq_db,
            current_sinr=signal_metrics.current.sinr_db,
            predicted_5s_rsrp=signal_metrics.predicted_5s.rsrp_dbm,
            predicted_30s_rsrp=signal_metrics.predicted_30s.rsrp_dbm,
            predicted_60s_rsrp=signal_metrics.predicted_60s.rsrp_dbm,
            prediction_confidence=signal_metrics.current.prediction_confidence,
            signal_trend=signal_metrics.current.rsrp_trend,
            improvement_potential=signal_metrics.improvement_potential,
            degradation_risk=signal_metrics.degradation_risk,
            stability_score=signal_metrics.stability_score,
        )

        logger.info(f"成功預測衛星 {request.satellite_id} 的信號品質")
        return response

    except Exception as e:
        logger.error(f"信號品質預測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"預測失敗: {str(e)}")


@router.get("/status")
async def get_system_status():
    """
    獲取 Phase 2.2 系統狀態

    返回所有服務組件的運行狀態和統計信息
    """
    try:
        scenario_generator, trigger_engine, scoring_service, signal_service = (
            await get_services()
        )

        # 收集各服務的統計信息
        scenario_stats = await scenario_generator.get_scenario_statistics()
        trigger_stats = trigger_engine.get_trigger_statistics()
        scoring_stats = scoring_service.get_scoring_statistics()
        signal_stats = signal_service.get_service_statistics()

        status = {
            "phase": "2.2",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "scenario_generator": {
                    "active": True,
                    "scenarios_generated": scenario_stats.get("total_scenarios", 0),
                    "average_generation_time": scenario_stats.get(
                        "avg_generation_time_s", 0.0
                    ),
                },
                "trigger_engine": {
                    "active": True,
                    "triggers_detected": trigger_stats.get(
                        "total_triggers_detected", 0
                    ),
                    "success_rate": trigger_stats.get("trigger_success_rate", 0.0),
                    "active_rules": trigger_stats.get("active_rules", 0),
                },
                "scoring_service": {
                    "active": True,
                    "candidates_scored": scoring_stats.get("candidates_scored", 0),
                    "filtering_efficiency": scoring_stats.get(
                        "filtering_efficiency", 0.0
                    ),
                    "scoring_method": scoring_stats.get(
                        "scoring_method", "weighted_sum"
                    ),
                },
                "signal_service": {
                    "active": True,
                    "predictions_made": signal_stats.get("predictions_made", 0),
                    "cache_hit_rate": signal_stats.get("cache_hit_rate", 0.0),
                    "active_satellites": signal_stats.get("active_satellites", 0),
                },
            },
            "performance_metrics": {
                "total_operations": (
                    scenario_stats.get("total_scenarios", 0)
                    + trigger_stats.get("total_triggers_detected", 0)
                    + scoring_stats.get("candidates_scored", 0)
                    + signal_stats.get("predictions_made", 0)
                ),
                "system_uptime": "Available on restart",
                "memory_usage": "Available with monitoring",
            },
        }

        return status

    except Exception as e:
        logger.error(f"獲取系統狀態失敗: {e}")
        return {
            "phase": "2.2",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


@router.post("/cleanup")
async def cleanup_old_data(max_age_hours: int = 6):
    """
    清理舊數據

    清理各服務中的歷史數據和緩存
    """
    try:
        scenario_generator, trigger_engine, scoring_service, signal_service = (
            await get_services()
        )

        # 清理各服務的舊數據
        await scenario_generator.cleanup_old_scenarios(max_age_hours)
        await trigger_engine.cleanup_old_data(max_age_hours)
        await signal_service.cleanup_old_data(max_age_hours)

        return {
            "status": "success",
            "message": f"成功清理超過 {max_age_hours} 小時的舊數據",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"數據清理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清理失敗: {str(e)}")


# 健康檢查端點
@router.get("/health")
async def health_check():
    """Phase 2.2 服務健康檢查"""
    return {
        "status": "healthy",
        "phase": "2.2",
        "timestamp": datetime.now().isoformat(),
        "services": [
            "scenario_generator",
            "trigger_engine",
            "scoring_service",
            "signal_service",
        ],
    }
