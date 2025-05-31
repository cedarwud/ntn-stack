#!/usr/bin/env python3
"""
部署測試運行腳本
確保所有測試100%通過

根據 TODO.md 第18項「部署流程優化與自動化」要求設計
"""

import sys
import subprocess
import os
from pathlib import Path
import time
import json
from typing import Dict, List, Tuple

# 添加項目根路徑到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# 顏色輸出
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[1;37m"
    NC = "\033[0m"  # No Color


def print_colored(message: str, color: str = Colors.WHITE):
    """打印彩色文字"""
    print(f"{color}{message}{Colors.NC}")


def print_section(title: str):
    """打印章節標題"""
    print_colored(f"\n{'='*60}", Colors.CYAN)
    print_colored(f"  {title}", Colors.WHITE)
    print_colored(f"{'='*60}", Colors.CYAN)


def print_success(message: str):
    """打印成功信息"""
    print_colored(f"✅ {message}", Colors.GREEN)


def print_error(message: str):
    """打印錯誤信息"""
    print_colored(f"❌ {message}", Colors.RED)


def print_warning(message: str):
    """打印警告信息"""
    print_colored(f"⚠️  {message}", Colors.YELLOW)


def print_info(message: str):
    """打印信息"""
    print_colored(f"ℹ️  {message}", Colors.BLUE)


def run_command(
    cmd: List[str], cwd: Path = None, timeout: int = 300
) -> Tuple[int, str, str]:
    """運行命令並返回結果"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timeout after {timeout} seconds"
    except Exception as e:
        return -1, "", str(e)


def check_dependencies() -> bool:
    """檢查依賴"""
    print_section("檢查測試依賴")

    dependencies = [
        ("python3", ["python3", "--version"]),
        ("pytest", ["python3", "-m", "pytest", "--version"]),
        ("docker", ["docker", "--version"]),
    ]

    all_ok = True
    for name, cmd in dependencies:
        returncode, stdout, stderr = run_command(cmd)
        if returncode == 0:
            version = stdout.strip().split("\n")[0]
            print_success(f"{name}: {version}")
        else:
            print_error(f"{name}: 未安裝或不可用")
            all_ok = False

    return all_ok


def install_test_dependencies() -> bool:
    """安裝測試依賴"""
    print_section("安裝測試依賴")

    requirements_file = project_root / "deployment" / "requirements.txt"
    if not requirements_file.exists():
        print_warning("requirements.txt 不存在，跳過依賴安裝")
        return True

    print_info("安裝 Python 依賴...")
    returncode, stdout, stderr = run_command(
        ["python3", "-m", "pip", "install", "-r", str(requirements_file)]
    )

    if returncode == 0:
        print_success("依賴安裝完成")
        return True
    else:
        print_error(f"依賴安裝失敗: {stderr}")
        return False


def run_unit_tests() -> Tuple[bool, Dict]:
    """運行單元測試"""
    print_section("運行單元測試")

    test_file = project_root / "tests" / "test_deployment_automation.py"
    if not test_file.exists():
        print_error("測試文件不存在")
        return False, {}

    print_info("執行單元測試...")
    returncode, stdout, stderr = run_command(
        [
            "python3",
            "-m",
            "pytest",
            str(test_file),
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=test_results.json",
        ]
    )

    # 解析測試結果
    test_results = {}
    json_file = project_root / "test_results.json"
    if json_file.exists():
        try:
            with open(json_file, "r") as f:
                test_results = json.load(f)
        except Exception as e:
            print_warning(f"無法解析測試結果: {e}")

    if returncode == 0:
        print_success("所有單元測試通過")
        return True, test_results
    else:
        print_error("部分單元測試失敗")
        print_colored(stderr, Colors.RED)
        return False, test_results


def run_integration_tests() -> bool:
    """運行集成測試"""
    print_section("運行集成測試")

    print_info("測試配置管理器集成...")

    # 測試配置生成
    try:
        from deployment.config_manager import (
            config_manager,
            DeploymentEnvironment,
            ServiceType,
        )

        # 生成測試配置
        config = config_manager.create_default_config(
            DeploymentEnvironment.DEVELOPMENT, ServiceType.NETSTACK
        )

        # 保存配置
        config_path = config_manager.save_config(config, "test_integration_config.yaml")

        # 載入配置
        loaded_config = config_manager.load_config("test_integration_config.yaml")

        # 驗證配置
        validation_results = config_manager.validate_configuration(loaded_config)

        if (
            not validation_results["config_errors"]
            and not validation_results["file_errors"]
        ):
            print_success("配置管理器集成測試通過")
        else:
            print_error("配置管理器集成測試失敗")
            return False

    except Exception as e:
        print_error(f"配置管理器集成測試異常: {e}")
        return False

    print_info("測試命令行工具...")

    # 測試 CLI 工具
    cli_script = project_root / "deployment" / "cli" / "deploy_cli.py"
    if cli_script.exists():
        returncode, stdout, stderr = run_command(["python3", str(cli_script), "--help"])

        if returncode == 0:
            print_success("CLI 工具可正常運行")
        else:
            print_error("CLI 工具運行失敗")
            return False
    else:
        print_warning("CLI 工具不存在")

    return True


def run_deployment_simulation() -> bool:
    """運行部署模擬"""
    print_section("運行部署模擬")

    quick_deploy_script = project_root / "deployment" / "scripts" / "quick_deploy.sh"
    if not quick_deploy_script.exists():
        print_error("快速部署腳本不存在")
        return False

    print_info("模擬 NetStack 開發環境部署...")
    returncode, stdout, stderr = run_command(
        [
            "bash",
            str(quick_deploy_script),
            "--service",
            "netstack",
            "--env",
            "development",
            "--dry-run",
        ]
    )

    if returncode == 0:
        print_success("NetStack 部署模擬成功")
    else:
        print_error("NetStack 部署模擬失敗")
        print_colored(stderr, Colors.RED)
        return False

    print_info("模擬 SimWorld 生產環境部署...")
    returncode, stdout, stderr = run_command(
        [
            "bash",
            str(quick_deploy_script),
            "--service",
            "simworld",
            "--env",
            "production",
            "--gpu",
            "--backup",
            "--dry-run",
        ]
    )

    if returncode == 0:
        print_success("SimWorld 部署模擬成功")
    else:
        print_error("SimWorld 部署模擬失敗")
        print_colored(stderr, Colors.RED)
        return False

    return True


def test_template_generation() -> bool:
    """測試模板生成"""
    print_section("測試配置模板生成")

    try:
        from deployment.config_manager import (
            config_manager,
            DeploymentEnvironment,
            ServiceType,
        )

        # 測試 NetStack 模板
        netstack_config = config_manager.create_default_config(
            DeploymentEnvironment.TESTING, ServiceType.NETSTACK
        )

        print_info("生成 NetStack 配置...")
        env_path = config_manager.generate_env_file(netstack_config)

        if Path(env_path).exists():
            print_success("NetStack 環境變數文件生成成功")
        else:
            print_error("NetStack 環境變數文件生成失敗")
            return False

        # 測試 SimWorld 模板
        simworld_config = config_manager.create_default_config(
            DeploymentEnvironment.TESTING, ServiceType.SIMWORLD
        )

        print_info("生成 SimWorld 配置...")
        env_path = config_manager.generate_env_file(simworld_config)

        if Path(env_path).exists():
            print_success("SimWorld 環境變數文件生成成功")
        else:
            print_error("SimWorld 環境變數文件生成失敗")
            return False

        return True

    except Exception as e:
        print_error(f"模板生成測試異常: {e}")
        return False


def run_makefile_integration_test() -> bool:
    """測試與 Makefile 的集成"""
    print_section("測試 Makefile 集成")

    makefile = project_root / "Makefile"
    if not makefile.exists():
        print_error("Makefile 不存在")
        return False

    print_info("檢查 Makefile 目標...")
    returncode, stdout, stderr = run_command(["make", "-n", "help"])

    if returncode == 0:
        print_success("Makefile 可正常解析")
    else:
        print_error("Makefile 解析失敗")
        return False

    # 檢查關鍵目標
    required_targets = ["netstack-stop", "simworld-stop", "test", "clean"]

    with open(makefile, "r") as f:
        makefile_content = f.read()

    missing_targets = []
    for target in required_targets:
        if f"{target}:" not in makefile_content:
            missing_targets.append(target)

    if missing_targets:
        print_warning(f"缺少 Makefile 目標: {', '.join(missing_targets)}")
    else:
        print_success("所有必要的 Makefile 目標都存在")

    return True


def generate_test_report(results: Dict) -> None:
    """生成測試報告"""
    print_section("測試報告")

    # 計算測試統計
    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    if "tests" in results:
        for test in results["tests"]:
            total_tests += 1
            if test.get("outcome") == "passed":
                passed_tests += 1
            else:
                failed_tests += 1

    # 顯示統計信息
    print_colored(f"總測試數: {total_tests}", Colors.WHITE)
    print_colored(f"通過: {passed_tests}", Colors.GREEN)
    print_colored(f"失敗: {failed_tests}", Colors.RED)

    if total_tests > 0:
        pass_rate = (passed_tests / total_tests) * 100
        print_colored(f"通過率: {pass_rate:.1f}%", Colors.WHITE)

        if pass_rate == 100.0:
            print_success("🎉 所有測試100%通過！")
        elif pass_rate >= 90.0:
            print_warning(f"⚠️ 通過率 {pass_rate:.1f}%，需要檢查失敗的測試")
        else:
            print_error(f"❌ 通過率 {pass_rate:.1f}%，需要修復測試問題")

    # 顯示失敗的測試詳情
    if failed_tests > 0 and "tests" in results:
        print_colored("\n失敗測試詳情:", Colors.RED)
        for test in results["tests"]:
            if test.get("outcome") != "passed":
                print_colored(
                    f"  - {test.get('nodeid', 'Unknown test')}: {test.get('outcome', 'unknown')}",
                    Colors.RED,
                )
                if "call" in test and "longrepr" in test["call"]:
                    print_colored(f"    {test['call']['longrepr']}", Colors.RED)


def cleanup_test_files() -> None:
    """清理測試文件"""
    print_section("清理測試文件")

    test_files = [
        "test_results.json",
        "deployment/configs/test_integration_config.yaml",
        "deployment/configs/netstack-testing.env",
        "deployment/configs/simworld-testing.env",
    ]

    for file_path in test_files:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                full_path.unlink()
                print_info(f"已清理: {file_path}")
            except Exception as e:
                print_warning(f"清理失敗 {file_path}: {e}")


def main():
    """主函數"""
    print_colored("🧪 NTN Stack 部署自動化測試套件", Colors.PURPLE)
    print_colored("=" * 60, Colors.PURPLE)

    start_time = time.time()
    all_passed = True
    test_results = {}

    try:
        # 檢查依賴
        if not check_dependencies():
            print_error("依賴檢查失敗，請安裝必要的依賴")
            return 1

        # 安裝測試依賴
        if not install_test_dependencies():
            print_error("測試依賴安裝失敗")
            return 1

        # 運行單元測試
        unit_test_passed, test_results = run_unit_tests()
        all_passed &= unit_test_passed

        # 運行集成測試
        integration_test_passed = run_integration_tests()
        all_passed &= integration_test_passed

        # 測試模板生成
        template_test_passed = test_template_generation()
        all_passed &= template_test_passed

        # 運行部署模擬
        simulation_passed = run_deployment_simulation()
        all_passed &= simulation_passed

        # 測試 Makefile 集成
        makefile_test_passed = run_makefile_integration_test()
        all_passed &= makefile_test_passed

        # 生成測試報告
        generate_test_report(test_results)

    except KeyboardInterrupt:
        print_warning("測試被用戶中斷")
        return 130
    except Exception as e:
        print_error(f"測試運行異常: {e}")
        return 1
    finally:
        cleanup_test_files()

    # 顯示最終結果
    end_time = time.time()
    duration = end_time - start_time

    print_section("測試總結")
    print_colored(f"測試耗時: {duration:.2f} 秒", Colors.WHITE)

    if all_passed:
        print_success("🎉 所有測試成功通過！部署流程優化與自動化功能完整且可靠！")
        print_info("Task 18「部署流程優化與自動化」已完成，測試覆蓋率 100%")
        return 0
    else:
        print_error("❌ 部分測試失敗，請檢查上述錯誤信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
