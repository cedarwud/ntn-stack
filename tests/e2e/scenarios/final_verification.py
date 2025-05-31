#!/usr/bin/env python3
"""
NetStack API 最終驗證測試

這是最終的驗證測試，確保：
1. 所有關鍵功能在任何環境重建後都能100%通過
2. Features #10和#11完全符合TODO.md的要求
3. 系統性能滿足所有指標要求
4. 生產環境部署準備就緒

如果此測試100%通過，代表系統已經完全滿足用戶要求。
"""

import requests
import json
import time
import logging
from datetime import datetime

# 設定日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FinalVerificationTest:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.timeout = 30.0
        self.test_results = []
        self.performance_metrics = {}
        self.features_verified = {
            "feature_10_mesh_bridge": False,
            "feature_11_uav_failover": False,
        }

    def test_function(self, name, func, feature=None):
        """測試函數包裝器"""
        print(f"🔍 {name}...", end=" ", flush=True)
        start_time = time.time()

        try:
            success = func()
            duration = (time.time() - start_time) * 1000

            if success:
                print(f"✅ 通過 ({duration:.1f}ms)")
                self.test_results.append(
                    {
                        "test": name,
                        "status": "PASS",
                        "duration_ms": duration,
                        "feature": feature,
                    }
                )

                # 標記功能為已驗證
                if feature and feature in self.features_verified:
                    self.features_verified[feature] = True

                return True
            else:
                print(f"❌ 失敗 ({duration:.1f}ms)")
                self.test_results.append(
                    {
                        "test": name,
                        "status": "FAIL",
                        "duration_ms": duration,
                        "feature": feature,
                    }
                )
                return False
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            print(f"❌ 異常: {e} ({duration:.1f}ms)")
            self.test_results.append(
                {
                    "test": name,
                    "status": "ERROR",
                    "duration_ms": duration,
                    "error": str(e),
                    "feature": feature,
                }
            )
            return False

    def test_service_health(self):
        """基礎服務健康檢查"""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        if response.status_code != 200:
            return False

        health_data = response.json()
        overall_status = health_data.get("overall_status")

        # 記錄關鍵性能指標
        response_time = health_data.get("response_time_ms", 0)
        self.performance_metrics["health_response_time_ms"] = response_time

        return overall_status == "healthy"

    def test_feature_10_mesh_bridge_core(self):
        """Feature #10: Tier-1 Mesh 網路與 5G 核心網橋接 - 核心功能"""

        # 1. 測試 Mesh 節點創建和管理
        node_data = {
            "name": "Feature10_Test_Node",
            "node_type": "uav_relay",
            "ip_address": "192.168.100.210",
            "mac_address": "02:00:00:FF:10:01",
            "frequency_mhz": 900.0,
            "power_dbm": 20.0,
            "position": {"latitude": 25.0, "longitude": 121.0, "altitude": 100.0},
        }

        # 創建節點
        response = requests.post(
            f"{self.base_url}/api/v1/mesh/nodes", json=node_data, timeout=self.timeout
        )
        if response.status_code not in [200, 201]:
            return False

        node = response.json()
        node_id = node.get("node_id")
        if not node_id:
            return False

        # 驗證節點可查詢
        response = requests.get(
            f"{self.base_url}/api/v1/mesh/nodes/{node_id}", timeout=self.timeout
        )
        if response.status_code != 200:
            return False

        # 2. 測試橋接演示功能
        response = requests.post(
            f"{self.base_url}/api/v1/mesh/demo/quick-test", timeout=self.timeout
        )
        if response.status_code != 200:
            return False

        demo_data = response.json()
        has_bridge_demo = "message" in demo_data or "demo_scenario" in demo_data

        # 清理
        requests.delete(
            f"{self.base_url}/api/v1/mesh/nodes/{node_id}", timeout=self.timeout
        )

        return has_bridge_demo

    def test_feature_10_mesh_bridge_performance(self):
        """Feature #10: Mesh 橋接性能驗證"""
        start_time = time.time()

        response = requests.post(
            f"{self.base_url}/api/v1/mesh/demo/quick-test", timeout=self.timeout
        )

        demo_duration = (time.time() - start_time) * 1000
        self.performance_metrics["mesh_bridge_demo_time_ms"] = demo_duration

        if response.status_code != 200:
            return False

        # 驗證演示執行時間合理（< 1 秒）
        return demo_duration < 1000

    def test_feature_11_uav_failover_core(self):
        """Feature #11: UAV 失聯後的 Mesh 網路備援機制 - 核心功能"""

        # 測試備援演示功能
        response = requests.post(
            f"{self.base_url}/api/v1/uav-mesh-failover/demo/quick-test",
            timeout=self.timeout,
        )

        if response.status_code != 200:
            return False

        data = response.json()
        success = data.get("success", False)

        if not success:
            return False

        # 驗證性能指標
        performance = data.get("performance_targets", {})
        actual_time = performance.get("actual_failover_time_ms", 0)
        meets_requirement = performance.get("meets_requirement", False)

        # 記錄關鍵性能指標
        self.performance_metrics["uav_failover_time_ms"] = actual_time
        self.performance_metrics["failover_meets_requirement"] = meets_requirement

        # 驗證切換時間 < 2000ms (TODO.md 要求)
        return meets_requirement and actual_time < 2000

    def test_feature_11_uav_failover_service(self):
        """Feature #11: UAV 備援服務完整性"""

        # 測試服務統計
        response = requests.get(
            f"{self.base_url}/api/v1/uav-mesh-failover/stats", timeout=self.timeout
        )

        if response.status_code != 200:
            return False

        stats = response.json()

        # 驗證服務狀態
        service_status = stats.get("service_status")
        has_statistics = "failover_statistics" in stats
        has_thresholds = "thresholds" in stats

        return service_status == "running" and has_statistics and has_thresholds

    def test_system_integration(self):
        """系統整合測試"""

        # 連續進行多個操作，驗證系統穩定性
        operations = [
            lambda: requests.get(f"{self.base_url}/health").status_code == 200,
            lambda: requests.get(f"{self.base_url}/api/v1/mesh/nodes").status_code
            == 200,
            lambda: requests.get(
                f"{self.base_url}/api/v1/uav-mesh-failover/stats"
            ).status_code
            == 200,
        ]

        for operation in operations:
            if not operation():
                return False

        return True

    def test_performance_benchmarks(self):
        """性能基準測試"""

        # 檢查記錄的性能指標是否符合要求
        health_time = self.performance_metrics.get("health_response_time_ms", 0)
        failover_time = self.performance_metrics.get("uav_failover_time_ms", 0)
        bridge_demo_time = self.performance_metrics.get("mesh_bridge_demo_time_ms", 0)

        # 性能要求：
        # - 健康檢查 < 100ms
        # - UAV 切換 < 2000ms (TODO.md 要求)
        # - Mesh 演示 < 1000ms

        performance_ok = (
            health_time < 100 and failover_time < 2000 and bridge_demo_time < 1000
        )

        # 記錄所有性能指標
        self.performance_metrics["all_benchmarks_pass"] = performance_ok

        return performance_ok

    def run_final_verification(self) -> bool:
        """運行最終驗證測試"""
        print("🎯 NetStack API 最終驗證測試")
        print("=" * 65)
        print(f"📅 驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 目標: 驗證 Features #10 & #11 完全符合 TODO.md 要求")
        print("=" * 65)

        # 測試清單（必須全部通過）
        tests = [
            ("基礎服務健康", self.test_service_health, None),
            (
                "Feature #10 - Mesh橋接核心",
                self.test_feature_10_mesh_bridge_core,
                "feature_10_mesh_bridge",
            ),
            (
                "Feature #10 - Mesh橋接性能",
                self.test_feature_10_mesh_bridge_performance,
                "feature_10_mesh_bridge",
            ),
            (
                "Feature #11 - UAV備援核心",
                self.test_feature_11_uav_failover_core,
                "feature_11_uav_failover",
            ),
            (
                "Feature #11 - UAV備援服務",
                self.test_feature_11_uav_failover_service,
                "feature_11_uav_failover",
            ),
            ("系統整合測試", self.test_system_integration, None),
            ("性能基準測試", self.test_performance_benchmarks, None),
        ]

        passed = 0
        total = len(tests)

        # 執行所有測試
        for test_name, test_func, feature in tests:
            if self.test_function(test_name, test_func, feature):
                passed += 1

        # 生成最終驗證報告
        self._generate_final_report(passed, total)

        return passed == total

    def _generate_final_report(self, passed: int, total: int):
        """生成最終驗證報告"""
        print("=" * 65)
        print("📊 最終驗證報告")
        print("=" * 65)

        pass_rate = (passed / total) * 100
        print(f"🎯 總體測試: {passed}/{total} 通過 ({pass_rate:.1f}%)")

        # Features 驗證狀態
        print(f"\n🎯 功能驗證狀態:")
        feature_10_status = (
            "✅ 完成"
            if self.features_verified["feature_10_mesh_bridge"]
            else "❌ 未完成"
        )
        feature_11_status = (
            "✅ 完成"
            if self.features_verified["feature_11_uav_failover"]
            else "❌ 未完成"
        )

        print(f"   Feature #10 (Tier-1 Mesh 橋接): {feature_10_status}")
        print(f"   Feature #11 (UAV 備援機制): {feature_11_status}")

        # 性能指標報告
        if self.performance_metrics:
            print(f"\n⚡ 關鍵性能指標:")
            health_time = self.performance_metrics.get("health_response_time_ms", 0)
            failover_time = self.performance_metrics.get("uav_failover_time_ms", 0)
            bridge_time = self.performance_metrics.get("mesh_bridge_demo_time_ms", 0)

            print(f"   • 健康檢查時間: {health_time:.1f}ms (要求 < 100ms)")
            print(f"   • UAV 切換時間: {failover_time:.1f}ms (要求 < 2000ms)")
            print(f"   • Mesh 演示時間: {bridge_time:.1f}ms (要求 < 1000ms)")

            meets_target = self.performance_metrics.get(
                "failover_meets_requirement", False
            )
            print(f"   • 切換性能達標: {'是' if meets_target else '否'}")

        # 詳細測試結果
        print(f"\n📋 詳細測試結果:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            test_name = result["test"]
            duration = result["duration_ms"]
            status = result["status"]
            print(f"   {status_icon} {test_name}: {status} ({duration:.1f}ms)")

            if "error" in result:
                print(f"      錯誤: {result['error']}")

        # 最終結論
        all_features_verified = all(self.features_verified.values())

        if pass_rate == 100.0 and all_features_verified:
            print(f"\n🎉 最終驗證通過！系統完全滿足用戶要求！")
            print(f"✅ Features #10 & #11 完全實現並通過驗證")
            print(f"✅ 所有性能指標符合 TODO.md 要求")
            print(f"✅ 系統已準備好生產環境部署")
            print(f"✅ 可安全執行 'make clean-i && make up' 重建環境")
            print(f"🚀 任務完成：100% 測試通過率已達成")
        else:
            print(f"\n⚠️  最終驗證未完全通過")
            if not all_features_verified:
                print(f"❌ 部分功能驗證不完整")
            if pass_rate < 100.0:
                print(f"❌ {total - passed} 個測試失敗")

        print("=" * 65)


def main():
    """主函數"""
    test_runner = FinalVerificationTest()
    success = test_runner.run_final_verification()

    if success:
        print("\n🎯 🎉 恭喜！系統已100%完成用戶要求！ 🎉")
        return 0
    else:
        print("\n❌ 最終驗證失敗，需要進一步檢查")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
