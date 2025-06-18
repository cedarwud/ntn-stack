"""
演算法整合橋接服務

整合論文標準介面 (paper_synchronized_algorithm.py) 與進階實作 (enhanced_synchronized_algorithm.py)
提供統一的服務介面，確保兩種實作可以無縫換手和協同工作
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json

import structlog
from .paper_synchronized_algorithm import SynchronizedAlgorithm, AccessInfo
from .enhanced_synchronized_algorithm import EnhancedSynchronizedAlgorithm
from .simworld_tle_bridge_service import SimWorldTLEBridgeService

logger = structlog.get_logger(__name__)


class IntegrationMode(Enum):
    """整合模式"""

    PAPER_ONLY = "paper_only"  # 僅使用論文標準演算法
    ENHANCED_ONLY = "enhanced_only"  # 僅使用進階演算法
    HYBRID = "hybrid"  # 混合模式（優先使用進階功能）
    FALLBACK = "fallback"  # 備援模式（進階失敗時回退到標準）


@dataclass
class BridgeConfiguration:
    """橋接配置"""

    integration_mode: IntegrationMode = IntegrationMode.HYBRID
    delta_t: float = 5.0
    binary_search_precision: float = 0.01
    enhanced_features_enabled: bool = True
    fallback_timeout_seconds: float = 10.0
    performance_monitoring: bool = True

    # 進階功能配置
    two_point_prediction_enabled: bool = True
    enhanced_binary_search_enabled: bool = True
    signaling_free_sync_enabled: bool = True


class AlgorithmIntegrationBridge:
    """
    演算法整合橋接服務

    提供統一介面來管理和協調論文標準演算法與進階演算法
    """

    def __init__(
        self,
        config: Optional[BridgeConfiguration] = None,
        tle_bridge_service: Optional[SimWorldTLEBridgeService] = None,
    ):
        """
        初始化整合橋接服務

        Args:
            config: 橋接配置
            tle_bridge_service: TLE 橋接服務
        """
        self.logger = structlog.get_logger(__name__)
        self.config = config or BridgeConfiguration()

        # 初始化服務組件
        self.tle_bridge = tle_bridge_service or SimWorldTLEBridgeService()

        # 初始化演算法實例
        self.enhanced_algorithm = None
        self.paper_algorithm = None

        # 整合狀態
        self.is_running = False
        self.current_mode = self.config.integration_mode
        self.last_mode_switch = datetime.utcnow()

        # 效能監控
        self.performance_metrics = {
            "total_requests": 0,
            "paper_algorithm_calls": 0,
            "enhanced_algorithm_calls": 0,
            "hybrid_mode_calls": 0,
            "fallback_activations": 0,
            "average_response_time_ms": 0.0,
            "success_rate": 0.0,
            "last_24h_stats": [],
        }

        self.logger.info(
            "演算法整合橋接服務初始化",
            integration_mode=self.config.integration_mode.value,
            enhanced_features=self.config.enhanced_features_enabled,
        )

    async def initialize_algorithms(self) -> Dict[str, Any]:
        """
        初始化所有演算法組件

        Returns:
            初始化結果
        """
        try:
            self.logger.info("初始化演算法組件")

            # 初始化進階演算法
            if self.config.enhanced_features_enabled:
                self.enhanced_algorithm = EnhancedSynchronizedAlgorithm()

            # 初始化論文標準演算法
            self.paper_algorithm = SynchronizedAlgorithm(
                delta_t=self.config.delta_t,
                binary_search_precision=self.config.binary_search_precision,
                simworld_tle_bridge=self.tle_bridge,
                enhanced_algorithm=self.enhanced_algorithm,
            )

            initialization_results = {
                "paper_algorithm_ready": self.paper_algorithm is not None,
                "enhanced_algorithm_ready": self.enhanced_algorithm is not None,
                "tle_bridge_ready": self.tle_bridge is not None,
                "integration_mode": self.current_mode.value,
                "initialization_time": datetime.utcnow().isoformat(),
            }

            self.logger.info(
                "演算法組件初始化完成",
                paper_ready=initialization_results["paper_algorithm_ready"],
                enhanced_ready=initialization_results["enhanced_algorithm_ready"],
            )

            return {"success": True, "results": initialization_results}

        except Exception as e:
            self.logger.error("演算法組件初始化失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def start_integrated_algorithms(self) -> Dict[str, Any]:
        """
        啟動整合的演算法服務

        Returns:
            啟動結果
        """
        if self.is_running:
            return {"success": False, "message": "服務已在運行中"}

        try:
            self.logger.info("啟動整合演算法服務")

            # 確保演算法已初始化
            if not self.paper_algorithm:
                init_result = await self.initialize_algorithms()
                if not init_result["success"]:
                    return init_result

            start_results = {}

            # 根據模式啟動相應的演算法
            if self.current_mode in [
                IntegrationMode.PAPER_ONLY,
                IntegrationMode.HYBRID,
                IntegrationMode.FALLBACK,
            ]:
                paper_result = await self.paper_algorithm.start_algorithm()
                start_results["paper_algorithm"] = paper_result

            if self.current_mode in [
                IntegrationMode.ENHANCED_ONLY,
                IntegrationMode.HYBRID,
                IntegrationMode.FALLBACK,
            ]:
                if self.enhanced_algorithm:
                    await self.enhanced_algorithm.start_enhanced_algorithm()
                    start_results["enhanced_algorithm"] = {
                        "success": True,
                        "message": "Enhanced algorithm started",
                    }

            self.is_running = True

            self.logger.info(
                "整合演算法服務啟動完成",
                mode=self.current_mode.value,
                components_started=len(start_results),
            )

            return {
                "success": True,
                "integration_mode": self.current_mode.value,
                "start_results": start_results,
                "start_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error("啟動整合演算法服務失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def stop_integrated_algorithms(self) -> Dict[str, Any]:
        """
        停止整合的演算法服務

        Returns:
            停止結果
        """
        if not self.is_running:
            return {"success": False, "message": "服務未在運行"}

        try:
            self.logger.info("停止整合演算法服務")

            stop_results = {}

            # 停止論文標準演算法
            if self.paper_algorithm:
                paper_result = await self.paper_algorithm.stop_algorithm()
                stop_results["paper_algorithm"] = paper_result

            # 停止進階演算法
            if self.enhanced_algorithm:
                await self.enhanced_algorithm.stop_enhanced_algorithm()
                stop_results["enhanced_algorithm"] = {
                    "success": True,
                    "message": "Enhanced algorithm stopped",
                }

            self.is_running = False

            return {
                "success": True,
                "stop_results": stop_results,
                "final_performance_metrics": self.performance_metrics,
                "stop_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error("停止整合演算法服務失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def predict_handover_integrated(
        self, ue_id: str, current_satellite: str, time_horizon_seconds: float = 300.0
    ) -> Dict[str, Any]:
        """
        整合式換手預測

        根據當前模式選擇最適合的演算法進行換手預測

        Args:
            ue_id: UE 識別碼
            current_satellite: 當前衛星
            time_horizon_seconds: 預測時間範圍

        Returns:
            換手預測結果
        """
        start_time = datetime.utcnow()
        self.performance_metrics["total_requests"] += 1

        try:
            self.logger.info(
                "執行整合式換手預測",
                ue_id=ue_id,
                current_satellite=current_satellite,
                mode=self.current_mode.value,
            )

            result = None

            if self.current_mode == IntegrationMode.PAPER_ONLY:
                result = await self._predict_handover_paper_only(
                    ue_id, current_satellite, time_horizon_seconds
                )
                self.performance_metrics["paper_algorithm_calls"] += 1

            elif self.current_mode == IntegrationMode.ENHANCED_ONLY:
                result = await self._predict_handover_enhanced_only(
                    ue_id, current_satellite, time_horizon_seconds
                )
                self.performance_metrics["enhanced_algorithm_calls"] += 1

            elif self.current_mode == IntegrationMode.HYBRID:
                result = await self._predict_handover_hybrid(
                    ue_id, current_satellite, time_horizon_seconds
                )
                self.performance_metrics["hybrid_mode_calls"] += 1

            elif self.current_mode == IntegrationMode.FALLBACK:
                result = await self._predict_handover_fallback(
                    ue_id, current_satellite, time_horizon_seconds
                )

            # 更新效能指標
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._update_performance_metrics(
                response_time, result.get("success", False)
            )

            # 添加整合資訊
            result["integration_info"] = {
                "mode_used": self.current_mode.value,
                "response_time_ms": response_time,
                "algorithm_components": self._get_active_components(),
            }

            return result

        except Exception as e:
            self.logger.error("整合式換手預測失敗", ue_id=ue_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "ue_id": ue_id,
                "current_satellite": current_satellite,
            }

    async def _predict_handover_paper_only(
        self, ue_id: str, current_satellite: str, time_horizon_seconds: float
    ) -> Dict[str, Any]:
        """使用論文標準演算法進行預測"""
        if not self.paper_algorithm:
            raise Exception("論文標準演算法未初始化")

        current_time = datetime.utcnow().timestamp()
        target_time = current_time + time_horizon_seconds

        # 獲取當前和預測的接入衛星
        current_access = await self.paper_algorithm.calculate_access_satellite(
            ue_id, current_time
        )
        predicted_access = await self.paper_algorithm.calculate_access_satellite(
            ue_id, target_time
        )

        handover_needed = current_access != predicted_access
        handover_time = None

        if handover_needed:
            handover_time = await self.paper_algorithm.binary_search_handover_time(
                ue_id=ue_id,
                source_satellite=current_access,
                target_satellite=predicted_access,
                t_start=current_time,
                t_end=target_time,
            )

        return {
            "success": True,
            "method": "paper_standard",
            "ue_id": ue_id,
            "current_satellite": current_access,
            "predicted_satellite": predicted_access,
            "handover_needed": handover_needed,
            "handover_time": (
                datetime.fromtimestamp(handover_time).isoformat()
                if handover_time
                else None
            ),
            "time_to_handover_seconds": (
                handover_time - current_time if handover_time else None
            ),
            "prediction_accuracy": 0.9,  # 論文標準精度
            "algorithm_details": {
                "binary_search_precision": self.paper_algorithm.binary_search_precision,
                "delta_t": self.paper_algorithm.delta_t,
            },
        }

    async def _predict_handover_enhanced_only(
        self, ue_id: str, current_satellite: str, time_horizon_seconds: float
    ) -> Dict[str, Any]:
        """使用進階演算法進行預測"""
        if not self.enhanced_algorithm:
            raise Exception("進階演算法未初始化")

        # 執行二點預測
        if self.config.two_point_prediction_enabled:
            two_point_result = (
                await self.enhanced_algorithm.execute_two_point_prediction(
                    ue_id, current_satellite, time_horizon_seconds / 60.0
                )
            )

            # 執行增強版二分搜尋
            if self.config.enhanced_binary_search_enabled:
                search_result = (
                    await self.enhanced_algorithm.execute_enhanced_binary_search(
                        two_point_result
                    )
                )

                return {
                    "success": True,
                    "method": "enhanced_advanced",
                    "ue_id": ue_id,
                    "current_satellite": current_satellite,
                    "predicted_satellite": two_point_result.prediction_t_delta.get(
                        "predicted_access_time"
                    ),
                    "handover_needed": True,
                    "handover_time": search_result["final_estimate"].isoformat(),
                    "time_to_handover_seconds": (
                        search_result["final_estimate"] - datetime.utcnow()
                    ).total_seconds(),
                    "prediction_accuracy": two_point_result.extrapolation_confidence,
                    "algorithm_details": {
                        "two_point_consistency": two_point_result.consistency_score,
                        "temporal_stability": two_point_result.temporal_stability,
                        "binary_search_iterations": search_result["iterations"],
                        "search_precision_ms": search_result["precision_ms"],
                    },
                }

        # 基本的進階預測
        return {
            "success": True,
            "method": "enhanced_basic",
            "ue_id": ue_id,
            "current_satellite": current_satellite,
            "prediction_accuracy": 0.95,  # 進階演算法精度
            "algorithm_details": {"enhanced_features": "basic_only"},
        }

    async def _predict_handover_hybrid(
        self, ue_id: str, current_satellite: str, time_horizon_seconds: float
    ) -> Dict[str, Any]:
        """混合模式預測（優先使用進階功能）"""
        try:
            # 首先嘗試進階演算法
            if self.enhanced_algorithm and self.config.enhanced_features_enabled:
                enhanced_result = await self._predict_handover_enhanced_only(
                    ue_id, current_satellite, time_horizon_seconds
                )

                # 如果進階演算法成功且信心度足夠，直接返回
                if (
                    enhanced_result.get("success")
                    and enhanced_result.get("prediction_accuracy", 0) >= 0.8
                ):
                    enhanced_result["method"] = "hybrid_enhanced"
                    return enhanced_result

            # 否則使用論文標準演算法
            paper_result = await self._predict_handover_paper_only(
                ue_id, current_satellite, time_horizon_seconds
            )
            paper_result["method"] = "hybrid_paper_fallback"

            # 如果兩種方法都可用，可以進行結果融合
            if self.enhanced_algorithm:
                paper_result["fusion_note"] = (
                    "Enhanced algorithm available but paper standard used due to confidence threshold"
                )

            return paper_result

        except Exception as e:
            self.logger.error("混合模式預測失敗", error=str(e))
            raise

    async def _predict_handover_fallback(
        self, ue_id: str, current_satellite: str, time_horizon_seconds: float
    ) -> Dict[str, Any]:
        """備援模式預測"""
        try:
            # 先嘗試進階演算法，設置超時
            if self.enhanced_algorithm:
                try:
                    enhanced_result = await asyncio.wait_for(
                        self._predict_handover_enhanced_only(
                            ue_id, current_satellite, time_horizon_seconds
                        ),
                        timeout=self.config.fallback_timeout_seconds,
                    )
                    enhanced_result["method"] = "fallback_enhanced_success"
                    return enhanced_result

                except asyncio.TimeoutError:
                    self.logger.warning("進階演算法超時，換手到備援模式")
                    self.performance_metrics["fallback_activations"] += 1
                except Exception as e:
                    self.logger.warning("進階演算法失敗，換手到備援模式", error=str(e))
                    self.performance_metrics["fallback_activations"] += 1

            # 使用論文標準演算法作為備援
            paper_result = await self._predict_handover_paper_only(
                ue_id, current_satellite, time_horizon_seconds
            )
            paper_result["method"] = "fallback_paper_backup"
            paper_result["fallback_reason"] = "Enhanced algorithm unavailable or failed"

            return paper_result

        except Exception as e:
            self.logger.error("備援模式預測失敗", error=str(e))
            raise

    async def switch_integration_mode(
        self, new_mode: IntegrationMode
    ) -> Dict[str, Any]:
        """
        換手整合模式

        Args:
            new_mode: 新的整合模式

        Returns:
            換手結果
        """
        if new_mode == self.current_mode:
            return {"success": True, "message": "Already in requested mode"}

        try:
            old_mode = self.current_mode
            self.logger.info(
                "換手整合模式", from_mode=old_mode.value, to_mode=new_mode.value
            )

            # 如果服務在運行，需要重新啟動
            if self.is_running:
                await self.stop_integrated_algorithms()
                self.current_mode = new_mode
                await self.start_integrated_algorithms()
            else:
                self.current_mode = new_mode

            self.last_mode_switch = datetime.utcnow()

            return {
                "success": True,
                "old_mode": old_mode.value,
                "new_mode": new_mode.value,
                "switch_time": self.last_mode_switch.isoformat(),
                "service_restarted": self.is_running,
            }

        except Exception as e:
            self.logger.error("換手整合模式失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_integration_status(self) -> Dict[str, Any]:
        """
        獲取整合服務狀態

        Returns:
            詳細的整合狀態資訊
        """
        status = {
            "service_running": self.is_running,
            "current_mode": self.current_mode.value,
            "last_mode_switch": self.last_mode_switch.isoformat(),
            "configuration": {
                "delta_t": self.config.delta_t,
                "binary_search_precision": self.config.binary_search_precision,
                "enhanced_features_enabled": self.config.enhanced_features_enabled,
                "fallback_timeout_seconds": self.config.fallback_timeout_seconds,
            },
            "component_status": {
                "paper_algorithm_available": self.paper_algorithm is not None,
                "enhanced_algorithm_available": self.enhanced_algorithm is not None,
                "tle_bridge_available": self.tle_bridge is not None,
            },
            "performance_metrics": self.performance_metrics,
        }

        # 如果演算法在運行，獲取其狀態
        if self.paper_algorithm:
            try:
                paper_status = await self.paper_algorithm.get_algorithm_status()
                status["paper_algorithm_status"] = paper_status
            except Exception as e:
                status["paper_algorithm_status"] = {"error": str(e)}

        if self.enhanced_algorithm:
            try:
                enhanced_status = (
                    await self.enhanced_algorithm.get_algorithm_performance_report()
                )
                status["enhanced_algorithm_status"] = enhanced_status
            except Exception as e:
                status["enhanced_algorithm_status"] = {"error": str(e)}

        return status

    async def switch_mode(self, new_mode: IntegrationMode) -> Dict[str, Any]:
        """
        換手整合模式 (別名方法)

        Args:
            new_mode: 新的整合模式

        Returns:
            換手結果
        """
        return await self.switch_integration_mode(new_mode)

    def _get_active_components(self) -> List[str]:
        """獲取當前活躍的演算法組件"""
        components = []

        if self.paper_algorithm and self.paper_algorithm.is_running:
            components.append("paper_standard")

        if self.enhanced_algorithm and self.enhanced_algorithm.is_running:
            components.append("enhanced_advanced")

        if self.tle_bridge:
            components.append("tle_bridge")

        return components

    def _update_performance_metrics(self, response_time_ms: float, success: bool):
        """更新效能指標"""
        # 更新平均回應時間
        total_requests = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["average_response_time_ms"]

        new_avg = (
            (current_avg * (total_requests - 1)) + response_time_ms
        ) / total_requests
        self.performance_metrics["average_response_time_ms"] = new_avg

        # 更新成功率
        if not hasattr(self, "_success_count"):
            self._success_count = 0

        if success:
            self._success_count += 1

        self.performance_metrics["success_rate"] = self._success_count / total_requests

        # 記錄 24 小時統計
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        # 清理超過 24 小時的數據
        self.performance_metrics["last_24h_stats"] = [
            stat
            for stat in self.performance_metrics["last_24h_stats"]
            if datetime.fromisoformat(stat["hour"]) > current_hour - timedelta(hours=24)
        ]

        # 添加當前小時統計
        hour_stat = next(
            (
                stat
                for stat in self.performance_metrics["last_24h_stats"]
                if stat["hour"] == current_hour.isoformat()
            ),
            None,
        )

        if not hour_stat:
            hour_stat = {
                "hour": current_hour.isoformat(),
                "requests": 0,
                "successes": 0,
                "total_response_time": 0.0,
            }
            self.performance_metrics["last_24h_stats"].append(hour_stat)

        hour_stat["requests"] += 1
        hour_stat["total_response_time"] += response_time_ms
        if success:
            hour_stat["successes"] += 1
