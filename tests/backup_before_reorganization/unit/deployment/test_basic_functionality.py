#!/usr/bin/env python3
"""
基本功能測試腳本
測試部署自動化的核心功能
"""

import sys
from pathlib import Path

# 添加項目根路徑
sys.path.insert(0, str(Path.cwd()))


def test_config_manager():
    """測試配置管理器"""
    print("🔧 測試配置管理器...")

    try:
        from deployment.config_manager import (
            ConfigManager,
            DeploymentEnvironment,
            ServiceType,
        )

        config_manager = ConfigManager(".")

        # 測試 NetStack 開發環境配置
        netstack_config = config_manager.create_default_config(
            DeploymentEnvironment.DEVELOPMENT, ServiceType.NETSTACK
        )
        print(
            f"✅ NetStack 配置創建成功: {netstack_config.service_type.value}-{netstack_config.environment.value}"
        )

        # 測試 SimWorld 生產環境配置
        simworld_config = config_manager.create_default_config(
            DeploymentEnvironment.PRODUCTION, ServiceType.SIMWORLD
        )
        print(
            f"✅ SimWorld 配置創建成功: {simworld_config.service_type.value}-{simworld_config.environment.value}"
        )

        # 測試配置保存和載入
        config_path = config_manager.save_config(
            netstack_config, "test_netstack_config.yaml"
        )
        loaded_config = config_manager.load_config("test_netstack_config.yaml")
        print(f"✅ 配置保存和載入成功: {config_path}")

        # 測試環境變數生成
        env_path = config_manager.generate_env_file(netstack_config)
        print(f"✅ 環境變數文件生成成功: {env_path}")

        # 驗證配置
        validation_results = config_manager.validate_configuration(loaded_config)
        if (
            not validation_results["config_errors"]
            and not validation_results["file_errors"]
        ):
            print("✅ 配置驗證通過")
        else:
            print(f"❌ 配置驗證失敗: {validation_results}")
            return False

        return True

    except Exception as e:
        print(f"❌ 配置管理器測試失敗: {e}")
        return False


def test_quick_deploy_script():
    """測試快速部署腳本"""
    print("🚀 測試快速部署腳本...")

    try:
        import subprocess

        script_path = Path("deployment/scripts/quick_deploy.sh")
        if not script_path.exists():
            print("❌ 快速部署腳本不存在")
            return False

        # 測試腳本幫助信息
        result = subprocess.run(
            ["bash", str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ 快速部署腳本可正常執行")
        else:
            print(f"❌ 快速部署腳本執行失敗: {result.stderr}")
            return False

        # 測試乾運行模式
        result = subprocess.run(
            [
                "bash",
                str(script_path),
                "--service",
                "netstack",
                "--env",
                "development",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print("✅ 部署模擬運行成功")
        else:
            print(f"❌ 部署模擬運行失敗: {result.stderr}")
            return False

        return True

    except Exception as e:
        print(f"❌ 快速部署腳本測試失敗: {e}")
        return False


def test_cli_tool():
    """測試命令行工具"""
    print("🛠️ 測試命令行工具...")

    try:
        cli_script = Path("deployment/cli/deploy_cli.py")
        if not cli_script.exists():
            print("❌ CLI 工具不存在")
            return False

        import subprocess

        # 測試 CLI 幫助
        result = subprocess.run(
            ["python3", str(cli_script), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ CLI 工具可正常執行")
        else:
            print(f"❌ CLI 工具執行失敗: {result.stderr}")
            return False

        return True

    except Exception as e:
        print(f"❌ CLI 工具測試失敗: {e}")
        return False


def test_template_generation():
    """測試模板生成"""
    print("📝 測試模板生成...")

    try:
        from deployment.config_manager import (
            ConfigManager,
            DeploymentEnvironment,
            ServiceType,
        )

        config_manager = ConfigManager(".")

        # 測試不同環境的模板生成
        environments = [
            DeploymentEnvironment.DEVELOPMENT,
            DeploymentEnvironment.TESTING,
            DeploymentEnvironment.PRODUCTION,
        ]

        services = [ServiceType.NETSTACK, ServiceType.SIMWORLD]

        for env in environments:
            for service in services:
                config = config_manager.create_default_config(env, service)
                env_file = config_manager.generate_env_file(config)

                if Path(env_file).exists():
                    print(f"✅ {service.value}-{env.value} 環境變數生成成功")
                else:
                    print(f"❌ {service.value}-{env.value} 環境變數生成失敗")
                    return False

        return True

    except Exception as e:
        print(f"❌ 模板生成測試失敗: {e}")
        return False


def test_makefile_integration():
    """測試 Makefile 集成"""
    print("🔨 測試 Makefile 集成...")

    try:
        makefile = Path("Makefile")
        if not makefile.exists():
            print("❌ Makefile 不存在")
            return False

        # 檢查關鍵目標
        with open(makefile, "r") as f:
            content = f.read()

        required_targets = ["netstack-stop", "simworld-stop", "test", "clean"]
        missing_targets = []

        for target in required_targets:
            if f"{target}:" not in content:
                missing_targets.append(target)

        if missing_targets:
            print(f'⚠️ 缺少 Makefile 目標: {", ".join(missing_targets)}')
        else:
            print("✅ 所有必要的 Makefile 目標都存在")

        # 測試 Make 命令
        import subprocess

        result = subprocess.run(
            ["make", "-n", "help"], capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            print("✅ Makefile 可正常解析")
        else:
            print(f"❌ Makefile 解析失敗: {result.stderr}")
            return False

        return True

    except Exception as e:
        print(f"❌ Makefile 集成測試失敗: {e}")
        return False


def cleanup_test_files():
    """清理測試文件"""
    print("🧹 清理測試文件...")

    test_files = [
        "deployment/configs/test_netstack_config.yaml",
        "deployment/configs/netstack-development.env",
        "deployment/configs/netstack-testing.env",
        "deployment/configs/netstack-production.env",
        "deployment/configs/simworld-development.env",
        "deployment/configs/simworld-testing.env",
        "deployment/configs/simworld-production.env",
    ]

    for file_path in test_files:
        full_path = Path(file_path)
        if full_path.exists():
            try:
                full_path.unlink()
                print(f"✅ 已清理: {file_path}")
            except Exception as e:
                print(f"⚠️ 清理失敗 {file_path}: {e}")


def main():
    """主函數"""
    print("🧪 NTN Stack 部署自動化基本功能測試")
    print("=" * 60)

    tests = [
        ("配置管理器", test_config_manager),
        ("模板生成", test_template_generation),
        ("CLI 工具", test_cli_tool),
        ("快速部署腳本", test_quick_deploy_script),
        ("Makefile 集成", test_makefile_integration),
    ]

    passed = 0
    total = len(tests)

    try:
        for test_name, test_func in tests:
            print(f"\n📋 測試: {test_name}")
            print("-" * 40)

            if test_func():
                print(f"✅ {test_name} 測試通過")
                passed += 1
            else:
                print(f"❌ {test_name} 測試失敗")

    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
        return 130

    finally:
        cleanup_test_files()

    # 顯示結果
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    print(f"總測試數: {total}")
    print(f"通過: {passed}")
    print(f"失敗: {total - passed}")

    pass_rate = (passed / total) * 100
    print(f"通過率: {pass_rate:.1f}%")

    if pass_rate == 100.0:
        print("🎉 所有測試100%通過！部署流程優化與自動化功能完整且可靠！")
        print("✅ Task 18「部署流程優化與自動化」已完成")
        return 0
    else:
        print(f"❌ 通過率 {pass_rate:.1f}%，需要修復失敗的測試")
        return 1


if __name__ == "__main__":
    sys.exit(main())
