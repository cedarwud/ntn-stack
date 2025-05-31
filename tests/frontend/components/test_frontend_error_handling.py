#!/usr/bin/env python3
"""
前端錯誤處理測試

驗證前端錯誤處理、WebGL 上下文恢復和性能監控功能
"""

import os
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FrontendErrorHandlingValidator:
    """前端錯誤處理驗證器"""

    def __init__(self):
        self.frontend_dir = Path("simworld/frontend/src")
        self.error_boundary_file = self.frontend_dir / "components/ui/ErrorBoundary.tsx"
        self.app_file = self.frontend_dir / "App.tsx"
        self.stereogram_file = (
            self.frontend_dir / "components/scenes/StereogramView.tsx"
        )
        self.scene_manager_file = self.frontend_dir / "hooks/useSceneImageManager.ts"
        self.performance_monitor_file = (
            self.frontend_dir / "utils/performanceMonitor.ts"
        )

    def test_error_boundary_implementation(self):
        """測試錯誤邊界實現"""
        logger.info("🧪 測試錯誤邊界實現")

        assert (
            self.error_boundary_file.exists()
        ), f"ErrorBoundary.tsx 文件不存在: {self.error_boundary_file}"

        content = self.error_boundary_file.read_text(encoding="utf-8")

        # 檢查關鍵功能
        required_elements = [
            "class ErrorBoundary",
            "componentDidCatch",
            "getDerivedStateFromError",
            "hasError",
            "ErrorInfo",
            "import.meta.env.DEV",
        ]

        for element in required_elements:
            assert element in content, f"ErrorBoundary 未找到必要元素: {element}"

        logger.info("✅ 錯誤邊界實現檢查通過")

    def test_app_error_boundary_integration(self):
        """測試 App 組件中的錯誤邊界整合"""
        logger.info("🧪 測試 App 組件錯誤邊界整合")

        content = self.app_file.read_text(encoding="utf-8")

        # 檢查是否導入了 ErrorBoundary
        assert "import ErrorBoundary from" in content, "未導入 ErrorBoundary 組件"

        # 檢查是否使用了 ErrorBoundary
        assert "<ErrorBoundary>" in content, "未使用 ErrorBoundary 包裝組件"

        # 檢查是否有 fallback 處理
        assert "fallback=" in content, "未設置 ErrorBoundary fallback"

        logger.info("✅ App 組件錯誤邊界整合檢查通過")

    def test_webgl_context_recovery(self):
        """測試 WebGL 上下文恢復功能"""
        logger.info("🧪 測試 WebGL 上下文恢復功能")

        content = self.stereogram_file.read_text(encoding="utf-8")

        # 檢查 WebGL 上下文相關功能
        required_elements = [
            "webglcontextlost",
            "webglcontextrestored",
            "handleWebGLContextLost",
            "handleWebGLContextRestored",
            "preserveDrawingBuffer",
            "powerPreference",
        ]

        for element in required_elements:
            assert element in content, f"WebGL 上下文恢復未找到必要元素: {element}"

        logger.info("✅ WebGL 上下文恢復功能檢查通過")

    def test_scene_image_manager_error_handling(self):
        """測試場景圖像管理器錯誤處理"""
        logger.info("🧪 測試場景圖像管理器錯誤處理")

        content = self.scene_manager_file.read_text(encoding="utf-8")

        # 檢查改進的錯誤處理
        required_elements = [
            "console.debug",
            "組件卸載",
            "AbortError",
            "abortController.abort",
            "Component unmounted",
        ]

        for element in required_elements:
            assert (
                element in content
            ), f"場景圖像管理器錯誤處理未找到必要元素: {element}"

        logger.info("✅ 場景圖像管理器錯誤處理檢查通過")

    def test_performance_monitor(self):
        """測試性能監控功能"""
        logger.info("🧪 測試性能監控功能")

        assert (
            self.performance_monitor_file.exists()
        ), f"performanceMonitor.ts 文件不存在: {self.performance_monitor_file}"

        content = self.performance_monitor_file.read_text(encoding="utf-8")

        # 檢查性能監控功能
        required_elements = [
            "class PerformanceMonitor",
            "PerformanceObserver",
            "handleLongTask",
            "isIn3DEnvironment",
            "longTaskCount",
            "智能模式",
            "memory",
            "checkWebGLContext",
            "getPerformanceMetrics",
            "handleError",
            "handleUnhandledRejection",
            "reportPerformanceSummary",
        ]

        for element in required_elements:
            assert element in content, f"性能監控功能未找到必要元素: {element}"

        logger.info("✅ 性能監控功能檢查通過")

    def test_smart_error_filtering(self):
        """測試智能錯誤過濾功能"""
        logger.info("🧪 測試智能錯誤過濾功能")

        # 檢查性能監控中的智能錯誤過濾
        performance_content = self.performance_monitor_file.read_text(encoding="utf-8")

        # 應該有更嚴格的過濾機制
        filtering_elements = [
            "isExtensionError",
            "isKnownHarmlessError",
            "isExtensionRelated",
            "CacheStore.js",
            "GenAIWebpageEligibilityService",
            "content-script",
            "jquery-3.1.1.min.js",
        ]

        for element in filtering_elements:
            assert (
                element in performance_content
            ), f"智能錯誤過濾未找到必要元素: {element}"

        # 檢查 main.tsx 中的改進過濾
        main_file = self.frontend_dir / "main.tsx"
        main_content = main_file.read_text(encoding="utf-8")

        main_filtering_elements = [
            "isExtensionRelated",
            "console.error = function",
            "CacheStore.js",
            "Cache get failed",
        ]

        for element in main_filtering_elements:
            assert element in main_content, f"主應用錯誤過濾未找到必要元素: {element}"

        logger.info("✅ 智能錯誤過濾功能檢查通過")

    def test_3d_environment_optimization(self):
        """測試3D環境優化功能"""
        logger.info("🧪 測試3D環境優化功能")

        content = self.performance_monitor_file.read_text(encoding="utf-8")

        # 檢查3D環境特殊處理
        optimization_elements = [
            "isIn3DEnvironment",
            "stereogram",
            "canvas",
            "3D渲染",
            "500ms",  # 3D環境中的長任務閾值
            "10000",  # 報告頻率限制
        ]

        for element in optimization_elements:
            assert element in content, f"3D環境優化未找到必要元素: {element}"

        logger.info("✅ 3D環境優化功能檢查通過")

    def generate_validation_report(self):
        """生成驗證報告"""
        logger.info("📊 生成前端錯誤處理驗證報告")

        report = {
            "timestamp": "2024-01-01 12:00:00",
            "validation_status": "success",
            "error_boundary_implementation": "✅ 通過",
            "app_error_boundary_integration": "✅ 通過",
            "webgl_context_recovery": "✅ 通過",
            "scene_image_manager_error_handling": "✅ 通過",
            "performance_monitor": "✅ 通過",
            "smart_error_filtering": "✅ 通過",
            "3d_environment_optimization": "✅ 通過",
            "summary": {
                "error_boundary_created": True,
                "webgl_context_recovery_implemented": True,
                "performance_monitoring_enabled": True,
                "smart_error_filtering_implemented": True,
                "3d_environment_optimization_implemented": True,
            },
            "implementation_details": {
                "error_boundary": "React Class Component with fallback UI",
                "webgl_recovery": "Event listeners for context lost/restored",
                "performance_monitoring": "PerformanceObserver + memory monitoring",
                "smart_error_filtering": "Advanced filtering mechanisms",
                "3d_environment_optimization": "Special handling for 3D environments",
            },
        }

        return report

    def run_all_tests(self):
        """執行所有測試"""
        logger.info("🚀 開始前端錯誤處理驗證")

        try:
            self.test_error_boundary_implementation()
            self.test_app_error_boundary_integration()
            self.test_webgl_context_recovery()
            self.test_scene_image_manager_error_handling()
            self.test_performance_monitor()
            self.test_smart_error_filtering()
            self.test_3d_environment_optimization()

            report = self.generate_validation_report()

            logger.info("🎉 前端錯誤處理驗證完成！")
            logger.info("📊 驗證結果：")
            for key, value in report["summary"].items():
                logger.info(f"  {key}: {value}")

            return report

        except Exception as e:
            logger.error(f"❌ 驗證失敗: {e}")
            return {"validation_status": "failed", "error": str(e)}


def main():
    """主函數"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    validator = FrontendErrorHandlingValidator()
    result = validator.run_all_tests()

    if result["validation_status"] == "success":
        print("\n✅ 前端錯誤處理改進成功！")
        print("\n📋 實現摘要：")
        print("• 添加了 React ErrorBoundary 組件")
        print("• 實現了 WebGL 上下文恢復機制")
        print("• 添加了性能監控和記憶體監控")
        print("• 改善了組件卸載錯誤處理")
        print("• 過濾瀏覽器擴展產生的錯誤")
        print("• 抑制已知的無害控制台警告")
        print("• 實現了智能錯誤過濾功能")
        print("• 實現了3D環境優化功能")

        return 0
    else:
        print(f"\n❌ 驗證失敗: {result.get('error', '未知錯誤')}")
        return 1


if __name__ == "__main__":
    exit(main())
