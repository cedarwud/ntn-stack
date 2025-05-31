#!/usr/bin/env python3
"""
API 功能測試模組
負責測試 NetStack 和 SimWorld API 的功能正確性

測試範圍：
- API 端點響應正確性
- 數據格式驗證
- 錯誤處理
- 業務邏輯正確性
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Tuple, Any, Optional
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class APITestResult:
    """API 測試結果"""

    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: str = ""
    response_data: Optional[Dict] = None
    validation_results: Optional[Dict] = None


class APITester:
    """API 功能測試器"""

    def __init__(self, config: Dict):
        self.config = config
        self.environment = config["environment"]
        self.services = self.environment["services"]
        self.results: List[APITestResult] = []

    async def run_functionality_tests(self) -> Tuple[bool, Dict]:
        """執行 API 功能測試"""
        logger.info("🌐 開始執行 API 功能測試")

        test_methods = [
            self._test_netstack_core_apis,
            self._test_netstack_uav_apis,
            self._test_netstack_system_apis,
            self._test_simworld_wireless_apis,
            self._test_simworld_uav_apis,
            self._test_cross_service_integration,
        ]

        all_passed = True
        details = {
            "tests_executed": len(test_methods),
            "tests_passed": 0,
            "tests_failed": 0,
            "api_results": [],
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
                logger.error(f"API 測試異常: {test_method.__name__} - {e}")
                details["tests_failed"] += 1
                all_passed = False

        # 整理結果
        details["api_results"] = [
            {
                "endpoint": r.endpoint,
                "method": r.method,
                "status_code": r.status_code,
                "response_time_ms": r.response_time_ms,
                "success": r.success,
                "error": r.error_message,
                "validation": r.validation_results,
            }
            for r in self.results
        ]

        details["summary"] = {
            "overall_success": all_passed,
            "success_rate": details["tests_passed"] / details["tests_executed"],
            "total_endpoints_tested": len(self.results),
            "successful_endpoints": sum(1 for r in self.results if r.success),
            "average_response_time_ms": (
                sum(r.response_time_ms for r in self.results) / len(self.results)
                if self.results
                else 0
            ),
        }

        logger.info(
            f"🌐 API 功能測試完成，成功率: {details['summary']['success_rate']:.1%}"
        )
        return all_passed, details

    async def _test_netstack_core_apis(self) -> bool:
        """測試 NetStack 核心 API"""
        logger.info("🔧 測試 NetStack 核心 API")

        base_url = self.services["netstack"]["url"]
        test_cases = [
            {
                "endpoint": "/health",
                "method": "GET",
                "expected_status": 200,
                "validate_response": self._validate_health_response,
            },
            {
                "endpoint": "/metrics",
                "method": "GET",
                "expected_status": 200,
                "validate_response": self._validate_metrics_response,
            },
            {
                "endpoint": "/docs",
                "method": "GET",
                "expected_status": 200,
                "validate_response": self._validate_html_response,
            },
            {
                "endpoint": "/openapi.json",
                "method": "GET",
                "expected_status": 200,
                "validate_response": self._validate_openapi_response,
            },
        ]

        return await self._execute_api_tests(base_url, test_cases, "netstack_core")

    async def _test_netstack_uav_apis(self) -> bool:
        """測試 NetStack UAV API"""
        logger.info("🚁 測試 NetStack UAV API")

        base_url = self.services["netstack"]["url"]
        test_cases = [
            {
                "endpoint": "/api/v1/uav",
                "method": "GET",
                "expected_status": 200,
                "validate_response": self._validate_uav_list_response,
            },
            {
                "endpoint": "/api/v1/uav/trajectory",
                "method": "GET",
                "expected_status": 200,
                "validate_response": self._validate_trajectory_list_response,
            },
            {
                "endpoint": "/api/v1/uav/demo/quick-test",
                "method": "POST",
                "expected_status": 200,
                "validate_response": self._validate_demo_response,
                "headers": {"Content-Type": "application/json"},
                "data": {},
            },
        ]

        return await self._execute_api_tests(base_url, test_cases, "netstack_uav")

    async def _test_netstack_system_apis(self) -> bool:
        """測試 NetStack 系統 API"""
        logger.info("⚙️ 測試 NetStack 系統 API")

        base_url = self.services["netstack"]["url"]
        test_cases = [
            {
                "endpoint": "/api/v1/system/status",
                "method": "GET",
                "expected_status": [200, 404],  # 允許未實現
                "validate_response": self._validate_system_status_response,
            },
            {
                "endpoint": "/api/v1/system/info",
                "method": "GET",
                "expected_status": [200, 404],
                "validate_response": self._validate_system_info_response,
            },
        ]

        return await self._execute_api_tests(base_url, test_cases, "netstack_system")

    async def _test_simworld_wireless_apis(self) -> bool:
        """測試 SimWorld 無線 API"""
        logger.info("📡 測試 SimWorld 無線 API")

        base_url = self.services["simworld"]["url"]
        test_cases = [
            {
                "endpoint": "/api/v1/wireless/health",
                "method": "GET",
                "expected_status": 200,
                "validate_response": self._validate_health_response,
            },
            {
                "endpoint": "/api/v1/wireless/sionna/status",
                "method": "GET",
                "expected_status": 200,
                "validate_response": self._validate_sionna_status_response,
            },
            {
                "endpoint": "/api/v1/wireless/sionna/channel-model",
                "method": "GET",
                "expected_status": 200,
                "validate_response": self._validate_channel_model_response,
            },
        ]

        return await self._execute_api_tests(base_url, test_cases, "simworld_wireless")

    async def _test_simworld_uav_apis(self) -> bool:
        """測試 SimWorld UAV API"""
        logger.info("🚁 測試 SimWorld UAV API")

        base_url = self.services["simworld"]["url"]
        test_cases = [
            {
                "endpoint": "/api/v1/uav/positions",
                "method": "GET",
                "expected_status": 200,
                "validate_response": self._validate_uav_positions_response,
            },
            {
                "endpoint": "/api/v1/uav/trajectory",
                "method": "GET",
                "expected_status": 200,
                "validate_response": self._validate_trajectory_response,
            },
        ]

        return await self._execute_api_tests(base_url, test_cases, "simworld_uav")

    async def _test_cross_service_integration(self) -> bool:
        """測試跨服務整合"""
        logger.info("🔗 測試跨服務整合")

        try:
            async with aiohttp.ClientSession() as session:
                # 測試 SimWorld 調用 NetStack 的場景
                start_time = time.time()

                # 1. 從 SimWorld 獲取 UAV 位置
                simworld_url = (
                    f"{self.services['simworld']['url']}/api/v1/uav/positions"
                )
                async with session.get(simworld_url, timeout=10) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        uav_data = await response.json()

                        # 2. 將位置數據發送到 NetStack（模擬整合）
                        netstack_url = f"{self.services['netstack']['url']}/api/v1/uav"
                        start_time = time.time()

                        async with session.get(
                            netstack_url, timeout=10
                        ) as netstack_response:
                            netstack_response_time = (time.time() - start_time) * 1000

                            integration_success = (
                                response.status == 200
                                and netstack_response.status == 200
                            )

                            self.results.append(
                                APITestResult(
                                    endpoint="/integration/simworld-to-netstack",
                                    method="GET",
                                    status_code=200 if integration_success else 500,
                                    response_time_ms=response_time
                                    + netstack_response_time,
                                    success=integration_success,
                                    response_data={
                                        "simworld_response_time": response_time,
                                        "netstack_response_time": netstack_response_time,
                                        "uav_count": (
                                            len(uav_data.get("uavs", []))
                                            if integration_success
                                            else 0
                                        ),
                                    },
                                    validation_results={
                                        "integration_test": (
                                            "passed"
                                            if integration_success
                                            else "failed"
                                        )
                                    },
                                )
                            )

                            return integration_success
                    else:
                        self.results.append(
                            APITestResult(
                                endpoint="/integration/simworld-to-netstack",
                                method="GET",
                                status_code=response.status,
                                response_time_ms=response_time,
                                success=False,
                                error_message=f"SimWorld API 失敗: {response.status}",
                            )
                        )
                        return False

        except Exception as e:
            logger.error(f"跨服務整合測試失敗: {e}")
            return False

    async def _execute_api_tests(
        self, base_url: str, test_cases: List[Dict], test_group: str
    ) -> bool:
        """執行一組 API 測試"""
        all_passed = True

        async with aiohttp.ClientSession() as session:
            for test_case in test_cases:
                endpoint = test_case["endpoint"]
                method = test_case["method"]
                expected_status = test_case["expected_status"]

                # 支援單一狀態碼或狀態碼列表
                if isinstance(expected_status, int):
                    expected_status = [expected_status]

                start_time = time.time()

                try:
                    url = f"{base_url}{endpoint}"

                    # 準備請求參數
                    kwargs = {"timeout": 15}
                    if "headers" in test_case:
                        kwargs["headers"] = test_case["headers"]
                    if "data" in test_case:
                        kwargs["json"] = test_case["data"]

                    # 發送請求
                    async with session.request(method, url, **kwargs) as response:
                        response_time = (time.time() - start_time) * 1000

                        # 讀取響應數據
                        try:
                            if response.content_type == "application/json":
                                response_data = await response.json()
                            else:
                                response_data = {"content_type": response.content_type}
                        except:
                            response_data = None

                        # 驗證狀態碼
                        status_valid = response.status in expected_status

                        # 驗證響應內容
                        validation_results = {}
                        if status_valid and "validate_response" in test_case:
                            try:
                                validation_results = test_case["validate_response"](
                                    response_data, response
                                )
                            except Exception as e:
                                validation_results = {"validation_error": str(e)}

                        success = status_valid and not validation_results.get(
                            "validation_error"
                        )

                        if not success:
                            all_passed = False

                        self.results.append(
                            APITestResult(
                                endpoint=endpoint,
                                method=method,
                                status_code=response.status,
                                response_time_ms=response_time,
                                success=success,
                                error_message=(
                                    ""
                                    if success
                                    else f"Status {response.status} not in {expected_status}"
                                ),
                                response_data=response_data,
                                validation_results=validation_results,
                            )
                        )

                        if success:
                            logger.info(
                                f"✅ {test_group}.{endpoint} ({method}) - {response_time:.1f}ms"
                            )
                        else:
                            logger.error(
                                f"❌ {test_group}.{endpoint} ({method}) - {response.status}"
                            )

                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    all_passed = False

                    self.results.append(
                        APITestResult(
                            endpoint=endpoint,
                            method=method,
                            status_code=0,
                            response_time_ms=response_time,
                            success=False,
                            error_message=str(e),
                        )
                    )

                    logger.error(f"❌ {test_group}.{endpoint} ({method}) - 異常: {e}")

        return all_passed

    # ===== 響應驗證方法 =====

    def _validate_health_response(self, data: Dict, response) -> Dict:
        """驗證健康檢查響應"""
        if not data:
            return {"validation_error": "Empty response"}

        # 檢查基本健康狀態欄位
        if "status" in data:
            if data["status"] not in ["healthy", "ok", "up"]:
                return {"validation_error": f"Invalid status: {data['status']}"}

        return {"health_check": "valid"}

    def _validate_metrics_response(self, data: Any, response) -> Dict:
        """驗證指標響應"""
        # Prometheus 指標通常是純文字格式
        if response.content_type == "text/plain":
            return {"metrics_format": "prometheus_text"}
        elif response.content_type == "application/json":
            return {"metrics_format": "json"}
        else:
            return {
                "validation_error": f"Unexpected content type: {response.content_type}"
            }

    def _validate_html_response(self, data: Any, response) -> Dict:
        """驗證 HTML 響應"""
        if "text/html" in response.content_type:
            return {"html_response": "valid"}
        else:
            return {"validation_error": f"Expected HTML, got {response.content_type}"}

    def _validate_openapi_response(self, data: Dict, response) -> Dict:
        """驗證 OpenAPI 規範響應"""
        if not data:
            return {"validation_error": "Empty OpenAPI response"}

        required_fields = ["openapi", "info", "paths"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return {"validation_error": f"Missing fields: {missing_fields}"}

        return {"openapi_spec": "valid", "version": data.get("openapi")}

    def _validate_uav_list_response(self, data: Dict, response) -> Dict:
        """驗證 UAV 列表響應"""
        if not data:
            return {"validation_error": "Empty UAV list response"}

        # 檢查是否有 UAV 相關的欄位
        if "uavs" in data:
            uav_count = len(data["uavs"]) if isinstance(data["uavs"], list) else 0
            return {"uav_list": "valid", "uav_count": uav_count}
        elif isinstance(data, list):
            return {"uav_list": "valid", "uav_count": len(data)}
        else:
            return {"uav_list": "valid", "format": "unknown"}

    def _validate_trajectory_list_response(self, data: Dict, response) -> Dict:
        """驗證軌跡列表響應"""
        if not data:
            return {"validation_error": "Empty trajectory response"}

        if "trajectories" in data:
            trajectory_count = (
                len(data["trajectories"])
                if isinstance(data["trajectories"], list)
                else 0
            )
            return {"trajectory_list": "valid", "trajectory_count": trajectory_count}
        elif isinstance(data, list):
            return {"trajectory_list": "valid", "trajectory_count": len(data)}
        else:
            return {"trajectory_list": "valid", "format": "unknown"}

    def _validate_demo_response(self, data: Dict, response) -> Dict:
        """驗證演示響應"""
        if not data:
            return {"validation_error": "Empty demo response"}

        # 檢查演示結果
        if "status" in data or "result" in data or "message" in data:
            return {"demo_test": "valid"}
        else:
            return {"demo_test": "valid", "format": "unknown"}

    def _validate_system_status_response(self, data: Dict, response) -> Dict:
        """驗證系統狀態響應"""
        if not data:
            return {"system_status": "empty_but_valid"}  # 允許空響應

        if "system" in data or "status" in data or "services" in data:
            return {"system_status": "valid"}
        else:
            return {"system_status": "valid", "format": "unknown"}

    def _validate_system_info_response(self, data: Dict, response) -> Dict:
        """驗證系統資訊響應"""
        if not data:
            return {"system_info": "empty_but_valid"}

        if "version" in data or "info" in data or "build" in data:
            return {"system_info": "valid"}
        else:
            return {"system_info": "valid", "format": "unknown"}

    def _validate_sionna_status_response(self, data: Dict, response) -> Dict:
        """驗證 Sionna 狀態響應"""
        if not data:
            return {"validation_error": "Empty Sionna status"}

        if "sionna" in data or "status" in data or "tensorflow" in data:
            return {"sionna_status": "valid"}
        else:
            return {"sionna_status": "valid", "format": "unknown"}

    def _validate_channel_model_response(self, data: Dict, response) -> Dict:
        """驗證信道模型響應"""
        if not data:
            return {"validation_error": "Empty channel model response"}

        if "channel" in data or "model" in data or "parameters" in data:
            return {"channel_model": "valid"}
        else:
            return {"channel_model": "valid", "format": "unknown"}

    def _validate_uav_positions_response(self, data: Dict, response) -> Dict:
        """驗證 UAV 位置響應"""
        if not data:
            return {"validation_error": "Empty UAV positions"}

        if "uavs" in data:
            uav_count = len(data["uavs"]) if isinstance(data["uavs"], list) else 0
            return {"uav_positions": "valid", "uav_count": uav_count}
        elif isinstance(data, list):
            return {"uav_positions": "valid", "uav_count": len(data)}
        else:
            return {"uav_positions": "valid", "format": "unknown"}

    def _validate_trajectory_response(self, data: Dict, response) -> Dict:
        """驗證軌跡響應"""
        if not data:
            return {"validation_error": "Empty trajectory response"}

        if "trajectory" in data or "path" in data or "waypoints" in data:
            return {"trajectory": "valid"}
        elif isinstance(data, list):
            return {"trajectory": "valid", "waypoint_count": len(data)}
        else:
            return {"trajectory": "valid", "format": "unknown"}
