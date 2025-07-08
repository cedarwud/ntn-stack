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

            self.app.include_router(health_router, tags=["健康檢查"])
            self._track_router("health_router", "健康檢查", True)
            self.app.include_router(ue_router, tags=["UE 管理"])
            self._track_router("ue_router", "UE 管理", True)
            self.app.include_router(handover_router, tags=["切換管理"])
            self._track_router("handover_router", "切換管理", True)
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
            from ...routers.test_router import router as test_router

            self.app.include_router(core_sync_router, tags=["核心同步機制"])
            self._track_router("core_sync_router", "核心同步機制", True)
            self.app.include_router(intelligent_fallback_router, tags=["智能回退機制"])
            self._track_router("intelligent_fallback_router", "智能回退機制", True)
            self.app.include_router(rl_monitoring_router, tags=["RL 監控"])
            self._track_router("rl_monitoring_router", "RL 監控", True)
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
