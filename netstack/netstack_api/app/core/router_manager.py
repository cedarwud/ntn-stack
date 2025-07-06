"""
NetStack API 路由器管理器
負責統一管理所有路由器的註冊和配置
"""

import structlog
from fastapi import FastAPI
from typing import Optional, List, Tuple

logger = structlog.get_logger(__name__)


class RouterManager:
    """
    路由器管理器
    負責按優先級註冊所有路由器
    """
    
    def __init__(self, app: FastAPI):
        """
        初始化路由器管理器
        
        Args:
            app: FastAPI 應用程式實例
        """
        self.app = app
        self.registered_routers = []
        
    def register_core_routers(self) -> None:
        """
        註冊核心路由器（必須成功）
        這些路由器是系統核心功能，註冊失敗會導致啟動失敗
        """
        logger.info("🚀 開始註冊核心路由器...")
        
        try:
            # 導入新的模組化路由器 (最高優先級)
            from ...app.api.health import router as health_router
            from ...app.api.v1.ue import router as ue_router
            from ...app.api.v1.handover import router as handover_router
            
            self.app.include_router(health_router, tags=["健康檢查"])
            self._track_router("health_router", "健康檢查", True)
            
            self.app.include_router(ue_router, tags=["UE 管理"])
            self._track_router("ue_router", "UE 管理", True)
            
            self.app.include_router(handover_router, tags=["切換管理"])
            self._track_router("handover_router", "切換管理", True)
            
            logger.info("✅ 新模組化路由器註冊完成")
            
        except Exception as e:
            logger.error("💥 核心路由器註冊失敗", error=str(e))
            raise
        
        try:
            # 導入現有的統一路由器
            from ...routers.unified_api_router import unified_router
            from ...routers.ai_decision_router import router as ai_decision_router
            from ...routers.core_sync_router import router as core_sync_router
            from ...routers.intelligent_fallback_router import router as intelligent_fallback_router
            
            self.app.include_router(unified_router, tags=["統一 API"])
            self._track_router("unified_router", "統一 API", True)
            
            self.app.include_router(ai_decision_router, tags=["AI 智慧決策"])
            self._track_router("ai_decision_router", "AI 智慧決策", True)
            
            self.app.include_router(core_sync_router, tags=["核心同步機制"])
            self._track_router("core_sync_router", "核心同步機制", True)
            
            self.app.include_router(intelligent_fallback_router, tags=["智能回退機制"])
            self._track_router("intelligent_fallback_router", "智能回退機制", True)
            
            logger.info("✅ 統一路由器註冊完成")
            
        except Exception as e:
            logger.error("💥 統一路由器註冊失敗", error=str(e))
            raise
            
        logger.info("🎉 核心路由器全部註冊完成")
    
    def register_optional_routers(self) -> None:
        """
        註冊可選路由器（允許失敗）
        這些路由器是擴展功能，註冊失敗不會影響核心功能
        """
        logger.info("🔧 開始註冊可選路由器...")
        
        # 定義可選路由器列表
        optional_routers = [
            {
                "import_path": "...routers.performance_router",
                "router_name": "router",
                "alias": "performance_router",
                "tag": "性能監控",
                "description": "系統性能監控和指標收集"
            },
            {
                "import_path": "...routers.rl_monitoring_router", 
                "router_name": "router",
                "alias": "rl_monitoring_router",
                "tag": "RL 訓練監控",
                "description": "強化學習訓練過程監控"
            },
            {
                "import_path": "...routers.satellite_tle_router",
                "router_name": "router", 
                "alias": "satellite_tle_router",
                "tag": "衛星 TLE 橋接",
                "description": "衛星軌道數據橋接服務"
            },
            {
                "import_path": "...routers.scenario_test_router",
                "router_name": "router",
                "alias": "scenario_test_router", 
                "tag": "場景測試驗證",
                "description": "網路場景測試和驗證"
            }
        ]
        
        successful_routers = 0
        total_routers = len(optional_routers)
        
        for router_config in optional_routers:
            success = self._register_single_optional_router(router_config)
            if success:
                successful_routers += 1
        
        logger.info(
            f"📊 可選路由器註冊完成: {successful_routers}/{total_routers} 成功",
            successful=successful_routers,
            total=total_routers,
            success_rate=f"{(successful_routers/total_routers)*100:.1f}%"
        )
    
    def _register_single_optional_router(self, router_config: dict) -> bool:
        """
        註冊單個可選路由器
        
        Args:
            router_config: 路由器配置字典
            
        Returns:
            bool: 註冊是否成功
        """
        try:
            # 動態導入路由器
            import importlib
            module = importlib.import_module(router_config["import_path"], package=__package__)
            router = getattr(module, router_config["router_name"])
            
            # 註冊路由器
            self.app.include_router(router, tags=[router_config["tag"]])
            
            # 記錄成功
            self._track_router(
                router_config["alias"], 
                router_config["tag"], 
                True, 
                router_config["description"]
            )
            
            logger.info(
                f"✅ {router_config['tag']} 路由器註冊成功",
                router=router_config["alias"],
                description=router_config["description"]
            )
            
            return True
            
        except ImportError as e:
            logger.warning(
                f"⚠️ {router_config['tag']} 路由器導入失敗，跳過註冊",
                router=router_config["alias"],
                error=str(e)
            )
            
            self._track_router(
                router_config["alias"], 
                router_config["tag"], 
                False, 
                f"導入失敗: {str(e)}"
            )
            
            return False
            
        except Exception as e:
            logger.error(
                f"💥 {router_config['tag']} 路由器註冊失敗",
                router=router_config["alias"],
                error=str(e)
            )
            
            self._track_router(
                router_config["alias"], 
                router_config["tag"], 
                False, 
                f"註冊失敗: {str(e)}"
            )
            
            return False
    
    def _track_router(self, router_name: str, tag: str, success: bool, description: str = "") -> None:
        """
        追蹤路由器註冊狀態
        
        Args:
            router_name: 路由器名稱
            tag: 路由器標籤
            success: 是否成功註冊
            description: 描述或錯誤訊息
        """
        self.registered_routers.append({
            "router_name": router_name,
            "tag": tag,
            "success": success,
            "description": description
        })
    
    def get_router_status(self) -> dict:
        """
        獲取所有路由器的註冊狀態
        
        Returns:
            dict: 路由器狀態摘要
        """
        total_routers = len(self.registered_routers)
        successful_routers = sum(1 for r in self.registered_routers if r["success"])
        
        return {
            "total_routers": total_routers,
            "successful_routers": successful_routers,
            "failed_routers": total_routers - successful_routers,
            "success_rate": (successful_routers / total_routers) * 100 if total_routers > 0 else 0,
            "routers": self.registered_routers
        }
    
    def get_available_endpoints(self) -> List[str]:
        """
        獲取所有可用的端點列表
        
        Returns:
            List[str]: 端點路徑列表
        """
        endpoints = []
        
        for route in self.app.routes:
            if hasattr(route, 'path'):
                endpoints.append(route.path)
        
        return sorted(list(set(endpoints)))
    
    def validate_router_health(self) -> dict:
        """
        驗證路由器健康狀態
        
        Returns:
            dict: 健康狀態報告
        """
        core_routers = [
            "health_router", "ue_router", "handover_router",
            "unified_router", "ai_decision_router", "core_sync_router", "intelligent_fallback_router"
        ]
        
        core_router_status = {}
        for router_name in core_routers:
            router_info = next(
                (r for r in self.registered_routers if r["router_name"] == router_name),
                None
            )
            core_router_status[router_name] = router_info["success"] if router_info else False
        
        all_core_healthy = all(core_router_status.values())
        
        return {
            "core_routers_healthy": all_core_healthy,
            "core_router_status": core_router_status,
            "total_endpoints": len(self.get_available_endpoints()),
            "overall_status": "healthy" if all_core_healthy else "degraded"
        }