"""
🎭 算法生態系統 API 路由

提供統一的多算法管理和換手決策 API。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ..algorithm_ecosystem import (
    HandoverOrchestrator,
    AlgorithmRegistry,
    EnvironmentManager,
    HandoverContext,
    HandoverDecision,
    AlgorithmInfo,
    GeoCoordinate,
    SignalMetrics,
    SatelliteInfo
)
from ..algorithm_ecosystem.adapters import (
    InfocomAlgorithmAdapter,
    SimpleThresholdAlgorithmAdapter,
    RandomAlgorithmAdapter
)
from ..algorithm_ecosystem.orchestrator import OrchestratorConfig, OrchestratorMode, DecisionStrategy

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/v1/algorithm-ecosystem", tags=["Algorithm Ecosystem"])

# 全局實例
_algorithm_registry: Optional[AlgorithmRegistry] = None
_environment_manager: Optional[EnvironmentManager] = None
_handover_orchestrator: Optional[HandoverOrchestrator] = None


# Pydantic 模型
class GeoCoordinateModel(BaseModel):
    """地理坐標模型"""
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="經度")
    altitude: float = Field(default=0.0, description="海拔高度 (米)")


class SignalMetricsModel(BaseModel):
    """信號質量指標模型"""
    rsrp: float = Field(..., description="參考信號接收功率")
    rsrq: float = Field(..., description="參考信號接收質量")
    sinr: float = Field(..., description="信噪干擾比")
    throughput: float = Field(default=0.0, description="吞吐量")
    latency: float = Field(default=0.0, description="延遲")


class SatelliteInfoModel(BaseModel):
    """衛星信息模型"""
    satellite_id: str = Field(..., description="衛星ID")
    position: GeoCoordinateModel = Field(..., description="衛星位置")
    velocity: Optional[GeoCoordinateModel] = Field(None, description="衛星速度")
    signal_metrics: Optional[SignalMetricsModel] = Field(None, description="信號指標")
    load_factor: float = Field(default=0.0, description="負載因子")


class HandoverPredictionRequest(BaseModel):
    """換手預測請求"""
    ue_id: str = Field(..., description="用戶設備ID")
    current_satellite: Optional[str] = Field(None, description="當前衛星ID")
    ue_location: GeoCoordinateModel = Field(..., description="UE位置")
    ue_velocity: Optional[GeoCoordinateModel] = Field(None, description="UE速度")
    current_signal_metrics: Optional[SignalMetricsModel] = Field(None, description="當前信號指標")
    candidate_satellites: List[SatelliteInfoModel] = Field(..., description="候選衛星列表")
    network_state: Dict[str, Any] = Field(default_factory=dict, description="網路狀態")
    scenario_info: Optional[Dict[str, Any]] = Field(None, description="場景信息")
    weather_conditions: Optional[Dict[str, Any]] = Field(None, description="天氣條件")
    traffic_load: Optional[Dict[str, Any]] = Field(None, description="流量負載")
    algorithm_name: Optional[str] = Field(None, description="指定算法名稱")
    use_cache: Optional[bool] = Field(None, description="是否使用緩存")


class HandoverDecisionResponse(BaseModel):
    """換手決策響應"""
    target_satellite: Optional[str] = Field(None, description="目標衛星ID")
    handover_decision: int = Field(..., description="換手決策類型")
    confidence: float = Field(..., description="決策信心度")
    timing: Optional[datetime] = Field(None, description="建議執行時間")
    decision_reason: str = Field(..., description="決策原因")
    algorithm_name: str = Field(..., description="執行算法名稱")
    decision_time: float = Field(..., description="決策耗時 (毫秒)")
    metadata: Dict[str, Any] = Field(..., description="額外元數據")


class AlgorithmInfoResponse(BaseModel):
    """算法信息響應"""
    name: str = Field(..., description="算法名稱")
    version: str = Field(..., description="算法版本")
    algorithm_type: str = Field(..., description="算法類型")
    description: str = Field(..., description="算法描述")
    parameters: Dict[str, Any] = Field(..., description="算法參數")
    author: Optional[str] = Field(None, description="作者")
    created_at: Optional[datetime] = Field(None, description="創建時間")
    performance_metrics: Optional[Dict[str, float]] = Field(None, description="性能指標")
    supported_scenarios: Optional[List[str]] = Field(None, description="支持場景")


class AlgorithmRegistrationRequest(BaseModel):
    """算法註冊請求"""
    name: str = Field(..., description="算法名稱")
    algorithm_type: str = Field(..., description="算法類型 (InfocomAlgorithmAdapter, SimpleThresholdAlgorithmAdapter, RandomAlgorithmAdapter)")
    config: Dict[str, Any] = Field(default_factory=dict, description="算法配置")
    enabled: bool = Field(default=True, description="是否啟用")
    priority: int = Field(default=10, description="優先級")


class OrchestratorConfigRequest(BaseModel):
    """協調器配置請求"""
    mode: str = Field(..., description="協調器模式")
    decision_strategy: str = Field(..., description="決策策略")
    default_algorithm: Optional[str] = Field(None, description="默認算法")
    fallback_algorithm: Optional[str] = Field(None, description="回退算法")
    timeout_seconds: float = Field(default=5.0, description="超時秒數")
    max_concurrent_requests: int = Field(default=100, description="最大並發請求數")
    enable_caching: bool = Field(default=True, description="啟用緩存")
    cache_ttl_seconds: int = Field(default=60, description="緩存TTL秒數")
    enable_monitoring: bool = Field(default=True, description="啟用監控")
    ab_test_config: Optional[Dict[str, Any]] = Field(None, description="A/B測試配置")


# 依賴注入
async def get_algorithm_registry() -> AlgorithmRegistry:
    """獲取算法註冊中心"""
    global _algorithm_registry
    if not _algorithm_registry:
        _algorithm_registry = AlgorithmRegistry()
        await _algorithm_registry.initialize()
    return _algorithm_registry


async def get_environment_manager() -> EnvironmentManager:
    """獲取環境管理器"""
    global _environment_manager
    if not _environment_manager:
        _environment_manager = EnvironmentManager()
        await _environment_manager.initialize()
    return _environment_manager


async def get_handover_orchestrator(
    registry: AlgorithmRegistry = Depends(get_algorithm_registry),
    env_manager: EnvironmentManager = Depends(get_environment_manager)
) -> HandoverOrchestrator:
    """獲取換手協調器"""
    global _handover_orchestrator
    if not _handover_orchestrator:
        _handover_orchestrator = HandoverOrchestrator(registry, env_manager)
        await _handover_orchestrator.initialize()
    return _handover_orchestrator


# API 端點
@router.post("/handover/predict", response_model=HandoverDecisionResponse)
async def predict_handover(
    request: HandoverPredictionRequest,
    orchestrator: HandoverOrchestrator = Depends(get_handover_orchestrator)
):
    """執行換手預測
    
    統一的換手決策 API，支持多算法協調。
    """
    try:
        # 轉換請求為 HandoverContext
        context = HandoverContext(
            ue_id=request.ue_id,
            current_satellite=request.current_satellite,
            ue_location=GeoCoordinate(
                latitude=request.ue_location.latitude,
                longitude=request.ue_location.longitude,
                altitude=request.ue_location.altitude
            ),
            ue_velocity=GeoCoordinate(
                latitude=request.ue_velocity.latitude,
                longitude=request.ue_velocity.longitude,
                altitude=request.ue_velocity.altitude
            ) if request.ue_velocity else None,
            current_signal_metrics=SignalMetrics(
                rsrp=request.current_signal_metrics.rsrp,
                rsrq=request.current_signal_metrics.rsrq,
                sinr=request.current_signal_metrics.sinr,
                throughput=request.current_signal_metrics.throughput,
                latency=request.current_signal_metrics.latency
            ) if request.current_signal_metrics else None,
            candidate_satellites=[
                SatelliteInfo(
                    satellite_id=sat.satellite_id,
                    position=GeoCoordinate(
                        latitude=sat.position.latitude,
                        longitude=sat.position.longitude,
                        altitude=sat.position.altitude
                    ),
                    velocity=GeoCoordinate(
                        latitude=sat.velocity.latitude,
                        longitude=sat.velocity.longitude,
                        altitude=sat.velocity.altitude
                    ) if sat.velocity else None,
                    signal_metrics=SignalMetrics(
                        rsrp=sat.signal_metrics.rsrp,
                        rsrq=sat.signal_metrics.rsrq,
                        sinr=sat.signal_metrics.sinr,
                        throughput=sat.signal_metrics.throughput,
                        latency=sat.signal_metrics.latency
                    ) if sat.signal_metrics else None,
                    load_factor=sat.load_factor
                )
                for sat in request.candidate_satellites
            ],
            network_state=request.network_state,
            timestamp=datetime.now(),
            scenario_info=request.scenario_info,
            weather_conditions=request.weather_conditions,
            traffic_load=request.traffic_load
        )
        
        # 執行預測
        decision = await orchestrator.predict_handover(
            context,
            algorithm_name=request.algorithm_name,
            use_cache=request.use_cache
        )
        
        # 轉換響應
        return HandoverDecisionResponse(
            target_satellite=decision.target_satellite,
            handover_decision=decision.handover_decision.value,
            confidence=decision.confidence,
            timing=decision.timing,
            decision_reason=decision.decision_reason,
            algorithm_name=decision.algorithm_name,
            decision_time=decision.decision_time,
            metadata=decision.metadata
        )
        
    except Exception as e:
        logger.error(f"換手預測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Handover prediction failed: {str(e)}")


@router.get("/algorithms", response_model=List[AlgorithmInfoResponse])
async def list_algorithms(
    registry: AlgorithmRegistry = Depends(get_algorithm_registry)
):
    """列出所有可用算法"""
    try:
        algorithms = registry.list_algorithms()
        return [
            AlgorithmInfoResponse(
                name=algo.name,
                version=algo.version,
                algorithm_type=algo.algorithm_type.value,
                description=algo.description,
                parameters=algo.parameters,
                author=algo.author,
                created_at=algo.created_at,
                performance_metrics=algo.performance_metrics,
                supported_scenarios=algo.supported_scenarios
            )
            for algo in algorithms
        ]
    except Exception as e:
        logger.error(f"列出算法失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list algorithms: {str(e)}")


@router.post("/algorithms/register")
async def register_algorithm(
    request: AlgorithmRegistrationRequest,
    registry: AlgorithmRegistry = Depends(get_algorithm_registry)
):
    """註冊新算法"""
    try:
        # 根據類型創建算法適配器
        if request.algorithm_type == "InfocomAlgorithmAdapter":
            algorithm = InfocomAlgorithmAdapter(request.name, request.config)
        elif request.algorithm_type == "SimpleThresholdAlgorithmAdapter":
            algorithm = SimpleThresholdAlgorithmAdapter(request.name, request.config)
        elif request.algorithm_type == "RandomAlgorithmAdapter":
            algorithm = RandomAlgorithmAdapter(request.name, request.config)
        else:
            raise ValueError(f"不支持的算法類型: {request.algorithm_type}")
        
        # 註冊算法
        await registry.register_algorithm(
            request.name,
            algorithm,
            request.config,
            request.enabled,
            request.priority
        )
        
        return {"message": f"算法 '{request.name}' 註冊成功"}
        
    except Exception as e:
        logger.error(f"註冊算法失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register algorithm: {str(e)}")


@router.delete("/algorithms/{algorithm_name}")
async def unregister_algorithm(
    algorithm_name: str,
    registry: AlgorithmRegistry = Depends(get_algorithm_registry)
):
    """註銷算法"""
    try:
        success = await registry.unregister_algorithm(algorithm_name)
        if success:
            return {"message": f"算法 '{algorithm_name}' 註銷成功"}
        else:
            raise HTTPException(status_code=404, detail=f"Algorithm '{algorithm_name}' not found")
    except Exception as e:
        logger.error(f"註銷算法失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unregister algorithm: {str(e)}")


@router.post("/algorithms/{algorithm_name}/enable")
async def enable_algorithm(
    algorithm_name: str,
    registry: AlgorithmRegistry = Depends(get_algorithm_registry)
):
    """啟用算法"""
    try:
        success = await registry.enable_algorithm(algorithm_name)
        if success:
            return {"message": f"算法 '{algorithm_name}' 已啟用"}
        else:
            raise HTTPException(status_code=404, detail=f"Algorithm '{algorithm_name}' not found")
    except Exception as e:
        logger.error(f"啟用算法失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enable algorithm: {str(e)}")


@router.post("/algorithms/{algorithm_name}/disable")
async def disable_algorithm(
    algorithm_name: str,
    registry: AlgorithmRegistry = Depends(get_algorithm_registry)
):
    """禁用算法"""
    try:
        success = await registry.disable_algorithm(algorithm_name)
        if success:
            return {"message": f"算法 '{algorithm_name}' 已禁用"}
        else:
            raise HTTPException(status_code=404, detail=f"Algorithm '{algorithm_name}' not found")
    except Exception as e:
        logger.error(f"禁用算法失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disable algorithm: {str(e)}")


@router.get("/orchestrator/stats")
async def get_orchestrator_stats(
    orchestrator: HandoverOrchestrator = Depends(get_handover_orchestrator)
):
    """獲取協調器統計信息"""
    try:
        return orchestrator.get_orchestrator_stats()
    except Exception as e:
        logger.error(f"獲取協調器統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get orchestrator stats: {str(e)}")


@router.post("/orchestrator/config")
async def update_orchestrator_config(
    request: OrchestratorConfigRequest,
    orchestrator: HandoverOrchestrator = Depends(get_handover_orchestrator)
):
    """更新協調器配置"""
    try:
        # 轉換配置
        config = OrchestratorConfig(
            mode=OrchestratorMode(request.mode),
            decision_strategy=DecisionStrategy(request.decision_strategy),
            default_algorithm=request.default_algorithm,
            fallback_algorithm=request.fallback_algorithm,
            timeout_seconds=request.timeout_seconds,
            max_concurrent_requests=request.max_concurrent_requests,
            enable_caching=request.enable_caching,
            cache_ttl_seconds=request.cache_ttl_seconds,
            enable_monitoring=request.enable_monitoring,
            ab_test_config=request.ab_test_config
        )
        
        await orchestrator.update_config(config)
        return {"message": "協調器配置更新成功"}
        
    except Exception as e:
        logger.error(f"更新協調器配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update orchestrator config: {str(e)}")


@router.get("/registry/stats")
async def get_registry_stats(
    registry: AlgorithmRegistry = Depends(get_algorithm_registry)
):
    """獲取註冊中心統計信息"""
    try:
        return registry.get_registry_stats()
    except Exception as e:
        logger.error(f"獲取註冊中心統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get registry stats: {str(e)}")


@router.get("/environment/stats")
async def get_environment_stats(
    env_manager: EnvironmentManager = Depends(get_environment_manager)
):
    """獲取環境管理器統計信息"""
    try:
        return env_manager.get_manager_stats()
    except Exception as e:
        logger.error(f"獲取環境管理器統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get environment stats: {str(e)}")


@router.get("/health")
async def health_check():
    """健康檢查"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "algorithm_ecosystem": "operational"
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    logger.info("算法生態系統 API 啟動")
    
    # 預註冊一些基本算法
    try:
        registry = await get_algorithm_registry()
        
        # 註冊 INFOCOM 算法
        await registry.register_algorithm(
            "ieee_infocom_2024",
            InfocomAlgorithmAdapter("ieee_infocom_2024"),
            {},
            True,
            15
        )
        
        # 註冊簡單閾值算法
        await registry.register_algorithm(
            "simple_threshold",
            SimpleThresholdAlgorithmAdapter("simple_threshold"),
            {},
            True,
            10
        )
        
        # 註冊隨機算法
        await registry.register_algorithm(
            "random_baseline",
            RandomAlgorithmAdapter("random_baseline"),
            {},
            True,
            5
        )
        
        logger.info("基本算法預註冊完成")
        
    except Exception as e:
        logger.error(f"算法預註冊失敗: {e}")


@router.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    logger.info("算法生態系統 API 關閉")
    
    global _handover_orchestrator, _algorithm_registry, _environment_manager
    
    try:
        if _handover_orchestrator:
            await _handover_orchestrator.cleanup()
        if _algorithm_registry:
            await _algorithm_registry.cleanup()
        if _environment_manager:
            await _environment_manager.cleanup()
    except Exception as e:
        logger.error(f"清理資源失敗: {e}")
    
    _handover_orchestrator = None
    _algorithm_registry = None
    _environment_manager = None