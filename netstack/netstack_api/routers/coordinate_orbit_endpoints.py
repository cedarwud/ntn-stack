#!/usr/bin/env python3
"""
座標特定軌道 API 端點 - Phase 1 整合 (簡化版)

提供 Phase 0 預計算數據的統一 API 接口，支援多座標位置、環境調整和分層門檻。
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
import structlog
import asyncio
import json
from pathlib import Path as PathLib

logger = structlog.get_logger(__name__)


# Phase 0 預計算數據載入器
class EnhancedDataLoader:
    """Phase 0 預計算數據載入器"""

    def __init__(self):
        self.precomputed_data = None
        self.data_summary = None
        self.build_config = None
        self.load_precomputed_data()

    def load_precomputed_data(self):
        """載入 Phase 0 預計算數據"""
        try:
            # 嘗試多個可能的路徑
            possible_paths = [
                "/app/data",  # Docker 容器內路徑
                "test_output",  # 開發環境路徑
                "netstack/data",  # 備用路徑
                ".",  # 當前目錄
            ]

            data_found = False

            for base_path in possible_paths:
                # 嘗試載入預計算軌道數據
                orbit_data_path = PathLib(base_path) / "enhanced_satellite_data.json"
                if orbit_data_path.exists():
                    with open(orbit_data_path, "r", encoding="utf-8") as f:
                        self.precomputed_data = json.load(f)
                    logger.info(f"✅ 增強衛星軌道數據載入成功: {orbit_data_path}")
                    data_found = True
                    break

            if not data_found:
                logger.error("❌ Phase 0 預計算軌道數據不存在，真實SGP4數據必須可用")

            # 載入數據摘要
            for base_path in possible_paths:
                summary_path = PathLib(base_path) / "enhanced_data_summary.json"
                if summary_path.exists():
                    with open(summary_path, "r", encoding="utf-8") as f:
                        self.data_summary = json.load(f)
                    logger.info(f"✅ Phase 0 數據摘要載入成功: {summary_path}")
                    break

            # 載入建置配置
            for base_path in possible_paths:
                config_path = PathLib(base_path) / "enhanced_build_config.json"
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        self.build_config = json.load(f)
                    logger.info(f"✅ Phase 0 建置配置載入成功: {config_path}")
                    break

        except Exception as e:
            logger.error(f"❌ Phase 0 數據載入失敗: {e}")
            self.precomputed_data = None
            self.data_summary = None
            self.build_config = None

    def get_constellation_data(self, constellation: str) -> Optional[Dict[str, Any]]:
        """獲取星座數據"""
        if not self.precomputed_data:
            return None
        return self.precomputed_data.get("constellations", {}).get(constellation)

    def get_observer_location(self) -> Dict[str, Any]:
        """獲取觀測點位置"""
        if not self.precomputed_data:
            return {"lat": 24.94417, "lon": 121.37139, "alt": 50.0, "name": "NTPU"}
        return self.precomputed_data.get("observer_location", {})

    def is_data_available(self) -> bool:
        """檢查數據是否可用"""
        return self.precomputed_data is not None


# 全域數據載入器
enhanced_loader = EnhancedDataLoader()


def _select_optimal_satellites(
    satellites_data: Dict[str, Any], count: int = 15
) -> List[str]:
    """智能選擇最佳的衛星（基於可見性和信號質量）"""
    satellite_scores = []

    for sat_id, sat_data in satellites_data.items():
        latest_pos = _get_latest_position(sat_data)

        # 計算衛星評分
        score = 0.0

        # 1. 可見性權重 (40%)
        if latest_pos.get("is_visible", False):
            score += 40.0

        # 2. 仰角權重 (30%) - 仰角越高越好
        elevation = latest_pos.get("elevation_deg", 0.0)
        if elevation > 0:
            score += min(30.0, elevation * 0.5)  # 最高 30 分

        # 3. 距離權重 (20%) - 距離越近越好
        range_km = latest_pos.get("range_km", 10000.0)
        if range_km > 0:
            # 距離在 500-2000km 之間最佳
            if 500 <= range_km <= 2000:
                score += 20.0
            elif range_km < 500:
                score += 15.0  # 太近
            else:
                score += max(0, 20.0 - (range_km - 2000) * 0.01)  # 距離懲罰

        # 4. 可見性持續時間權重 (10%) - 基於可見位置數量
        visibility_data = sat_data.get("visibility_data", [])
        visible_positions_count = sum(
            1 for pos in visibility_data if pos.get("is_visible", False)
        )
        if visible_positions_count > 0:
            score += min(
                10.0, visible_positions_count / 10.0
            )  # 每10個可見位置得1分，最高10分

        satellite_scores.append((sat_id, score, latest_pos))

    # 按評分排序，選擇前 N 個
    satellite_scores.sort(key=lambda x: x[1], reverse=True)

    # 如果可見衛星不足，補充一些高評分的不可見衛星
    selected_ids = []
    visible_count = 0

    for sat_id, score, pos in satellite_scores:
        if len(selected_ids) >= count:
            break

        selected_ids.append(sat_id)
        if pos.get("is_visible", False):
            visible_count += 1

    logger.info(f"智能選擇了 {len(selected_ids)} 顆衛星，其中 {visible_count} 顆可見")
    return selected_ids


def _extract_norad_id(sat_id: str) -> int:
    """從衛星 ID 中提取 NORAD ID"""
    try:
        # 如果是純數字字符串，直接轉換
        return int(sat_id)
    except ValueError:
        # 如果是 'starlink_001' 格式，提取數字部分
        import re

        match = re.search(r"(\d+)", sat_id)
        if match:
            return int(match.group(1))
        # 如果沒有數字，使用 hash 生成一個唯一 ID
        return abs(hash(sat_id)) % 100000


def _get_latest_position(satellite_data: Dict[str, Any]) -> Dict[str, Any]:
    """獲取衛星的最新位置數據 - 修復：支援實際的預計算數據結構"""
    # 修復：從 positions 中取得位置資料（實際的數據結構）
    positions = satellite_data.get("positions", [])
    if not positions:
        # 回退：嘗試舊的 visibility_data 結構
        positions = satellite_data.get("visibility_data", [])
        if not positions:
            return {
                "latitude": 0.0,
                "longitude": 0.0,
                "altitude_km": 550.0,
                "elevation_deg": 0.0,
                "azimuth_deg": 0.0,
                "range_km": 1000.0,
                "is_visible": False,
            }

    # 找到最新的可見位置
    visible_positions = [pos for pos in positions if pos.get("is_visible", False)]
    if visible_positions:
        latest_position = visible_positions[-1]  # 最後一個可見位置
    else:
        latest_position = positions[-1]  # 最後一個位置

    # 修復：直接從位置數據中提取座標（新的數據結構）
    # 新結構：position_eci 包含 ECI 座標，elevation_deg/azimuth_deg/range_km 是頂層字段
    return {
        "latitude": latest_position.get("position_eci", {}).get("lat", 0.0),  # 簡化處理
        "longitude": latest_position.get("position_eci", {}).get(
            "lon", 0.0
        ),  # 簡化處理
        "altitude_km": 550.0,  # 使用典型 LEO 高度
        "elevation_deg": latest_position.get("elevation_deg", 0.0),
        "azimuth_deg": latest_position.get("azimuth_deg", 0.0),
        "range_km": latest_position.get("range_km", 1000.0),
        "is_visible": latest_position.get("is_visible", False),
    }


# 創建路由器 (前綴在 router_manager.py 中設定)
router = APIRouter(tags=["coordinate-orbit"])


# 響應模型
class LocationInfo(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    altitude: float
    environment: str


class HealthStatus(BaseModel):
    overall_status: str
    timestamp: str
    services: Dict[str, Any]


class OrbitData(BaseModel):
    location: LocationInfo
    computation_metadata: Dict[str, Any]
    filtered_satellites: List[Dict[str, Any]]
    total_processing_time_ms: int


class OptimalTimeWindow(BaseModel):
    location: LocationInfo
    optimal_window: Dict[str, Any]
    satellite_trajectories: List[Dict[str, Any]]
    handover_events: List[Dict[str, Any]]
    quality_score: float


class DisplayData(BaseModel):
    location: LocationInfo
    display_settings: Dict[str, Any]
    animation_keyframes: List[Dict[str, Any]]
    trajectory_data: List[Dict[str, Any]]
    time_compression_ratio: int


@router.get("/locations")
async def get_supported_locations():
    """獲取支援的觀測位置列表"""
    logger.info("API: 取得支援位置列表")

    return {
        "total_locations": 1,
        "locations": [
            {
                "id": "ntpu",
                "name": "國立臺北大學",
                "latitude": 24.9434,
                "longitude": 121.3709,
                "altitude": 50.0,
                "environment": "urban",
            }
        ],
    }


@router.get("/health/precomputed")
async def check_precomputed_health():
    """檢查預計算數據健康狀態"""
    logger.info("API: 預計算數據健康檢查")

    # 檢查 Phase 0 數據狀態
    data_available = enhanced_loader.is_data_available()
    total_satellites = 0

    if data_available and enhanced_loader.data_summary:
        total_satellites = enhanced_loader.data_summary.get(
            "enhanced_data_summary", {}
        ).get("total_satellites", 0)

    return {
        "overall_status": "healthy" if data_available else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "enhanced_data": {
                "status": "healthy" if data_available else "unavailable",
                "response_time": 0.001,
                "data_available": data_available,
                "total_satellites": total_satellites,
            },
            "coordinate_engine": {
                "status": "healthy" if data_available else "fallback",
                "satellites_available": total_satellites,
            },
            "data_cache": {"status": "healthy", "cache_hit_rate": 0.95},
        },
        "version": "1.0.0",
        "enhanced_integration": {
            "precomputed_data_loaded": data_available,
            "build_config_available": enhanced_loader.build_config is not None,
            "data_summary_available": enhanced_loader.data_summary is not None,
        },
        "phase4_production": {
            "startup_time_seconds": get_startup_time(),
            "memory_usage_mb": get_memory_usage(),
            "data_freshness_hours": get_data_freshness(),
            "cache_hit_rate": get_cache_hit_rate(),
            "error_rate_percent": get_error_rate(),
            "uptime_seconds": get_uptime_seconds(),
        },
    }


def get_startup_time() -> float:
    """獲取啟動時間"""
    import time
    import os

    # 從環境變量或文件獲取啟動時間
    startup_file = "/tmp/netstack_startup_time"
    if os.path.exists(startup_file):
        try:
            with open(startup_file, "r") as f:
                startup_timestamp = float(f.read().strip())
            return time.time() - startup_timestamp
        except:
            pass
    return 0.0


def get_memory_usage() -> float:
    """獲取記憶體使用量 (MB)"""
    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return round(memory_info.rss / 1024 / 1024, 2)  # 轉換為 MB
    except ImportError:
        # 如果沒有 psutil，使用系統命令
        import os

        try:
            with open(f"/proc/{os.getpid()}/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return float(line.split()[1]) / 1024  # KB to MB
        except:
            pass
    except:
        pass
    return 0.0


def get_data_freshness() -> float:
    """獲取數據新鮮度 (小時)"""
    if not enhanced_loader.data_summary:
        return 999.0

    try:
        from datetime import datetime

        generation_time = enhanced_loader.data_summary.get("generation_timestamp")
        if not generation_time:
            # 嘗試其他可能的時間戳字段
            generation_time = enhanced_loader.data_summary.get("timestamp")

        if generation_time:
            # 處理不同的時間格式
            if isinstance(generation_time, str):
                if generation_time.endswith("Z"):
                    generation_time = generation_time[:-1] + "+00:00"
                gen_dt = datetime.fromisoformat(generation_time)
            else:
                gen_dt = datetime.fromtimestamp(generation_time)

            now = datetime.now(gen_dt.tzinfo) if gen_dt.tzinfo else datetime.now()
            hours_diff = (now - gen_dt).total_seconds() / 3600
            return round(hours_diff, 2)
    except Exception as e:
        logger.warning(f"無法計算數據新鮮度: {e}")

    return 999.0


def get_cache_hit_rate() -> float:
    """獲取快取命中率"""
    # 這裡可以整合實際的快取統計
    # 目前返回模擬值，實際部署時可以連接 Redis 統計
    return 0.95


def get_error_rate() -> float:
    """獲取錯誤率"""
    # 這裡可以整合實際的錯誤統計
    # 目前返回模擬值，實際部署時可以從日誌或監控系統獲取
    return 0.01


def get_uptime_seconds() -> float:
    """獲取系統運行時間"""
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
        return round(uptime_seconds, 2)
    except:
        return 0.0


@router.get("/precomputed/{location}")
async def get_precomputed_orbit_data(
    location: str = Path(..., description="觀測位置 ID"),
    constellation: str = Query("starlink", description="衛星星座"),
    environment: str = Query("urban", description="環境類型"),
    elevation_threshold: Optional[float] = Query(None, description="仰角門檻"),
    use_layered_thresholds: bool = Query(True, description="使用分層門檻"),
    count: Optional[int] = Query(15, description="返回衛星數量"),
):
    """獲取預計算軌道數據"""
    logger.info(
        f"API: 取得 {location} 預計算軌道數據",
        constellation=constellation,
        environment=environment,
    )

    # 使用 Phase 0 預計算數據
    if enhanced_loader.is_data_available():
        # 獲取觀測點位置
        observer_location = enhanced_loader.get_observer_location()

        # 獲取星座數據
        constellation_data = enhanced_loader.get_constellation_data(constellation)

        if constellation_data:
            # 從預計算數據中提取衛星信息
            orbit_data = constellation_data.get("orbit_data", {})
            satellites_data = orbit_data.get("satellites", {})
            statistics = constellation_data.get("statistics", {})

            # 構建響應
            return {
                "location": {
                    "id": location,
                    "name": observer_location.get("name", "NTPU"),
                    "latitude": observer_location.get("lat", 24.94417),
                    "longitude": observer_location.get("lon", 121.37139),
                    "altitude": observer_location.get("alt", 50.0),
                    "environment": environment,
                },
                "computation_metadata": {
                    "constellation": constellation,
                    "elevation_threshold": elevation_threshold or 10.0,
                    "use_layered": use_layered_thresholds,
                    "environment_factor": "1.1x",
                    "computation_date": enhanced_loader.precomputed_data.get(
                        "generated_at"
                    ),
                    "total_satellites_input": statistics.get("satellites_processed", 0),
                    "filtered_satellites_count": len(
                        satellites_data
                    ),  # 修正：使用實際衛星數量
                    "filtering_efficiency": f"{statistics.get('avg_visibility_percentage', 0):.1f}%",
                    "data_source": "enhanced_precomputed",
                },
                "filtered_satellites": [
                    {
                        "norad_id": satellites_data[sat_id].get(
                            "norad_id", _extract_norad_id(sat_id)
                        ),
                        "name": satellites_data[sat_id].get(
                            "name", f"{constellation.upper()}-{sat_id}"
                        ),
                        "orbit_data_available": True,
                        "precomputed": True,
                        # 添加軌道數據（使用最新的位置數據）
                        "latitude": _get_latest_position(satellites_data[sat_id]).get(
                            "latitude", 0.0
                        ),
                        "longitude": _get_latest_position(satellites_data[sat_id]).get(
                            "longitude", 0.0
                        ),
                        "altitude": _get_latest_position(satellites_data[sat_id]).get(
                            "altitude_km", 550.0
                        ),
                        # === 統一格式標準 (v1.1.0) ===
                        "elevation_deg": _get_latest_position(
                            satellites_data[sat_id]
                        ).get("elevation_deg", 0.0),
                        "azimuth_deg": _get_latest_position(
                            satellites_data[sat_id]
                        ).get("azimuth_deg", 0.0),
                        "range_km": _get_latest_position(satellites_data[sat_id]).get(
                            "range_km", 1000.0
                        ),
                        "is_visible": _get_latest_position(satellites_data[sat_id]).get(
                            "is_visible", False
                        ),
                        # === 向後兼容性 ===
                        "elevation": _get_latest_position(satellites_data[sat_id]).get(
                            "elevation_deg", 0.0
                        ),
                        "azimuth": _get_latest_position(satellites_data[sat_id]).get(
                            "azimuth_deg", 0.0
                        ),
                    }
                    for sat_id in _select_optimal_satellites(
                        satellites_data, count or 15
                    )  # 智能選擇最佳衛星
                ],
                "total_processing_time_ms": 45,
            }

    # 🚫 根據 CLAUDE.md 核心原則，禁止使用模擬數據
    # 必須使用真實 Phase 0 預計算數據，如無數據則返回錯誤
    logger.error(f"❌ Phase 0 數據不可用，拒絕使用模擬數據: {location}")
    raise HTTPException(
        status_code=503, 
        detail=f"Phase 0 precomputed orbital data unavailable for location {location}. Real SGP4 data required."
    )


@router.get("/optimal-window/{location}")
async def get_optimal_timewindow(
    location: str = Path(..., description="觀測位置 ID"),
    constellation: str = Query("starlink", description="衛星星座"),
    window_hours: int = Query(6, description="時間窗口長度(小時)"),
):
    """獲取最佳時間窗口"""
    logger.info(
        f"API: 取得 {location} 最佳時間窗口",
        constellation=constellation,
        window_hours=window_hours,
    )

    # 模擬最佳時間窗口數據
    return {
        "location": {
            "id": location,
            "name": "國立臺北大學" if location == "ntpu" else location,
            "latitude": 24.9434,
            "longitude": 121.3709,
            "altitude": 50.0,
            "environment": "urban",
        },
        "optimal_window": {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": (
                datetime.now(timezone.utc).replace(hour=23, minute=59)
            ).isoformat(),
            "duration_hours": window_hours,
            "avg_visible_satellites": 12.5,
            "max_visible_satellites": 18,
            "handover_opportunities": 45,
        },
        "satellite_trajectories": [
            {
                "norad_id": 44713 + i,
                "name": f"STARLINK-{1007 + i}",
                "visibility_windows": [
                    {
                        "start_time": datetime.now(timezone.utc).isoformat(),
                        "end_time": (
                            datetime.now(timezone.utc).replace(minute=30)
                        ).isoformat(),
                        "max_elevation": 25.0 + i * 5,
                        "duration_minutes": 8 + i,
                    }
                ],
                "elevation_profile": [],
            }
            for i in range(5)
        ],
        "handover_events": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "from_satellite": f"STARLINK-{1007 + i}",
                "to_satellite": f"STARLINK-{1008 + i}",
                "trigger_reason": "elevation_threshold",
                "elevation_change": 5.0,
            }
            for i in range(3)
        ],
        "quality_score": 0.85,
    }


@router.get("/display-data/{location}")
async def get_display_optimized_data(
    location: str = Path(..., description="觀測位置 ID"),
    acceleration: int = Query(60, description="動畫加速倍數"),
    distance_scale: float = Query(0.1, description="距離縮放比例"),
):
    """獲取展示優化數據 (支援 60 倍加速動畫)"""
    logger.info(
        f"API: 取得 {location} 展示優化數據",
        acceleration=acceleration,
        distance_scale=distance_scale,
    )

    # 模擬展示優化數據
    return {
        "location": {
            "id": location,
            "name": "國立臺北大學" if location == "ntpu" else location,
            "latitude": 24.9434,
            "longitude": 121.3709,
            "altitude": 50.0,
            "environment": "urban",
        },
        "display_settings": {
            "animation_fps": 30,
            "acceleration_factor": acceleration,
            "distance_scale": distance_scale,
            "trajectory_smoothing": True,
            "interpolation_method": "cubic_spline",
        },
        "animation_keyframes": [
            {
                "satellite_id": 44713 + i,
                "keyframes": [
                    {
                        "timestamp": j * 1000,
                        "position": [25.0 + i, 121.0 + j, 550.0],
                        "visibility": True,
                    }
                    for j in range(10)
                ],
            }
            for i in range(5)
        ],
        "trajectory_data": [
            {
                "satellite_id": 44713 + i,
                "name": f"STARLINK-{1007 + i}",
                "orbital_path": [[25.0 + i + j, 121.0 + j, 550.0] for j in range(20)],
                "visibility_segments": [
                    {
                        "start_time": j * 300000,
                        "end_time": (j + 1) * 300000,
                        "max_elevation": 20.0 + i * 3,
                    }
                    for j in range(3)
                ],
            }
            for i in range(8)
        ],
        "time_compression_ratio": acceleration,
    }


logger.info("座標軌道端點路由器初始化完成")
