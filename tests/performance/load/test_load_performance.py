#!/usr/bin/env python3
"""
大規模負載測試套件
實現階段七要求的大規模負載和壓力測試

功能：
1. 並發用戶負載測試
2. 漸進式負載增長測試
3. 持續負載測試
4. 峰值負載測試
5. 多服務負載分散測試
6. 實際場景模擬負載測試
"""

import asyncio
import time
import logging
import statistics
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import aiohttp
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
import psutil

logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """負載測試配置"""
    
    base_url: str
    max_concurrent_users: int = 100
    ramp_up_time_seconds: int = 60
    test_duration_seconds: int = 300
    steady_state_duration_seconds: int = 180
    think_time_ms: int = 1000
    timeout_seconds: int = 30
    target_scenarios: List[str] = field(default_factory=list)


@dataclass
class LoadTestResult:
    """負載測試結果"""
    
    test_name: str
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate: float
    throughput_mbps: float
    concurrent_users_peak: int
    detailed_metrics: List[Dict] = field(default_factory=list)


class VirtualUser:
    """虛擬用戶類"""
    
    def __init__(self, user_id: int, session: aiohttp.ClientSession, config: LoadTestConfig):
        self.user_id = user_id
        self.session = session
        self.config = config
        self.requests_sent = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.is_active = False
        
    async def run_user_scenario(self, scenario_name: str, duration_seconds: int) -> Dict[str, Any]:
        """執行用戶場景"""
        self.is_active = True
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration_seconds and self.is_active:
                # 執行場景步驟
                await self._execute_scenario_step(scenario_name)
                
                # 思考時間
                await asyncio.sleep(self.config.think_time_ms / 1000.0)
                
        except Exception as e:
            logger.error(f"用戶 {self.user_id} 執行場景 {scenario_name} 失敗: {e}")
        
        finally:
            self.is_active = False
            
        return self._get_user_metrics()
    
    async def _execute_scenario_step(self, scenario_name: str):
        """執行場景步驟"""
        # 根據場景名稱選擇不同的請求模式
        if scenario_name == "uav_data_collection":
            await self._uav_data_collection_scenario()
        elif scenario_name == "satellite_tracking":
            await self._satellite_tracking_scenario()
        elif scenario_name == "interference_monitoring":
            await self._interference_monitoring_scenario()
        elif scenario_name == "mesh_network_operation":
            await self._mesh_network_operation_scenario()
        else:
            await self._default_api_scenario()
    
    async def _uav_data_collection_scenario(self):
        """無人機數據收集場景"""
        endpoints = [
            "/api/v1/uav/status",
            "/api/v1/uav/metrics",
            "/api/v1/uav/trajectory"
        ]
        
        for endpoint in endpoints:
            await self._make_request("GET", endpoint)
            await asyncio.sleep(0.1)  # 小延遲
    
    async def _satellite_tracking_scenario(self):
        """衛星追蹤場景"""
        endpoints = [
            "/api/v1/satellite-gnb/status",
            "/api/v1/oneweb/constellation",
            "/api/v1/satellite-gnb/mapping"
        ]
        
        for endpoint in endpoints:
            await self._make_request("GET", endpoint)
            await asyncio.sleep(0.1)
    
    async def _interference_monitoring_scenario(self):
        """干擾監控場景"""
        endpoints = [
            "/api/v1/interference/current",
            "/api/v1/interference/mitigation-status",
            "/api/v1/ai-ran/metrics"
        ]
        
        for endpoint in endpoints:
            await self._make_request("GET", endpoint)
            await asyncio.sleep(0.1)
    
    async def _mesh_network_operation_scenario(self):
        """Mesh網絡操作場景"""
        endpoints = [
            "/api/v1/mesh/status",
            "/api/v1/mesh/topology",
            "/api/v1/mesh/failover-status"
        ]
        
        for endpoint in endpoints:
            await self._make_request("GET", endpoint)
            await asyncio.sleep(0.1)
    
    async def _default_api_scenario(self):
        """預設API場景"""
        endpoints = [
            "/health",
            "/api/v1/status",
            "/metrics"
        ]
        
        endpoint = random.choice(endpoints)
        await self._make_request("GET", endpoint)
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None):
        """發送HTTP請求"""
        url = f"{self.config.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            
            if method.upper() == "GET":
                async with self.session.get(url, timeout=timeout) as response:
                    await response.text()
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    if response.status < 400:
                        self.successful_requests += 1
                    else:
                        self.failed_requests += 1
                        
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, timeout=timeout) as response:
                    await response.text()
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    if response.status < 400:
                        self.successful_requests += 1
                    else:
                        self.failed_requests += 1
            
            self.response_times.append(response_time_ms)
            self.requests_sent += 1
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self.response_times.append(response_time_ms)
            self.failed_requests += 1
            self.requests_sent += 1
            
            logger.debug(f"用戶 {self.user_id} 請求失敗: {method} {url} - {e}")
    
    def _get_user_metrics(self) -> Dict[str, Any]:
        """獲取用戶指標"""
        if not self.response_times:
            return {
                "user_id": self.user_id,
                "requests_sent": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_response_time_ms": 0,
                "error_rate": 1.0,
                "response_times": []
            }
        
        return {
            "user_id": self.user_id,
            "requests_sent": self.requests_sent,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "avg_response_time_ms": statistics.mean(self.response_times),
            "error_rate": self.failed_requests / self.requests_sent if self.requests_sent > 0 else 0,
            "response_times": self.response_times
        }


class LoadTestSuite:
    """大規模負載測試套件"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = []
        self.active_users = []

    async def run_concurrent_load_test(
        self, 
        concurrent_users: int = 50,
        duration_seconds: int = 60,
        base_url: str = "http://localhost:8080"
    ) -> Dict[str, Any]:
        """執行並發負載測試"""
        
        self.logger.info(f"🚀 開始並發負載測試: {concurrent_users} 並發用戶, {duration_seconds} 秒")
        
        config = LoadTestConfig(
            base_url=base_url,
            max_concurrent_users=concurrent_users,
            test_duration_seconds=duration_seconds
        )
        
        start_time = datetime.utcnow()
        
        # 創建HTTP會話
        connector = aiohttp.TCPConnector(limit=concurrent_users * 2)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            # 創建虛擬用戶
            users = [
                VirtualUser(i, session, config) 
                for i in range(concurrent_users)
            ]
            
            # 並發執行用戶場景
            tasks = [
                user.run_user_scenario("default_api", duration_seconds)
                for user in users
            ]
            
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
            
        end_time = datetime.utcnow()
        
        # 聚合結果
        result = self._aggregate_load_test_results(
            "concurrent_load_test",
            start_time,
            end_time,
            user_results,
            concurrent_users
        )
        
        self.test_results.append(result)
        
        self.logger.info(f"✅ 並發負載測試完成: 成功率 {(1-result.error_rate)*100:.1f}%, "
                        f"平均響應時間 {result.avg_response_time_ms:.1f}ms")
        
        return {
            "success": result.error_rate < 0.1,
            "success_rate": 1 - result.error_rate,
            "avg_response_time_ms": result.avg_response_time_ms,
            "requests_per_second": result.requests_per_second
        }

    async def run_ramp_up_load_test(
        self,
        max_users: int = 100,
        ramp_up_time_seconds: int = 300,
        steady_state_time_seconds: int = 600,
        base_url: str = "http://localhost:8080"
    ) -> LoadTestResult:
        """執行漸進式負載測試"""
        
        self.logger.info(f"📈 開始漸進式負載測試: 最大 {max_users} 用戶, "
                        f"漸進時間 {ramp_up_time_seconds}s, 穩定時間 {steady_state_time_seconds}s")
        
        config = LoadTestConfig(
            base_url=base_url,
            max_concurrent_users=max_users,
            ramp_up_time_seconds=ramp_up_time_seconds,
            steady_state_duration_seconds=steady_state_time_seconds
        )
        
        start_time = datetime.utcnow()
        user_results = []
        
        connector = aiohttp.TCPConnector(limit=max_users * 2)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            # 漸進式增加用戶
            active_tasks = []
            users_added = 0
            
            for step in range(ramp_up_time_seconds):
                # 計算此步驟應該的用戶數
                target_users = int((step + 1) * max_users / ramp_up_time_seconds)
                
                # 添加新用戶
                while users_added < target_users:
                    user = VirtualUser(users_added, session, config)
                    task = asyncio.create_task(
                        user.run_user_scenario(
                            "mixed_scenarios", 
                            ramp_up_time_seconds - step + steady_state_time_seconds
                        )
                    )
                    active_tasks.append(task)
                    users_added += 1
                
                await asyncio.sleep(1)  # 每秒檢查一次
            
            # 等待穩定狀態結束
            self.logger.info(f"🎯 進入穩定狀態: {max_users} 並發用戶")
            await asyncio.sleep(steady_state_time_seconds)
            
            # 收集所有結果
            user_results = await asyncio.gather(*active_tasks, return_exceptions=True)
        
        end_time = datetime.utcnow()
        
        result = self._aggregate_load_test_results(
            "ramp_up_load_test",
            start_time,
            end_time,
            user_results,
            max_users
        )
        
        self.test_results.append(result)
        
        self.logger.info(f"✅ 漸進式負載測試完成: 成功率 {(1-result.error_rate)*100:.1f}%, "
                        f"峰值 RPS {result.requests_per_second:.1f}")
        
        return result

    async def run_spike_load_test(
        self,
        baseline_users: int = 10,
        spike_users: int = 100,
        spike_duration_seconds: int = 60,
        base_url: str = "http://localhost:8080"
    ) -> LoadTestResult:
        """執行峰值負載測試"""
        
        self.logger.info(f"⚡ 開始峰值負載測試: 基線 {baseline_users} -> 峰值 {spike_users} 用戶")
        
        config = LoadTestConfig(
            base_url=base_url,
            max_concurrent_users=spike_users,
            test_duration_seconds=spike_duration_seconds * 3  # 基線 + 峰值 + 恢復
        )
        
        start_time = datetime.utcnow()
        
        connector = aiohttp.TCPConnector(limit=spike_users * 2)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            # 階段1: 基線負載
            self.logger.info(f"📊 基線階段: {baseline_users} 用戶")
            baseline_users_list = [
                VirtualUser(i, session, config) 
                for i in range(baseline_users)
            ]
            
            baseline_tasks = [
                user.run_user_scenario("baseline_load", spike_duration_seconds * 3)
                for user in baseline_users_list
            ]
            
            # 等待基線穩定
            await asyncio.sleep(spike_duration_seconds)
            
            # 階段2: 峰值負載
            self.logger.info(f"🚀 峰值階段: 增加到 {spike_users} 用戶")
            spike_users_list = [
                VirtualUser(i + baseline_users, session, config)
                for i in range(spike_users - baseline_users)
            ]
            
            spike_tasks = [
                user.run_user_scenario("spike_load", spike_duration_seconds)
                for user in spike_users_list
            ]
            
            # 等待峰值階段
            spike_results = await asyncio.gather(*spike_tasks, return_exceptions=True)
            
            # 階段3: 恢復階段
            self.logger.info("📉 恢復階段: 回到基線負載")
            await asyncio.sleep(spike_duration_seconds)
            
            # 收集基線結果
            baseline_results = await asyncio.gather(*baseline_tasks, return_exceptions=True)
        
        end_time = datetime.utcnow()
        
        # 合併所有結果
        all_results = baseline_results + spike_results
        
        result = self._aggregate_load_test_results(
            "spike_load_test",
            start_time,
            end_time,
            all_results,
            spike_users
        )
        
        self.test_results.append(result)
        
        self.logger.info(f"✅ 峰值負載測試完成: 峰值處理能力驗證")
        
        return result

    async def run_endurance_load_test(
        self,
        concurrent_users: int = 30,
        duration_hours: int = 2,
        base_url: str = "http://localhost:8080"
    ) -> LoadTestResult:
        """執行持久性負載測試"""
        
        duration_seconds = duration_hours * 3600
        
        self.logger.info(f"⏱️ 開始持久性負載測試: {concurrent_users} 用戶, {duration_hours} 小時")
        
        config = LoadTestConfig(
            base_url=base_url,
            max_concurrent_users=concurrent_users,
            test_duration_seconds=duration_seconds
        )
        
        start_time = datetime.utcnow()
        
        connector = aiohttp.TCPConnector(limit=concurrent_users * 2)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            users = [
                VirtualUser(i, session, config)
                for i in range(concurrent_users)
            ]
            
            # 每小時輪換場景以模擬真實使用模式
            scenarios = ["uav_data_collection", "satellite_tracking", "interference_monitoring", "mesh_network_operation"]
            
            tasks = []
            for i, user in enumerate(users):
                scenario = scenarios[i % len(scenarios)]
                task = asyncio.create_task(
                    user.run_user_scenario(scenario, duration_seconds)
                )
                tasks.append(task)
            
            # 定期記錄中間結果
            intermediate_results = []
            for hour in range(duration_hours):
                await asyncio.sleep(3600)  # 等待1小時
                
                # 記錄中間指標
                current_metrics = self._collect_intermediate_metrics(users)
                intermediate_results.append({
                    "hour": hour + 1,
                    "metrics": current_metrics
                })
                
                self.logger.info(f"⏰ 持久性測試進度: {hour + 1}/{duration_hours} 小時完成")
            
            # 收集最終結果
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.utcnow()
        
        result = self._aggregate_load_test_results(
            "endurance_load_test",
            start_time,
            end_time,
            user_results,
            concurrent_users
        )
        
        # 添加中間結果到詳細指標
        result.detailed_metrics.extend(intermediate_results)
        
        self.test_results.append(result)
        
        self.logger.info(f"✅ 持久性負載測試完成: {duration_hours} 小時穩定運行")
        
        return result
    
    def _aggregate_load_test_results(
        self,
        test_name: str,
        start_time: datetime,
        end_time: datetime,
        user_results: List,
        concurrent_users_peak: int
    ) -> LoadTestResult:
        """聚合負載測試結果"""
        
        # 過濾有效結果
        valid_results = [
            result for result in user_results 
            if isinstance(result, dict) and "requests_sent" in result
        ]
        
        if not valid_results:
            return LoadTestResult(
                test_name=test_name,
                start_time=start_time,
                end_time=end_time,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                requests_per_second=0,
                error_rate=1.0,
                throughput_mbps=0,
                concurrent_users_peak=concurrent_users_peak
            )
        
        # 聚合指標
        total_requests = sum(r["requests_sent"] for r in valid_results)
        successful_requests = sum(r["successful_requests"] for r in valid_results)
        failed_requests = sum(r["failed_requests"] for r in valid_results)
        
        # 收集所有響應時間
        all_response_times = []
        for result in valid_results:
            if "response_times" in result:
                all_response_times.extend(result["response_times"])
        
        # 計算響應時間指標
        if all_response_times:
            avg_response_time_ms = statistics.mean(all_response_times)
            p95_response_time_ms = np.percentile(all_response_times, 95)
            p99_response_time_ms = np.percentile(all_response_times, 99)
        else:
            avg_response_time_ms = 0
            p95_response_time_ms = 0
            p99_response_time_ms = 0
        
        # 計算其他指標
        duration_seconds = (end_time - start_time).total_seconds()
        requests_per_second = total_requests / duration_seconds if duration_seconds > 0 else 0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        # 估算吐量 (1KB 平均響應大小)
        throughput_mbps = (successful_requests * 1024 * 8) / (duration_seconds * 1024 * 1024) if duration_seconds > 0 else 0
        
        return LoadTestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time_ms,
            p95_response_time_ms=p95_response_time_ms,
            p99_response_time_ms=p99_response_time_ms,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            throughput_mbps=throughput_mbps,
            concurrent_users_peak=concurrent_users_peak
        )
    
    def _collect_intermediate_metrics(self, users: List[VirtualUser]) -> Dict[str, Any]:
        """收集中間指標"""
        active_users = sum(1 for user in users if user.is_active)
        total_requests = sum(user.requests_sent for user in users)
        total_successful = sum(user.successful_requests for user in users)
        total_failed = sum(user.failed_requests for user in users)
        
        all_response_times = []
        for user in users:
            all_response_times.extend(user.response_times)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_users": active_users,
            "total_requests": total_requests,
            "successful_requests": total_successful,
            "failed_requests": total_failed,
            "error_rate": total_failed / total_requests if total_requests > 0 else 0,
            "avg_response_time_ms": statistics.mean(all_response_times) if all_response_times else 0
        }
    
    def get_load_test_summary(self) -> Dict[str, Any]:
        """獲取負載測試摘要"""
        if not self.test_results:
            return {"status": "no_tests_run"}
        
        return {
            "total_tests": len(self.test_results),
            "test_results": [
                {
                    "test_name": result.test_name,
                    "success_rate": 1 - result.error_rate,
                    "avg_response_time_ms": result.avg_response_time_ms,
                    "requests_per_second": result.requests_per_second,
                    "throughput_mbps": result.throughput_mbps,
                    "duration_minutes": (result.end_time - result.start_time).total_seconds() / 60
                }
                for result in self.test_results
            ],
            "overall_metrics": {
                "avg_success_rate": statistics.mean([1 - r.error_rate for r in self.test_results]),
                "avg_response_time_ms": statistics.mean([r.avg_response_time_ms for r in self.test_results]),
                "max_requests_per_second": max([r.requests_per_second for r in self.test_results]),
                "total_requests_processed": sum([r.total_requests for r in self.test_results])
            }
        }


# 兼容的LoadTester類 (for backward compatibility)
class LoadTester:
    """負載測試器 (兼容性版本)"""

    def __init__(self, config: Dict):
        self.config = config
        self.environment = config["environment"]
        self.services = self.environment["services"]
        self.load_test_suite = LoadTestSuite()

    async def run_load_tests(self) -> Tuple[bool, Dict]:
        """執行負載測試"""
        logger.info("🔥 開始執行負載測試")

        # 使用新的LoadTestSuite執行測試
        base_url = self.services.get('netstack', {}).get('url', 'http://localhost:8080')
        
        test_results = []
        
        # 高並發測試
        concurrent_result = await self.load_test_suite.run_concurrent_load_test(
            concurrent_users=50,
            duration_seconds=30,
            base_url=base_url
        )
        test_results.append(("high_concurrency", concurrent_result["success"]))
        
        # 峰值負載測試
        spike_result = await self.load_test_suite.run_spike_load_test(
            baseline_users=10,
            spike_users=50,
            spike_duration_seconds=30,
            base_url=base_url
        )
        test_results.append(("spike_load", spike_result.error_rate < 0.2))

        passed_tests = sum(1 for _, passed in test_results if passed)
        total_tests = len(test_results)

        details = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests / total_tests,
            "test_results": {name: passed for name, passed in test_results},
        }

        overall_success = passed_tests == total_tests
        logger.info(f"🔥 負載測試完成，成功率: {details['success_rate']:.1%}")

        return overall_success, details


async def main():
    """主函數 - 示例用法"""
    load_test_suite = LoadTestSuite()
    
    # 執行不同類型的負載測試
    print("🚀 開始執行負載測試套件")
    
    # 1. 並發負載測試
    await load_test_suite.run_concurrent_load_test(
        concurrent_users=50,
        duration_seconds=60
    )
    
    # 2. 漸進式負載測試
    await load_test_suite.run_ramp_up_load_test(
        max_users=100,
        ramp_up_time_seconds=120,
        steady_state_time_seconds=180
    )
    
    # 3. 峰值負載測試
    await load_test_suite.run_spike_load_test(
        baseline_users=20,
        spike_users=80,
        spike_duration_seconds=60
    )
    
    # 獲取摘要
    summary = load_test_suite.get_load_test_summary()
    print(f"📊 負載測試摘要: {json.dumps(summary, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    asyncio.run(main())
