"""
SimWorld 代理服務

提供與 SimWorld 後端服務的通信接口，實現統一 API 網關功能
"""

import logging
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SimWorldProxyService:
    """SimWorld 代理服務"""

    def __init__(self, simworld_base_url: str = "http://simworld-backend:8000"):
        self.base_url = simworld_base_url
        self.api_base_url = f"{simworld_base_url}/api/v1"
        self.timeout = 30.0
        self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """獲取 HTTP 客戶端"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """關閉客戶端連接"""
        if self._client:
            await self._client.aclose()
            self._client = None

    # ===== 健康檢查 =====

    async def check_health(self) -> Dict[str, Any]:
        """檢查 SimWorld 服務健康狀態"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/ping")

            if response.status_code == 200:
                return {
                    "healthy": True,
                    "status": "running",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "version": "0.1.0",
                }
            else:
                return {
                    "healthy": False,
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                }
        except Exception as e:
            logger.error(f"SimWorld 健康檢查失敗: {e}")
            return {"healthy": False, "status": "error", "error": str(e)}

    # ===== 衛星相關 API =====

    async def get_satellite_info(self, satellite_id: int) -> Dict[str, Any]:
        """獲取衛星信息"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.api_base_url}/satellite/{satellite_id}")

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"獲取衛星信息失敗 (ID: {satellite_id}): {e}")
            raise

    async def get_satellite_position(
        self, satellite_id: int, observer: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """獲取衛星當前位置"""
        try:
            client = await self._get_client()

            # 構建請求數據
            request_data = {}
            if observer:
                request_data = observer

            response = await client.post(
                f"{self.api_base_url}/satellite/{satellite_id}/position",
                json=request_data,
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"獲取衛星位置失敗 (ID: {satellite_id}): {e}")
            raise

    async def list_satellites(
        self, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """列出衛星"""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.api_base_url}/satellite",
                params={"limit": limit, "offset": offset},
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"列出衛星失敗: {e}")
            raise

    # ===== 無線通道相關 API =====

    async def wireless_quick_simulation(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """快速無線通道模擬"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.api_base_url}/wireless/quick-simulation", json=request_data
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"無線模擬失敗: {e}")
            raise

    async def wireless_health_check(self) -> Dict[str, Any]:
        """無線模組健康檢查"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.api_base_url}/wireless/health")

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"無線模組健康檢查失敗: {e}")
            raise

    # ===== 干擾相關 API =====

    async def simulate_interference(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """模擬干擾"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.api_base_url}/interference/simulate", json=request_data
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"干擾模擬失敗: {e}")
            raise

    # ===== 座標轉換相關 API =====

    async def convert_geo_to_cartesian(
        self, geo_coords: Dict[str, float]
    ) -> Dict[str, Any]:
        """地理座標轉笛卡爾座標"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.api_base_url}/coordinates/geo-to-cartesian", json=geo_coords
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"座標轉換失敗: {e}")
            raise

    async def convert_cartesian_to_geo(
        self, cartesian_coords: Dict[str, float]
    ) -> Dict[str, Any]:
        """笛卡爾座標轉地理座標"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.api_base_url}/coordinates/cartesian-to-geo",
                json=cartesian_coords,
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"座標轉換失敗: {e}")
            raise

    # ===== 設備相關 API =====

    async def list_devices(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """列出設備"""
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.api_base_url}/device", params={"limit": limit, "offset": offset}
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"列出設備失敗: {e}")
            raise

    async def create_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建設備"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.api_base_url}/device", json=device_data
            )

            if response.status_code == 201:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"創建設備失敗: {e}")
            raise

    # ===== 模擬相關 API =====

    async def run_simulation(self, simulation_params: Dict[str, Any]) -> Dict[str, Any]:
        """運行模擬"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.api_base_url}/simulation/run", json=simulation_params
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"運行模擬失敗: {e}")
            raise

    # ===== 批量操作 =====

    async def batch_request(
        self, requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """批量請求處理"""
        results = []

        for request in requests:
            try:
                method = request.get("method", "GET").upper()
                path = request.get("path", "")
                data = request.get("data", {})

                client = await self._get_client()

                if method == "GET":
                    response = await client.get(f"{self.api_base_url}{path}")
                elif method == "POST":
                    response = await client.post(
                        f"{self.api_base_url}{path}", json=data
                    )
                elif method == "PUT":
                    response = await client.put(f"{self.api_base_url}{path}", json=data)
                elif method == "DELETE":
                    response = await client.delete(f"{self.api_base_url}{path}")
                else:
                    raise ValueError(f"不支援的 HTTP 方法: {method}")

                if response.status_code < 400:
                    results.append(
                        {
                            "success": True,
                            "data": response.json() if response.content else None,
                            "status_code": response.status_code,
                        }
                    )
                else:
                    results.append(
                        {
                            "success": False,
                            "error": f"HTTP {response.status_code}: {response.text}",
                            "status_code": response.status_code,
                        }
                    )

            except Exception as e:
                results.append({"success": False, "error": str(e), "status_code": 500})

        return results

    # ===== 服務統計 =====

    async def get_service_stats(self) -> Dict[str, Any]:
        """獲取服務統計信息"""
        try:
            # 並行檢查各個模組的健康狀態
            health_tasks = [self.check_health(), self.wireless_health_check()]

            health_results = await asyncio.gather(*health_tasks, return_exceptions=True)

            stats = {
                "timestamp": datetime.utcnow().isoformat(),
                "service_health": {
                    "main_service": (
                        health_results[0]
                        if not isinstance(health_results[0], Exception)
                        else {"healthy": False, "error": str(health_results[0])}
                    ),
                    "wireless_module": (
                        health_results[1]
                        if not isinstance(health_results[1], Exception)
                        else {"healthy": False, "error": str(health_results[1])}
                    ),
                },
                "overall_healthy": all(
                    result.get("healthy", False)
                    for result in health_results
                    if not isinstance(result, Exception)
                ),
            }

            return stats

        except Exception as e:
            logger.error(f"獲取服務統計失敗: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "overall_healthy": False,
            }
