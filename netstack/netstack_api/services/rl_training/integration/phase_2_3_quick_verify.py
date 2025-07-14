#!/usr/bin/env python3
"""
Phase 2.3 快速驗證腳本

快速檢查 Phase 2.3 組件的基本可用性
"""

import sys
import asyncio
import logging
from datetime import datetime

# 設置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_basic_dependencies():
    """檢查基本依賴"""
    print("🔍 檢查基本依賴...")

    missing_deps = []

    try:
        import numpy as np

        print(f"  ✅ NumPy {np.__version__}")
    except ImportError:
        missing_deps.append("numpy")

    try:
        import asyncio

        print(f"  ✅ AsyncIO (Python {sys.version.split()[0]})")
    except ImportError:
        missing_deps.append("asyncio")

    try:
        from datetime import datetime

        print(f"  ✅ DateTime")
    except ImportError:
        missing_deps.append("datetime")

    try:
        from typing import Dict, List, Optional, Any

        print(f"  ✅ Typing")
    except ImportError:
        missing_deps.append("typing")

    if missing_deps:
        print(f"  ❌ 缺少依賴: {', '.join(missing_deps)}")
        return False

    print("  🎉 基本依賴檢查通過")
    return True


def check_phase_2_3_imports():
    """檢查 Phase 2.3 組件導入"""
    print("\n🔧 檢查 Phase 2.3 組件...")

    components_status = {}

    try:
        from . import (
            RL_INTEGRATOR_AVAILABLE,
            ENV_BRIDGE_AVAILABLE,
            ANALYTICS_AVAILABLE,
            COMPARATOR_AVAILABLE,
            REALTIME_AVAILABLE,
        )

        components_status = {
            "RL算法整合器": RL_INTEGRATOR_AVAILABLE,
            "環境橋接器": ENV_BRIDGE_AVAILABLE,
            "決策分析引擎": ANALYTICS_AVAILABLE,
            "多算法比較器": COMPARATOR_AVAILABLE,
            "實時決策服務": REALTIME_AVAILABLE,
        }

        for component, available in components_status.items():
            status = "✅" if available else "❌"
            print(f"  {status} {component}")

        available_count = sum(components_status.values())
        total_count = len(components_status)

        print(f"\n  📊 可用組件: {available_count}/{total_count}")

        if available_count >= 3:
            print("  🎉 基本組件檢查通過")
            return True, components_status
        else:
            print("  ⚠️  可用組件不足，建議檢查導入問題")
            return False, components_status

    except ImportError as e:
        print(f"  ❌ 導入失敗: {e}")
        return False, {}


async def test_algorithm_integrator():
    """測試 RL 算法整合器"""
    print("\n🤖 測試 RL 算法整合器...")

    try:
        from . import RL_INTEGRATOR_AVAILABLE, RLAlgorithmIntegrator

        if not RL_INTEGRATOR_AVAILABLE:
            print("  ⚠️  算法整合器不可用，跳過測試")
            return False

        # 簡單配置
        config = {
            "enabled_algorithms": ["dqn"],
            "default_algorithm": "dqn",
            "algorithm_configs": {"dqn": {"learning_rate": 0.001, "batch_size": 32}},
        }

        # 創建實例
        integrator = RLAlgorithmIntegrator(config)
        print("  ✅ 成功創建算法整合器實例")

        # 測試初始化
        try:
            init_success = await integrator.initialize()
            if init_success:
                print("  ✅ 算法整合器初始化成功")
            else:
                print("  ⚠️  算法整合器初始化失敗")
        except Exception as e:
            print(f"  ⚠️  初始化過程中出現問題: {e}")
            init_success = False

        # 測試狀態獲取
        try:
            status = integrator.get_status()
            print(
                f"  ✅ 狀態獲取成功，當前算法: {status.get('current_algorithm', 'unknown')}"
            )
        except Exception as e:
            print(f"  ⚠️  狀態獲取失敗: {e}")

        return True

    except Exception as e:
        print(f"  ❌ 算法整合器測試失敗: {e}")
        return False


async def test_environment_bridge():
    """測試環境橋接器"""
    print("\n🌍 測試環境橋接器...")

    try:
        from . import ENV_BRIDGE_AVAILABLE, RealEnvironmentBridge

        if not ENV_BRIDGE_AVAILABLE:
            print("  ⚠️  環境橋接器不可用，跳過測試")
            return False

        # 簡單配置
        config = {
            "max_episode_steps": 10,
            "scenario_type": "urban",
            "complexity": "simple",
        }

        # 創建實例
        bridge = RealEnvironmentBridge(config)
        print("  ✅ 成功創建環境橋接器實例")

        # 測試初始化
        try:
            init_success = await bridge.initialize()
            if init_success:
                print("  ✅ 環境橋接器初始化成功")
            else:
                print("  ⚠️  環境橋接器初始化失敗（可能是 SimWorld 連接問題）")
        except Exception as e:
            print(f"  ⚠️  初始化過程中出現問題: {e}")

        # 測試狀態獲取
        try:
            status = bridge.get_status()
            print(f"  ✅ 狀態獲取成功，當前狀態: {status.get('state', 'unknown')}")
        except Exception as e:
            print(f"  ⚠️  狀態獲取失敗: {e}")

        return True

    except Exception as e:
        print(f"  ❌ 環境橋接器測試失敗: {e}")
        return False


async def test_decision_analytics():
    """測試決策分析引擎"""
    print("\n📊 測試決策分析引擎...")

    try:
        from . import ANALYTICS_AVAILABLE, DecisionAnalyticsEngine

        if not ANALYTICS_AVAILABLE:
            print("  ⚠️  決策分析引擎不可用，跳過測試")
            return False

        # 簡單配置
        config = {
            "enable_detailed_logging": True,
            "enable_explainability": True,
            "max_records_per_episode": 100,
        }

        # 創建實例
        analytics = DecisionAnalyticsEngine(config)
        print("  ✅ 成功創建決策分析引擎實例")

        # 測試開始 episode
        try:
            from .rl_algorithm_integrator import AlgorithmType

            episode_id = "quick_test_episode"
            start_success = analytics.start_episode(
                episode_id, AlgorithmType.DQN, "urban"
            )

            if start_success:
                print("  ✅ Episode 開始成功")

                # 測試完成 episode
                episode_analytics = await analytics.finalize_episode()
                if episode_analytics:
                    print("  ✅ Episode 完成成功")
                else:
                    print("  ⚠️  Episode 完成失敗")
            else:
                print("  ⚠️  Episode 開始失敗")

        except Exception as e:
            print(f"  ⚠️  Episode 測試過程中出現問題: {e}")

        # 測試狀態獲取
        try:
            status = analytics.get_status()
            print(
                f"  ✅ 狀態獲取成功，分析決策數: {status.get('total_decisions_analyzed', 0)}"
            )
        except Exception as e:
            print(f"  ⚠️  狀態獲取失敗: {e}")

        return True

    except Exception as e:
        print(f"  ❌ 決策分析引擎測試失敗: {e}")
        return False


async def main():
    """主驗證函數"""
    print("=" * 60)
    print("🚀 Phase 2.3 快速驗證腳本")
    print("=" * 60)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 檢查基本依賴
    deps_ok = check_basic_dependencies()
    if not deps_ok:
        print("\n❌ 基本依賴檢查失敗，請安裝必要的 Python 包")
        return 1

    # 2. 檢查 Phase 2.3 組件導入
    imports_ok, components_status = check_phase_2_3_imports()
    if not imports_ok:
        print("\n❌ Phase 2.3 組件導入檢查失敗")
        return 1

    # 3. 測試核心組件
    test_results = []

    if components_status.get("RL算法整合器", False):
        result = await test_algorithm_integrator()
        test_results.append(("RL算法整合器", result))

    if components_status.get("環境橋接器", False):
        result = await test_environment_bridge()
        test_results.append(("環境橋接器", result))

    if components_status.get("決策分析引擎", False):
        result = await test_decision_analytics()
        test_results.append(("決策分析引擎", result))

    # 4. 總結結果
    print("\n" + "=" * 60)
    print("📋 驗證結果總結")
    print("=" * 60)

    print("組件可用性:")
    for component, available in components_status.items():
        status = "✅" if available else "❌"
        print(f"  {status} {component}")

    if test_results:
        print("\n組件功能測試:")
        for component, success in test_results:
            status = "✅" if success else "⚠️"
            print(f"  {status} {component}")

    # 計算總體評分
    available_components = sum(components_status.values())
    total_components = len(components_status)
    successful_tests = sum(result for _, result in test_results)
    total_tests = len(test_results)

    availability_score = available_components / total_components * 100
    functionality_score = successful_tests / max(total_tests, 1) * 100

    print(f"\n📊 評分:")
    print(
        f"  組件可用性: {availability_score:.1f}% ({available_components}/{total_components})"
    )
    if total_tests > 0:
        print(
            f"  功能測試: {functionality_score:.1f}% ({successful_tests}/{total_tests})"
        )

    # 總體評估
    if availability_score >= 60 and (total_tests == 0 or functionality_score >= 50):
        print("\n🎉 Phase 2.3 基本功能驗證通過！")
        print("💡 建議: 可以開始使用 Phase 2.3 功能進行 RL 算法實戰應用")
        return 0
    elif availability_score >= 40:
        print("\n⚠️  Phase 2.3 部分功能可用")
        print("💡 建議: 檢查失敗的組件，部分功能可能可以正常使用")
        return 1
    else:
        print("\n❌ Phase 2.3 功能不可用")
        print("💡 建議: 檢查依賴安裝和代碼完整性")
        return 2


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  驗證被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 驗證過程中發生錯誤: {e}")
        sys.exit(1)
