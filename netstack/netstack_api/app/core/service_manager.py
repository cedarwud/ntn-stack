"""
NetStack API 服務管理器
負責統一管理所有服務的初始化和依賴注入
"""

import structlog
from fastapi import FastAPI
from typing import Optional

# 適配器導入
from ...adapters.mongo_adapter import MongoAdapter
from ...adapters.redis_adapter import RedisAdapter
from ...adapters.open5gs_adapter import Open5GSAdapter

# 服務導入
from ...services.ue_service import UEService
from ...services.slice_service import SliceService, SliceType
from ...services.health_service import HealthService
from ...services.ueransim_service import UERANSIMConfigService
from ...services.satellite_gnb_mapping_service import SatelliteGnbMappingService
from ...services.sionna_integration_service import SionnaIntegrationService
from ...services.interference_control_service import InterferenceControlService
# ConnectionQualityService removed - UAV functionality not needed
from ...services.mesh_bridge_service import MeshBridgeService
# UAVMeshFailoverService removed - UAV functionality not needed

# 導入 RL 訓練服務
try:
    from ...services.rl_training.rl_training_service import get_rl_training_service

    RL_TRAINING_AVAILABLE = True
except ImportError:
    RL_TRAINING_AVAILABLE = False

logger = structlog.get_logger(__name__)

if not RL_TRAINING_AVAILABLE:
    logger.warning("RL 訓練服務不可用")


class ServiceManager:
    """
    服務管理器
    負責按正確的依賴順序初始化所有服務
    """

    def __init__(
        self,
        mongo_adapter: MongoAdapter,
        redis_adapter: RedisAdapter,
        open5gs_adapter: Open5GSAdapter,
    ):
        """
        初始化服務管理器

        Args:
            mongo_adapter: MongoDB 適配器
            redis_adapter: Redis 適配器
            open5gs_adapter: Open5GS 適配器
        """
        self.mongo_adapter = mongo_adapter
        self.redis_adapter = redis_adapter
        self.open5gs_adapter = open5gs_adapter

    async def initialize_services(self, app: FastAPI) -> None:
        """
        按依賴順序初始化所有服務並注入到 FastAPI 應用狀態

        Args:
            app: FastAPI 應用程式實例
        """
        logger.info("🔧 開始初始化服務...")

        try:
            # === 第一層：基礎服務 (無依賴) ===
            logger.info("📦 初始化基礎服務...")

            app.state.ue_service = UEService(self.mongo_adapter, self.open5gs_adapter)
            logger.info("✅ UE 服務初始化完成")

            app.state.slice_service = SliceService(
                self.mongo_adapter, self.open5gs_adapter, self.redis_adapter
            )
            logger.info("✅ Slice 服務初始化完成")

            app.state.health_service = HealthService(
                self.mongo_adapter, self.redis_adapter
            )
            logger.info("✅ 健康檢查服務初始化完成")

            app.state.ueransim_service = UERANSIMConfigService()
            logger.info("✅ UERANSIM 配置服務初始化完成")

            app.state.satellite_service = SatelliteGnbMappingService(self.mongo_adapter)
            logger.info("✅ 衛星 gNodeB 映射服務初始化完成")

            app.state.sionna_service = SionnaIntegrationService()
            logger.info("✅ Sionna 整合服務初始化完成")

            app.state.interference_service = InterferenceControlService()
            logger.info("✅ 干擾控制服務初始化完成")

            # === 第二層：進階服務 (依賴基礎服務) ===
            logger.info("🔧 初始化進階服務...")

            # ConnectionQualityService removed - UAV functionality not needed
            logger.info("✅ UAV 連接品質服務已移除")

            app.state.mesh_service = MeshBridgeService(
                self.mongo_adapter, self.redis_adapter, self.open5gs_adapter
            )
            logger.info("✅ Mesh 橋接服務初始化完成")

            # === 第三層：複合服務 (依賴多個服務) ===
            logger.info("⚡ 初始化複合服務...")

            # UAVMeshFailoverService removed - UAV functionality not needed  
            logger.info("✅ UAV Mesh 故障轉移服務已移除")

            # === RL 訓練服務初始化 ===
            logger.info("🧠 初始化 RL 訓練服務...")
            try:
                from ...services.rl_training.rl_training_service import (
                    get_rl_training_service,
                )

                app.state.rl_training_service = get_rl_training_service()
                success = await app.state.rl_training_service.initialize()
                if success:
                    logger.info("✅ RL 訓練服務初始化完成")
                else:
                    logger.warning("⚠️ RL 訓練服務初始化失敗，但繼續執行")
            except Exception as e:
                logger.error(f"❌ RL 訓練服務初始化失敗: {e}")
                # 設置為 None，讓系統知道服務不可用
                app.state.rl_training_service = None

            logger.info("🎉 所有服務初始化完成！")

        except Exception as e:
            logger.error("💥 服務初始化失敗", error=str(e), exc_info=True)
            raise

    def get_service_status(self, app: FastAPI) -> dict:
        """
        獲取所有服務的狀態摘要

        Args:
            app: FastAPI 應用程式實例

        Returns:
            dict: 服務狀態摘要
        """
        services = [
            "ue_service",
            "slice_service",
            "health_service",
            "ueransim_service",
            "satellite_service",
            "sionna_service",
            "interference_service",
            "connection_service",
            "mesh_service",
            "uav_failover_service",
            "rl_training_service",  # 添加 RL 訓練服務
        ]

        status = {}
        for service_name in services:
            service = getattr(app.state, service_name, None)
            status[service_name] = {
                "initialized": service is not None,
                "type": type(service).__name__ if service else None,
            }

        return {
            "total_services": len(services),
            "initialized_services": sum(1 for s in status.values() if s["initialized"]),
            "services": status,
        }


class ServiceHealthChecker:
    """
    服務健康檢查器
    用於檢查各服務的運行狀態
    """

    @staticmethod
    async def check_all_services(app: FastAPI) -> dict:
        """
        檢查所有服務的健康狀態

        Args:
            app: FastAPI 應用程式實例

        Returns:
            dict: 健康檢查結果
        """
        results = {}

        # 檢查基礎適配器連接
        try:
            if hasattr(app.state, "health_service"):
                health_result = await app.state.health_service.get_overall_health()
                results["adapters"] = health_result
            else:
                results["adapters"] = {
                    "status": "unknown",
                    "message": "健康服務未初始化",
                }
        except Exception as e:
            results["adapters"] = {"status": "error", "message": str(e)}

        # 檢查服務可用性
        service_checks = {}
        services = [
            "ue_service",
            "slice_service",
            "connection_service",
            "mesh_service",
            "uav_failover_service",
        ]

        for service_name in services:
            service = getattr(app.state, service_name, None)
            service_checks[service_name] = {
                "available": service is not None,
                "type": type(service).__name__ if service else None,
            }

        results["services"] = service_checks

        # 計算整體健康狀態
        total_services = len(service_checks)
        healthy_services = sum(1 for s in service_checks.values() if s["available"])

        results["summary"] = {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "health_percentage": (
                (healthy_services / total_services) * 100 if total_services > 0 else 0
            ),
            "overall_status": (
                "healthy" if healthy_services == total_services else "degraded"
            ),
        }

        return results
