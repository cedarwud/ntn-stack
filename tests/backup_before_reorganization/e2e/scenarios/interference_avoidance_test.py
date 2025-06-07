#!/usr/bin/env python3
"""
干擾規避測試場景
實現 TODO.md 中的場景2：干擾出現和規避場景
測試 AI-RAN 抗干擾能力和快速頻率跳變效果
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List
import aiohttp
import json

logger = logging.getLogger(__name__)


class InterferenceAvoidanceTest:
    """干擾規避測試場景"""

    def __init__(self, netstack_url: str, simworld_url: str):
        self.netstack_url = netstack_url
        self.simworld_url = simworld_url
        self.test_data = {}
        self.performance_metrics = {}
        self.interference_data = {}

    async def run_scenario(self, session: aiohttp.ClientSession) -> Dict:
        """執行干擾規避測試場景"""
        logger.info("📡 開始執行干擾規避測試場景")

        scenario_start = time.time()
        results = {
            "scenario_name": "干擾出現和規避場景",
            "start_time": datetime.utcnow().isoformat(),
            "steps": [],
            "performance_metrics": {},
            "success": False,
        }

        try:
            # 步驟 1: 建立正常連接
            step1_result = await self._establish_normal_connection(session)
            results["steps"].append(step1_result)
            if not step1_result["success"]:
                return results

            # 步驟 2: 測量基線性能
            step2_result = await self._measure_baseline_performance(session)
            results["steps"].append(step2_result)
            if not step2_result["success"]:
                return results

            # 步驟 3: 注入干擾信號
            step3_result = await self._inject_interference(session)
            results["steps"].append(step3_result)
            if not step3_result["success"]:
                return results

            # 步驟 4: 監控干擾檢測
            step4_result = await self._monitor_interference_detection(session)
            results["steps"].append(step4_result)
            if not step4_result["success"]:
                return results

            # 步驟 5: 驗證頻率跳變
            step5_result = await self._verify_frequency_hopping(session)
            results["steps"].append(step5_result)
            if not step5_result["success"]:
                return results

            # 步驟 6: 測試通信恢復
            step6_result = await self._test_communication_restoration(session)
            results["steps"].append(step6_result)
            if not step6_result["success"]:
                return results

            # 步驟 7: 驗證性能恢復
            step7_result = await self._verify_performance_recovery(session)
            results["steps"].append(step7_result)

            results["success"] = step7_result["success"]
            logger.info("✅ 干擾規避測試場景完成")

        except Exception as e:
            logger.error(f"❌ 干擾規避測試場景異常: {e}")
            results["error"] = str(e)

        finally:
            scenario_duration = time.time() - scenario_start
            results["duration_seconds"] = scenario_duration
            results["end_time"] = datetime.utcnow().isoformat()
            results["performance_metrics"] = self.performance_metrics
            results["interference_data"] = self.interference_data

        return results

    async def _establish_normal_connection(
        self, session: aiohttp.ClientSession
    ) -> Dict:
        """步驟1: 建立正常連接"""
        logger.info("🔗 建立正常連接")
        step_start = time.time()

        # UAV 配置
        uav_config = {
            "uav_id": "interference_test_uav",
            "position": {"latitude": 25.0330, "longitude": 121.5654, "altitude": 800},
            "communication": {
                "frequency_ghz": 12.5,
                "bandwidth_mhz": 100,
                "modulation": "16QAM",
                "coding_rate": "3/4",
                "adaptive_modulation": True,
                "interference_mitigation": True,
            },
        }

        try:
            # 創建 UAV
            async with session.post(
                f"{self.netstack_url}/api/v1/uav/create", json=uav_config
            ) as response:
                if response.status != 201:
                    error_text = await response.text()
                    return {
                        "step_name": "建立正常連接",
                        "success": False,
                        "duration_ms": (time.time() - step_start) * 1000,
                        "error": f"UAV 創建失敗: HTTP {response.status} - {error_text}",
                    }

                uav_data = await response.json()
                self.test_data["uav_id"] = uav_data.get("uav_id", uav_config["uav_id"])

            # 建立衛星連接
            connection_config = {
                "uav_id": self.test_data["uav_id"],
                "satellite_selection": "best_signal",
                "frequency_ghz": 12.5,
                "interference_monitoring": True,
                "adaptive_parameters": True,
            }

            async with session.post(
                f"{self.netstack_url}/api/v1/satellite/connect", json=connection_config
            ) as response:
                step_duration = time.time() - step_start

                if response.status == 200:
                    connection_data = await response.json()
                    self.test_data["connection_id"] = connection_data.get(
                        "connection_id"
                    )
                    self.test_data["initial_frequency"] = connection_data.get(
                        "frequency_ghz", 12.5
                    )

                    logger.info(
                        f"✅ 正常連接建立成功: {self.test_data['connection_id']}"
                    )

                    return {
                        "step_name": "建立正常連接",
                        "success": True,
                        "duration_ms": step_duration * 1000,
                        "details": f"連接ID: {self.test_data['connection_id']}, 初始頻率: {self.test_data['initial_frequency']} GHz",
                    }
                else:
                    error_text = await response.text()
                    return {
                        "step_name": "建立正常連接",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": f"連接建立失敗: HTTP {response.status} - {error_text}",
                    }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 建立正常連接異常: {e}")
            return {
                "step_name": "建立正常連接",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _measure_baseline_performance(
        self, session: aiohttp.ClientSession
    ) -> Dict:
        """步驟2: 測量基線性能"""
        logger.info("📊 測量基線性能")
        step_start = time.time()

        try:
            # 進行基線性能測試
            baseline_results = []

            for i in range(5):  # 測量5次取平均
                test_start = time.time()

                # 測試延遲
                async with session.get(
                    f"{self.netstack_url}/api/v1/connectivity/ping",
                    params={"uav_id": self.test_data["uav_id"]},
                ) as response:
                    test_duration = time.time() - test_start

                    if response.status == 200:
                        ping_data = await response.json()
                        latency_ms = ping_data.get("latency_ms", test_duration * 1000)
                        baseline_results.append(latency_ms)
                        logger.debug(f"基線測試 {i+1}: {latency_ms:.1f}ms")
                    else:
                        baseline_results.append(999.0)

                await asyncio.sleep(0.5)

            # 計算基線指標
            if baseline_results:
                baseline_latency = sum(baseline_results) / len(baseline_results)
                self.performance_metrics["baseline_latency_ms"] = baseline_latency

                # 測量基線吞吐量
                throughput_test_data = {"size_kb": 50, "test_duration_sec": 5}

                async with session.post(
                    f"{self.netstack_url}/api/v1/throughput/test",
                    json={
                        "uav_id": self.test_data["uav_id"],
                        "test_config": throughput_test_data,
                    },
                ) as response:
                    if response.status == 200:
                        throughput_data = await response.json()
                        baseline_throughput = throughput_data.get("throughput_mbps", 0)
                        self.performance_metrics["baseline_throughput_mbps"] = (
                            baseline_throughput
                        )
                    else:
                        self.performance_metrics["baseline_throughput_mbps"] = 0

                step_duration = time.time() - step_start

                logger.info(
                    f"✅ 基線性能測量完成: 延遲 {baseline_latency:.1f}ms, 吞吐量 {self.performance_metrics['baseline_throughput_mbps']:.1f} Mbps"
                )

                return {
                    "step_name": "測量基線性能",
                    "success": True,
                    "duration_ms": step_duration * 1000,
                    "details": f"基線延遲: {baseline_latency:.1f}ms, 基線吞吐量: {self.performance_metrics['baseline_throughput_mbps']:.1f} Mbps",
                    "baseline_metrics": {
                        "latency_ms": baseline_latency,
                        "throughput_mbps": self.performance_metrics[
                            "baseline_throughput_mbps"
                        ],
                    },
                }
            else:
                return {
                    "step_name": "測量基線性能",
                    "success": False,
                    "duration_ms": (time.time() - step_start) * 1000,
                    "error": "無法獲取基線性能數據",
                }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 測量基線性能異常: {e}")
            return {
                "step_name": "測量基線性能",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _inject_interference(self, session: aiohttp.ClientSession) -> Dict:
        """步驟3: 注入干擾信號"""
        logger.info("🚨 注入干擾信號")
        step_start = time.time()

        # 干擾配置
        interference_config = {
            "type": "continuous_wave",
            "frequency_ghz": self.test_data.get("initial_frequency", 12.5),
            "bandwidth_mhz": 20,
            "power_dbm": -70,  # 足夠強的干擾信號
            "duration_sec": 30,
            "pattern": "constant",
            "location": {
                "latitude": 25.0340,  # 靠近 UAV 位置
                "longitude": 121.5664,
                "altitude": 0,
            },
        }

        try:
            # 調用 SimWorld API 注入干擾
            async with session.post(
                f"{self.simworld_url}/api/v1/interference/inject",
                json=interference_config,
            ) as response:
                step_duration = time.time() - step_start

                if response.status == 200:
                    interference_data = await response.json()
                    self.interference_data["interference_id"] = interference_data.get(
                        "interference_id"
                    )
                    self.interference_data["start_time"] = datetime.utcnow().isoformat()
                    self.interference_data["config"] = interference_config

                    logger.info(
                        f"✅ 干擾信號注入成功: {self.interference_data['interference_id']}"
                    )

                    # 等待干擾信號穩定
                    await asyncio.sleep(2)

                    return {
                        "step_name": "注入干擾信號",
                        "success": True,
                        "duration_ms": step_duration * 1000,
                        "details": f"干擾ID: {self.interference_data['interference_id']}, 頻率: {interference_config['frequency_ghz']} GHz, 功率: {interference_config['power_dbm']} dBm",
                    }
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ 干擾信號注入失敗: HTTP {response.status} - {error_text}"
                    )

                    return {
                        "step_name": "注入干擾信號",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": f"HTTP {response.status}: {error_text}",
                    }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 注入干擾信號異常: {e}")
            return {
                "step_name": "注入干擾信號",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _monitor_interference_detection(
        self, session: aiohttp.ClientSession
    ) -> Dict:
        """步驟4: 監控干擾檢測"""
        logger.info("🔍 監控干擾檢測")
        step_start = time.time()

        max_detection_time = 5.0  # 最大檢測時間 5 秒
        detection_interval = 0.1  # 每 100ms 檢查一次

        try:
            detection_start = time.time()
            interference_detected = False
            detection_time = 0

            while (time.time() - detection_start) < max_detection_time:
                # 檢查干擾狀態
                async with session.get(
                    f"{self.netstack_url}/api/v1/interference/status",
                    params={"uav_id": self.test_data["uav_id"]},
                ) as response:
                    if response.status == 200:
                        interference_status = await response.json()

                        if interference_status.get("interference_detected", False):
                            detection_time = (
                                time.time() - detection_start
                            ) * 1000  # 轉換為毫秒
                            interference_detected = True

                            self.performance_metrics[
                                "interference_detection_time_ms"
                            ] = detection_time
                            self.interference_data["detection_time_ms"] = detection_time
                            self.interference_data["interference_level_db"] = (
                                interference_status.get("interference_level_db", 0)
                            )

                            logger.info(f"✅ 干擾檢測成功: {detection_time:.1f}ms")
                            break

                await asyncio.sleep(detection_interval)

            step_duration = time.time() - step_start

            if interference_detected:
                # 檢查檢測時間是否符合要求 (< 100ms)
                if detection_time <= 100:
                    return {
                        "step_name": "監控干擾檢測",
                        "success": True,
                        "duration_ms": step_duration * 1000,
                        "details": f"干擾檢測時間: {detection_time:.1f}ms, 干擾強度: {self.interference_data.get('interference_level_db', 0):.1f} dB",
                        "detection_time_ms": detection_time,
                    }
                else:
                    return {
                        "step_name": "監控干擾檢測",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": f"干擾檢測時間過長: {detection_time:.1f}ms > 100ms",
                        "detection_time_ms": detection_time,
                    }
            else:
                return {
                    "step_name": "監控干擾檢測",
                    "success": False,
                    "duration_ms": step_duration * 1000,
                    "error": f"在 {max_detection_time} 秒內未檢測到干擾",
                }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 監控干擾檢測異常: {e}")
            return {
                "step_name": "監控干擾檢測",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _verify_frequency_hopping(self, session: aiohttp.ClientSession) -> Dict:
        """步驟5: 驗證頻率跳變"""
        logger.info("🔄 驗證頻率跳變")
        step_start = time.time()

        max_hop_time = 2.0  # 最大跳變時間 2 秒
        check_interval = 0.05  # 每 50ms 檢查一次

        try:
            hop_start = time.time()
            frequency_changed = False
            hop_time = 0
            new_frequency = None

            initial_frequency = self.test_data.get("initial_frequency", 12.5)

            while (time.time() - hop_start) < max_hop_time:
                # 檢查當前頻率
                async with session.get(
                    f"{self.netstack_url}/api/v1/frequency/current",
                    params={"uav_id": self.test_data["uav_id"]},
                ) as response:
                    if response.status == 200:
                        frequency_data = await response.json()
                        current_frequency = frequency_data.get(
                            "frequency_ghz", initial_frequency
                        )

                        # 檢查頻率是否已改變
                        if (
                            abs(current_frequency - initial_frequency) > 0.1
                        ):  # 頻率變化超過 100MHz
                            hop_time = (time.time() - hop_start) * 1000  # 轉換為毫秒
                            frequency_changed = True
                            new_frequency = current_frequency

                            self.performance_metrics["frequency_hop_time_ms"] = hop_time
                            self.test_data["new_frequency"] = new_frequency

                            logger.info(
                                f"✅ 頻率跳變成功: {initial_frequency} GHz -> {new_frequency} GHz ({hop_time:.1f}ms)"
                            )
                            break

                await asyncio.sleep(check_interval)

            step_duration = time.time() - step_start

            if frequency_changed:
                # 檢查跳變時間是否符合要求 (< 50ms)
                if hop_time <= 50:
                    return {
                        "step_name": "驗證頻率跳變",
                        "success": True,
                        "duration_ms": step_duration * 1000,
                        "details": f"頻率跳變: {initial_frequency} -> {new_frequency} GHz ({hop_time:.1f}ms)",
                        "hop_time_ms": hop_time,
                        "frequency_change": {
                            "from_ghz": initial_frequency,
                            "to_ghz": new_frequency,
                        },
                    }
                else:
                    return {
                        "step_name": "驗證頻率跳變",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": f"頻率跳變時間過長: {hop_time:.1f}ms > 50ms",
                        "hop_time_ms": hop_time,
                    }
            else:
                return {
                    "step_name": "驗證頻率跳變",
                    "success": False,
                    "duration_ms": step_duration * 1000,
                    "error": f"在 {max_hop_time} 秒內未檢測到頻率跳變",
                }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 驗證頻率跳變異常: {e}")
            return {
                "step_name": "驗證頻率跳變",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _test_communication_restoration(
        self, session: aiohttp.ClientSession
    ) -> Dict:
        """步驟6: 測試通信恢復"""
        logger.info("🔗 測試通信恢復")
        step_start = time.time()

        max_restoration_time = 2.0  # 最大恢復時間 2 秒
        test_interval = 0.1  # 每 100ms 測試一次

        try:
            restoration_start = time.time()
            communication_restored = False
            restoration_time = 0

            while (time.time() - restoration_start) < max_restoration_time:
                # 測試通信連接
                ping_start = time.time()

                async with session.get(
                    f"{self.netstack_url}/api/v1/connectivity/test",
                    params={"uav_id": self.test_data["uav_id"]},
                ) as response:
                    ping_duration = time.time() - ping_start

                    if response.status == 200:
                        connectivity_data = await response.json()

                        # 檢查連接是否恢復正常
                        if connectivity_data.get("connection_status") == "active":
                            latency_ms = connectivity_data.get(
                                "latency_ms", ping_duration * 1000
                            )

                            # 檢查延遲是否在可接受範圍內 (< 100ms)
                            if latency_ms < 100:
                                restoration_time = (
                                    time.time() - restoration_start
                                ) * 1000
                                communication_restored = True

                                self.performance_metrics[
                                    "communication_restoration_time_ms"
                                ] = restoration_time
                                self.performance_metrics[
                                    "post_interference_latency_ms"
                                ] = latency_ms

                                logger.info(
                                    f"✅ 通信恢復成功: {restoration_time:.1f}ms, 恢復後延遲: {latency_ms:.1f}ms"
                                )
                                break

                await asyncio.sleep(test_interval)

            step_duration = time.time() - step_start

            if communication_restored:
                # 檢查恢復時間是否符合要求 (< 500ms)
                if restoration_time <= 500:
                    return {
                        "step_name": "測試通信恢復",
                        "success": True,
                        "duration_ms": step_duration * 1000,
                        "details": f"通信恢復時間: {restoration_time:.1f}ms, 恢復後延遲: {self.performance_metrics['post_interference_latency_ms']:.1f}ms",
                        "restoration_time_ms": restoration_time,
                    }
                else:
                    return {
                        "step_name": "測試通信恢復",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": f"通信恢復時間過長: {restoration_time:.1f}ms > 500ms",
                        "restoration_time_ms": restoration_time,
                    }
            else:
                return {
                    "step_name": "測試通信恢復",
                    "success": False,
                    "duration_ms": step_duration * 1000,
                    "error": f"在 {max_restoration_time} 秒內通信未恢復",
                }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 測試通信恢復異常: {e}")
            return {
                "step_name": "測試通信恢復",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }

    async def _verify_performance_recovery(
        self, session: aiohttp.ClientSession
    ) -> Dict:
        """步驟7: 驗證性能恢復"""
        logger.info("📈 驗證性能恢復")
        step_start = time.time()

        try:
            # 測量恢復後的性能
            recovery_results = []

            for i in range(5):  # 測量5次取平均
                test_start = time.time()

                async with session.get(
                    f"{self.netstack_url}/api/v1/connectivity/ping",
                    params={"uav_id": self.test_data["uav_id"]},
                ) as response:
                    test_duration = time.time() - test_start

                    if response.status == 200:
                        ping_data = await response.json()
                        latency_ms = ping_data.get("latency_ms", test_duration * 1000)
                        recovery_results.append(latency_ms)
                    else:
                        recovery_results.append(999.0)

                await asyncio.sleep(0.2)

            if recovery_results:
                recovery_latency = sum(recovery_results) / len(recovery_results)
                self.performance_metrics["recovery_latency_ms"] = recovery_latency

                # 測量恢復後的吞吐量
                async with session.post(
                    f"{self.netstack_url}/api/v1/throughput/test",
                    json={
                        "uav_id": self.test_data["uav_id"],
                        "test_config": {"size_kb": 50, "test_duration_sec": 3},
                    },
                ) as response:
                    if response.status == 200:
                        throughput_data = await response.json()
                        recovery_throughput = throughput_data.get("throughput_mbps", 0)
                        self.performance_metrics["recovery_throughput_mbps"] = (
                            recovery_throughput
                        )
                    else:
                        recovery_throughput = 0
                        self.performance_metrics["recovery_throughput_mbps"] = 0

                # 計算性能保持率
                baseline_latency = self.performance_metrics.get(
                    "baseline_latency_ms", 50
                )
                baseline_throughput = self.performance_metrics.get(
                    "baseline_throughput_mbps", 25
                )

                latency_retention = (
                    (baseline_latency / recovery_latency) * 100
                    if recovery_latency > 0
                    else 0
                )
                throughput_retention = (
                    (recovery_throughput / baseline_throughput) * 100
                    if baseline_throughput > 0
                    else 0
                )

                self.performance_metrics["latency_retention_percent"] = (
                    latency_retention
                )
                self.performance_metrics["throughput_retention_percent"] = (
                    throughput_retention
                )

                step_duration = time.time() - step_start

                # 檢查性能保持率要求 (> 80%)
                performance_acceptable = throughput_retention >= 80

                if performance_acceptable:
                    logger.info(
                        f"✅ 性能恢復驗證通過: 延遲 {recovery_latency:.1f}ms, 吞吐量保持率 {throughput_retention:.1f}%"
                    )

                    return {
                        "step_name": "驗證性能恢復",
                        "success": True,
                        "duration_ms": step_duration * 1000,
                        "details": f"恢復後延遲: {recovery_latency:.1f}ms, 吞吐量保持率: {throughput_retention:.1f}%",
                        "recovery_metrics": {
                            "latency_ms": recovery_latency,
                            "throughput_mbps": recovery_throughput,
                            "throughput_retention_percent": throughput_retention,
                        },
                    }
                else:
                    logger.error(
                        f"❌ 性能恢復不符合要求: 吞吐量保持率 {throughput_retention:.1f}% < 80%"
                    )

                    return {
                        "step_name": "驗證性能恢復",
                        "success": False,
                        "duration_ms": step_duration * 1000,
                        "error": f"性能恢復不符合要求: 吞吐量保持率 {throughput_retention:.1f}% < 80%",
                        "recovery_metrics": {
                            "throughput_retention_percent": throughput_retention
                        },
                    }
            else:
                return {
                    "step_name": "驗證性能恢復",
                    "success": False,
                    "duration_ms": (time.time() - step_start) * 1000,
                    "error": "無法獲取恢復後的性能數據",
                }

        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"❌ 驗證性能恢復異常: {e}")
            return {
                "step_name": "驗證性能恢復",
                "success": False,
                "duration_ms": step_duration * 1000,
                "error": str(e),
            }
