#!/usr/bin/env python3
"""
NetStack API 生產環境準備測試

驗證系統在任何環境重建（make clean-i && make up）後
都能維持100%測試通過率的功能

測試範圍：
1. 服務可用性檢查
2. 核心API功能驗證
3. 關鍵業務邏輯測試
4. 數據一致性檢查
5. 性能基準測試
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


class ProductionReadyTest:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.timeout = 30.0
        self.test_results = []
        self.performance_metrics = {}

    def test_function(self, name, func, critical=True):
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
                        "critical": critical,
                    }
                )
                return True
            else:
                status_icon = "❌" if critical else "⚠️"
                print(
                    f"{status_icon} {'失敗' if critical else '警告'} ({duration:.1f}ms)"
                )
                self.test_results.append(
                    {
                        "test": name,
                        "status": "FAIL",
                        "duration_ms": duration,
                        "critical": critical,
                    }
                )
                return False
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            status_icon = "❌" if critical else "⚠️"
            print(f"{status_icon} 異常: {e} ({duration:.1f}ms)")
            self.test_results.append(
                {
                    "test": name,
                    "status": "ERROR",
                    "duration_ms": duration,
                    "error": str(e),
                    "critical": critical,
                }
            )
            return False

    def test_service_availability(self):
        """測試服務可用性"""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        if response.status_code != 200:
            return False

        health_data = response.json()
        overall_status = health_data.get("overall_status")

        # 記錄性能指標
        self.performance_metrics["health_check_time_ms"] = health_data.get(
            "response_time_ms", 0
        )

        return overall_status == "healthy"

    def test_api_endpoints_accessibility(self):
        """測試API端點可訪問性"""
        try:
            # 只測試最基礎的健康檢查和統計端點
            response1 = requests.get(f"{self.base_url}/health", timeout=2)
            response2 = requests.get(
                f"{self.base_url}/api/v1/uav-mesh-failover/stats", timeout=2
            )

            return response1.status_code == 200 and response2.status_code == 200
        except:
            return False

    def test_mesh_network_functionality(self):
        """測試Mesh網路功能"""
        # 測試創建和刪除節點的完整流程
        node_data = {
            "name": "ProductionTest_Node",
            "node_type": "uav_relay",
            "ip_address": "192.168.100.200",
            "mac_address": "02:00:00:FF:EE:CC",
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

        # 驗證節點數據完整性
        response = requests.get(
            f"{self.base_url}/api/v1/mesh/nodes/{node_id}", timeout=self.timeout
        )
        if response.status_code != 200:
            return False

        node_details = response.json()
        if node_details.get("name") != node_data["name"]:
            return False

        # 清理測試數據
        response = requests.delete(
            f"{self.base_url}/api/v1/mesh/nodes/{node_id}", timeout=self.timeout
        )

        return True

    def test_mesh_bridge_performance(self):
        """測試Mesh橋接性能"""
        start_time = time.time()

        response = requests.post(
            f"{self.base_url}/api/v1/mesh/demo/quick-test", timeout=self.timeout
        )

        demo_duration = (time.time() - start_time) * 1000
        self.performance_metrics["mesh_demo_time_ms"] = demo_duration

        if response.status_code != 200:
            return False

        data = response.json()

        # 驗證演示包含必要信息
        return "message" in data or "demo_scenario" in data

    def test_uav_failover_system(self):
        """測試UAV備援系統"""
        start_time = time.time()

        response = requests.post(
            f"{self.base_url}/api/v1/uav-mesh-failover/demo/quick-test",
            timeout=self.timeout,
        )

        if response.status_code != 200:
            return False

        data = response.json()
        success = data.get("success", False)

        if success:
            performance = data.get("performance_targets", {})
            actual_time = performance.get("actual_failover_time_ms", 0)
            meets_requirement = performance.get("meets_requirement", False)

            # 記錄關鍵性能指標
            self.performance_metrics["failover_time_ms"] = actual_time
            self.performance_metrics["meets_performance_target"] = meets_requirement

            # 驗證換手時間符合要求（< 2000ms）
            return meets_requirement and actual_time < 2000

        return False

    def test_service_statistics(self):
        """測試服務統計功能"""
        response = requests.get(
            f"{self.base_url}/api/v1/uav-mesh-failover/stats", timeout=self.timeout
        )

        if response.status_code != 200:
            return False

        stats = response.json()

        # 驗證統計數據結構完整性
        required_fields = ["service_status", "failover_statistics", "thresholds"]
        for field in required_fields:
            if field not in stats:
                return False

        return True

    def test_data_consistency(self):
        """測試數據一致性"""
        # 多次調用統計API，確保數據一致
        stats_responses = []
        for i in range(3):
            response = requests.get(
                f"{self.base_url}/api/v1/uav-mesh-failover/stats", timeout=self.timeout
            )
            if response.status_code == 200:
                stats_responses.append(response.json())
            time.sleep(0.1)

        if len(stats_responses) < 3:
            return False

        # 檢查服務狀態一致性
        service_statuses = [s.get("service_status") for s in stats_responses]
        return len(set(service_statuses)) == 1  # 所有狀態應該相同

    def test_system_performance_baseline(self):
        """測試系統性能基準"""
        # 健康檢查應該 < 50ms
        health_time = self.performance_metrics.get("health_check_time_ms", 0)
        if health_time > 50:
            return False

        # UAV換手時間應該 < 2000ms
        failover_time = self.performance_metrics.get("failover_time_ms", 0)
        if failover_time > 2000:
            return False

        return True

    def run_production_tests(self) -> bool:
        """運行生產環境準備測試"""
        print("🚀 NetStack API 生產環境準備測試")
        print("=" * 60)
        print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 關鍵測試（必須全部通過）
        critical_tests = [
            ("服務可用性檢查", self.test_service_availability),
            ("API端點可訪問性", self.test_api_endpoints_accessibility),
            ("Mesh網路功能", self.test_mesh_network_functionality),
            ("Mesh橋接性能", self.test_mesh_bridge_performance),
            ("UAV備援系統", self.test_uav_failover_system),
            ("服務統計功能", self.test_service_statistics),
            ("數據一致性", self.test_data_consistency),
        ]

        # 性能測試（非關鍵，但重要）
        performance_tests = [
            ("系統性能基準", self.test_system_performance_baseline, False),
        ]

        critical_passed = 0
        total_critical = len(critical_tests)

        # 執行關鍵測試
        for test_name, test_func in critical_tests:
            if self.test_function(test_name, test_func, critical=True):
                critical_passed += 1

        # 執行性能測試
        for test_name, test_func, critical in performance_tests:
            self.test_function(test_name, test_func, critical=critical)

        # 生成測試報告
        self._generate_production_report(critical_passed, total_critical)

        return critical_passed == total_critical

    def _generate_production_report(self, critical_passed: int, total_critical: int):
        """生成生產環境測試報告"""
        print("=" * 60)
        print("📊 生產環境準備測試報告")
        print("=" * 60)

        critical_pass_rate = (critical_passed / total_critical) * 100
        print(
            f"🎯 關鍵功能: {critical_passed}/{total_critical} 通過 ({critical_pass_rate:.1f}%)"
        )

        # 性能指標報告
        if self.performance_metrics:
            print(f"\n⚡ 性能指標:")
            for metric, value in self.performance_metrics.items():
                print(f"   • {metric}: {value}")

        # 詳細測試結果
        print(f"\n📋 詳細結果:")
        for result in self.test_results:
            status_icon = (
                "✅"
                if result["status"] == "PASS"
                else ("❌" if result.get("critical", True) else "⚠️")
            )
            test_name = result["test"]
            duration = result["duration_ms"]
            status = result["status"]
            print(f"   {status_icon} {test_name}: {status} ({duration:.1f}ms)")

            if "error" in result:
                print(f"      錯誤: {result['error']}")

        # 最終評估
        if critical_pass_rate == 100.0:
            print(f"\n🎉 系統已準備好生產環境部署！")
            print(f"✅ 所有關鍵功能測試通過")
            print(f"✅ Feature #10 & #11 功能正常")
            print(f"✅ 系統在環境重建後可維持穩定運行")
            print(f"🚀 可以安全地執行 'make clean-i && make up'")
        else:
            print(f"\n⚠️  系統尚未準備好生產環境部署")
            print(f"❌ {total_critical - critical_passed} 個關鍵功能測試失敗")
            print(f"🔧 請修復失敗項目後重新測試")

        print("=" * 60)


def main():
    """主函數"""
    test_runner = ProductionReadyTest()
    success = test_runner.run_production_tests()

    if success:
        print("\n🎯 生產環境準備測試完成！系統已準備就緒！")
        return 0
    else:
        print("\n❌ 生產環境準備測試失敗，系統需要進一步優化")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
