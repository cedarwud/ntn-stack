"""
AI 智慧決策 API 路由

階段八：進階 AI 智慧決策與自動化調優
提供綜合 AI 決策、自動調優和預測性維護的 API 接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import structlog

from ..services.ai_decision_engine import (
    AIDecisionEngine, 
    DecisionContext, 
    SystemMetrics, 
    OptimizationObjective
)
from ..services.automated_optimization_service import (
    AutomatedOptimizationService,
    PerformanceMetrics,
    OptimizationParameter
)
from ..services.ai_ran_anti_interference_service import AIRANAntiInterferenceService
from ..adapters.redis_adapter import RedisAdapter

logger = structlog.get_logger(__name__)

# Pydantic 模型定義
class SystemMetricsRequest(BaseModel):
    latency_ms: float = Field(..., ge=0, description="延遲（毫秒）")
    throughput_mbps: float = Field(..., ge=0, description="吞吐量（Mbps）")
    coverage_percentage: float = Field(..., ge=0, le=100, description="覆蓋率（%）")
    power_consumption_w: float = Field(..., ge=0, description="功耗（瓦特）")
    sinr_db: float = Field(..., description="SINR（dB）")
    packet_loss_rate: float = Field(..., ge=0, le=1, description="封包損失率")
    handover_success_rate: float = Field(..., ge=0, le=1, description="換手成功率")
    interference_level_db: float = Field(..., description="干擾等級（dB）")
    resource_utilization: float = Field(..., ge=0, le=1, description="資源使用率")
    cost_efficiency: float = Field(..., ge=0, description="成本效率")

class OptimizationObjectiveRequest(BaseModel):
    name: str = Field(..., description="目標名稱")
    weight: float = Field(..., ge=0, le=1, description="權重")
    target_value: Optional[float] = Field(None, description="目標值")
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    is_maximize: bool = Field(True, description="是否最大化")

class DecisionContextRequest(BaseModel):
    system_metrics: SystemMetricsRequest
    network_state: Dict[str, Any] = Field(..., description="網路狀態")
    interference_data: Dict[str, Any] = Field(..., description="干擾數據")
    optimization_objectives: List[OptimizationObjectiveRequest] = Field(..., description="優化目標")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="約束條件")

class AIDecisionRequest(BaseModel):
    context: DecisionContextRequest
    urgent_mode: bool = Field(False, description="緊急模式")

class OptimizationParameterRequest(BaseModel):
    name: str = Field(..., description="參數名稱")
    value: float = Field(..., description="參數值")

class ManualOptimizationRequest(BaseModel):
    target_objectives: Optional[Dict[str, float]] = Field(None, description="目標值")
    parameter_overrides: Optional[List[OptimizationParameterRequest]] = Field(None, description="參數覆蓋")

# 創建路由器
router = APIRouter(prefix="/api/v1/ai-decision", tags=["AI Decision Engine"])

# 全局服務實例（將在應用啟動時初始化）
ai_decision_engine: Optional[AIDecisionEngine] = None
automated_optimization_service: Optional[AutomatedOptimizationService] = None
ai_ran_service: Optional[AIRANAntiInterferenceService] = None

def get_ai_decision_engine() -> AIDecisionEngine:
    """獲取 AI 決策引擎依賴"""
    if ai_decision_engine is None:
        raise HTTPException(status_code=503, detail="AI 決策引擎未初始化")
    return ai_decision_engine

def get_optimization_service() -> AutomatedOptimizationService:
    """獲取自動優化服務依賴"""
    if automated_optimization_service is None:
        raise HTTPException(status_code=503, detail="自動優化服務未初始化")
    return automated_optimization_service

def get_ai_ran_service() -> AIRANAntiInterferenceService:
    """獲取 AI-RAN 服務依賴"""
    if ai_ran_service is None:
        raise HTTPException(status_code=503, detail="AI-RAN 服務未初始化")
    return ai_ran_service

@router.post("/comprehensive-decision", response_model=Dict)
async def make_comprehensive_decision(
    request: AIDecisionRequest,
    engine: AIDecisionEngine = Depends(get_ai_decision_engine)
) -> Dict:
    """
    執行綜合智慧決策
    
    基於當前系統狀態、網路條件和優化目標，
    使用多種 AI 技術生成最佳的系統調整決策。
    """
    try:
        # 轉換請求數據為內部格式
        context = DecisionContext(
            system_metrics=SystemMetrics(
                latency_ms=request.context.system_metrics.latency_ms,
                throughput_mbps=request.context.system_metrics.throughput_mbps,
                coverage_percentage=request.context.system_metrics.coverage_percentage,
                power_consumption_w=request.context.system_metrics.power_consumption_w,
                sinr_db=request.context.system_metrics.sinr_db,
                packet_loss_rate=request.context.system_metrics.packet_loss_rate,
                handover_success_rate=request.context.system_metrics.handover_success_rate,
                interference_level_db=request.context.system_metrics.interference_level_db,
                resource_utilization=request.context.system_metrics.resource_utilization,
                cost_efficiency=request.context.system_metrics.cost_efficiency,
                timestamp=datetime.utcnow()
            ),
            network_state=request.context.network_state,
            interference_data=request.context.interference_data,
            historical_performance=[],  # 會從歷史數據中填充
            optimization_objectives=[
                OptimizationObjective(
                    name=obj.name,
                    weight=obj.weight,
                    target_value=obj.target_value,
                    min_value=obj.min_value,
                    max_value=obj.max_value,
                    is_maximize=obj.is_maximize
                ) for obj in request.context.optimization_objectives
            ],
            constraints=request.context.constraints
        )
        
        # 執行綜合決策
        result = await engine.comprehensive_decision_making(context, request.urgent_mode)
        
        if result['success']:
            logger.info(
                "綜合智慧決策完成",
                decision_id=result['decision_id'],
                confidence=result['confidence_score'],
                urgent_mode=request.urgent_mode
            )
        
        return result
        
    except Exception as e:
        logger.error("綜合智慧決策失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"決策執行失敗: {str(e)}")

@router.get("/status", response_model=Dict)
async def get_ai_decision_status(
    engine: AIDecisionEngine = Depends(get_ai_decision_engine)
) -> Dict:
    """獲取 AI 決策引擎狀態"""
    try:
        return await engine.get_service_status()
    except Exception as e:
        logger.error("獲取 AI 決策引擎狀態失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")

@router.post("/optimization/manual", response_model=Dict)
async def trigger_manual_optimization(
    request: ManualOptimizationRequest,
    background_tasks: BackgroundTasks,
    service: AutomatedOptimizationService = Depends(get_optimization_service)
) -> Dict:
    """
    手動觸發系統優化
    
    立即執行一次完整的系統參數優化週期，
    可選擇性地指定特定的優化目標。
    """
    try:
        if service.is_optimization_running:
            return {
                'success': False,
                'error': '優化正在進行中，請稍後再試',
                'estimated_completion_time': None
            }
        
        # 在背景執行優化
        background_tasks.add_task(service.manual_optimization, request.target_objectives)
        
        return {
            'success': True,
            'message': '手動優化已啟動',
            'optimization_cycle': service.current_optimization_cycle + 1,
            'estimated_duration_minutes': 5
        }
        
    except Exception as e:
        logger.error("手動優化啟動失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"優化啟動失敗: {str(e)}")

@router.get("/optimization/status", response_model=Dict)
async def get_optimization_status(
    service: AutomatedOptimizationService = Depends(get_optimization_service)
) -> Dict:
    """獲取自動優化服務狀態"""
    try:
        return await service.get_service_status()
    except Exception as e:
        logger.error("獲取優化狀態失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")

@router.get("/optimization/report", response_model=Dict)
async def get_optimization_report(
    days: int = 7,
    service: AutomatedOptimizationService = Depends(get_optimization_service)
) -> Dict:
    """
    獲取優化報告
    
    提供指定天數內的優化活動報告，
    包括成功率、改善程度和趨勢分析。
    """
    try:
        if days < 1 or days > 90:
            raise HTTPException(status_code=400, detail="天數必須在 1-90 之間")
        
        return await service.get_optimization_report(days)
        
    except Exception as e:
        logger.error("獲取優化報告失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"獲取報告失敗: {str(e)}")

@router.post("/interference/detect-and-mitigate", response_model=Dict)
async def detect_and_mitigate_interference(
    ue_positions: List[Dict],
    gnb_positions: List[Dict],
    current_sinr: List[float],
    network_state: Dict[str, Any],
    fast_mode: bool = False,
    ai_ran_service: AIRANAntiInterferenceService = Depends(get_ai_ran_service)
) -> Dict:
    """
    干擾檢測與智能緩解
    
    結合干擾檢測和 AI 決策，提供一站式的
    干擾檢測和自動緩解方案。
    """
    try:
        # 1. 執行干擾檢測
        detection_result = await ai_ran_service.detect_interference(
            ue_positions, gnb_positions, current_sinr
        )
        
        if not detection_result['success']:
            return detection_result
        
        # 2. 如果檢測到干擾，執行智能緩解
        mitigation_result = None
        if detection_result['interference_detected']:
            mitigation_result = await ai_ran_service.ai_mitigation_decision(
                detection_result, network_state, fast_mode
            )
        
        return {
            'success': True,
            'detection_result': detection_result,
            'mitigation_result': mitigation_result,
            'interference_detected': detection_result['interference_detected'],
            'mitigation_applied': mitigation_result is not None and mitigation_result.get('success', False),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("干擾檢測與緩解失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"處理失敗: {str(e)}")

@router.post("/ai-ran/train", response_model=Dict)
async def train_ai_ran_model(
    training_episodes: int = 1000,
    save_interval: int = 100,
    background_tasks: BackgroundTasks,
    ai_ran_service: AIRANAntiInterferenceService = Depends(get_ai_ran_service)
) -> Dict:
    """
    訓練 AI-RAN 模型
    
    在背景執行 AI-RAN 深度強化學習模型的訓練，
    提升抗干擾決策的準確性和效果。
    """
    try:
        if training_episodes < 100 or training_episodes > 10000:
            raise HTTPException(
                status_code=400, 
                detail="訓練輪數必須在 100-10000 之間"
            )
        
        # 在背景執行訓練
        background_tasks.add_task(
            ai_ran_service.train_ai_model, 
            training_episodes, 
            save_interval
        )
        
        return {
            'success': True,
            'message': 'AI-RAN 模型訓練已啟動',
            'training_episodes': training_episodes,
            'save_interval': save_interval,
            'estimated_duration_minutes': training_episodes * 0.01  # 粗略估算
        }
        
    except Exception as e:
        logger.error("AI-RAN 訓練啟動失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"訓練啟動失敗: {str(e)}")

@router.get("/ai-ran/status", response_model=Dict)
async def get_ai_ran_status(
    ai_ran_service: AIRANAntiInterferenceService = Depends(get_ai_ran_service)
) -> Dict:
    """獲取 AI-RAN 服務狀態"""
    try:
        return await ai_ran_service.get_service_status()
    except Exception as e:
        logger.error("獲取 AI-RAN 狀態失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")

@router.get("/health-analysis", response_model=Dict)
async def get_system_health_analysis(
    include_predictions: bool = True,
    engine: AIDecisionEngine = Depends(get_ai_decision_engine)
) -> Dict:
    """
    系統健康分析
    
    提供當前系統健康狀態的全面分析，
    包括故障風險預測和維護建議。
    """
    try:
        # 獲取當前系統指標（這裡應該從實際監控系統獲取）
        current_metrics = SystemMetrics(
            latency_ms=45.0,
            throughput_mbps=75.0,
            coverage_percentage=82.0,
            power_consumption_w=120.0,
            sinr_db=18.0,
            packet_loss_rate=0.02,
            handover_success_rate=0.95,
            interference_level_db=-85.0,
            resource_utilization=0.65,
            cost_efficiency=8.5,
            timestamp=datetime.utcnow()
        )
        
        network_state = {
            'cpu_utilization': 65.0,
            'memory_utilization': 70.0,
            'disk_utilization': 45.0,
            'temperature_celsius': 42.0,
            'active_connections': 1250
        }
        
        # 執行健康分析
        health_analysis = engine.predictive_maintenance.analyze_system_health(
            current_metrics, network_state
        )
        
        if include_predictions:
            # 添加額外的預測信息
            health_analysis['trend_analysis'] = {
                'projected_health_score_24h': max(0.1, health_analysis['health_score'] - 0.05),
                'maintenance_urgency': health_analysis['risk_level'],
                'recommended_monitoring_frequency': 'hourly' if health_analysis['risk_level'] == 'high' else 'daily'
            }
        
        return {
            'success': True,
            'health_analysis': health_analysis,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'system_metrics': {
                'latency_ms': current_metrics.latency_ms,
                'throughput_mbps': current_metrics.throughput_mbps,
                'coverage_percentage': current_metrics.coverage_percentage,
                'sinr_db': current_metrics.sinr_db
            }
        }
        
    except Exception as e:
        logger.error("系統健康分析失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"健康分析失敗: {str(e)}")

@router.get("/performance-prediction", response_model=Dict)
async def get_performance_prediction(
    prediction_hours: int = 24,
    confidence_threshold: float = 0.6,
    engine: AIDecisionEngine = Depends(get_ai_decision_engine)
) -> Dict:
    """
    性能預測
    
    基於歷史數據和當前趨勢，預測未來一段時間內
    的系統性能變化和潛在問題。
    """
    try:
        if prediction_hours < 1 or prediction_hours > 168:  # 最多一週
            raise HTTPException(
                status_code=400, 
                detail="預測時間必須在 1-168 小時之間"
            )
        
        if confidence_threshold < 0.1 or confidence_threshold > 1.0:
            raise HTTPException(
                status_code=400,
                detail="信心閾值必須在 0.1-1.0 之間"
            )
        
        # 模擬性能預測（實際實現中會使用機器學習模型）
        current_time = datetime.utcnow()
        predictions = []
        
        for hour in range(0, prediction_hours, 4):  # 每4小時一個預測點
            prediction_time = current_time + timedelta(hours=hour)
            
            # 模擬預測數據
            predictions.append({
                'timestamp': prediction_time.isoformat(),
                'predicted_latency_ms': 45.0 + hour * 0.5,  # 假設略微增長
                'predicted_throughput_mbps': max(70.0, 75.0 - hour * 0.2),
                'predicted_availability': max(0.95, 0.98 - hour * 0.001),
                'confidence_score': max(0.5, 0.9 - hour * 0.01),
                'risk_factors': [
                    'increasing_latency' if hour > 12 else None,
                    'throughput_degradation' if hour > 8 else None
                ]
            })
        
        # 過濾低信心預測
        high_confidence_predictions = [
            p for p in predictions 
            if p['confidence_score'] >= confidence_threshold
        ]
        
        return {
            'success': True,
            'prediction_period_hours': prediction_hours,
            'confidence_threshold': confidence_threshold,
            'total_predictions': len(predictions),
            'high_confidence_predictions': len(high_confidence_predictions),
            'predictions': high_confidence_predictions,
            'summary': {
                'overall_trend': 'stable',
                'major_risks': ['latency_increase'],
                'recommended_actions': ['monitor_cpu_usage', 'consider_load_balancing']
            }
        }
        
    except Exception as e:
        logger.error("性能預測失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"預測失敗: {str(e)}")

@router.post("/enable-auto-tuning", response_model=Dict)
async def enable_auto_tuning(
    interval_seconds: int = 300,
    engine: AIDecisionEngine = Depends(get_ai_decision_engine)
) -> Dict:
    """
    啟用自動調優
    
    啟動系統的自動調優功能，定期執行
    智能參數調整以維持最佳性能。
    """
    try:
        if interval_seconds < 60 or interval_seconds > 3600:
            raise HTTPException(
                status_code=400,
                detail="調優間隔必須在 60-3600 秒之間"
            )
        
        await engine.enable_auto_tuning(interval_seconds)
        
        return {
            'success': True,
            'message': '自動調優已啟用',
            'interval_seconds': interval_seconds,
            'next_tuning_time': (datetime.utcnow() + timedelta(seconds=interval_seconds)).isoformat()
        }
        
    except Exception as e:
        logger.error("啟用自動調優失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"啟用失敗: {str(e)}")

@router.post("/disable-auto-tuning", response_model=Dict)
async def disable_auto_tuning(
    engine: AIDecisionEngine = Depends(get_ai_decision_engine)
) -> Dict:
    """停用自動調優"""
    try:
        await engine.disable_auto_tuning()
        
        return {
            'success': True,
            'message': '自動調優已停用'
        }
        
    except Exception as e:
        logger.error("停用自動調優失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"停用失敗: {str(e)}")

@router.get("/decision-history", response_model=Dict)
async def get_decision_history(
    limit: int = 50,
    hours: int = 24,
    engine: AIDecisionEngine = Depends(get_ai_decision_engine)
) -> Dict:
    """
    獲取決策歷史
    
    回傳最近的 AI 決策記錄，用於分析
    決策效果和系統學習進度。
    """
    try:
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=400,
                detail="記錄數量限制必須在 1-1000 之間"
            )
        
        if hours < 1 or hours > 720:  # 最多30天
            raise HTTPException(
                status_code=400,
                detail="時間範圍必須在 1-720 小時之間"
            )
        
        # 從決策歷史中獲取記錄
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_decisions = []
        for decision in list(engine.decision_history)[-limit:]:
            decision_time = datetime.fromisoformat(decision['timestamp'])
            if decision_time >= cutoff_time:
                # 簡化決策記錄以減少響應大小
                simplified_decision = {
                    'decision_id': decision['decision_id'],
                    'timestamp': decision['timestamp'],
                    'confidence_score': decision['comprehensive_decision'].get('confidence', 0),
                    'actions_count': len(decision['comprehensive_decision'].get('actions', [])),
                    'urgent_mode': decision['urgent_mode'],
                    'decision_time_seconds': decision['decision_time_seconds'],
                    'health_risk_level': decision['health_analysis'].get('risk_level', 'unknown')
                }
                recent_decisions.append(simplified_decision)
        
        return {
            'success': True,
            'total_decisions': len(recent_decisions),
            'time_range_hours': hours,
            'decisions': recent_decisions,
            'statistics': {
                'average_confidence': sum(d['confidence_score'] for d in recent_decisions) / len(recent_decisions) if recent_decisions else 0,
                'urgent_decisions': len([d for d in recent_decisions if d['urgent_mode']]),
                'high_risk_decisions': len([d for d in recent_decisions if d['health_risk_level'] == 'high'])
            }
        }
        
    except Exception as e:
        logger.error("獲取決策歷史失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"獲取歷史失敗: {str(e)}")

# 服務初始化函數（應在應用啟動時調用）
async def initialize_ai_services(redis_adapter: RedisAdapter):
    """初始化 AI 服務"""
    global ai_decision_engine, automated_optimization_service, ai_ran_service
    
    try:
        # 初始化 AI-RAN 服務
        ai_ran_service = AIRANAntiInterferenceService(
            redis_adapter=redis_adapter,
            simworld_api_url="http://simworld-backend:8000"
        )
        
        # 初始化自動優化服務
        automated_optimization_service = AutomatedOptimizationService(
            redis_adapter=redis_adapter,
            optimization_interval_minutes=30
        )
        
        # 初始化 AI 決策引擎
        ai_decision_engine = AIDecisionEngine(
            redis_adapter=redis_adapter,
            ai_ran_service=ai_ran_service
        )
        
        logger.info("所有 AI 服務已成功初始化")
        
    except Exception as e:
        logger.error("AI 服務初始化失敗", error=str(e))
        raise

async def shutdown_ai_services():
    """關閉 AI 服務"""
    global ai_decision_engine, automated_optimization_service, ai_ran_service
    
    try:
        # 這裡可以添加清理邏輯
        logger.info("AI 服務已關閉")
        
    except Exception as e:
        logger.error("AI 服務關閉失敗", error=str(e))