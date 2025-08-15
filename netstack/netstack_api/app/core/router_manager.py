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

            # RL System 已移除

            # 嘗試導入 WebSocket 路由器
            try:
                from ...routers.websocket_router import websocket_router

                websocket_available = True
            except ImportError:
                websocket_available = False
                logger.warning("WebSocket router 不可用，跳過註冊")

            # 嘗試導入增強版路由器 - 如果不存在則跳過
            # Enhanced RL training routes 已移除
            enhanced_rl_available = False

            # 暫時禁用satellite_ops_router，使用simple_satellite_router
            intelligent_satellite_ops_available = False
            logger.info("智能衛星操作路由器暫時禁用，使用simple_satellite_router")
                
            # 備用：嘗試導入簡單衛星操作路由器（零依賴版本）
            try:
                from netstack_api.routers.simple_satellite_router import (
                    router as simple_satellite_ops_router,
                )

                simple_satellite_ops_available = True
                logger.info("✅ 簡單衛星操作路由器導入成功 (備用)")
            except ImportError as e:
                simple_satellite_ops_available = False
                logger.warning(f"Simple Satellite Operations router 不可用，跳過註冊: {e}")

            self.app.include_router(health_router, tags=["健康檢查"])
            self._track_router("health_router", "健康檢查", True)
            self.app.include_router(ue_router, tags=["UE 管理"])
            self._track_router("ue_router", "UE 管理", True)
            self.app.include_router(handover_router, tags=["切換管理"])
            self._track_router("handover_router", "切換管理", True)

            # 只有在成功導入時才註冊 RL System 路由器
            # RL System 路由器已移除

            # 註冊 WebSocket 路由器
            if websocket_available:
                self.app.include_router(websocket_router, tags=["WebSocket 實時推送"])
                self._track_router("websocket_router", "WebSocket 實時推送", True)
                logger.info("✅ WebSocket 路由器註冊完成")

            # 註冊智能衛星操作路由器（優先）
            if intelligent_satellite_ops_available:
                self.app.include_router(intelligent_satellite_ops_router, tags=["衛星操作-智能版"])
                self._track_router("intelligent_satellite_ops_router", "衛星操作-智能版", True)
                logger.info("✅ 智能衛星操作路由器註冊完成")
            elif simple_satellite_ops_available:
                # 備用：註冊簡單衛星操作路由器（零依賴版本）
                self.app.include_router(simple_satellite_ops_router, tags=["衛星操作-簡單版"])
                self._track_router("simple_satellite_ops_router", "衛星操作-簡單版", True)
                logger.info("✅ 簡單衛星操作路由器註冊完成 (備用)")

            # 嘗試導入換手事件API路由器
            try:
                import sys
                sys.path.append('/home/sat/ntn-stack/netstack')
                from src.api.v1.handover_events import (
                    router as handover_events_router,
                )

                self.app.include_router(handover_events_router, tags=["換手事件"])
                self._track_router("handover_events_router", "換手事件", True)
                logger.info("✅ 換手事件路由器註冊完成")
            except ImportError as e:
                logger.warning(f"換手事件路由器不可用，跳過註冊: {e}")

            # 嘗試導入測量事件路由器
            try:
                from ...routers.measurement_events_router_simple import (
                    router as measurement_events_router,
                )

                self.app.include_router(measurement_events_router, tags=["測量事件"])
                self._track_router("measurement_events_router", "測量事件", True)
                logger.info("✅ 測量事件路由器註冊完成")
            except ImportError:
                logger.warning("測量事件路由器不可用，跳過註冊")

            # 嘗試導入軌道路由器
            try:
                from netstack_api.routers.orbit_router import router as orbit_router

                self.app.include_router(orbit_router, tags=["軌道計算"])
                self._track_router("orbit_router", "軌道計算", True)
                logger.info("✅ 軌道路由器註冊完成")
            except Exception as e:
                logger.error(f"❌ 軌道路由器註冊失敗: {e}")
                import traceback
                logger.error(f"詳細錯誤: {traceback.format_exc()}")
                self._track_router("orbit_router", "軌道計算", False, f"註冊失敗: {str(e)}")

            # 嘗試導入衛星預計算路由器 (Phase 2)
            try:
                from ...routers.satellite_precompute_router import (
                    router as precompute_router,
                )

                self.app.include_router(precompute_router, tags=["衛星預計算"])
                self._track_router("satellite_precompute_router", "衛星預計算", True)
                logger.info("✅ 衛星預計算路由器註冊完成")
            except ImportError:
                logger.warning("衛星預計算路由器不可用，跳過註冊")

            # 嘗試導入衛星數據路由器 (統一數據架構)
            logger.info("🔍 開始註冊衛星數據路由器...")
            try:
                logger.info("📥 正在導入衛星數據路由器...")
                from ...routers.satellite_data_router import (
                    router as satellite_data_router,
                )

                logger.info(f"✅ 衛星數據路由器導入成功: {satellite_data_router}")
                logger.info(f"📋 路由器前綴: {satellite_data_router.prefix}")
                logger.info(f"📋 路由器路由數量: {len(satellite_data_router.routes)}")

                logger.info("🔗 正在註冊路由器到 FastAPI...")
                self.app.include_router(satellite_data_router, tags=["衛星數據管理"])
                self._track_router("satellite_data_router", "衛星數據管理", True)
                logger.info("✅ 衛星數據路由器註冊完成")
            except Exception as e:
                logger.error(f"❌ 衛星數據路由器註冊失敗: {e}")
                import traceback

                logger.error(f"詳細錯誤: {traceback.format_exc()}")

            # 嘗試導入 SIB19 路由器
            try:
                from ...routers.sib19_router import router as sib19_router

                self.app.include_router(sib19_router, tags=["SIB19 統一平台"])
                self._track_router("sib19_router", "SIB19 統一平台", True)
                logger.info("✅ SIB19 路由器註冊完成")
            except ImportError:
                logger.warning("SIB19 路由器不可用，跳過註冊")

            # 嘗試導入 Phase 2 背景下載狀態路由器
            try:
                from ...routers.phase2_status_router import (
                    router as phase2_status_router,
                )

                self.app.include_router(phase2_status_router, tags=["Phase 2 背景下載"])
                self._track_router("phase2_status_router", "Phase 2 背景下載", True)
                logger.info("✅ Phase 2 狀態路由器註冊完成")
            except ImportError:
                logger.warning("Phase 2 狀態路由器不可用，跳過註冊")

            logger.info("✅ 新模組化路由器註冊完成")
        except Exception as e:
            logger.exception("💥 新核心路由器註冊失敗")
            raise

        try:
            # from ...routers.core_sync_router import (
            #     router as core_sync_router,
            # )  # 已刪除 - IEEE INFOCOM 2024 相關組件
            # from ...routers.intelligent_fallback_router import (
            #     router as intelligent_fallback_router,
            # )  # 已刪除 - IEEE INFOCOM 2024 相關組件

            # RL 路由器已移除
            # from ...routers.test_router import router as test_router  # 已刪除 - 開發測試組件

            # self.app.include_router(core_sync_router, tags=["核心同步機制"])  # 已刪除
            # self._track_router("core_sync_router", "核心同步機制", True)  # 已刪除
            # self.app.include_router(intelligent_fallback_router, tags=["智能回退機制"])  # 已刪除
            # self._track_router("intelligent_fallback_router", "智能回退機制", True)  # 已刪除
            # RL 路由器註冊已移除
            # self.app.include_router(test_router, tags=["測試"])  # 已刪除
            # self._track_router("test_router", "測試", True)  # 已刪除

            # Phase 1: 座標軌道端點 (Phase 0 預計算數據整合)
            try:
                from ...routers.coordinate_orbit_endpoints import (
                    router as coordinate_orbit_router,
                )

                self.app.include_router(
                    coordinate_orbit_router,
                    prefix="/api/v1/satellites",
                    tags=["Phase 1 - 座標軌道預計算"],
                )
                self._track_router(
                    "coordinate_orbit_router", "Phase 1 - 座標軌道預計算", True
                )
                logger.info("✅ Phase 1 座標軌道路由器註冊完成")
            except Exception as e:
                logger.exception("💥 Phase 1 座標軌道路由器註冊失敗")
                self._track_router(
                    "coordinate_orbit_router",
                    "Phase 1 - 座標軌道預計算",
                    False,
                    f"註冊失敗: {str(e)}",
                )

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

        # LEO Config Router - P0.2 配置系統統一
        try:
            from ...routers.leo_config_router import (
                router as leo_config_router,
            )

            self.app.include_router(
                leo_config_router, tags=["LEO配置系統"]
            )
            self._track_router(
                "leo_config_router",
                "LEO配置系統",
                True,
                "P0.2 靜態註冊成功",
            )
            logger.info("✅ LEO配置系統路由器靜態註冊成功")
        except Exception as e:
            logger.exception("💥 LEO配置系統路由器靜態註冊失敗")
            self._track_router(
                "leo_config_router",
                "LEO配置系統",
                False,
                "P0.2 靜態註冊失敗",
            )

        # LEO Frontend Data Router - P0.3 輸出格式對接
        try:
            from ...routers.leo_frontend_data_router import (
                router as leo_frontend_data_router,
            )

            self.app.include_router(
                leo_frontend_data_router, tags=["LEO前端數據"]
            )
            self._track_router(
                "leo_frontend_data_router",
                "LEO前端數據",
                True,
                "P0.3 靜態註冊成功",
            )
            logger.info("✅ LEO前端數據路由器靜態註冊成功")
        except Exception as e:
            logger.exception("💥 LEO前端數據路由器靜態註冊失敗")
            self._track_router(
                "leo_frontend_data_router",
                "LEO前端數據",
                False,
                "P0.3 靜態註冊失敗",
            )

        # 算法生態系統路由器 - 靜態註冊
        try:
            from ...routers.algorithm_ecosystem import (
                router as algorithm_ecosystem_router,
            )

            self.app.include_router(algorithm_ecosystem_router, tags=["算法生態系統"])
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
        # Phase 2.2 RL API 已移除

        # Phase 2.3 API 路由器 - 使用簡化版本
        # Phase 2.3 RL API 已移除

        # Phase 3 RL API 已移除

        # Phase 4 API 路由器已移除

        optional_routers = [
            # {
            #     "import_path": "netstack.netstack_api.routers.orchestrator_router",
            #     "tag": "AI Decision Orchestrator (V2)",
            # },
            # AI 決策狀態路由器已移除
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
            # RL training router removed
            # "core_sync_router",  # 已刪除 - IEEE INFOCOM 2024 相關組件
            # "intelligent_fallback_router",  # 已刪除 - IEEE INFOCOM 2024 相關組件
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
