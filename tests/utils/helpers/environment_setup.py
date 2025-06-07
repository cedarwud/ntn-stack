#!/usr/bin/env python3
"""
NTN Stack 測試環境設置工具
負責測試環境的檢查、設置和管理
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import venv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 設置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EnvironmentSetup:
    """測試環境設置類別"""

    def __init__(self):
        self.base_dir = Path.cwd()
        self.tests_dir = self.base_dir / "tests"
        self.venv_dir = self.tests_dir / "venv"
        self.required_services = {
            "netstack": "http://localhost:8080/health",
            "simworld_frontend": "http://localhost:3000",
            "simworld_backend": "http://localhost:8000/health",
        }
        self.required_dependencies = [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
            "requests>=2.28.0",
            "aiohttp>=3.8.0",
            "selenium>=4.0.0",
            "beautifulsoup4>=4.11.0",
            "pyyaml>=6.0",
            "jinja2>=3.1.0",
        ]

    def setup_environment(self) -> bool:
        """設置測試環境"""
        logger.info("🚀 開始設置測試環境...")

        try:
            # 1. 創建必要的目錄結構
            if not self._create_directories():
                return False

            # 2. 設置虛擬環境
            if not self._setup_virtual_environment():
                return False

            # 3. 安裝測試依賴
            if not self._install_dependencies():
                return False

            # 4. 創建配置文件
            if not self._create_config_files():
                return False

            # 5. 設置環境變數
            if not self._setup_environment_variables():
                return False

            # 6. 驗證設置
            if not self._verify_setup():
                return False

            logger.info("✅ 測試環境設置完成")
            return True

        except Exception as e:
            logger.error(f"❌ 測試環境設置失敗: {e}")
            return False

    async def check_environment(self) -> Dict[str, bool]:
        """檢查測試環境狀態"""
        logger.info("🔍 檢查測試環境狀態...")

        results = {
            "directories": self._check_directories(),
            "virtual_env": self._check_virtual_environment(),
            "dependencies": self._check_dependencies(),
            "services": await self._check_services(),
            "configs": self._check_config_files(),
        }

        # 輸出檢查結果
        self._print_check_results(results)

        return results

    def _setup_virtual_environment(self) -> bool:
        """設置虛擬環境"""
        logger.info("🐍 設置虛擬環境...")

        try:
            if not self.venv_dir.exists():
                # 創建虛擬環境
                venv.create(self.venv_dir, with_pip=True)
                logger.info(f"✅ 虛擬環境已創建: {self.venv_dir}")
            else:
                logger.info("✅ 虛擬環境已存在")

            return True

        except Exception as e:
            logger.error(f"❌ 虛擬環境設置失敗: {e}")
            return False

    def _get_venv_python(self) -> str:
        """獲取虛擬環境的 Python 路徑"""
        if os.name == "nt":  # Windows
            return str(self.venv_dir / "Scripts" / "python.exe")
        else:  # Unix/Linux/macOS
            return str(self.venv_dir / "bin" / "python")

    def _get_venv_pip(self) -> str:
        """獲取虛擬環境的 pip 路徑"""
        if os.name == "nt":  # Windows
            return str(self.venv_dir / "Scripts" / "pip.exe")
        else:  # Unix/Linux/macOS
            return str(self.venv_dir / "bin" / "pip")

    def _create_directories(self) -> bool:
        """創建必要的目錄結構"""
        logger.info("📁 創建目錄結構...")

        directories = [
            "tests/unit/netstack",
            "tests/unit/simworld",
            "tests/unit/deployment",
            "tests/unit/monitoring",
            "tests/integration/api",
            "tests/integration/services",
            "tests/integration/cross_service",
            "tests/e2e/scenarios",
            "tests/e2e/performance",
            "tests/e2e/standards",
            "tests/shell/netstack",
            "tests/shell/connectivity",
            "tests/shell/deployment",
            "tests/frontend/components",
            "tests/frontend/ui",
            "tests/frontend/integration",
            "tests/tools",
            "tests/configs",
            "tests/reports",
            "tests/logs",
            "tests/archive",
        ]

        try:
            for directory in directories:
                dir_path = self.base_dir / directory
                dir_path.mkdir(parents=True, exist_ok=True)

                # 創建 __init__.py 文件（如果是 Python 包目錄）
                if any(part in directory for part in ["unit", "integration", "tools"]):
                    init_file = dir_path / "__init__.py"
                    if not init_file.exists():
                        init_file.touch()

            logger.info("✅ 目錄結構創建完成")
            return True

        except Exception as e:
            logger.error(f"❌ 目錄創建失敗: {e}")
            return False

    def _install_dependencies(self) -> bool:
        """安裝測試依賴"""
        logger.info("📦 安裝測試依賴...")

        try:
            # 創建 requirements-test.txt
            requirements_file = self.tests_dir / "requirements-test.txt"
            with open(requirements_file, "w", encoding="utf-8") as f:
                f.write("# NTN Stack 測試依賴\n")
                for dep in self.required_dependencies:
                    f.write(f"{dep}\n")

            # 使用虛擬環境的 pip 安裝依賴
            pip_path = self._get_venv_pip()
            result = subprocess.run(
                [pip_path, "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info("✅ 測試依賴安裝完成")
                return True
            else:
                logger.error(f"❌ 依賴安裝失敗: {result.stderr}")
                # 嘗試使用系統包管理器安裝基本依賴
                return self._install_system_dependencies()

        except Exception as e:
            logger.error(f"❌ 依賴安裝異常: {e}")
            return self._install_system_dependencies()

    def _install_system_dependencies(self) -> bool:
        """使用系統包管理器安裝依賴"""
        logger.info("📦 嘗試使用系統包管理器安裝依賴...")

        try:
            # 檢查是否為 Ubuntu/Debian 系統
            if Path("/etc/debian_version").exists():
                packages = [
                    "python3-pytest",
                    "python3-requests",
                    "python3-aiohttp",
                    "python3-yaml",
                    "python3-jinja2",
                ]

                logger.info("檢測到 Debian/Ubuntu 系統，嘗試安裝系統包...")
                for package in packages:
                    try:
                        result = subprocess.run(
                            ["dpkg", "-l", package], capture_output=True, text=True
                        )

                        if result.returncode == 0:
                            logger.info(f"✅ {package} 已安裝")
                        else:
                            logger.warning(
                                f"⚠️ {package} 未安裝，請執行: sudo apt install {package}"
                            )
                    except Exception:
                        logger.warning(f"⚠️ 無法檢查 {package} 狀態")

                logger.info("✅ 系統依賴檢查完成")
                return True
            else:
                logger.warning("⚠️ 非 Debian/Ubuntu 系統，請手動安裝測試依賴")
                return True

        except Exception as e:
            logger.error(f"❌ 系統依賴安裝失敗: {e}")
            return False

    def _create_config_files(self) -> bool:
        """創建配置文件"""
        logger.info("⚙️ 創建配置文件...")

        try:
            # pytest 配置
            pytest_config = """
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
markers =
    unit: 單元測試
    integration: 整合測試
    e2e: 端到端測試
    performance: 性能測試
    slow: 慢速測試
    smoke: 煙霧測試
"""

            pytest_file = self.base_dir / "pytest.ini"
            with open(pytest_file, "w", encoding="utf-8") as f:
                f.write(pytest_config)

            # 測試環境配置
            test_env_config = {
                "environments": {
                    "development": {
                        "netstack_url": "http://localhost:8080",
                        "simworld_frontend_url": "http://localhost:3000",
                        "simworld_backend_url": "http://localhost:8000",
                        "timeout": 30,
                    },
                    "testing": {
                        "netstack_url": "http://localhost:8081",
                        "simworld_frontend_url": "http://localhost:3001",
                        "simworld_backend_url": "http://localhost:8001",
                        "timeout": 60,
                    },
                },
                "test_suites": {
                    "smoke": {"timeout": 30, "parallel": False},
                    "quick": {"timeout": 120, "parallel": True},
                    "full": {"timeout": 1200, "parallel": True},
                },
            }

            config_file = self.tests_dir / "configs" / "test_environments.yaml"
            import yaml

            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    test_env_config, f, default_flow_style=False, allow_unicode=True
                )

            logger.info("✅ 配置文件創建完成")
            return True

        except Exception as e:
            logger.error(f"❌ 配置文件創建失敗: {e}")
            return False

    def _setup_environment_variables(self) -> bool:
        """設置環境變數"""
        logger.info("🌍 設置環境變數...")

        try:
            env_vars = {
                "PYTHONPATH": str(self.base_dir),
                "TEST_ENV": "development",
                "NETSTACK_URL": "http://localhost:8080",
                "SIMWORLD_FRONTEND_URL": "http://localhost:3000",
                "SIMWORLD_BACKEND_URL": "http://localhost:8000",
            }

            # 創建 .env 文件
            env_file = self.tests_dir / ".env"
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("# NTN Stack 測試環境變數\n")
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")

            # 設置當前進程的環境變數
            for key, value in env_vars.items():
                os.environ[key] = value

            logger.info("✅ 環境變數設置完成")
            return True

        except Exception as e:
            logger.error(f"❌ 環境變數設置失敗: {e}")
            return False

    def _verify_setup(self) -> bool:
        """驗證設置"""
        logger.info("✅ 驗證環境設置...")

        try:
            # 檢查 Python 模組導入
            test_imports = ["pytest", "httpx", "requests", "aiohttp", "yaml"]

            for module in test_imports:
                try:
                    __import__(module)
                    logger.info(f"✅ {module} 模組可用")
                except ImportError:
                    logger.error(f"❌ {module} 模組不可用")
                    return False

            # 檢查目錄結構
            required_dirs = [
                "tests/unit",
                "tests/integration",
                "tests/e2e",
                "tests/tools",
                "tests/configs",
            ]

            for directory in required_dirs:
                dir_path = self.base_dir / directory
                if not dir_path.exists():
                    logger.error(f"❌ 目錄不存在: {directory}")
                    return False

            logger.info("✅ 環境設置驗證通過")
            return True

        except Exception as e:
            logger.error(f"❌ 環境驗證失敗: {e}")
            return False

    def _check_directories(self) -> bool:
        """檢查目錄結構"""
        required_dirs = [
            "tests/unit",
            "tests/integration",
            "tests/e2e",
            "tests/shell",
            "tests/frontend",
            "tests/tools",
            "tests/configs",
        ]

        for directory in required_dirs:
            if not (self.base_dir / directory).exists():
                return False

        return True

    def _check_dependencies(self) -> bool:
        """檢查依賴安裝"""
        try:
            import pytest
            import httpx
            import requests
            import aiohttp

            return True
        except ImportError:
            return False

    async def _check_services(self) -> bool:
        """檢查服務狀態"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                for service, url in self.required_services.items():
                    try:
                        async with session.get(url, timeout=5) as response:
                            if response.status != 200:
                                return False
                    except Exception:
                        return False

            return True

        except Exception:
            return False

    def _check_config_files(self) -> bool:
        """檢查配置文件"""
        config_files = [
            "pytest.ini",
            "tests/configs/test_environments.yaml",
            "tests/.env",
        ]

        for config_file in config_files:
            if not (self.base_dir / config_file).exists():
                return False

        return True

    def _print_check_results(self, results: Dict[str, bool]):
        """輸出檢查結果"""
        print("\n🔍 測試環境檢查結果:")
        print("=" * 40)

        status_map = {
            "directories": "📁 目錄結構",
            "dependencies": "📦 依賴安裝",
            "services": "🚀 服務狀態",
            "configs": "⚙️ 配置文件",
        }

        for key, status in results.items():
            status_icon = "✅" if status else "❌"
            print(
                f"{status_icon} {status_map.get(key, key)}: {'正常' if status else '異常'}"
            )

        overall_status = all(results.values())
        print(f"\n🎯 整體狀態: {'✅ 正常' if overall_status else '❌ 需要修復'}")

    def reset_environment(self) -> bool:
        """重設測試環境"""
        logger.info("🔄 重設測試環境...")

        try:
            # 清理測試產物
            cleanup_dirs = ["tests/reports", "tests/logs", "tests/__pycache__"]
            for cleanup_dir in cleanup_dirs:
                dir_path = self.base_dir / cleanup_dir
                if dir_path.exists():
                    import shutil

                    shutil.rmtree(dir_path)

            # 重新設置
            return self.setup_environment()

        except Exception as e:
            logger.error(f"❌ 環境重設失敗: {e}")
            return False


async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="NTN Stack 測試環境設置工具")
    parser.add_argument("--setup", action="store_true", help="設置測試環境")
    parser.add_argument("--check", action="store_true", help="檢查測試環境")
    parser.add_argument("--reset", action="store_true", help="重設測試環境")

    args = parser.parse_args()

    env_setup = EnvironmentSetup()

    if args.setup:
        success = env_setup.setup_environment()
        sys.exit(0 if success else 1)
    elif args.check:
        results = await env_setup.check_environment()
        overall_status = all(results.values())
        sys.exit(0 if overall_status else 1)
    elif args.reset:
        success = env_setup.reset_environment()
        sys.exit(0 if success else 1)
    else:
        # 默認執行檢查
        results = await env_setup.check_environment()
        overall_status = all(results.values())
        sys.exit(0 if overall_status else 1)


if __name__ == "__main__":
    asyncio.run(main())
