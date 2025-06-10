"""
智能回退決策引擎 API 路由
提供回退策略管理和決策 API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..services.intelligent_fallback_service import (
    intelligent_fallback_service,
    FallbackDecisionContext,
    DecisionOutcome,
    FallbackStrategy,
    PerformanceMetrics
)
from ..services.handover_fault_tolerance_service import (
    HandoverAnomaly,
    HandoverContext,
    AnomalyType,
    AnomalySeverity
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/intelligent-fallback", tags=["Intelligent Fallback"])


# 請求/響應模型
from pydantic import BaseModel

class FallbackDecisionRequest(BaseModel):
    anomaly_id: str
    anomaly_type: str
    severity: str
    ue_id: str
    handover_id: str
    source_satellite: str
    target_satellite: str
    available_satellites: List[str]
    system_load: float
    time_constraints: float
    retry_count: int = 0
    network_conditions: Dict[str, Any] = {}
    signal_quality: Dict[str, float] = {}


class FallbackDecisionResponse(BaseModel):
    decision_id: str
    strategy: str
    target_satellite: Optional[str]
    estimated_recovery_time: float
    confidence: float
    description: str
    priority: int
    timestamp: datetime


class DecisionOutcomeRequest(BaseModel):
    decision_id: str
    outcome: str
    actual_recovery_time: float
    success_achieved: bool
    lessons_learned: List[str] = []


class PerformanceMetricsResponse(BaseModel):
    total_decisions: int
    successful_decisions: int
    success_rate: float
    average_recovery_time: float
    strategy_success_rates: Dict[str, float]
    accuracy_trend: List[float]
    decision_latency: float


class StrategyRecommendationResponse(BaseModel):
    strategy: str
    success_rate: float
    average_recovery_time: float
    total_attempts: int
    recommended_scenarios: List[str]


@router.post("/decision", response_model=FallbackDecisionResponse)
async def make_fallback_decision(request: FallbackDecisionRequest):
    """
    智能回退決策
    
    基於當前異常情況和環境條件，選擇最佳的回退策略
    """
    try:
        # 構建異常對象
        anomaly = HandoverAnomaly(
            anomaly_id=request.anomaly_id,
            anomaly_type=AnomalyType(request.anomaly_type),
            severity=AnomalySeverity(request.severity),
            ue_id=request.ue_id,
            handover_id=request.handover_id,
            timestamp=datetime.utcnow(),
            description=f"異常類型: {request.anomaly_type}",
            affected_satellites=[request.target_satellite],
            signal_metrics=request.signal_quality,
            recovery_suggestions=[]
        )
        
        # 構建換手上下文
        handover_context = HandoverContext(
            ue_id=request.ue_id,
            handover_id=request.handover_id,
            source_satellite=request.source_satellite,
            target_satellite=request.target_satellite,
            start_time=datetime.utcnow(),
            current_position=(0.0, 0.0, 0.0),  # 實際實現中從請求獲取
            signal_quality=request.signal_quality,
            network_conditions=request.network_conditions
        )
        
        # 構建決策上下文
        decision_context = FallbackDecisionContext(
            anomaly=anomaly,
            handover_context=handover_context,
            available_satellites=request.available_satellites,
            network_conditions=request.network_conditions,
            system_load=request.system_load,
            historical_success_rate={},  # 實際實現中從歷史數據獲取
            time_constraints=request.time_constraints,
            retry_count=request.retry_count
        )
        
        # 執行智能決策
        fallback_action = await intelligent_fallback_service.make_intelligent_fallback_decision(
            decision_context
        )
        
        return FallbackDecisionResponse(
            decision_id=fallback_action.action_id,
            strategy=fallback_action.strategy,
            target_satellite=fallback_action.target_satellite,
            estimated_recovery_time=fallback_action.estimated_recovery_time,
            confidence=fallback_action.confidence,
            description=fallback_action.description,
            priority=fallback_action.priority,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"回退決策失敗: {e}")
        raise HTTPException(status_code=500, detail=f"決策失敗: {str(e)}")


@router.post("/outcome")
async def record_decision_outcome(request: DecisionOutcomeRequest):
    """
    記錄決策結果
    
    用於機器學習和模型改進
    """
    try:
        outcome = DecisionOutcome(request.outcome)
        
        await intelligent_fallback_service.record_decision_outcome(
            decision_id=request.decision_id,
            outcome=outcome,
            actual_recovery_time=request.actual_recovery_time,
            success_achieved=request.success_achieved,
            lessons=request.lessons_learned
        )
        
        return {"status": "success", "message": "決策結果已記錄"}
        
    except Exception as e:
        logger.error(f"記錄決策結果失敗: {e}")
        raise HTTPException(status_code=500, detail=f"記錄失敗: {str(e)}")


@router.get("/metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics():
    """
    獲取性能指標
    
    返回智能回退系統的整體性能統計
    """
    try:
        metrics = intelligent_fallback_service.get_performance_metrics()
        
        success_rate = 0.0
        if metrics.total_decisions > 0:
            success_rate = metrics.successful_decisions / metrics.total_decisions
        
        return PerformanceMetricsResponse(
            total_decisions=metrics.total_decisions,
            successful_decisions=metrics.successful_decisions,
            success_rate=success_rate,
            average_recovery_time=metrics.average_recovery_time,
            strategy_success_rates=metrics.strategy_success_rates,
            accuracy_trend=metrics.accuracy_trend,
            decision_latency=metrics.decision_latency
        )
        
    except Exception as e:
        logger.error(f"獲取性能指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取指標失敗: {str(e)}")


@router.get("/strategies/{anomaly_type}/{severity}", response_model=List[StrategyRecommendationResponse])
async def get_strategy_recommendations(anomaly_type: str, severity: str):
    """
    獲取策略建議
    
    基於異常類型和嚴重程度返回推薦的回退策略
    """
    try:
        anomaly_type_enum = AnomalyType(anomaly_type)
        severity_enum = AnomalySeverity(severity)
        
        recommendations = await intelligent_fallback_service.get_strategy_recommendations(
            anomaly_type_enum, severity_enum
        )
        
        return [
            StrategyRecommendationResponse(
                strategy=rec['strategy'],
                success_rate=rec['success_rate'],
                average_recovery_time=rec['average_recovery_time'],
                total_attempts=rec['total_attempts'],
                recommended_scenarios=rec['recommended_scenarios']
            )
            for rec in recommendations
        ]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"無效的參數: {str(e)}")
    except Exception as e:
        logger.error(f"獲取策略建議失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取建議失敗: {str(e)}")


@router.get("/strategies")
async def get_all_strategies():
    """
    獲取所有可用的回退策略
    """
    try:
        strategies = [
            {
                "name": strategy.value,
                "description": _get_strategy_description(strategy)
            }
            for strategy in FallbackStrategy
        ]
        
        return {"strategies": strategies}
        
    except Exception as e:
        logger.error(f"獲取策略列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取策略失敗: {str(e)}")


@router.get("/decision-history")
async def get_decision_history(limit: int = 50):
    """
    獲取決策歷史
    """
    try:
        history = intelligent_fallback_service.decision_history[-limit:]
        
        formatted_history = []
        for record in history:
            formatted_history.append({
                "decision_id": record.decision_id,
                "timestamp": record.timestamp.isoformat(),
                "anomaly_type": record.context.anomaly.anomaly_type.value,
                "severity": record.context.anomaly.severity.value,
                "selected_strategy": record.selected_option.strategy.value,
                "estimated_recovery_time": record.selected_option.estimated_recovery_time,
                "actual_recovery_time": record.actual_recovery_time,
                "outcome": record.outcome.value,
                "success_achieved": record.success_achieved,
                "ue_id": record.context.handover_context.ue_id
            })
        
        return {"history": formatted_history}
        
    except Exception as e:
        logger.error(f"獲取決策歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取歷史失敗: {str(e)}")


@router.post("/reset-learning")
async def reset_learning_model():
    """
    重置學習模型
    
    清除歷史數據和學習緩衝區，重新開始學習
    """
    try:
        # 清除歷史數據
        intelligent_fallback_service.decision_history.clear()
        intelligent_fallback_service.learning_buffer.clear()
        
        # 重置策略統計
        for strategy in FallbackStrategy:
            intelligent_fallback_service.strategy_performance[strategy] = {
                'total_attempts': 0,
                'successful_attempts': 0,
                'average_recovery_time': 0.0,
                'failure_reasons': {},
                'context_patterns': []
            }
        
        return {"status": "success", "message": "學習模型已重置"}
        
    except Exception as e:
        logger.error(f"重置學習模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"重置失敗: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康檢查
    """
    try:
        metrics = intelligent_fallback_service.get_performance_metrics()
        
        return {
            "status": "healthy",
            "service": "Intelligent Fallback Service",
            "total_decisions": metrics.total_decisions,
            "uptime": "運行中",
            "learning_buffer_size": len(intelligent_fallback_service.learning_buffer)
        }
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=f"健康檢查失敗: {str(e)}")


def _get_strategy_description(strategy: FallbackStrategy) -> str:
    """獲取策略描述"""
    descriptions = {
        FallbackStrategy.ROLLBACK_TO_SOURCE: "回滾到源衛星，恢復到換手前的穩定狀態",
        FallbackStrategy.SELECT_ALTERNATIVE_SATELLITE: "選擇替代衛星，避開問題目標",
        FallbackStrategy.DELAY_HANDOVER: "延遲換手執行，等待條件改善",
        FallbackStrategy.ADJUST_POWER_PARAMETERS: "調整功率參數，改善信號品質",
        FallbackStrategy.FREQUENCY_HOPPING: "頻率跳躍，避開干擾頻段",
        FallbackStrategy.LOAD_BALANCING: "負載均衡，重新分配網路資源",
        FallbackStrategy.EMERGENCY_FALLBACK: "緊急回退，確保系統穩定運行"
    }
    return descriptions.get(strategy, "未知策略")