# AI決策系統營運管理工具
# 階段8：營運管理工具實現
# 提供決策系統啟停控制、參數調優、緊急處理等功能

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

import aiohttp
import redis.asyncio as redis
from prometheus_client.parser import text_string_to_metric_families

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """系統狀態枚舉"""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    TRAINING = "training"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    EMERGENCY = "emergency"


class AlertSeverity(Enum):
    """告警嚴重程度"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class SystemHealth:
    """系統健康狀態"""

    component: str
    health_score: float  # 0-100
    last_check: datetime
    issues: List[str]
    recommendations: List[str]


@dataclass
class PerformanceMetrics:
    """性能指標數據"""

    decision_latency_avg: float
    decision_success_rate: float
    throughput_rps: float
    system_cpu_usage: float
    system_memory_usage: float
    timestamp: datetime


class DecisionSystemManager:
    """
    AI決策系統營運管理器

    主要功能：
    1. RL算法啟停控制
    2. 決策參數實時調優
    3. 訓練會話管理和監控
    4. 系統配置熱更新
    5. 緊急處理機制
    6. 健康檢查自動化
    """

    def __init__(
        self,
        netstack_api_url: str = "http://localhost:8080",
        redis_url: str = "redis://localhost:6379",
        prometheus_url: str = "http://localhost:9090",
    ):
        self.netstack_api_url = netstack_api_url
        self.redis_url = redis_url
        self.prometheus_url = prometheus_url

        self.redis_client: Optional[redis.Redis] = None
        self.current_state = SystemState.INITIALIZING
        self.health_checks: Dict[str, SystemHealth] = {}
        self.performance_history: List[PerformanceMetrics] = []

        # 配置閾值
        self.thresholds = {
            "latency_critical": 0.020,  # 20ms
            "latency_warning": 0.015,  # 15ms
            "success_rate_critical": 0.90,
            "success_rate_warning": 0.95,
            "cpu_critical": 85.0,
            "memory_critical": 90.0,
            "throughput_min": 500.0,
        }

    async def initialize(self):
        """初始化管理器"""
        try:
            # 連接Redis
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()

            # 檢查服務狀態
            await self._check_service_connectivity()

            # 載入系統配置
            await self._load_system_configuration()

            self.current_state = SystemState.ACTIVE
            logger.info("決策系統管理器初始化完成")

        except Exception as e:
            self.current_state = SystemState.ERROR
            logger.error(f"管理器初始化失敗: {e}")
            raise

    # =================================================================
    # 1. RL算法啟停控制
    # =================================================================

    async def start_rl_algorithm(self, algorithm: str, config: Dict[str, Any]) -> bool:
        """啟動RL算法"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"algorithm": algorithm, "config": config, "action": "start"}

                async with session.post(
                    f"{self.netstack_api_url}/api/v1/rl/control", json=payload
                ) as response:
                    if response.status == 200:
                        await self._log_operation(
                            f"RL算法 {algorithm} 啟動成功",
                            "rl_control",
                            {"algorithm": algorithm, "action": "start"},
                        )
                        return True
                    else:
                        error_msg = await response.text()
                        logger.error(f"啟動RL算法失敗: {error_msg}")
                        return False

        except Exception as e:
            logger.error(f"啟動RL算法異常: {e}")
            return False

    async def stop_rl_algorithm(self, algorithm: str, graceful: bool = True) -> bool:
        """停止RL算法"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "algorithm": algorithm,
                    "action": "stop",
                    "graceful": graceful,
                }

                async with session.post(
                    f"{self.netstack_api_url}/api/v1/rl/control", json=payload
                ) as response:
                    if response.status == 200:
                        await self._log_operation(
                            f"RL算法 {algorithm} 停止成功",
                            "rl_control",
                            {
                                "algorithm": algorithm,
                                "action": "stop",
                                "graceful": graceful,
                            },
                        )
                        return True
                    else:
                        error_msg = await response.text()
                        logger.error(f"停止RL算法失敗: {error_msg}")
                        return False

        except Exception as e:
            logger.error(f"停止RL算法異常: {e}")
            return False

    async def get_rl_algorithm_status(self) -> Dict[str, Any]:
        """獲取RL算法狀態"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.netstack_api_url}/api/v1/rl/status"
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": "無法獲取算法狀態"}

        except Exception as e:
            logger.error(f"獲取算法狀態異常: {e}")
            return {"error": str(e)}

    # =================================================================
    # 2. 決策參數實時調優
    # =================================================================

    async def update_decision_parameters(self, parameters: Dict[str, Any]) -> bool:
        """更新決策參數"""
        try:
            # 驗證參數
            validation_result = await self._validate_parameters(parameters)
            if not validation_result["valid"]:
                logger.error(f"參數驗證失敗: {validation_result['errors']}")
                return False

            # 備份當前參數
            current_params = await self._get_current_parameters()
            backup_key = f"params_backup_{int(time.time())}"
            await self.redis_client.set(backup_key, json.dumps(current_params))

            # 更新參數
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.netstack_api_url}/api/v1/ai_decision_integration/parameters",
                    json=parameters,
                ) as response:
                    if response.status == 200:
                        await self._log_operation(
                            "決策參數更新成功",
                            "parameter_update",
                            {"parameters": parameters, "backup_key": backup_key},
                        )
                        return True
                    else:
                        error_msg = await response.text()
                        logger.error(f"參數更新失敗: {error_msg}")
                        return False

        except Exception as e:
            logger.error(f"更新決策參數異常: {e}")
            return False

    async def rollback_parameters(self, backup_key: str) -> bool:
        """回滾參數到備份版本"""
        try:
            backup_data = await self.redis_client.get(backup_key)
            if not backup_data:
                logger.error(f"備份鍵 {backup_key} 不存在")
                return False

            parameters = json.loads(backup_data)
            return await self.update_decision_parameters(parameters)

        except Exception as e:
            logger.error(f"參數回滾異常: {e}")
            return False

    # =================================================================
    # 3. 緊急處理機制
    # =================================================================

    async def trigger_emergency_mode(self, reason: str) -> bool:
        """觸發緊急模式"""
        try:
            self.current_state = SystemState.EMERGENCY

            emergency_config = {
                "mode": "emergency",
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "actions": [
                    "switch_to_fallback_algorithm",
                    "increase_monitoring_frequency",
                    "disable_training",
                    "alert_operations_team",
                ],
            }

            # 切換到預設算法
            await self._switch_to_fallback_algorithm()

            # 停止所有訓練
            await self._stop_all_training()

            # 增加監控頻率
            await self._increase_monitoring_frequency()

            # 發送緊急告警
            await self._send_emergency_alert(reason)

            # 記錄緊急模式觸發
            await self._log_operation(
                f"緊急模式已觸發: {reason}", "emergency_mode", emergency_config
            )

            return True

        except Exception as e:
            logger.error(f"觸發緊急模式失敗: {e}")
            return False

    async def exit_emergency_mode(self) -> bool:
        """退出緊急模式"""
        try:
            # 檢查系統健康狀態
            health_check = await self.comprehensive_health_check()
            if not health_check["healthy"]:
                logger.warning("系統健康檢查未通過，無法退出緊急模式")
                return False

            # 恢復正常監控頻率
            await self._restore_normal_monitoring()

            # 恢復算法運行
            await self._restore_algorithm_operation()

            self.current_state = SystemState.ACTIVE

            await self._log_operation(
                "已退出緊急模式",
                "emergency_mode_exit",
                {"timestamp": datetime.now().isoformat()},
            )

            return True

        except Exception as e:
            logger.error(f"退出緊急模式失敗: {e}")
            return False

    async def manual_decision_override(
        self, satellite_id: str, target_satellite: str, reason: str
    ) -> bool:
        """手動決策覆蓋"""
        try:
            override_data = {
                "type": "manual_override",
                "satellite_id": satellite_id,
                "target_satellite": target_satellite,
                "reason": reason,
                "operator": "system_admin",  # 可以從認證信息獲取
                "timestamp": datetime.now().isoformat(),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.netstack_api_url}/api/v1/ai_decision_integration/manual_override",
                    json=override_data,
                ) as response:
                    if response.status == 200:
                        await self._log_operation(
                            f"手動決策覆蓋: {satellite_id} -> {target_satellite}",
                            "manual_override",
                            override_data,
                        )
                        return True
                    else:
                        error_msg = await response.text()
                        logger.error(f"手動覆蓋失敗: {error_msg}")
                        return False

        except Exception as e:
            logger.error(f"手動決策覆蓋異常: {e}")
            return False

    # =================================================================
    # 4. 健康檢查自動化
    # =================================================================

    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """綜合健康檢查"""
        health_report = {
            "healthy": True,
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "recommendations": [],
            "critical_issues": [],
        }

        try:
            # 檢查核心服務
            service_health = await self._check_core_services()
            health_report["components"]["services"] = service_health

            # 檢查性能指標
            performance_health = await self._check_performance_metrics()
            health_report["components"]["performance"] = performance_health

            # 檢查數據庫連接
            db_health = await self._check_database_connectivity()
            health_report["components"]["database"] = db_health

            # 檢查告警狀態
            alert_health = await self._check_active_alerts()
            health_report["components"]["alerts"] = alert_health

            # 生成總體健康狀態
            component_scores = [
                comp["health_score"]
                for comp in health_report["components"].values()
                if "health_score" in comp
            ]

            overall_score = (
                sum(component_scores) / len(component_scores) if component_scores else 0
            )
            health_report["overall_health_score"] = overall_score
            health_report["healthy"] = overall_score >= 80.0

            # 更新健康檢查記錄
            for comp_name, comp_data in health_report["components"].items():
                if "health_score" in comp_data:
                    self.health_checks[comp_name] = SystemHealth(
                        component=comp_name,
                        health_score=comp_data["health_score"],
                        last_check=datetime.now(),
                        issues=comp_data.get("issues", []),
                        recommendations=comp_data.get("recommendations", []),
                    )

            return health_report

        except Exception as e:
            logger.error(f"健康檢查異常: {e}")
            health_report["healthy"] = False
            health_report["error"] = str(e)
            return health_report

    async def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """獲取性能趨勢分析"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)

            # 從Prometheus獲取歷史數據
            metrics_data = await self._fetch_prometheus_metrics(start_time, end_time)

            trends = {
                "period": f"{hours}h",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "trends": {},
                "predictions": {},
                "recommendations": [],
            }

            # 分析延遲趨勢
            if "decision_latency" in metrics_data:
                latency_trend = self._analyze_trend(metrics_data["decision_latency"])
                trends["trends"]["decision_latency"] = latency_trend

                if latency_trend["slope"] > 0.001:  # 延遲增長趨勢
                    trends["recommendations"].append(
                        "決策延遲呈增長趨勢，建議檢查算法效能並考慮資源優化"
                    )

            # 分析成功率趨勢
            if "success_rate" in metrics_data:
                success_trend = self._analyze_trend(metrics_data["success_rate"])
                trends["trends"]["success_rate"] = success_trend

                if success_trend["slope"] < -0.01:  # 成功率下降趨勢
                    trends["recommendations"].append(
                        "決策成功率呈下降趨勢，建議檢查算法配置和訓練質量"
                    )

            return trends

        except Exception as e:
            logger.error(f"性能趨勢分析異常: {e}")
            return {"error": str(e)}

    # =================================================================
    # 私有輔助方法
    # =================================================================

    async def _check_service_connectivity(self):
        """檢查服務連通性"""
        services = [
            ("NetStack API", f"{self.netstack_api_url}/health"),
            ("Prometheus", f"{self.prometheus_url}/-/healthy"),
        ]

        for service_name, url in services:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            logger.info(f"{service_name} 連接正常")
                        else:
                            raise Exception(f"HTTP {response.status}")
            except Exception as e:
                logger.error(f"{service_name} 連接失敗: {e}")
                raise

    async def _load_system_configuration(self):
        """載入系統配置"""
        try:
            config_key = "ntn_system_config"
            config_data = await self.redis_client.get(config_key)

            if config_data:
                config = json.loads(config_data)
                self.thresholds.update(config.get("thresholds", {}))
                logger.info("系統配置載入成功")
            else:
                # 設置默認配置
                default_config = {"thresholds": self.thresholds}
                await self.redis_client.set(config_key, json.dumps(default_config))
                logger.info("使用默認系統配置")

        except Exception as e:
            logger.warning(f"載入系統配置失敗，使用默認配置: {e}")

    async def _switch_to_fallback_algorithm(self):
        """切換到備用算法"""
        fallback_config = {
            "algorithm": "dqn_fallback",
            "config": {
                "exploration_rate": 0.1,
                "learning_rate": 0.001,
                "safe_mode": True,
            },
        }
        await self.start_rl_algorithm("dqn_fallback", fallback_config["config"])

    async def _stop_all_training(self):
        """停止所有訓練"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.netstack_api_url}/api/v1/rl/stop_all_training"
                ) as response:
                    if response.status == 200:
                        logger.info("所有訓練已停止")
                    else:
                        logger.error("停止訓練失敗")
        except Exception as e:
            logger.error(f"停止訓練異常: {e}")

    async def _send_emergency_alert(self, reason: str):
        """發送緊急告警"""
        alert_data = {
            "alertname": "EmergencyModeActivated",
            "severity": "critical",
            "summary": f"AI決策系統進入緊急模式",
            "description": f"原因: {reason}",
            "timestamp": datetime.now().isoformat(),
        }

        # 這裡可以整合多種告警渠道
        logger.critical(f"🚨 緊急告警: {alert_data}")

    async def _log_operation(
        self, message: str, operation_type: str, details: Dict[str, Any]
    ):
        """記錄操作日誌"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "operation_type": operation_type,
            "details": details,
            "state": self.current_state.value,
        }

        # 記錄到Redis和日誌
        log_key = f"operation_log:{int(time.time())}"
        await self.redis_client.set(
            log_key, json.dumps(log_entry), ex=86400 * 7
        )  # 保留7天
        logger.info(f"操作記錄: {message}")

    async def _validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """驗證參數有效性"""
        # 簡化的參數驗證邏輯
        errors = []

        if "learning_rate" in parameters:
            lr = parameters["learning_rate"]
            if not (0.0001 <= lr <= 0.1):
                errors.append("learning_rate 必須在 0.0001-0.1 範圍內")

        if "exploration_rate" in parameters:
            er = parameters["exploration_rate"]
            if not (0.0 <= er <= 1.0):
                errors.append("exploration_rate 必須在 0.0-1.0 範圍內")

        return {"valid": len(errors) == 0, "errors": errors}

    async def _get_current_parameters(self) -> Dict[str, Any]:
        """獲取當前參數"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.netstack_api_url}/api/v1/ai_decision_integration/parameters"
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {}
        except Exception:
            return {}


# 使用示例和工具函數
async def main():
    """主函數示例"""
    manager = DecisionSystemManager()

    try:
        await manager.initialize()

        # 進行健康檢查
        health_report = await manager.comprehensive_health_check()
        print(f"系統健康狀態: {health_report['healthy']}")

        # 獲取性能趨勢
        trends = await manager.get_performance_trends(hours=6)
        print(f"性能趨勢: {trends}")

    except Exception as e:
        logger.error(f"管理器運行異常: {e}")


if __name__ == "__main__":
    asyncio.run(main())
