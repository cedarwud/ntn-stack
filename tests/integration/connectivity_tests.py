#!/usr/bin/env python3
"""
連接性測試模組
負責測試系統各組件間的基本連接性和網路通信能力

測試範圍：
- Docker 容器間網路連接
- 服務間 API 通信
- 資料庫連接
- 網路延遲和可達性
"""

import asyncio
import logging
import time
from typing import Dict, List, Tuple, Any
import aiohttp
import docker
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConnectivityResult:
    """連接性測試結果"""

    test_name: str
    source: str
    target: str
    success: bool
    latency_ms: float
    error_message: str = ""
    additional_info: Dict[str, Any] = None


class ConnectivityTester:
    """連接性測試器"""

    def __init__(self, config: Dict):
        self.config = config
        self.environment = config["environment"]
        self.services = self.environment["services"]
        self.results: List[ConnectivityResult] = []

    async def run_basic_tests(self) -> Tuple[bool, Dict]:
        """執行基本連接測試"""
        logger.info("🔗 開始執行基本連接測試")

        test_methods = [
            self._test_docker_network_connectivity,
            self._test_service_to_service_communication,
            self._test_database_connectivity,
            self._test_external_network_access,
            self._test_internal_api_endpoints,
        ]

        all_passed = True
        details = {
            "tests_executed": len(test_methods),
            "tests_passed": 0,
            "tests_failed": 0,
            "connectivity_results": [],
            "summary": {},
        }

        for test_method in test_methods:
            try:
                test_passed = await test_method()
                if test_passed:
                    details["tests_passed"] += 1
                else:
                    details["tests_failed"] += 1
                    all_passed = False

            except Exception as e:
                logger.error(f"連接測試異常: {test_method.__name__} - {e}")
                details["tests_failed"] += 1
                all_passed = False

        # 整理結果
        details["connectivity_results"] = [
            {
                "test_name": r.test_name,
                "source": r.source,
                "target": r.target,
                "success": r.success,
                "latency_ms": r.latency_ms,
                "error": r.error_message,
            }
            for r in self.results
        ]

        details["summary"] = {
            "overall_success": all_passed,
            "success_rate": details["tests_passed"] / details["tests_executed"],
            "average_latency_ms": (
                sum(r.latency_ms for r in self.results if r.success)
                / len([r for r in self.results if r.success])
                if self.results
                else 0
            ),
        }

        logger.info(
            f"🔗 基本連接測試完成，成功率: {details['summary']['success_rate']:.1%}"
        )
        return all_passed, details

    async def _test_docker_network_connectivity(self) -> bool:
        """測試 Docker 容器間網路連接"""
        logger.info("🐳 測試 Docker 容器間網路連接")

        try:
            client = docker.from_env()

            # 獲取容器資訊
            netstack_container = client.containers.get(
                self.services["netstack"]["container_name"]
            )
            simworld_container = client.containers.get(
                self.services["simworld"]["container_name"]
            )

            # 測試 netstack -> simworld 連接
            start_time = time.time()
            try:
                # 在 netstack 容器中 ping simworld
                result = netstack_container.exec_run(
                    "ping -c 1 -W 5 172.20.0.2", timeout=10
                )
                latency = (time.time() - start_time) * 1000

                success = result.exit_code == 0
                self.results.append(
                    ConnectivityResult(
                        test_name="docker_ping_netstack_to_simworld",
                        source="netstack-api",
                        target="simworld_backend",
                        success=success,
                        latency_ms=latency,
                        error_message="" if success else result.output.decode(),
                    )
                )

            except Exception as e:
                self.results.append(
                    ConnectivityResult(
                        test_name="docker_ping_netstack_to_simworld",
                        source="netstack-api",
                        target="simworld_backend",
                        success=False,
                        latency_ms=0,
                        error_message=str(e),
                    )
                )

            # 測試 simworld -> netstack 連接
            start_time = time.time()
            try:
                result = simworld_container.exec_run(
                    "ping -c 1 -W 5 172.20.0.40", timeout=10
                )
                latency = (time.time() - start_time) * 1000

                success = result.exit_code == 0
                self.results.append(
                    ConnectivityResult(
                        test_name="docker_ping_simworld_to_netstack",
                        source="simworld_backend",
                        target="netstack-api",
                        success=success,
                        latency_ms=latency,
                        error_message="" if success else result.output.decode(),
                    )
                )

            except Exception as e:
                self.results.append(
                    ConnectivityResult(
                        test_name="docker_ping_simworld_to_netstack",
                        source="simworld_backend",
                        target="netstack-api",
                        success=False,
                        latency_ms=0,
                        error_message=str(e),
                    )
                )

            # 檢查結果
            docker_tests = [r for r in self.results if "docker_ping" in r.test_name]
            all_docker_passed = all(r.success for r in docker_tests)

            if all_docker_passed:
                logger.info("✅ Docker 容器間網路連接正常")
            else:
                logger.error("❌ Docker 容器間網路連接存在問題")

            return all_docker_passed

        except Exception as e:
            logger.error(f"Docker 網路連接測試失敗: {e}")
            return False

    async def _test_service_to_service_communication(self) -> bool:
        """測試服務間 API 通信"""
        logger.info("🌐 測試服務間 API 通信")

        async with aiohttp.ClientSession() as session:
            # 測試 NetStack API 可達性
            start_time = time.time()
            try:
                async with session.get(
                    f"{self.services['netstack']['url']}/health", timeout=10
                ) as response:
                    latency = (time.time() - start_time) * 1000
                    success = response.status == 200

                    self.results.append(
                        ConnectivityResult(
                            test_name="api_netstack_health",
                            source="test_client",
                            target="netstack_api",
                            success=success,
                            latency_ms=latency,
                            error_message="" if success else f"HTTP {response.status}",
                        )
                    )

            except Exception as e:
                latency = (time.time() - start_time) * 1000
                self.results.append(
                    ConnectivityResult(
                        test_name="api_netstack_health",
                        source="test_client",
                        target="netstack_api",
                        success=False,
                        latency_ms=latency,
                        error_message=str(e),
                    )
                )

            # 測試 SimWorld API 可達性
            start_time = time.time()
            try:
                async with session.get(
                    f"{self.services['simworld']['url']}/api/v1/wireless/health",
                    timeout=10,
                ) as response:
                    latency = (time.time() - start_time) * 1000
                    success = response.status == 200

                    self.results.append(
                        ConnectivityResult(
                            test_name="api_simworld_health",
                            source="test_client",
                            target="simworld_api",
                            success=success,
                            latency_ms=latency,
                            error_message="" if success else f"HTTP {response.status}",
                        )
                    )

            except Exception as e:
                latency = (time.time() - start_time) * 1000
                self.results.append(
                    ConnectivityResult(
                        test_name="api_simworld_health",
                        source="test_client",
                        target="simworld_api",
                        success=False,
                        latency_ms=latency,
                        error_message=str(e),
                    )
                )

            # 測試跨服務通信 (SimWorld -> NetStack)
            start_time = time.time()
            try:
                # 模擬 SimWorld 調用 NetStack API
                async with session.get(
                    f"{self.services['netstack']['internal_url']}/api/v1/system/status",
                    timeout=10,
                ) as response:
                    latency = (time.time() - start_time) * 1000
                    success = response.status in [200, 404]  # 允許 404，主要測試連接性

                    self.results.append(
                        ConnectivityResult(
                            test_name="cross_service_simworld_to_netstack",
                            source="simworld",
                            target="netstack_internal",
                            success=success,
                            latency_ms=latency,
                            error_message="" if success else f"HTTP {response.status}",
                        )
                    )

            except Exception as e:
                latency = (time.time() - start_time) * 1000
                self.results.append(
                    ConnectivityResult(
                        test_name="cross_service_simworld_to_netstack",
                        source="simworld",
                        target="netstack_internal",
                        success=False,
                        latency_ms=latency,
                        error_message=str(e),
                    )
                )

        # 檢查結果
        api_tests = [
            r
            for r in self.results
            if "api_" in r.test_name or "cross_service" in r.test_name
        ]
        all_api_passed = all(r.success for r in api_tests)

        if all_api_passed:
            logger.info("✅ 服務間 API 通信正常")
        else:
            logger.error("❌ 服務間 API 通信存在問題")

        return all_api_passed

    async def _test_database_connectivity(self) -> bool:
        """測試資料庫連接"""
        logger.info("🗄️ 測試資料庫連接")

        try:
            # 測試 MongoDB 連接
            start_time = time.time()
            try:
                import pymongo

                client = pymongo.MongoClient(
                    self.environment["database"]["mongo_url"],
                    serverSelectionTimeoutMS=5000,
                )
                # 嘗試連接
                client.server_info()
                latency = (time.time() - start_time) * 1000

                self.results.append(
                    ConnectivityResult(
                        test_name="database_mongodb_connection",
                        source="test_client",
                        target="mongodb",
                        success=True,
                        latency_ms=latency,
                    )
                )

            except Exception as e:
                latency = (time.time() - start_time) * 1000
                self.results.append(
                    ConnectivityResult(
                        test_name="database_mongodb_connection",
                        source="test_client",
                        target="mongodb",
                        success=False,
                        latency_ms=latency,
                        error_message=str(e),
                    )
                )

            # 測試 Redis 連接
            start_time = time.time()
            try:
                import redis

                r = redis.Redis.from_url(
                    self.environment["database"]["redis_url"], socket_timeout=5
                )
                r.ping()
                latency = (time.time() - start_time) * 1000

                self.results.append(
                    ConnectivityResult(
                        test_name="database_redis_connection",
                        source="test_client",
                        target="redis",
                        success=True,
                        latency_ms=latency,
                    )
                )

            except Exception as e:
                latency = (time.time() - start_time) * 1000
                self.results.append(
                    ConnectivityResult(
                        test_name="database_redis_connection",
                        source="test_client",
                        target="redis",
                        success=False,
                        latency_ms=latency,
                        error_message=str(e),
                    )
                )

            # 檢查結果
            db_tests = [r for r in self.results if "database_" in r.test_name]
            all_db_passed = all(r.success for r in db_tests)

            if all_db_passed:
                logger.info("✅ 資料庫連接正常")
            else:
                logger.error("❌ 資料庫連接存在問題")

            return all_db_passed

        except ImportError as e:
            logger.warning(f"資料庫驅動未安裝，跳過資料庫連接測試: {e}")
            return True  # 不影響整體測試

    async def _test_external_network_access(self) -> bool:
        """測試外部網路訪問"""
        logger.info("🌍 測試外部網路訪問")

        test_urls = ["https://www.google.com", "https://httpbin.org/status/200"]

        async with aiohttp.ClientSession() as session:
            for url in test_urls:
                start_time = time.time()
                try:
                    async with session.get(url, timeout=10) as response:
                        latency = (time.time() - start_time) * 1000
                        success = response.status == 200

                        self.results.append(
                            ConnectivityResult(
                                test_name=f"external_access_{url.split('//')[1].split('/')[0]}",
                                source="test_client",
                                target=url,
                                success=success,
                                latency_ms=latency,
                                error_message=(
                                    "" if success else f"HTTP {response.status}"
                                ),
                            )
                        )

                except Exception as e:
                    latency = (time.time() - start_time) * 1000
                    self.results.append(
                        ConnectivityResult(
                            test_name=f"external_access_{url.split('//')[1].split('/')[0]}",
                            source="test_client",
                            target=url,
                            success=False,
                            latency_ms=latency,
                            error_message=str(e),
                        )
                    )

        # 檢查結果
        external_tests = [r for r in self.results if "external_access" in r.test_name]
        all_external_passed = all(r.success for r in external_tests)

        if all_external_passed:
            logger.info("✅ 外部網路訪問正常")
        else:
            logger.warning("⚠️ 外部網路訪問存在問題（可能是網路限制）")

        return True  # 外部網路問題不影響實驗室測試

    async def _test_internal_api_endpoints(self) -> bool:
        """測試內部 API 端點可達性"""
        logger.info("🔌 測試內部 API 端點")

        # NetStack 內部端點
        netstack_endpoints = [
            "/health",
            "/metrics",
            "/api/v1/system/status",
            "/api/v1/uav",
            "/docs",
        ]

        # SimWorld 內部端點
        simworld_endpoints = [
            "/api/v1/wireless/health",
            "/api/v1/uav/positions",
            "/api/v1/wireless/sionna/status",
        ]

        async with aiohttp.ClientSession() as session:
            # 測試 NetStack 端點
            for endpoint in netstack_endpoints:
                start_time = time.time()
                try:
                    url = f"{self.services['netstack']['url']}{endpoint}"
                    async with session.get(url, timeout=10) as response:
                        latency = (time.time() - start_time) * 1000
                        success = response.status < 500  # 允許 4xx，主要排除 5xx

                        self.results.append(
                            ConnectivityResult(
                                test_name=f"netstack_endpoint_{endpoint.replace('/', '_').replace('.', '_')}",
                                source="test_client",
                                target=f"netstack{endpoint}",
                                success=success,
                                latency_ms=latency,
                                error_message=(
                                    "" if success else f"HTTP {response.status}"
                                ),
                            )
                        )

                except Exception as e:
                    latency = (time.time() - start_time) * 1000
                    self.results.append(
                        ConnectivityResult(
                            test_name=f"netstack_endpoint_{endpoint.replace('/', '_').replace('.', '_')}",
                            source="test_client",
                            target=f"netstack{endpoint}",
                            success=False,
                            latency_ms=latency,
                            error_message=str(e),
                        )
                    )

            # 測試 SimWorld 端點
            for endpoint in simworld_endpoints:
                start_time = time.time()
                try:
                    url = f"{self.services['simworld']['url']}{endpoint}"
                    async with session.get(url, timeout=10) as response:
                        latency = (time.time() - start_time) * 1000
                        success = response.status < 500

                        self.results.append(
                            ConnectivityResult(
                                test_name=f"simworld_endpoint_{endpoint.replace('/', '_').replace('.', '_')}",
                                source="test_client",
                                target=f"simworld{endpoint}",
                                success=success,
                                latency_ms=latency,
                                error_message=(
                                    "" if success else f"HTTP {response.status}"
                                ),
                            )
                        )

                except Exception as e:
                    latency = (time.time() - start_time) * 1000
                    self.results.append(
                        ConnectivityResult(
                            test_name=f"simworld_endpoint_{endpoint.replace('/', '_').replace('.', '_')}",
                            source="test_client",
                            target=f"simworld{endpoint}",
                            success=False,
                            latency_ms=latency,
                            error_message=str(e),
                        )
                    )

        # 檢查結果
        endpoint_tests = [r for r in self.results if "endpoint_" in r.test_name]
        critical_endpoints = [
            r for r in endpoint_tests if r.test_name.endswith("_health")
        ]

        # 至少健康檢查端點必須通過
        critical_passed = all(r.success for r in critical_endpoints)

        if critical_passed:
            logger.info("✅ 關鍵 API 端點可達")
        else:
            logger.error("❌ 關鍵 API 端點不可達")

        return critical_passed
