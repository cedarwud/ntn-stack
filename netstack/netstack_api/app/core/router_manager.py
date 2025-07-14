"""
NetStack API 路由器管理器
負責統一管理所有路由器的註冊和配置
"""

import structlog
from fastapi import FastAPI
from fastapi.routing import APIRoute
from typing import Optional, List, Tuple, Dict
import importlib
import logging

logger = logging.getLogger(__name__)


class RouterManager:
    """統一管理所有API路由器"""

    def __init__(self, app: FastAPI):
        """
        初始化路由器管理器

        Args:
            app: FastAPI 應用程式實例
        """
        self.app = app
        self.registered_routers: List[Dict] = []

    def register_core_routers(self) -> None:
        """註冊核心路由器"""
        logger.info("🚀 開始註冊核心路由器...")
        try:
            from ..api.health import router as health_router
            from ..api.v1.ue import router as ue_router
            from ..api.v1.handover import (
                router as handover_router,
            )

            # 嘗試導入 RL System 的路由器 - 如果不存在則跳過
            try:
                from ...services.rl_training.api.training_routes import (
                    router as new_rl_training_router,
                )

                rl_training_available = True
            except ImportError:
                rl_training_available = False
                logger.warning("RL System training routes 不可用，跳過註冊")

            # 嘗試導入 WebSocket 路由器
            try:
                from ...routers.websocket_router import websocket_router
                websocket_available = True
            except ImportError:
                websocket_available = False
                logger.warning("WebSocket router 不可用，跳過註冊")

            # 嘗試導入增強版路由器 - 如果不存在則跳過
            try:
                from ...services.rl_training.api.enhanced_training_routes import (
                    router as enhanced_rl_training_router,
                )

                enhanced_rl_available = True
            except ImportError:
                enhanced_rl_available = False
                logger.warning("RL System enhanced training routes 不可用，跳過註冊")

            self.app.include_router(health_router, tags=["健康檢查"])
            self._track_router("health_router", "健康檢查", True)
            self.app.include_router(ue_router, tags=["UE 管理"])
            self._track_router("ue_router", "UE 管理", True)
            self.app.include_router(handover_router, tags=["切換管理"])
            self._track_router("handover_router", "切換管理", True)

            # 只有在成功導入時才註冊 RL System 路由器
            if rl_training_available:
                self.app.include_router(
                    new_rl_training_router,
                    prefix="/api/v1/rl/training",
                    tags=["RL 訓練 (基礎)"],
                )
                self._track_router("new_rl_training_router", "RL 訓練 (基礎)", True)
                logger.info("✅ RL System 基礎路由器註冊完成")

            # 只有在成功導入時才註冊增強版路由器
            if enhanced_rl_available:
                self.app.include_router(
                    enhanced_rl_training_router,
                    prefix="/api/v1/rl/enhanced",
                    tags=["RL 訓練 (增強版)"],
                )
                self._track_router(
                    "enhanced_rl_training_router", "RL 訓練 (增強版)", True
                )
                logger.info("✅ RL System 增強版路由器註冊完成")

            # 註冊 WebSocket 路由器
            if websocket_available:
                self.app.include_router(
                    websocket_router,
                    tags=["WebSocket 實時推送"]
                )
                self._track_router("websocket_router", "WebSocket 實時推送", True)
                logger.info("✅ WebSocket 路由器註冊完成")

            logger.info("✅ 新模組化路由器註冊完成")
        except Exception as e:
            logger.exception("💥 新核心路由器註冊失敗")
            raise

        try:
            from ...routers.core_sync_router import (
                router as core_sync_router,
            )
            from ...routers.intelligent_fallback_router import (
                router as intelligent_fallback_router,
            )
            from ...routers.rl_monitoring_router import (
                router as rl_monitoring_router,
            )

            # from ...routers.rl_training_router import (
            #     router as rl_training_router,
            # )
            from ...routers.test_router import router as test_router

            self.app.include_router(core_sync_router, tags=["核心同步機制"])
            self._track_router("core_sync_router", "核心同步機制", True)
            self.app.include_router(intelligent_fallback_router, tags=["智能回退機制"])
            self._track_router("intelligent_fallback_router", "智能回退機制", True)
            self.app.include_router(rl_monitoring_router, tags=["RL 監控"])
            self._track_router("rl_monitoring_router", "RL 監控", True)
            # self.app.include_router(rl_training_router, tags=["RL 訓練"])
            # self._track_router("rl_training_router", "RL 訓練", True)
            self.app.include_router(test_router, tags=["測試"])
            self._track_router("test_router", "測試", True)
            logger.info("✅ 舊核心路由器註冊完成")
        except Exception as e:
            logger.exception("💥 舊核心路由器註冊失敗")
            raise
        logger.info("🎉 核心路由器全部註冊完成")

    def register_optional_routers(self) -> None:
        """註冊可選的路由器"""
        logger.info("🔧 開始註冊可選路由器...")

        # --- 放棄動態載入，改用靜態導入 ---
        try:
            from ...routers.orchestrator_router import (
                router as orchestrator_router,
            )

            self.app.include_router(
                orchestrator_router, tags=["AI Decision Orchestrator (V2)"]
            )
            self._track_router(
                "orchestrator_router",
                "AI Decision Orchestrator (V2)",
                True,
                "靜態註冊成功",
            )
            logger.info("✅ V2 協調器路由器靜態註冊成功")
        except Exception as e:
            logger.exception("💥 V2 協調器路由器靜態註冊失敗")
            self._track_router(
                "orchestrator_router",
                "AI Decision Orchestrator (V2)",
                False,
                "靜態註冊失敗",
            )

        # 算法生態系統路由器 - 靜態註冊
        try:
            from ...routers.algorithm_ecosystem import router as algorithm_ecosystem_router
            
            self.app.include_router(
                algorithm_ecosystem_router, tags=["算法生態系統"]
            )
            self._track_router(
                "algorithm_ecosystem_router",
                "算法生態系統",
                True,
                "靜態註冊成功",
            )
            logger.info("✅ 算法生態系統路由器靜態註冊成功")
        except Exception as e:
            logger.exception("💥 算法生態系統路由器靜態註冊失敗")
            self._track_router(
                "algorithm_ecosystem_router",
                "算法生態系統",
                False,
                f"靜態註冊失敗: {str(e)}",
            )

        # Phase 2.2 API 路由器 - 靜態註冊
        try:
            from ...services.rl_training.api.phase_2_2_api import router as phase_2_2_router
            
            self.app.include_router(
                phase_2_2_router, 
                prefix="/api/v1/rl/phase-2-2",
                tags=["Phase 2.2 - 真實換手場景生成"]
            )
            self._track_router(
                "phase_2_2_router",
                "Phase 2.2 - 真實換手場景生成",
                True,
                "靜態註冊成功",
            )
            logger.info("✅ Phase 2.2 API 路由器靜態註冊成功")
        except Exception as e:
            logger.exception("💥 Phase 2.2 API 路由器靜態註冊失敗")
            self._track_router(
                "phase_2_2_router",
                "Phase 2.2 - 真實換手場景生成",
                False,
                f"靜態註冊失敗: {str(e)}",
            )

        # Phase 2.3 API 路由器 - 使用簡化版本
        try:
            from ...services.rl_training.api.phase_2_3_simple_api import router as phase_2_3_router
            
            self.app.include_router(
                phase_2_3_router, 
                prefix="/api/v1/rl/phase-2-3",
                tags=["Phase 2.3 - RL 算法實戰應用"]
            )
            self._track_router(
                "phase_2_3_router",
                "Phase 2.3 - RL 算法實戰應用",
                True,
                "簡化版本註冊成功",
            )
            logger.info("✅ Phase 2.3 簡化 API 路由器靜態註冊成功")
        except Exception as e:
            logger.exception("💥 Phase 2.3 簡化 API 路由器靜態註冊失敗")
            self._track_router(
                "phase_2_3_router",
                "Phase 2.3 - RL 算法實戰應用",
                False,
                f"靜態註冊失敗: {str(e)}",
            )

        # Phase 3 API 路由器 - 決策透明化與視覺化 (完整版)
        try:
            from ...services.rl_training.api.phase_3_api import router as phase_3_router
            
            self.app.include_router(
                phase_3_router, 
                prefix="/api/v1/rl/phase-3",
                tags=["Phase 3 - 決策透明化與視覺化"]
            )
            self._track_router(
                "phase_3_router",
                "Phase 3 - 決策透明化與視覺化",
                True,
                "完整版本註冊成功",
            )
            logger.info("✅ Phase 3 完整 API 路由器靜態註冊成功")
        except Exception as e:
            logger.exception("💥 Phase 3 完整 API 路由器靜態註冊失敗")
            self._track_router(
                "phase_3_router",
                "Phase 3 - 決策透明化與視覺化",
                False,
                f"完整版註冊失敗: {str(e)}",
            )

        optional_routers = [
            # {
            #     "import_path": "netstack.netstack_api.routers.orchestrator_router",
            #     "tag": "AI Decision Orchestrator (V2)",
            # },
            {
                "import_path": "netstack_api.routers.ai_decision_status_router",
                "tag": "AI 決策狀態",
            },
            {
                "import_path": "netstack_api.routers.performance_router",
                "tag": "性能監控",
            },
        ]
        for router_config in optional_routers:
            self._register_single_optional_router(router_config)

    def _register_single_optional_router(self, router_config: Dict[str, str]) -> None:
        """動態導入並註冊單個可選路由器"""
        router_name = router_config["import_path"].split(".")[-1]
        try:
            module = importlib.import_module(router_config["import_path"])
            router = getattr(module, "router")
            self.app.include_router(router, tags=[router_config["tag"]])
            self._track_router(router_name, router_config["tag"], True, "註冊成功")
        except ModuleNotFoundError:
            msg = f"模組未找到，跳過註冊: {router_config['import_path']}"
            logger.warning(f"⚠️ {router_config['tag']} 路由器註冊失敗 (可選) - {msg}")
            self._track_router(router_name, router_config["tag"], False, msg)
        except Exception:
            msg = f"導入或註冊時發生未知錯誤: {router_config['import_path']}"
            logger.exception(f"💥 {router_config['tag']} 路由器註冊失敗 (可選)")
            self._track_router(router_name, router_config["tag"], False, msg)

    def _track_router(
        self, router_name: str, tag: str, success: bool, description: str = ""
    ) -> None:
        """記錄路由器的註冊狀態"""
        self.registered_routers.append(
            {
                "name": router_name,
                "tag": tag,
                "status": "success" if success else "failed",
                "description": description,
            }
        )

    def get_router_status(self) -> dict:
        """獲取所有路由器的註冊狀態"""
        total = len(self.registered_routers)
        successful = sum(1 for r in self.registered_routers if r["status"] == "success")
        return {
            "total_routers": total,
            "successful_routers": successful,
            "failed_routers": total - successful,
            "routers": self.registered_routers,
        }

    def get_available_endpoints(self) -> List[str]:
        """獲取所有可用的端點列表"""
        return list(
            sorted({r.path for r in self.app.routes if isinstance(r, APIRoute)})
        )

    def validate_router_health(self) -> dict:
        """
        驗證路由器健康狀態

        Returns:
            dict: 健康狀態報告
        """
        core_routers = [
            "health_router",
            "ue_router",
            "handover_router",
            "new_rl_training_router",
            "core_sync_router",
            "intelligent_fallback_router",
        ]

        core_router_status = {}
        for router_name in core_routers:
            router_info = next(
                (r for r in self.registered_routers if r["name"] == router_name),
                None,
            )
            core_router_status[router_name] = (
                router_info["status"] == "success" if router_info else False
            )

        all_core_healthy = all(core_router_status.values())

        return {
            "core_routers_healthy": all_core_healthy,
            "core_router_status": core_router_status,
            "total_endpoints": len(self.get_available_endpoints()),
            "overall_status": "healthy" if all_core_healthy else "degraded",
        }

    def get_registered_routers(self) -> List[Dict]:
        return self.registered_routers
