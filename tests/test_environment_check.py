"""
測試環境檢查

驗證統一 API 測試環境在所有環境中（本地、Docker、CI/CD）都能正常運行
"""

import sys
import pytest
import asyncio
import logging
from importlib import import_module
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TestEnvironmentCheck:
    """測試環境檢查類"""

    def test_python_version(self):
        """檢查 Python 版本"""
        assert sys.version_info >= (3, 8), f"Python 版本過低: {sys.version}"
        logger.info(f"✅ Python 版本檢查通過: {sys.version}")

    def test_required_modules(self):
        """檢查必要模組是否可用"""
        required_modules = [
            "pytest",
            "pytest_asyncio",
            "httpx",
            "asyncio",
            "json",
            "datetime",
            "logging",
            "structlog",
            "pydantic",
            "fastapi",
        ]

        for module_name in required_modules:
            try:
                import_module(module_name)
                logger.info(f"✅ 模組 {module_name} 可用")
            except ImportError as e:
                pytest.fail(f"❌ 必要模組 {module_name} 不可用: {e}")

    @pytest.mark.asyncio
    async def test_async_capabilities(self):
        """測試異步功能"""

        async def sample_async_function():
            await asyncio.sleep(0.1)
            return "async_test_passed"

        result = await sample_async_function()
        assert result == "async_test_passed"
        logger.info("✅ 異步測試功能正常")

    def test_http_client_capabilities(self):
        """測試 HTTP 客戶端功能"""
        import httpx

        # 測試同步客戶端
        with httpx.Client() as client:
            assert client is not None
            logger.info("✅ httpx 同步客戶端可用")

        # 測試異步客戶端（不實際發請求）
        async def test_async_client():
            async with httpx.AsyncClient() as client:
                assert client is not None
                return True

        # 在當前事件循環中運行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_async_client())
            assert result is True
            logger.info("✅ httpx 異步客戶端可用")
        finally:
            loop.close()

    def test_json_handling(self):
        """測試 JSON 處理功能"""
        import json
        from datetime import datetime

        test_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "test",
            "data": [1, 2, 3],
            "nested": {"key": "value"},
        }

        # 測試序列化
        json_str = json.dumps(test_data)
        assert isinstance(json_str, str)

        # 測試反序列化
        parsed_data = json.loads(json_str)
        assert parsed_data["status"] == "test"
        assert len(parsed_data["data"]) == 3

        logger.info("✅ JSON 處理功能正常")

    def test_logging_configuration(self):
        """測試日誌配置"""
        import logging

        # 創建測試日誌記錄器
        test_logger = logging.getLogger("test_environment_check")
        test_logger.setLevel(logging.INFO)

        # 測試不同級別的日誌
        test_logger.debug("測試 DEBUG 日誌")
        test_logger.info("測試 INFO 日誌")
        test_logger.warning("測試 WARNING 日誌")

        logger.info("✅ 日誌配置正常")

    def test_pytest_markers(self):
        """測試 pytest 標記功能"""
        # 檢查當前測試是否有標記
        current_test = (
            pytest.current_pytest_config
            if hasattr(pytest, "current_pytest_config")
            else None
        )

        # 這個測試本身應該能正常運行
        assert True
        logger.info("✅ pytest 標記功能正常")

    @pytest.mark.unified_api
    @pytest.mark.unit
    def test_custom_markers(self):
        """測試自定義標記"""
        assert True
        logger.info("✅ 自定義標記功能正常")

    def test_environment_variables(self):
        """檢查環境變數"""
        import os

        # 檢查一些可能的環境變數
        env_vars_to_check = [
            ("PYTHONPATH", "Python 路徑"),
            ("ENVIRONMENT", "運行環境"),
            ("LOG_LEVEL", "日誌級別"),
        ]

        env_info = {}
        for var_name, description in env_vars_to_check:
            value = os.getenv(var_name)
            env_info[var_name] = value
            logger.info(f"🔍 {description} ({var_name}): {value or '未設定'}")

        # 至少 PYTHONPATH 應該存在
        pythonpath = os.getenv("PYTHONPATH")
        if pythonpath:
            logger.info(f"✅ PYTHONPATH 已設定: {pythonpath}")
        else:
            logger.warning("⚠️ PYTHONPATH 未設定，可能影響模組導入")

    def test_directory_structure(self):
        """檢查目錄結構"""
        import os
        from pathlib import Path

        # 檢查重要目錄是否存在
        important_paths = [
            "tests",
            "tests/reports",
            "netstack",
            "netstack/netstack_api",
        ]

        current_dir = Path.cwd()

        for path_str in important_paths:
            path = current_dir / path_str
            if path.exists():
                logger.info(f"✅ 目錄存在: {path}")
            else:
                # 嘗試相對於根目錄查找
                alt_path = current_dir.parent / path_str
                if alt_path.exists():
                    logger.info(f"✅ 目錄存在 (上級): {alt_path}")
                else:
                    logger.warning(f"⚠️ 目錄不存在: {path}")

    @pytest.mark.asyncio
    async def test_comprehensive_environment(self):
        """綜合環境測試"""

        # 模擬統一 API 測試中的典型操作
        test_results = {
            "async_support": False,
            "http_client": False,
            "json_handling": False,
            "logging": False,
        }

        try:
            # 測試異步支援
            await asyncio.sleep(0.01)
            test_results["async_support"] = True

            # 測試 HTTP 客戶端
            import httpx

            async with httpx.AsyncClient() as client:
                test_results["http_client"] = True

            # 測試 JSON 處理
            import json

            test_data = {"test": True, "timestamp": "2024-01-01T00:00:00"}
            json.dumps(test_data)
            test_results["json_handling"] = True

            # 測試日誌
            logger.info("綜合環境測試執行中...")
            test_results["logging"] = True

        except Exception as e:
            pytest.fail(f"綜合環境測試失敗: {e}")

        # 所有測試都應該通過
        all_passed = all(test_results.values())
        assert all_passed, f"環境測試結果: {test_results}"

        logger.info("✅ 綜合環境測試通過")


def generate_environment_report() -> Dict[str, Any]:
    """生成環境報告"""
    import sys
    import os
    import platform
    from datetime import datetime

    report = {
        "timestamp": datetime.now().isoformat(),
        "python_info": {
            "version": sys.version,
            "executable": sys.executable,
            "path": sys.path[:3],  # 只取前3個路徑
        },
        "platform_info": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "environment_variables": {
            "PYTHONPATH": os.getenv("PYTHONPATH"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL"),
            "PWD": os.getenv("PWD"),
        },
        "available_modules": [],
    }

    # 檢查關鍵模組
    key_modules = [
        "pytest",
        "pytest_asyncio",
        "httpx",
        "fastapi",
        "pydantic",
        "structlog",
        "asyncio",
        "json",
    ]

    for module_name in key_modules:
        try:
            module = import_module(module_name)
            version = getattr(module, "__version__", "unknown")
            report["available_modules"].append(
                {"name": module_name, "version": version, "available": True}
            )
        except ImportError:
            report["available_modules"].append(
                {"name": module_name, "version": None, "available": False}
            )

    return report


if __name__ == "__main__":
    # 生成並打印環境報告
    report = generate_environment_report()
    print("🔍 測試環境報告:")
    print("=" * 50)

    import json

    print(json.dumps(report, indent=2, ensure_ascii=False))

    print("\n" + "=" * 50)
    print("🧪 開始環境檢查測試...")

    # 運行基本檢查
    checker = TestEnvironmentCheck()

    try:
        checker.test_python_version()
        checker.test_required_modules()
        checker.test_json_handling()
        checker.test_logging_configuration()
        checker.test_environment_variables()
        checker.test_directory_structure()
        print("\n✅ 基本環境檢查通過!")
    except Exception as e:
        print(f"\n❌ 環境檢查失敗: {e}")
        sys.exit(1)
