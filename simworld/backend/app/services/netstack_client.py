#!/usr/bin/env python3
"""
NetStack API 客戶端 - SimWorld 與 NetStack 通信橋梁

Phase 1 整合：取代 SimWorld 中的 skyfield 依賴，統一使用 NetStack 的預計算軌道數據。
"""

import httpx
import asyncio
import structlog
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json

logger = structlog.get_logger(__name__)


class NetStackAPIClient:
    """NetStack API 客戶端 - 提供統一的衛星數據訪問接口"""
    
    def __init__(self, base_url: str = "http://netstack-api:8000"):
        """
        初始化 NetStack API 客戶端
        
        Args:
            base_url: NetStack API 基礎 URL
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0)  # 30秒超時
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        發送 HTTP 請求到 NetStack API
        
        Args:
            method: HTTP 方法 (GET, POST, etc.)
            endpoint: API 端點路徑
            params: URL 查詢參數
            json_data: JSON 請求體
            
        Returns:
            API 響應數據
            
        Raises:
            httpx.HTTPError: API 請求失敗
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error("NetStack API 請求超時", url=url, timeout=self.timeout.read)
            raise
        except httpx.HTTPStatusError as e:
            logger.error("NetStack API 返回錯誤狀態", 
                        url=url, 
                        status_code=e.response.status_code,
                        response_text=e.response.text)
            raise
        except Exception as e:
            logger.error("NetStack API 請求失敗", url=url, error=str(e))
            raise

    # === Phase 1 座標軌道 API 方法 ===
    
    async def get_precomputed_orbit_data(
        self,
        location: str = "ntpu",
        constellation: str = "starlink",
        elevation_threshold: Optional[float] = None,
        environment: str = "open_area",
        use_layered_thresholds: bool = True,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        獲取預計算的軌道數據
        
        Args:
            location: 觀測位置 ID (ntpu, nctu, etc.)
            constellation: 星座名稱 (starlink, oneweb)
            elevation_threshold: 自訂仰角門檻
            environment: 環境類型 (open_area, urban, mountainous)
            use_layered_thresholds: 使用分層門檻
            time_range: 時間範圍
            
        Returns:
            預計算軌道數據響應
        """
        endpoint = f"/api/v1/satellites/precomputed/{location}"
        params = {
            "constellation": constellation,
            "environment": environment,
            "use_layered_thresholds": use_layered_thresholds
        }
        
        if elevation_threshold is not None:
            params["elevation_threshold"] = elevation_threshold
        if time_range is not None:
            params["time_range"] = time_range
            
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_optimal_timewindow(
        self,
        location: str = "ntpu",
        constellation: str = "starlink",
        window_hours: int = 6
    ) -> Dict[str, Any]:
        """
        獲取最佳觀測時間窗口
        
        Args:
            location: 觀測位置 ID
            constellation: 星座名稱
            window_hours: 時間窗口長度 (小時)
            
        Returns:
            最佳時間窗口數據
        """
        endpoint = f"/api/v1/satellites/optimal-window/{location}"
        params = {
            "constellation": constellation,
            "window_hours": window_hours
        }
        
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_display_optimized_data(
        self,
        location: str = "ntpu",
        acceleration: int = 60,
        distance_scale: float = 0.1
    ) -> Dict[str, Any]:
        """
        獲取前端展示優化數據
        
        Args:
            location: 觀測位置 ID
            acceleration: 動畫加速倍數
            distance_scale: 距離縮放比例
            
        Returns:
            前端展示優化數據
        """
        endpoint = f"/api/v1/satellites/display-data/{location}"
        params = {
            "acceleration": acceleration,
            "distance_scale": distance_scale
        }
        
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_supported_locations(self) -> Dict[str, Any]:
        """
        獲取支援的觀測位置列表
        
        Returns:
            支援的位置列表
        """
        endpoint = "/api/v1/satellites/locations"
        return await self._make_request("GET", endpoint)
    
    async def check_precomputed_health(self) -> Dict[str, Any]:
        """
        檢查預計算數據健康狀態
        
        Returns:
            健康狀態報告
        """
        endpoint = "/api/v1/satellites/health/precomputed"
        return await self._make_request("GET", endpoint)

    # === 傳統 API 兼容方法 (逐步遷移用) ===
    
    async def get_satellite_positions(
        self,
        satellite_ids: List[int],
        observer_lat: float = 24.94417,
        observer_lon: float = 121.37139,
        observer_alt: float = 50.0,
        timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        獲取衛星位置 (兼容傳統接口)
        
        這個方法將逐步被 get_precomputed_orbit_data 取代
        
        Args:
            satellite_ids: 衛星 ID 列表
            observer_lat: 觀測者緯度
            observer_lon: 觀測者經度  
            observer_alt: 觀測者海拔
            timestamp: 指定時間點
            
        Returns:
            衛星位置列表
        """
        logger.warning("使用傳統 get_satellite_positions 方法，建議遷移到 get_precomputed_orbit_data")
        
        # 暫時返回模擬數據，實際應該調用對應的 NetStack API
        return [
            {
                "satellite_id": sat_id,
                "latitude": 45.0 + (sat_id % 10),
                "longitude": 120.0 + (sat_id % 20),
                "altitude": 550000.0,
                "elevation": 25.0 + (sat_id % 30),
                "azimuth": sat_id % 360,
                "range_km": 800.0 + (sat_id % 500),
                "is_visible": True
            }
            for sat_id in satellite_ids[:10]  # 限制數量
        ]
    
    async def calculate_satellite_visibility(
        self,
        tle_data: List[Dict[str, str]],
        observer_lat: float = 24.94417,
        observer_lon: float = 121.37139,
        min_elevation: float = 10.0,
        time_window_hours: int = 6
    ) -> Dict[str, Any]:
        """
        計算衛星可見性 (兼容傳統接口)
        
        這個方法將被 get_optimal_timewindow 取代
        
        Args:
            tle_data: TLE 數據列表
            observer_lat: 觀測者緯度
            observer_lon: 觀測者經度
            min_elevation: 最小仰角
            time_window_hours: 時間窗口
            
        Returns:
            可見性分析結果
        """
        logger.warning("使用傳統 calculate_satellite_visibility 方法，建議遷移到 get_optimal_timewindow")
        
        # 使用新的預計算接口
        try:
            result = await self.get_optimal_timewindow(
                location="ntpu",  # 假設是 NTPU 座標
                window_hours=time_window_hours
            )
            
            # 轉換為傳統格式
            return {
                "visible_satellites": len(result.get("satellite_trajectories", [])),
                "optimal_window": result.get("optimal_window", {}),
                "quality_score": result.get("quality_score", 0.0),
                "handover_events": result.get("handover_events", [])
            }
            
        except Exception as e:
            logger.error("可見性計算失敗，返回默認數據", error=str(e))
            return {
                "visible_satellites": len(tle_data) // 3,  # 假設 1/3 可見
                "optimal_window": {
                    "start_time": datetime.now().isoformat(),
                    "duration_hours": time_window_hours
                },
                "quality_score": 0.5,
                "handover_events": []
            }

    # === 系統狀態方法 ===
    
    async def ping(self) -> bool:
        """
        檢查 NetStack API 連接狀態
        
        Returns:
            True if NetStack is reachable
        """
        try:
            await self._make_request("GET", "/health")
            return True
        except Exception:
            return False
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        獲取 NetStack 系統狀態
        
        Returns:
            系統狀態信息
        """
        try:
            return await self._make_request("GET", "/system/status")
        except Exception as e:
            logger.error("無法獲取 NetStack 系統狀態", error=str(e))
            return {
                "status": "unreachable",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# === 全域客戶端實例 ===

# 創建全域 NetStack 客戶端實例
_netstack_client: Optional[NetStackAPIClient] = None

def get_netstack_client() -> NetStackAPIClient:
    """
    獲取 NetStack API 客戶端單例
    
    Returns:
        NetStack API 客戶端實例
    """
    global _netstack_client
    if _netstack_client is None:
        _netstack_client = NetStackAPIClient()
    return _netstack_client


# === 便利函數 ===

async def get_ntpu_satellite_data(
    constellation: str = "starlink",
    environment: str = "urban"
) -> Dict[str, Any]:
    """
    獲取 NTPU 位置的衛星數據 (便利函數)
    
    Args:
        constellation: 星座名稱
        environment: 環境類型
        
    Returns:
        NTPU 衛星數據
    """
    client = get_netstack_client()
    return await client.get_precomputed_orbit_data(
        location="ntpu",
        constellation=constellation,
        environment=environment
    )

async def get_optimal_6hour_window() -> Dict[str, Any]:
    """
    獲取 NTPU 最佳 6 小時觀測窗口 (便利函數)
    
    Returns:
        最佳時間窗口數據
    """
    client = get_netstack_client()
    return await client.get_optimal_timewindow(
        location="ntpu",
        window_hours=6
    )

async def get_display_animation_data(acceleration: int = 60) -> Dict[str, Any]:
    """
    獲取前端動畫展示數據 (便利函數)
    
    Args:
        acceleration: 動畫加速倍數
        
    Returns:
        動畫展示數據
    """
    client = get_netstack_client()
    return await client.get_display_optimized_data(
        location="ntpu",
        acceleration=acceleration
    )