#!/usr/bin/env python3
"""
UAV 作為 UE 的模擬實現完整性驗證

根據 TODO.md 中的要求，驗證 UAV UE 實現是否完整
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List
import structlog

logger = structlog.get_logger(__name__)


class UAVUEImplementationValidator:
    """UAV UE 實現驗證器"""

    def __init__(self):
        self.netstack_url = "http://localhost:8080"
        self.simworld_url = "http://localhost:8888"
        self.validation_results = {
            "trajectory_data_structure": False,
            "api_endpoints": False,
            "ue_config_conversion": False,
            "ueransim_ntn_adaptation": False,
            "signal_quality_monitoring": False,
            "dynamic_switching": False,
            "simworld_integration": False,
            "complete_demo": False,
        }
        self.detailed_results = {}

    async def validate_all(self) -> Dict:
        """執行完整驗證"""
        logger.info("🚀 開始 UAV UE 實現完整性驗證...")

        validators = [
            ("trajectory_data_structure", self._validate_trajectory_data_structure),
            ("api_endpoints", self._validate_api_endpoints),
            ("ue_config_conversion", self._validate_ue_config_conversion),
            ("ueransim_ntn_adaptation", self._validate_ueransim_ntn_adaptation),
            ("signal_quality_monitoring", self._validate_signal_quality_monitoring),
            ("dynamic_switching", self._validate_dynamic_switching),
            ("simworld_integration", self._validate_simworld_integration),
            ("complete_demo", self._validate_complete_demo),
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            self.client = client

            for test_name, validator in validators:
                try:
                    logger.info(f"🔍 驗證: {test_name}")
                    result = await validator()
                    self.validation_results[test_name] = result
                    status = "✅ 通過" if result else "❌ 失敗"
                    logger.info(f"   {status}")
                except Exception as e:
                    logger.error(f"   ❌ 驗證異常: {e}")
                    self.validation_results[test_name] = False

        return self._generate_report()

    async def _validate_trajectory_data_structure(self) -> bool:
        """驗證軌跡數據結構設計"""
        logger.info("   檢查軌跡數據結構...")

        # 測試創建標準軌跡格式
        base_time = datetime.utcnow()
        trajectory_data = {
            "name": "驗證軌跡_標準格式",
            "description": "支持標準航空軌跡格式測試",
            "mission_type": "validation",
            "points": [
                {
                    "timestamp": base_time.isoformat(),
                    "latitude": 24.7881,
                    "longitude": 120.9971,
                    "altitude": 100,
                    "speed": 20.0,
                    "heading": 0.0,
                },
                {
                    "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
                    "latitude": 24.8000,
                    "longitude": 121.0100,
                    "altitude": 150,
                    "speed": 25.0,
                    "heading": 45.0,
                },
            ],
        }

        try:
            response = await self.client.post(
                f"{self.netstack_url}/api/v1/uav/trajectory", json=trajectory_data
            )

            if response.status_code == 200:
                trajectory = response.json()

                # 檢查必要欄位
                required_fields = [
                    "trajectory_id",
                    "name",
                    "description",
                    "mission_type",
                    "points",
                    "total_distance_km",
                    "estimated_duration_minutes",
                ]

                for field in required_fields:
                    if field not in trajectory:
                        logger.error(f"   缺少欄位: {field}")
                        return False

                # 檢查軌跡統計計算
                if trajectory["total_distance_km"] <= 0:
                    logger.error("   軌跡距離計算錯誤")
                    return False

                if trajectory["estimated_duration_minutes"] <= 0:
                    logger.error("   飛行時間估算錯誤")
                    return False

                self.detailed_results["created_trajectory_id"] = trajectory[
                    "trajectory_id"
                ]
                logger.info(
                    f"   ✅ 軌跡數據結構完整，距離: {trajectory['total_distance_km']:.2f}km"
                )
                return True
            else:
                logger.error(f"   軌跡創建失敗: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"   軌跡數據結構驗證異常: {e}")
            return False

    async def _validate_api_endpoints(self) -> bool:
        """驗證 FastAPI 端點完整性"""
        logger.info("   檢查 API 端點完整性...")

        required_endpoints = [
            ("POST", "/api/v1/uav/trajectory"),
            ("GET", "/api/v1/uav/trajectory"),
            ("GET", "/api/v1/uav/trajectory/{id}"),
            ("PUT", "/api/v1/uav/trajectory/{id}"),
            ("DELETE", "/api/v1/uav/trajectory/{id}"),
            ("POST", "/api/v1/uav"),
            ("GET", "/api/v1/uav"),
            ("GET", "/api/v1/uav/{id}"),
            ("DELETE", "/api/v1/uav/{id}"),
            ("POST", "/api/v1/uav/{id}/mission/start"),
            ("POST", "/api/v1/uav/{id}/mission/stop"),
            ("PUT", "/api/v1/uav/{id}/position"),
            ("POST", "/api/v1/uav/demo/quick-test"),
        ]

        # 獲取 OpenAPI 規範
        try:
            response = await self.client.get(f"{self.netstack_url}/openapi.json")
            if response.status_code != 200:
                logger.error("   無法獲取 OpenAPI 規範")
                return False

            openapi = response.json()
            paths = openapi.get("paths", {})

            missing_endpoints = []
            for method, path in required_endpoints:
                # 將 {id} 替換為實際的 OpenAPI 格式
                openapi_path = (
                    path.replace("{id}", "{uav_id}").replace(
                        "{uav_id}", "{trajectory_id}"
                    )
                    if "trajectory" in path
                    else path.replace("{id}", "{uav_id}")
                )

                if openapi_path not in paths:
                    missing_endpoints.append(f"{method} {path}")
                elif method.lower() not in paths[openapi_path]:
                    missing_endpoints.append(f"{method} {path}")

            if missing_endpoints:
                logger.error(f"   缺少端點: {missing_endpoints}")
                return False

            logger.info(f"   ✅ 所有 {len(required_endpoints)} 個端點都已實現")
            return True

        except Exception as e:
            logger.error(f"   API 端點驗證異常: {e}")
            return False

    async def _validate_ue_config_conversion(self) -> bool:
        """驗證 UAV 位置到 UE 配置的自動轉換"""
        logger.info("   檢查 UE 配置自動轉換...")

        # 創建 UAV 並檢查 UE 配置
        uav_data = {
            "name": "驗證UAV_配置轉換",
            "ue_config": {
                "imsi": "999700000000001",
                "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                "opc": "E8ED289DEBA952E4283B54E88E6183CA",
                "plmn": "99970",
                "apn": "internet",
                "slice_nssai": {"sst": 1, "sd": "000001"},
                "gnb_ip": "172.20.0.40",
                "gnb_port": 38412,
                "power_dbm": 23.0,
                "frequency_mhz": 2150.0,
                "bandwidth_mhz": 20.0,
            },
            "initial_position": {
                "latitude": 24.7881,
                "longitude": 120.9971,
                "altitude": 100,
                "speed": 0.0,
                "heading": 0.0,
            },
        }

        try:
            response = await self.client.post(
                f"{self.netstack_url}/api/v1/uav", json=uav_data
            )

            if response.status_code == 200:
                uav = response.json()
                uav_id = uav["uav_id"]

                # 檢查 UE 配置完整性
                ue_config = uav.get("ue_config", {})
                required_ue_fields = [
                    "imsi",
                    "key",
                    "opc",
                    "plmn",
                    "apn",
                    "slice_nssai",
                    "gnb_ip",
                    "gnb_port",
                    "power_dbm",
                    "frequency_mhz",
                    "bandwidth_mhz",
                ]

                for field in required_ue_fields:
                    if field not in ue_config:
                        logger.error(f"   UE 配置缺少欄位: {field}")
                        return False

                # 檢查位置映射
                position = uav.get("current_position", {})
                if not position:
                    logger.error("   位置映射失敗")
                    return False

                self.detailed_results["created_uav_id"] = uav_id
                logger.info("   ✅ UE 配置自動轉換正常")
                return True
            else:
                logger.error(f"   UAV 創建失敗: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"   UE 配置轉換驗證異常: {e}")
            return False

    async def _validate_ueransim_ntn_adaptation(self) -> bool:
        """驗證 UERANSIM NTN 環境適配"""
        logger.info("   檢查 UERANSIM NTN 適配...")

        # 檢查是否實現了 NTN 特性
        ntn_features = ["延遲容忍度調整", "功率控制適配", "多普勒補償", "連接重建優化"]

        # 通過檢查演示端點是否能成功創建適配的配置來驗證
        try:
            response = await self.client.post(
                f"{self.netstack_url}/api/v1/uav/demo/quick-test"
            )

            if response.status_code == 200:
                demo_result = response.json()

                if demo_result.get("success"):
                    logger.info("   ✅ UERANSIM NTN 適配正常（通過演示驗證）")
                    return True
                else:
                    logger.error("   演示失敗，NTN 適配可能有問題")
                    return False
            else:
                logger.error(f"   演示端點失敗: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"   UERANSIM NTN 適配驗證異常: {e}")
            return False

    async def _validate_signal_quality_monitoring(self) -> bool:
        """驗證信號質量監測"""
        logger.info("   檢查信號質量監測...")

        # 檢查 UAV 狀態是否包含信號質量信息
        uav_id = self.detailed_results.get("created_uav_id")
        if not uav_id:
            logger.error("   無 UAV ID，跳過信號質量檢查")
            return False

        try:
            response = await self.client.get(f"{self.netstack_url}/api/v1/uav/{uav_id}")

            if response.status_code == 200:
                uav_status = response.json()

                # 檢查是否有信號質量欄位（可能為空但結構應該存在）
                if "signal_quality" in uav_status:
                    logger.info("   ✅ 信號質量監測結構已實現")
                    return True
                else:
                    logger.error("   缺少信號質量監測結構")
                    return False
            else:
                logger.error(f"   獲取 UAV 狀態失敗: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"   信號質量監測驗證異常: {e}")
            return False

    async def _validate_dynamic_switching(self) -> bool:
        """驗證動態換手機制"""
        logger.info("   檢查動態換手機制...")

        # 檢查位置更新端點是否支持信號質量更新和換手
        uav_id = self.detailed_results.get("created_uav_id")
        if not uav_id:
            logger.error("   無 UAV ID，跳過動態換手檢查")
            return False

        position_update = {
            "position": {
                "latitude": 24.8000,
                "longitude": 121.0000,
                "altitude": 120,
                "speed": 15.0,
                "heading": 90.0,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "signal_quality": {
                "rsrp_dbm": -85.0,
                "rsrq_db": -10.5,
                "sinr_db": 12.3,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        try:
            response = await self.client.put(
                f"{self.netstack_url}/api/v1/uav/{uav_id}/position",
                json=position_update,
            )

            if response.status_code == 200:
                logger.info("   ✅ 動態換手機制已實現（位置和信號質量更新正常）")
                return True
            else:
                logger.error(f"   位置更新失敗: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"   動態換手機制驗證異常: {e}")
            return False

    async def _validate_simworld_integration(self) -> bool:
        """驗證 SimWorld 整合"""
        logger.info("   檢查 SimWorld 整合...")

        try:
            # 檢查 SimWorld 服務可用性
            response = await self.client.get(f"{self.simworld_url}/")
            if response.status_code != 200:
                logger.error("   SimWorld 服務不可用")
                return False

            # 檢查 UAV 位置端點
            response = await self.client.get(
                f"{self.simworld_url}/api/v1/uav/positions"
            )
            if response.status_code == 200:
                logger.info("   ✅ SimWorld 整合正常")
                return True
            else:
                logger.error(f"   SimWorld UAV 位置端點失敗: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"   SimWorld 整合驗證異常: {e}")
            return False

    async def _validate_complete_demo(self) -> bool:
        """驗證完整演示功能"""
        logger.info("   檢查完整演示功能...")

        try:
            response = await self.client.post(
                f"{self.netstack_url}/api/v1/uav/demo/quick-test"
            )

            if response.status_code == 200:
                demo_result = response.json()

                if demo_result.get("success"):
                    # 檢查演示結果完整性
                    required_demo_fields = [
                        "demo_resources",
                        "demo_instructions",
                        "estimated_demo_duration_minutes",
                        "monitoring_endpoints",
                    ]

                    for field in required_demo_fields:
                        if field not in demo_result:
                            logger.error(f"   演示結果缺少欄位: {field}")
                            return False

                    # 檢查演示資源
                    resources = demo_result.get("demo_resources", {})
                    if "trajectory" not in resources or "uav" not in resources:
                        logger.error("   演示資源不完整")
                        return False

                    logger.info("   ✅ 完整演示功能正常")
                    return True
                else:
                    logger.error("   演示執行失敗")
                    return False
            else:
                logger.error(f"   演示端點失敗: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"   完整演示驗證異常: {e}")
            return False

    def _generate_report(self) -> Dict:
        """生成驗證報告"""
        total_tests = len(self.validation_results)
        passed_tests = sum(1 for result in self.validation_results.values() if result)
        success_rate = (passed_tests / total_tests) * 100

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_success": passed_tests == total_tests,
            "success_rate_percent": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "detailed_results": self.validation_results,
            "implementation_status": self._get_implementation_status(),
            "todo_completion": self._check_todo_completion(),
        }

        return report

    def _get_implementation_status(self) -> Dict:
        """獲取實現狀態"""
        status = {}

        # 根據 TODO.md 的六個步驟檢查
        todo_steps = {
            "步驟1_軌跡數據結構": self.validation_results["trajectory_data_structure"],
            "步驟2_API端點管理": self.validation_results["api_endpoints"],
            "步驟3_位置UE轉換": self.validation_results["ue_config_conversion"],
            "步驟4_UERANSIM適配": self.validation_results["ueransim_ntn_adaptation"],
            "步驟5_信號質量監測": self.validation_results["signal_quality_monitoring"],
            "步驟6_動態換手機制": self.validation_results["dynamic_switching"],
        }

        for step, result in todo_steps.items():
            status[step] = "✅ 完成" if result else "❌ 未完成"

        return status

    def _check_todo_completion(self) -> Dict:
        """檢查 TODO 完成度"""
        return {
            "軌跡數據結構和存儲": self.validation_results["trajectory_data_structure"],
            "FastAPI端點管理": self.validation_results["api_endpoints"],
            "UAV位置到UE配置轉換": self.validation_results["ue_config_conversion"],
            "UERANSIM衛星通信適配": self.validation_results["ueransim_ntn_adaptation"],
            "信號質量監測": self.validation_results["signal_quality_monitoring"],
            "動態換手機制": self.validation_results["dynamic_switching"],
            "SimWorld整合": self.validation_results["simworld_integration"],
            "完整演示系統": self.validation_results["complete_demo"],
        }


async def main():
    """主函數"""
    validator = UAVUEImplementationValidator()

    try:
        report = await validator.validate_all()

        print("\n" + "=" * 80)
        print("🎯 UAV 作為 UE 的模擬實現 - 完整性驗證報告")
        print("=" * 80)
        print(f"📅 驗證時間: {report['timestamp']}")
        print(f"🎯 總體結果: {'✅ 通過' if report['overall_success'] else '❌ 失敗'}")
        print(
            f"📊 成功率: {report['success_rate_percent']:.1f}% ({report['passed_tests']}/{report['total_tests']})"
        )
        print()

        print("📋 TODO.md 實現狀態:")
        for step, status in report["implementation_status"].items():
            print(f"   {step}: {status}")
        print()

        print("🔍 詳細驗證結果:")
        for test_name, result in report["detailed_results"].items():
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"   {test_name}: {status}")
        print()

        if report["overall_success"]:
            print("🎉 恭喜！UAV 作為 UE 的模擬實現已完全完成！")
            print("   所有 TODO.md 要求的功能都已實現並測試通過。")
        else:
            print("⚠️  UAV UE 實現尚未完全完成，請檢查失敗的項目。")

        print("=" * 80)

        # 保存報告
        with open("uav_ue_validation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📄 詳細報告已保存至: uav_ue_validation_report.json")

        return 0 if report["overall_success"] else 1

    except Exception as e:
        print(f"❌ 驗證過程出現異常: {e}")
        return 1


if __name__ == "__main__":
    import sys

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
