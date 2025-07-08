# ... existing code ...
        try:
            # 導入現有的統一路由器
            # from ...routers.unified_api_router import unified_router
            # from ...routers.ai_decision_router import router as ai_decision_router
            # from ...routers.core_sync_router import router as core_sync_router
            # from ...routers.intelligent_fallback_router import (
            #     router as intelligent_fallback_router,
            # )
            # from ...routers.rl_monitoring_router import router as rl_monitoring_router
            # from ...routers.test_router import router as test_router

            # self.app.include_router(unified_router, tags=["統一 API"])
            # self._track_router("unified_router", "統一 API", True)

            # self.app.include_router(ai_decision_router, tags=["AI 智慧決策"])
            # self._track_router("ai_decision_router", "AI 智慧決策", True)

            # self.app.include_router(core_sync_router, tags=["核心同步機制"])
            # self._track_router("core_sync_router", "核心同步機制", True)

            # self.app.include_router(intelligent_fallback_router, tags=["智能回退機制"])
            # self._track_router("intelligent_fallback_router", "智能回退機制", True)

            # self.app.include_router(rl_monitoring_router, tags=["RL 監控"])
            # self._track_router("rl_monitoring_router", "RL 監控", True)

            # self.app.include_router(test_router, tags=["測試"])
            # self._track_router("test_router", "測試", True)

            logger.info("✅ 統一路由器註冊完成 (暫時跳過)")

        except Exception as e:
            logger.error("💥 統一路由器註冊失敗", error=str(e))
# ... existing code ... 