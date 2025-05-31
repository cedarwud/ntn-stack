#!/usr/bin/env python3
"""
UAV-衛星連接質量評估系統測試

測試連接質量監控、評估和異常檢測功能
"""

import asyncio
import logging
import httpx
import json
import time
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)


class UAVSatelliteConnectionQualityTest:
    """UAV 衛星連接質量評估系統測試"""

    def __init__(self):
        self.netstack_url = "http://localhost:8080"
        self.test_results = {}

    async def run_all_tests(self) -> Dict:
        """執行所有測試"""
        logger.info("🚀 開始 UAV-衛星連接質量評估系統測試...")

        test_methods = [
            ("test_connection_quality_overview", self._test_overview),
            ("test_quality_thresholds", self._test_thresholds),
            ("test_uav_creation_and_monitoring", self._test_uav_monitoring),
            ("test_signal_quality_update", self._test_signal_update),
            ("test_quality_assessment", self._test_quality_assessment),
            ("test_quality_history", self._test_quality_history),
            ("test_anomaly_detection", self._test_anomaly_detection),
            ("test_quality_trends", self._test_quality_trends),
            ("test_comprehensive_scenario", self._test_comprehensive_scenario),
        ]

        async with httpx.AsyncClient(timeout=60.0) as client:
            self.client = client

            for test_name, test_method in test_methods:
                try:
                    logger.info(f"🔍 執行測試: {test_name}")
                    result = await test_method()
                    self.test_results[test_name] = {
                        "status": "PASSED" if result else "FAILED",
                        "details": result,
                    }
                    status = "✅ 通過" if result else "❌ 失敗"
                    logger.info(f"   {status}")
                except Exception as e:
                    logger.error(f"   ❌ 測試異常: {e}")
                    self.test_results[test_name] = {"status": "ERROR", "error": str(e)}

        return self._generate_test_report()

    async def _test_overview(self) -> bool:
        """測試連接質量系統概覽"""
        try:
            response = await self.client.get(
                f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/overview"
            )

            if response.status_code != 200:
                logger.error(f"概覽端點失敗: {response.status_code}")
                return False

            overview = response.json()

            required_fields = [
                "system_status",
                "monitored_uav_count",
                "assessment_capabilities",
                "supported_metrics",
                "evaluation_grades",
            ]

            for field in required_fields:
                if field not in overview:
                    logger.error(f"概覽缺少欄位: {field}")
                    return False

            # 檢查評估能力
            capabilities = overview["assessment_capabilities"]
            expected_capabilities = [
                "signal_quality_assessment",
                "performance_assessment",
                "stability_assessment",
                "ntn_adaptation_assessment",
                "anomaly_detection",
                "trend_analysis",
                "predictive_analysis",
            ]

            for capability in expected_capabilities:
                if not capabilities.get(capability, False):
                    logger.error(f"缺少評估能力: {capability}")
                    return False

            logger.info("✅ 系統概覽正常")
            return True

        except Exception as e:
            logger.error(f"概覽測試失敗: {e}")
            return False

    async def _test_thresholds(self) -> bool:
        """測試質量評估閾值管理"""
        try:
            # 獲取默認閾值
            response = await self.client.get(
                f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/thresholds"
            )

            if response.status_code != 200:
                logger.error(f"獲取閾值失敗: {response.status_code}")
                return False

            default_thresholds = response.json()

            # 檢查默認閾值結構
            required_threshold_fields = [
                "sinr_excellent_db",
                "sinr_good_db",
                "sinr_poor_db",
                "rsrp_excellent_dbm",
                "rsrp_good_dbm",
                "rsrp_poor_dbm",
                "throughput_excellent_mbps",
                "throughput_good_mbps",
                "throughput_poor_mbps",
                "signal_weight",
                "performance_weight",
                "stability_weight",
            ]

            for field in required_threshold_fields:
                if field not in default_thresholds:
                    logger.error(f"閾值缺少欄位: {field}")
                    return False

            # 測試更新閾值
            updated_thresholds = default_thresholds.copy()
            updated_thresholds["sinr_excellent_db"] = 20.0  # 修改一個值

            response = await self.client.put(
                f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/thresholds",
                json=updated_thresholds,
            )

            if response.status_code != 200:
                logger.error(f"更新閾值失敗: {response.status_code}")
                return False

            update_result = response.json()
            if not update_result.get("success", False):
                logger.error("閾值更新未成功")
                return False

            logger.info("✅ 閾值管理正常")
            return True

        except Exception as e:
            logger.error(f"閾值測試失敗: {e}")
            return False

    async def _test_uav_monitoring(self) -> bool:
        """測試 UAV 創建和監控功能"""
        try:
            # 創建測試 UAV
            uav_data = {
                "name": "測試UAV_連接質量評估",
                "ue_config": {
                    "imsi": "999700000000101",
                    "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                    "opc": "E8ED289DEBA952E4283B54E88E6183CA",
                    "plmn": "99970",
                    "apn": "internet",
                    "slice_nssai": {"sst": 1, "sd": "000001"},
                    "gnb_ip": "172.20.0.40",
                    "gnb_port": 38412,
                },
                "initial_position": {
                    "latitude": 24.7881,
                    "longitude": 120.9971,
                    "altitude": 200,
                    "speed": 0.0,
                    "heading": 0.0,
                },
            }

            response = await self.client.post(
                f"{self.netstack_url}/api/v1/uav", json=uav_data
            )

            if response.status_code != 200:
                logger.error(f"UAV 創建失敗: {response.status_code}")
                return False

            uav = response.json()
            self.test_uav_id = uav["uav_id"]

            # 開始連接質量監控
            response = await self.client.post(
                f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/start-monitoring/{self.test_uav_id}",
                params={"assessment_interval": 10},
            )

            if response.status_code != 200:
                logger.error(f"開始監控失敗: {response.status_code}")
                return False

            monitoring_result = response.json()
            if not monitoring_result.get("success", False):
                logger.error("監控啟動未成功")
                return False

            # 檢查監控端點
            endpoints = monitoring_result.get("monitoring_endpoints", {})
            required_endpoints = ["current_quality", "quality_history", "anomalies"]

            for endpoint in required_endpoints:
                if endpoint not in endpoints:
                    logger.error(f"缺少監控端點: {endpoint}")
                    return False

            logger.info("✅ UAV 監控功能正常")
            return True

        except Exception as e:
            logger.error(f"UAV 監控測試失敗: {e}")
            return False

    async def _test_signal_update(self) -> bool:
        """測試信號質量更新功能"""
        try:
            # 更新信號質量數據
            signal_quality = {
                "rsrp_dbm": -85.0,
                "rsrq_db": -10.5,
                "sinr_db": 12.3,
                "cqi": 8,
                "throughput_mbps": 25.5,
                "latency_ms": 45.0,
                "packet_loss_rate": 0.02,
                "jitter_ms": 5.0,
                "link_budget_margin_db": 15.0,
                "doppler_shift_hz": 500.0,
                "beam_alignment_score": 0.85,
                "interference_level_db": -95.0,
                "measurement_confidence": 0.9,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            response = await self.client.post(
                f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/{self.test_uav_id}/update-signal",
                json=signal_quality,
            )

            if response.status_code != 200:
                logger.error(f"信號質量更新失敗: {response.status_code}")
                return False

            quality_metrics = response.json()

            # 檢查質量指標結構
            required_metrics = [
                "sinr_db",
                "rsrp_dbm",
                "rsrq_db",
                "cqi",
                "throughput_mbps",
                "latency_ms",
                "packet_loss_rate",
                "data_freshness_score",
            ]

            for metric in required_metrics:
                if metric not in quality_metrics:
                    logger.error(f"質量指標缺少欄位: {metric}")
                    return False

            # 檢查數據新鮮度評分
            if quality_metrics["data_freshness_score"] < 0.8:
                logger.warning("數據新鮮度評分較低")

            logger.info("✅ 信號質量更新功能正常")
            return True

        except Exception as e:
            logger.error(f"信號質量更新測試失敗: {e}")
            return False

    async def _test_quality_assessment(self) -> bool:
        """測試連接質量評估功能"""
        try:
            # 等待一段時間讓數據累積
            await asyncio.sleep(2)

            response = await self.client.get(
                f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/{self.test_uav_id}",
                params={"time_window_minutes": 1},
            )

            if response.status_code != 200:
                logger.error(f"質量評估失敗: {response.status_code}")
                return False

            assessment = response.json()

            # 檢查評估結果結構
            required_assessment_fields = [
                "overall_quality_score",
                "quality_grade",
                "signal_quality_score",
                "performance_score",
                "stability_score",
                "ntn_adaptation_score",
                "identified_issues",
                "recommendations",
                "confidence_level",
            ]

            for field in required_assessment_fields:
                if field not in assessment:
                    logger.error(f"評估結果缺少欄位: {field}")
                    return False

            # 檢查評分範圍
            score_fields = [
                "overall_quality_score",
                "signal_quality_score",
                "performance_score",
                "stability_score",
                "ntn_adaptation_score",
            ]

            for field in score_fields:
                score = assessment[field]
                if not (0 <= score <= 100):
                    logger.error(f"評分超出範圍 [0-100]: {field} = {score}")
                    return False

            # 檢查質量等級
            valid_grades = ["優秀", "良好", "一般", "差"]
            if assessment["quality_grade"] not in valid_grades:
                logger.error(f"無效的質量等級: {assessment['quality_grade']}")
                return False

            logger.info(
                f"✅ 質量評估功能正常 - 評分: {assessment['overall_quality_score']:.1f}, "
                f"等級: {assessment['quality_grade']}"
            )
            return True

        except Exception as e:
            logger.error(f"質量評估測試失敗: {e}")
            return False

    async def _test_quality_history(self) -> bool:
        """測試連接質量歷史功能"""
        try:
            response = await self.client.get(
                f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/{self.test_uav_id}/history",
                params={"hours": 1},
            )

            if response.status_code != 200:
                logger.error(f"質量歷史查詢失敗: {response.status_code}")
                return False

            history = response.json()

            # 檢查歷史數據結構
            required_history_fields = [
                "uav_id",
                "start_time",
                "end_time",
                "sample_count",
                "metrics_summary",
                "quality_assessments",
                "anomaly_events",
            ]

            for field in required_history_fields:
                if field not in history:
                    logger.error(f"歷史數據缺少欄位: {field}")
                    return False

            # 檢查統計摘要
            metrics_summary = history["metrics_summary"]
            if metrics_summary:
                for metric_name, stats in metrics_summary.items():
                    required_stats = ["mean", "min", "max", "std"]
                    for stat in required_stats:
                        if stat not in stats:
                            logger.error(f"統計摘要缺少統計項: {metric_name}.{stat}")
                            return False

            logger.info(f"✅ 質量歷史功能正常 - 樣本數: {history['sample_count']}")
            return True

        except Exception as e:
            logger.error(f"質量歷史測試失敗: {e}")
            return False

    async def _test_anomaly_detection(self) -> bool:
        """測試異常檢測功能"""
        try:
            # 模擬一些異常的信號質量數據
            anomalous_signals = [
                {
                    "rsrp_dbm": -120.0,
                    "sinr_db": -5.0,
                    "throughput_mbps": 1.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },  # 信號極差
                {
                    "rsrp_dbm": -90.0,
                    "sinr_db": 2.0,
                    "throughput_mbps": 50.0,
                    "packet_loss_rate": 0.5,
                    "timestamp": datetime.now(UTC).isoformat(),
                },  # 高丟包率
                {
                    "rsrp_dbm": -80.0,
                    "sinr_db": 15.0,
                    "throughput_mbps": 2.0,
                    "latency_ms": 500.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },  # 高延遲
            ]

            # 發送異常數據
            for signal in anomalous_signals:
                await self.client.post(
                    f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/{self.test_uav_id}/update-signal",
                    json=signal,
                )
                await asyncio.sleep(0.5)

            # 檢測異常
            response = await self.client.get(
                f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/{self.test_uav_id}/anomalies"
            )

            if response.status_code != 200:
                logger.error(f"異常檢測失敗: {response.status_code}")
                return False

            anomalies = response.json()

            # 檢查異常事件結構
            if anomalies:
                for anomaly in anomalies:
                    required_anomaly_fields = [
                        "type",
                        "severity",
                        "description",
                        "timestamp",
                    ]
                    for field in required_anomaly_fields:
                        if field not in anomaly:
                            logger.error(f"異常事件缺少欄位: {field}")
                            return False

            logger.info(f"✅ 異常檢測功能正常 - 檢測到 {len(anomalies)} 個異常")
            return True

        except Exception as e:
            logger.error(f"異常檢測測試失敗: {e}")
            return False

    async def _test_quality_trends(self) -> bool:
        """測試質量趨勢分析"""
        try:
            # 模擬趨勢變化 - 逐漸改善的信號
            improving_signals = [
                {
                    "rsrp_dbm": -100.0,
                    "sinr_db": 5.0,
                    "throughput_mbps": 10.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                {
                    "rsrp_dbm": -95.0,
                    "sinr_db": 8.0,
                    "throughput_mbps": 15.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                {
                    "rsrp_dbm": -90.0,
                    "sinr_db": 12.0,
                    "throughput_mbps": 25.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                {
                    "rsrp_dbm": -85.0,
                    "sinr_db": 15.0,
                    "throughput_mbps": 35.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                {
                    "rsrp_dbm": -80.0,
                    "sinr_db": 18.0,
                    "throughput_mbps": 45.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            ]

            # 發送改善趨勢數據
            for signal in improving_signals:
                await self.client.post(
                    f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/{self.test_uav_id}/update-signal",
                    json=signal,
                )
                await asyncio.sleep(0.2)

            # 等待趨勢分析
            await asyncio.sleep(1)

            # 獲取質量評估（包含趨勢）
            response = await self.client.get(
                f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/{self.test_uav_id}",
                params={"time_window_minutes": 1},
            )

            if response.status_code != 200:
                logger.error(f"趨勢評估失敗: {response.status_code}")
                return False

            assessment = response.json()

            # 檢查趨勢分析
            quality_trend = assessment.get("quality_trend")
            valid_trends = ["improving", "stable", "degrading"]

            if quality_trend not in valid_trends:
                logger.error(f"無效的趨勢值: {quality_trend}")
                return False

            logger.info(f"✅ 質量趨勢分析正常 - 趨勢: {quality_trend}")
            return True

        except Exception as e:
            logger.error(f"質量趨勢測試失敗: {e}")
            return False

    async def _test_comprehensive_scenario(self) -> bool:
        """測試綜合場景"""
        try:
            # 模擬真實的 UAV 飛行場景
            flight_scenario = [
                # 起飛階段 - 信號逐漸變弱
                {
                    "rsrp_dbm": -70.0,
                    "sinr_db": 20.0,
                    "throughput_mbps": 80.0,
                    "latency_ms": 30.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                {
                    "rsrp_dbm": -75.0,
                    "sinr_db": 18.0,
                    "throughput_mbps": 70.0,
                    "latency_ms": 35.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                {
                    "rsrp_dbm": -80.0,
                    "sinr_db": 15.0,
                    "throughput_mbps": 60.0,
                    "latency_ms": 40.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                # 巡航階段 - 穩定
                {
                    "rsrp_dbm": -85.0,
                    "sinr_db": 12.0,
                    "throughput_mbps": 45.0,
                    "latency_ms": 50.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                {
                    "rsrp_dbm": -86.0,
                    "sinr_db": 11.5,
                    "throughput_mbps": 43.0,
                    "latency_ms": 52.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                {
                    "rsrp_dbm": -84.0,
                    "sinr_db": 12.5,
                    "throughput_mbps": 47.0,
                    "latency_ms": 48.0,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                # 干擾階段 - 質量下降
                {
                    "rsrp_dbm": -95.0,
                    "sinr_db": 5.0,
                    "throughput_mbps": 15.0,
                    "latency_ms": 120.0,
                    "packet_loss_rate": 0.1,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                {
                    "rsrp_dbm": -100.0,
                    "sinr_db": 2.0,
                    "throughput_mbps": 8.0,
                    "latency_ms": 200.0,
                    "packet_loss_rate": 0.2,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                # 恢復階段 - 逐漸改善
                {
                    "rsrp_dbm": -90.0,
                    "sinr_db": 8.0,
                    "throughput_mbps": 25.0,
                    "latency_ms": 80.0,
                    "packet_loss_rate": 0.05,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                {
                    "rsrp_dbm": -85.0,
                    "sinr_db": 12.0,
                    "throughput_mbps": 40.0,
                    "latency_ms": 55.0,
                    "packet_loss_rate": 0.02,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            ]

            # 執行飛行場景
            for i, signal in enumerate(flight_scenario):
                # 為每個信號添加新的時間戳
                signal["timestamp"] = datetime.now(UTC).isoformat()

                await self.client.post(
                    f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/{self.test_uav_id}/update-signal",
                    json=signal,
                )

                # 每隔幾個數據點進行評估
                if i % 3 == 0:
                    assessment_response = await self.client.get(
                        f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/{self.test_uav_id}",
                        params={"time_window_minutes": 1},
                    )

                    if assessment_response.status_code == 200:
                        assessment = assessment_response.json()
                        logger.debug(
                            f"飛行階段 {i//3 + 1}: 評分 {assessment['overall_quality_score']:.1f}, "
                            f"等級 {assessment['quality_grade']}"
                        )

                await asyncio.sleep(0.3)

            # 最終評估
            final_response = await self.client.get(
                f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/{self.test_uav_id}",
                params={"time_window_minutes": 2},
            )

            if final_response.status_code != 200:
                logger.error(f"最終評估失敗: {final_response.status_code}")
                return False

            final_assessment = final_response.json()

            # 檢查是否識別了問題
            issues = final_assessment.get("identified_issues", [])
            recommendations = final_assessment.get("recommendations", [])

            if not issues:
                logger.warning("未識別到預期的問題")
            else:
                logger.info(f"識別到 {len(issues)} 個問題")

            if not recommendations:
                logger.warning("未生成改善建議")
            else:
                logger.info(f"生成了 {len(recommendations)} 個建議")

            # 檢查歷史數據
            history_response = await self.client.get(
                f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/{self.test_uav_id}/history",
                params={"hours": 1},
            )

            if history_response.status_code == 200:
                history = history_response.json()
                logger.info(f"歷史數據樣本數: {history['sample_count']}")

            logger.info("✅ 綜合場景測試完成")
            return True

        except Exception as e:
            logger.error(f"綜合場景測試失敗: {e}")
            return False

        finally:
            # 清理 - 停止監控
            try:
                await self.client.post(
                    f"{self.netstack_url}/api/v1/uav-satellite/connection-quality/stop-monitoring/{self.test_uav_id}"
                )
                logger.info("✅ 測試清理完成")
            except:
                pass

    def _generate_test_report(self) -> Dict:
        """生成測試報告"""
        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result["status"] == "PASSED"
        )
        failed_tests = sum(
            1 for result in self.test_results.values() if result["status"] == "FAILED"
        )
        error_tests = sum(
            1 for result in self.test_results.values() if result["status"] == "ERROR"
        )

        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests,
                "success_rate_percent": success_rate,
            },
            "overall_status": (
                "PASSED" if failed_tests == 0 and error_tests == 0 else "FAILED"
            ),
            "detailed_results": self.test_results,
            "system_validation": {
                "connection_quality_assessment": passed_tests >= 6,
                "anomaly_detection": "test_anomaly_detection"
                in [
                    name
                    for name, result in self.test_results.items()
                    if result["status"] == "PASSED"
                ],
                "quality_monitoring": "test_uav_creation_and_monitoring"
                in [
                    name
                    for name, result in self.test_results.items()
                    if result["status"] == "PASSED"
                ],
                "comprehensive_scenarios": "test_comprehensive_scenario"
                in [
                    name
                    for name, result in self.test_results.items()
                    if result["status"] == "PASSED"
                ],
            },
        }

        return report


async def main():
    """主函數"""
    tester = UAVSatelliteConnectionQualityTest()

    try:
        report = await tester.run_all_tests()

        print("\n" + "=" * 80)
        print("🎯 UAV-衛星連接質量評估系統測試報告")
        print("=" * 80)
        print(f"📅 測試時間: {report['timestamp']}")
        print(
            f"🎯 總體結果: {'✅ 通過' if report['overall_status'] == 'PASSED' else '❌ 失敗'}"
        )
        print(
            f"📊 成功率: {report['test_summary']['success_rate_percent']:.1f}% "
            f"({report['test_summary']['passed_tests']}/{report['test_summary']['total_tests']})"
        )
        print()

        print("🔍 詳細測試結果:")
        for test_name, result in report["detailed_results"].items():
            status_icon = {"PASSED": "✅", "FAILED": "❌", "ERROR": "💥"}.get(
                result["status"], "❓"
            )
            print(f"   {status_icon} {test_name}: {result['status']}")
            if "error" in result:
                print(f"      錯誤: {result['error']}")
        print()

        print("️ 系統功能驗證:")
        validation = report["system_validation"]
        for feature, status in validation.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {feature}: {'通過' if status else '失敗'}")
        print()

        if report["overall_status"] == "PASSED":
            print("🎉 UAV-衛星連接質量評估系統功能完整，所有測試通過！")
            print("   系統具備完整的連接質量監控、評估、異常檢測和預測能力。")
        else:
            print("⚠️  UAV-衛星連接質量評估系統部分功能存在問題。")
            print("   請檢查失敗的測試項目並進行修復。")

        print("=" * 80)

        # 保存報告
        with open(
            "uav_satellite_connection_quality_test_report.json", "w", encoding="utf-8"
        ) as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📄 詳細報告已保存至: uav_satellite_connection_quality_test_report.json")

        return 0 if report["overall_status"] == "PASSED" else 1

    except Exception as e:
        print(f"❌ 測試過程出現異常: {e}")
        return 1


if __name__ == "__main__":
    import sys

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
