"""
端點實現模組 - 從 algorithm_ecosystem_router.py 中提取的端點邏輯
按功能分組但集中管理，避免過度拆散成小文件
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import HTTPException, BackgroundTasks

from .schemas import *
from .dependencies import (
    get_algorithm_registry,
    get_environment_manager,
    get_handover_orchestrator,
    check_services_health
)
from ...algorithm_ecosystem import (
    HandoverContext,
    GeoCoordinate,
    SignalMetrics,
    SatelliteInfo
)
from ...algorithm_ecosystem.adapters import (
    InfocomAlgorithmAdapter,
    SimpleThresholdAlgorithmAdapter,
    RandomAlgorithmAdapter
)
from ...algorithm_ecosystem.orchestrator import OrchestratorConfig

logger = logging.getLogger(__name__)


class AlgorithmEcosystemEndpoints:
    """算法生態系統端點實現類"""
    
    # === 核心預測端點 ===
    
    @staticmethod
    async def predict_handover(request: HandoverPredictionRequest) -> HandoverDecisionResponse:
        """換手預測端點"""
        try:
            orchestrator = get_handover_orchestrator()
            
            # 轉換請求數據
            context = HandoverContext(
                user_id=request.ue_id,
                current_satellite_id=request.current_satellite,
                user_location=GeoCoordinate(
                    latitude=request.ue_location.latitude,
                    longitude=request.ue_location.longitude,
                    altitude=request.ue_location.altitude
                ),
                user_velocity=GeoCoordinate(
                    latitude=request.ue_velocity.latitude,
                    longitude=request.ue_velocity.longitude,
                    altitude=request.ue_velocity.altitude
                ) if request.ue_velocity else None,
                signal_metrics=SignalMetrics(
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
                target_satellite=decision.target_satellite_id,
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

    # === 算法管理端點 ===
    
    @staticmethod
    async def list_algorithms() -> List[AlgorithmInfoResponse]:
        """列出所有可用算法"""
        try:
            registry = get_algorithm_registry()
            algorithms = registry.list_algorithms()
            return [
                AlgorithmInfoResponse(
                    name=algo.name,
                    version=algo.version,
                    algorithm_type=algo.algorithm_type.value,
                    enabled=algo.enabled,
                    description=algo.description,
                    priority=algo.priority,
                    configuration=algo.configuration,
                    performance_metrics=algo.performance_metrics
                )
                for algo in algorithms
            ]
        except Exception as e:
            logger.error(f"列出算法失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list algorithms: {str(e)}")

    @staticmethod
    async def register_algorithm(request: AlgorithmRegistrationRequest) -> OperationResponse:
        """註冊新算法"""
        try:
            registry = get_algorithm_registry()
            
            # 根據類型創建算法適配器
            if request.algorithm_type == "InfocomAlgorithmAdapter":
                algorithm = InfocomAlgorithmAdapter()
            elif request.algorithm_type == "SimpleThresholdAlgorithmAdapter":
                algorithm = SimpleThresholdAlgorithmAdapter()
            elif request.algorithm_type == "RandomAlgorithmAdapter":
                algorithm = RandomAlgorithmAdapter()
            else:
                raise ValueError(f"不支持的算法類型: {request.algorithm_type}")
            
            # 註冊算法
            await registry.register_algorithm(algorithm)
            
            # 如果需要立即啟用
            if request.enable_immediately:
                registry.enable_algorithm(request.name)
            
            return OperationResponse(
                success=True,
                message=f"算法 {request.name} 註冊成功",
                data={"algorithm_name": request.name}
            )
            
        except Exception as e:
            logger.error(f"註冊算法失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to register algorithm: {str(e)}")

    @staticmethod
    async def unregister_algorithm(algorithm_name: str) -> OperationResponse:
        """註銷算法"""
        try:
            registry = get_algorithm_registry()
            registry.unregister_algorithm(algorithm_name)
            
            return OperationResponse(
                success=True,
                message=f"算法 {algorithm_name} 註銷成功"
            )
            
        except Exception as e:
            logger.error(f"註銷算法失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to unregister algorithm: {str(e)}")

    @staticmethod
    async def enable_algorithm(algorithm_name: str) -> OperationResponse:
        """啟用算法"""
        try:
            registry = get_algorithm_registry()
            registry.enable_algorithm(algorithm_name)
            
            return OperationResponse(
                success=True,
                message=f"算法 {algorithm_name} 已啟用"
            )
            
        except Exception as e:
            logger.error(f"啟用算法失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to enable algorithm: {str(e)}")

    @staticmethod
    async def disable_algorithm(algorithm_name: str) -> OperationResponse:
        """禁用算法"""
        try:
            registry = get_algorithm_registry()
            registry.disable_algorithm(algorithm_name)
            
            return OperationResponse(
                success=True,
                message=f"算法 {algorithm_name} 已禁用"
            )
            
        except Exception as e:
            logger.error(f"禁用算法失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to disable algorithm: {str(e)}")

    # === 協調器管理端點 ===
    
    @staticmethod
    async def get_orchestrator_stats() -> StatsResponse:
        """獲取協調器統計信息"""
        try:
            orchestrator = get_handover_orchestrator()
            stats = orchestrator.get_orchestrator_stats()
            
            return StatsResponse(
                component="handover_orchestrator",
                timestamp=datetime.now(),
                data=stats
            )
            
        except Exception as e:
            logger.error(f"獲取協調器統計失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get orchestrator stats: {str(e)}")

    @staticmethod
    async def update_orchestrator_config(request: OrchestratorConfigRequest) -> OperationResponse:
        """更新協調器配置"""
        try:
            orchestrator = get_handover_orchestrator()
            
            # 創建新配置
            new_config = OrchestratorConfig(
                mode=request.mode,
                decision_strategy=request.decision_strategy,
                default_algorithm=request.default_algorithm,
                enable_caching=request.enable_caching,
                cache_ttl_seconds=request.cache_ttl_seconds,
                max_concurrent_requests=request.max_concurrent_requests,
                ab_test_config=request.ab_test_config,
                ensemble_config=request.ensemble_config
            )
            
            await orchestrator.update_config(new_config)
            
            return OperationResponse(
                success=True,
                message="協調器配置更新成功"
            )
            
        except Exception as e:
            logger.error(f"更新協調器配置失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update orchestrator config: {str(e)}")

    # === 環境管理端點 ===
    
    @staticmethod
    async def get_environment_stats() -> StatsResponse:
        """獲取環境統計信息"""
        try:
            env_manager = get_environment_manager()
            stats = env_manager.get_stats()
            
            return StatsResponse(
                component="environment_manager",
                timestamp=datetime.now(),
                data=stats
            )
            
        except Exception as e:
            logger.error(f"獲取環境統計失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get environment stats: {str(e)}")

    # === A/B測試端點 ===
    
    @staticmethod
    async def set_ab_test_config(request: ABTestConfigRequest) -> OperationResponse:
        """設置A/B測試配置"""
        try:
            orchestrator = get_handover_orchestrator()
            orchestrator.set_ab_test_config(request.test_id, request.traffic_split)
            
            return OperationResponse(
                success=True,
                message=f"A/B測試 {request.test_id} 配置成功"
            )
            
        except Exception as e:
            logger.error(f"設置A/B測試配置失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to set A/B test config: {str(e)}")

    @staticmethod
    async def get_ab_test_performance(test_id: str) -> Dict[str, Any]:
        """獲取A/B測試性能數據"""
        try:
            orchestrator = get_handover_orchestrator()
            performance_data = orchestrator.get_ab_test_performance(test_id)
            
            return performance_data
            
        except Exception as e:
            logger.error(f"獲取A/B測試性能失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get A/B test performance: {str(e)}")

    # === 指標和健康檢查端點 ===
    
    @staticmethod
    async def get_registry_stats() -> StatsResponse:
        """獲取註冊中心統計信息"""
        try:
            registry = get_algorithm_registry()
            stats = registry.get_stats()
            
            return StatsResponse(
                component="algorithm_registry",
                timestamp=datetime.now(),
                data=stats
            )
            
        except Exception as e:
            logger.error(f"獲取註冊中心統計失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get registry stats: {str(e)}")

    @staticmethod
    async def health_check() -> HealthCheckResponse:
        """健康檢查"""
        try:
            health_status = check_services_health()
            
            return HealthCheckResponse(
                status="healthy" if health_status["overall_healthy"] else "unhealthy",
                timestamp=datetime.now(),
                services=health_status["services"]
            )
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

    @staticmethod
    async def export_metrics(request: MetricsExportRequest) -> Dict[str, Any]:
        """導出指標數據"""
        try:
            orchestrator = get_handover_orchestrator()
            metrics_data = orchestrator.export_metrics_for_analysis()
            
            # 根據請求過濾數據
            if request.algorithms:
                filtered_algorithms = {
                    name: data for name, data in metrics_data.get("algorithms", {}).items()
                    if name in request.algorithms
                }
                metrics_data["algorithms"] = filtered_algorithms
            
            return metrics_data
            
        except Exception as e:
            logger.error(f"導出指標失敗: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to export metrics: {str(e)}")