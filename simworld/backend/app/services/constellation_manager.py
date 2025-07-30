"""
衛星星座管理系統 - 多衛星星座配置和管理

功能：
1. 多星座同時管理（Starlink, OneWeb, GPS等）
2. 衛星可見性計算和篩選
3. 最佳衛星選擇算法
4. 星座覆蓋分析

符合 d2.md 中 Phase 3 的要求
"""

import asyncio
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor


# TLE 數據現在由 NetStack 統一管理，移除本地 TLE 服務依賴
@dataclass
class TLEData:
    """簡化的 TLE 數據類型（用於向後兼容）"""

    name: str
    line1: str
    line2: str
    epoch: Optional[str] = None
    
    @property
    def satellite_name(self) -> str:
        """為了向後兼容提供 satellite_name 屬性"""
        return self.name
        
    @property
    def catalog_number(self) -> int:
        """從 TLE line1 提取 NORAD ID"""
        try:
            return int(self.line1[2:7])
        except:
            return 40000  # 預設值


from .sgp4_calculator import SGP4Calculator, OrbitPosition
from .distance_calculator import DistanceCalculator, Position

logger = logging.getLogger(__name__)


@dataclass
class SatelliteInfo:
    """衛星信息結構"""

    tle_data: TLEData
    current_position: Optional[OrbitPosition] = None
    elevation_angle: float = 0.0
    azimuth_angle: float = 0.0
    distance: float = 0.0
    is_visible: bool = False
    signal_strength: float = 0.0
    constellation: str = ""


@dataclass
class ConstellationConfig:
    """星座配置"""

    name: str
    min_elevation: float = 10.0  # 最小仰角（度）
    max_satellites: int = 50  # 最大同時跟蹤衛星數
    priority: int = 1  # 優先級（1最高）
    frequency_band: str = "Ku"  # 頻段
    enabled: bool = True


@dataclass
class CoverageAnalysis:
    """覆蓋分析結果"""

    total_satellites: int
    visible_satellites: int
    best_satellite: Optional[SatelliteInfo]
    coverage_percentage: float
    average_elevation: float
    constellation_distribution: Dict[str, int]


class ConstellationManager:
    """衛星星座管理器"""

    def __init__(self):
        # TLE 數據現在由 NetStack 統一管理，移除本地 TLE 服務
        # self.tle_service = TLEDataService()  # 已移除
        self.sgp4_calculator = SGP4Calculator()
        self.distance_calculator = DistanceCalculator()

        # 預定義星座配置 - 與 NetStack 96分鐘預處理標準一致
        self.constellation_configs = {
            "starlink": ConstellationConfig(
                name="Starlink",
                min_elevation=10.0,  # 與 NetStack 預處理標準一致（10°）
                max_satellites=10,
                priority=1,
                frequency_band="Ku/Ka",
                enabled=True,
            ),
            "oneweb": ConstellationConfig(
                name="OneWeb",
                min_elevation=10.0,  # 與 NetStack 預處理標準一致（10°）
                max_satellites=8,
                priority=2,
                frequency_band="Ku",
                enabled=True,
            ),
            "gps": ConstellationConfig(
                name="GPS",
                min_elevation=10.0,  # 與 NetStack 預處理標準一致（10°）
                max_satellites=12,
                priority=3,
                frequency_band="L",
                enabled=True,
            ),
        }

        # 緩存
        self._satellite_cache: Dict[str, List[SatelliteInfo]] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)  # 緩存5分鐘

        # 初始化標記
        self._initialized = False

    async def get_visible_satellites(
        self,
        observer_position: Position,
        timestamp: Optional[datetime] = None,
        constellations: Optional[List[str]] = None,
    ) -> List[SatelliteInfo]:
        """
        獲取指定位置可見的衛星

        Args:
            observer_position: 觀測者位置
            timestamp: 觀測時間（默認當前時間）
            constellations: 指定星座列表（默認所有啟用的星座）

        Returns:
            可見衛星列表
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        if constellations is None:
            constellations = [
                name
                for name, config in self.constellation_configs.items()
                if config.enabled
            ]

        try:
            # 檢查緩存
            if self._is_cache_valid():
                logger.debug("使用緩存的衛星數據")
                cached_satellites = []
                for constellation in constellations:
                    if constellation in self._satellite_cache:
                        cached_satellites.extend(self._satellite_cache[constellation])
            else:
                # 重新計算
                logger.info(f"計算可見衛星: {constellations}")
                cached_satellites = await self._calculate_satellite_positions(
                    constellations, timestamp
                )

            # 篩選可見衛星
            visible_satellites = []
            for sat_info in cached_satellites:
                if sat_info.constellation not in constellations:
                    continue

                config = self.constellation_configs.get(sat_info.constellation)
                if not config or not config.enabled:
                    continue

                # 計算相對於觀測者的角度和距離
                if sat_info.current_position:
                    elevation = self.distance_calculator.calculate_elevation_angle(
                        observer_position, sat_info.current_position
                    )
                    azimuth = self.distance_calculator.calculate_azimuth_angle(
                        observer_position, sat_info.current_position
                    )

                    # 計算距離
                    distance_result = self.distance_calculator.calculate_d2_distances(
                        observer_position, sat_info.current_position, observer_position
                    )

                    # 如果衛星已經從 NetStack 標記為可見，使用 NetStack 的數據（96分鐘預處理）
                    if hasattr(sat_info, 'is_visible') and sat_info.is_visible and sat_info.elevation_angle > 0:
                        # 使用 NetStack 預處理的數據，不需要重新計算
                        visible_satellites.append(sat_info)
                    else:
                        # 舊的計算邏輯作為備用
                        sat_info.elevation_angle = elevation
                        sat_info.azimuth_angle = azimuth
                        sat_info.distance = (
                            distance_result.satellite_distance / 1000
                        )  # 轉換為 km
                        sat_info.is_visible = elevation >= config.min_elevation
                        sat_info.signal_strength = self._calculate_signal_strength(
                            elevation, sat_info.distance
                        )

                        if sat_info.is_visible:
                            visible_satellites.append(sat_info)

            # 按優先級和信號強度排序
            visible_satellites.sort(
                key=lambda x: (
                    -self.constellation_configs[x.constellation].priority,
                    -x.signal_strength,
                    x.distance,
                )
            )

            # 限制每個星座的衛星數量
            filtered_satellites = []
            constellation_counts = {}

            for sat_info in visible_satellites:
                constellation = sat_info.constellation
                config = self.constellation_configs[constellation]

                if constellation_counts.get(constellation, 0) < config.max_satellites:
                    filtered_satellites.append(sat_info)
                    constellation_counts[constellation] = (
                        constellation_counts.get(constellation, 0) + 1
                    )

            logger.info(f"找到 {len(filtered_satellites)} 顆可見衛星")
            return filtered_satellites

        except Exception as e:
            logger.error(f"獲取可見衛星失敗: {e}")
            return []

    async def get_best_satellite(
        self,
        observer_position: Position,
        timestamp: Optional[datetime] = None,
        constellation: Optional[str] = None,
    ) -> Optional[SatelliteInfo]:
        """
        獲取最佳衛星（信號最強、仰角最高）

        Args:
            observer_position: 觀測者位置
            timestamp: 觀測時間
            constellation: 指定星座（可選）

        Returns:
            最佳衛星信息
        """
        constellations = [constellation] if constellation else None
        visible_satellites = await self.get_visible_satellites(
            observer_position, timestamp, constellations
        )

        if not visible_satellites:
            return None

        # 選擇信號最強的衛星
        best_satellite = max(visible_satellites, key=lambda x: x.signal_strength)

        logger.info(
            f"最佳衛星: {best_satellite.tle_data.satellite_name} "
            f"(仰角: {best_satellite.elevation_angle:.1f}°, "
            f"信號強度: {best_satellite.signal_strength:.2f})"
        )

        return best_satellite

    async def analyze_coverage(
        self,
        observer_position: Position,
        timestamp: Optional[datetime] = None,
        analysis_duration_minutes: int = 60,
    ) -> CoverageAnalysis:
        """
        分析指定時間段的星座覆蓋情況

        Args:
            observer_position: 觀測者位置
            timestamp: 開始時間
            analysis_duration_minutes: 分析時長（分鐘）

        Returns:
            覆蓋分析結果
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        try:
            logger.info(f"開始覆蓋分析: {analysis_duration_minutes} 分鐘")

            # 獲取當前可見衛星
            visible_satellites = await self.get_visible_satellites(
                observer_position, timestamp
            )

            if not visible_satellites:
                return CoverageAnalysis(
                    total_satellites=0,
                    visible_satellites=0,
                    best_satellite=None,
                    coverage_percentage=0.0,
                    average_elevation=0.0,
                    constellation_distribution={},
                )

            # 統計星座分布
            constellation_distribution = {}
            total_elevation = 0.0

            for sat_info in visible_satellites:
                constellation = sat_info.constellation
                constellation_distribution[constellation] = (
                    constellation_distribution.get(constellation, 0) + 1
                )
                total_elevation += sat_info.elevation_angle

            # 計算平均仰角
            average_elevation = (
                total_elevation / len(visible_satellites) if visible_satellites else 0.0
            )

            # 獲取最佳衛星
            best_satellite = max(visible_satellites, key=lambda x: x.signal_strength)

            # 計算覆蓋百分比（基於可見衛星數量和配置的最大值）
            total_max_satellites = sum(
                config.max_satellites
                for config in self.constellation_configs.values()
                if config.enabled
            )
            coverage_percentage = (
                (len(visible_satellites) / total_max_satellites) * 100
                if total_max_satellites > 0
                else 0.0
            )

            analysis_result = CoverageAnalysis(
                total_satellites=len(visible_satellites),
                visible_satellites=len(visible_satellites),
                best_satellite=best_satellite,
                coverage_percentage=min(coverage_percentage, 100.0),
                average_elevation=average_elevation,
                constellation_distribution=constellation_distribution,
            )

            logger.info(
                f"覆蓋分析完成: {len(visible_satellites)} 顆可見衛星, "
                f"覆蓋率: {coverage_percentage:.1f}%"
            )

            return analysis_result

        except Exception as e:
            logger.error(f"覆蓋分析失敗: {e}")
            return CoverageAnalysis(
                total_satellites=0,
                visible_satellites=0,
                best_satellite=None,
                coverage_percentage=0.0,
                average_elevation=0.0,
                constellation_distribution={},
            )

    async def predict_satellite_passes(
        self,
        observer_position: Position,
        satellite_id: str,
        start_time: datetime,
        duration_hours: int = 24,
    ) -> List[Dict]:
        """
        預測衛星過境時間

        Args:
            observer_position: 觀測者位置
            satellite_id: 衛星 NORAD ID
            start_time: 開始時間
            duration_hours: 預測時長（小時）

        Returns:
            過境預測列表
        """
        try:
            # TLE 服務已移除，返回模擬數據
            logger.warning(f"TLE 服務已移除，返回衛星 {satellite_id} 的模擬過境數據")
            
            # 返回模擬的過境數據
            mock_passes = []
            current_time = start_time
            for i in range(0, duration_hours, 3):  # 每3小時一次過境
                pass_time = current_time + timedelta(hours=i, minutes=30)
                mock_passes.append({
                    "start_time": pass_time.isoformat(),
                    "end_time": (pass_time + timedelta(minutes=10)).isoformat(),
                    "max_elevation_time": (pass_time + timedelta(minutes=5)).isoformat(),
                    "max_elevation": 45.0 + (i % 3) * 15,  # 45-75度變化
                    "azimuth": 90.0 + (i % 4) * 90,        # 四個方向輪替
                    "duration_minutes": 10.0,
                })
            
            return mock_passes

        except Exception as e:
            logger.error(f"衛星過境預測失敗: {e}")
            return []

    async def _calculate_satellite_positions(
        self, constellations: List[str], timestamp: datetime
    ) -> List[SatelliteInfo]:
        """計算所有衛星的當前位置 - 使用 NetStack 96 分鐘預處理數據"""
        all_satellites = []

        logger.info(f"從 NetStack 獲取 96 分鐘預處理數據，星座: {constellations}")
        
        try:
            # 調用 NetStack 的預處理數據 API
            import aiohttp
            netstack_url = "http://netstack-api:8080/api/v1/satellites/precomputed/ntpu"
            
            for constellation in constellations:
                if constellation not in self.constellation_configs:
                    continue
                    
                config = self.constellation_configs[constellation]
                
                try:
                    async with aiohttp.ClientSession() as session:
                        params = {
                            "constellation": constellation,
                            "count": config.max_satellites
                        }
                        async with session.get(netstack_url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                filtered_satellites = data.get("filtered_satellites", [])
                                logger.info(f"從 NetStack 獲取 {constellation} 星座數據: {len(filtered_satellites)} 顆衛星")
                                
                                for sat_data in filtered_satellites:
                                    # 從預處理數據構建 TLE 數據
                                    sat_name = sat_data.get("name", f"{constellation}-{sat_data.get('norad_id', 'unknown')}")
                                    norad_id = sat_data.get("norad_id", 40000)
                                    
                                    mock_tle = TLEData(
                                        name=sat_name,
                                        line1=f"1 {norad_id:05d}U 23001001 23001.50000000  .00001000  00000-0  50000-4 0  9999",
                                        line2=f"2 {norad_id:05d}  53.0000   0.0000 0001000   0.0000   0.0000 15.50000000    10"
                                    )
                                    
                                    # 從預處理數據提取位置信息（NetStack API 直接提供位置數據）
                                    if sat_data.get("is_visible", False):
                                        from .sgp4_calculator import OrbitPosition
                                        current_position = OrbitPosition(
                                            latitude=sat_data.get("latitude", 0.0),
                                            longitude=sat_data.get("longitude", 0.0),
                                            altitude=sat_data.get("altitude", 550.0),
                                            velocity=(7.8, 0.0, 0.0),  # 典型軌道速度 (x, y, z)
                                            timestamp=timestamp,
                                            satellite_id=str(norad_id)
                                        )
                                        
                                        # 計算觀測角度和信號強度（使用 NetStack 預計算數據）
                                        elevation_angle = sat_data.get("elevation_deg", 0.0)
                                        azimuth_angle = sat_data.get("azimuth_deg", 0.0)
                                        range_km = sat_data.get("range_km", 1000.0)
                                        
                                        # 基於仰角計算信號強度
                                        signal_strength = max(0.1, elevation_angle / 90.0 * 0.9 + 0.1)
                                        
                                        sat_info = SatelliteInfo(
                                            tle_data=mock_tle,
                                            current_position=current_position,
                                            constellation=constellation,
                                            elevation_angle=elevation_angle,
                                            azimuth_angle=azimuth_angle,
                                            signal_strength=signal_strength,
                                            distance=range_km,
                                            is_visible=True
                                        )
                                        all_satellites.append(sat_info)
                                        
                            else:
                                logger.warning(f"NetStack API 調用失敗: {response.status} for {constellation}")
                                
                except Exception as e:
                    logger.error(f"從 NetStack 獲取 {constellation} 數據失敗: {e}")
                    
        except Exception as e:
            logger.error(f"NetStack API 調用失敗: {e}")
            
        # 如果沒有從 NetStack 獲取到數據，使用簡單的模擬數據作為備用
        if not all_satellites:
            logger.warning("NetStack 數據獲取失敗，使用備用模擬數據")
            for constellation in constellations:
                if constellation not in self.constellation_configs:
                    continue
                    
                config = self.constellation_configs[constellation]
                
                # 生成少量備用衛星數據
                for i in range(min(config.max_satellites, 3)):
                    mock_tle = TLEData(
                        name=f"{constellation}_backup_{i+1}",
                        line1=f"1 {50000+i:05d}U 23001{i:03d} 23001.50000000  .00001000  00000-0  50000-4 0  9999",
                        line2=f"2 {50000+i:05d}  53.0000 {i*72:7.4f} 0001000 {i*36:7.4f} {i*45:7.4f} 15.50000000{i*1000:6d}"
                    )
                    
                    orbital_angle = (i * 72 + timestamp.timestamp() * 0.001) % 360
                    radius_km = 550 + i * 10
                    
                    lat = 45 * math.sin(math.radians(orbital_angle))
                    lon = (orbital_angle + timestamp.timestamp() * 0.01) % 360 - 180
                    alt = radius_km
                    
                    from .sgp4_calculator import OrbitPosition
                    mock_position = OrbitPosition(
                        latitude=lat,
                        longitude=lon,
                        altitude=alt,
                        velocity=(7.8, 0.0, 0.0),  # 典型軌道速度 (x, y, z)
                        timestamp=timestamp,
                        satellite_id=f"{constellation}_backup_{i+1}"
                    )
                    
                    sat_info = SatelliteInfo(
                        tle_data=mock_tle,
                        current_position=mock_position,
                        constellation=constellation,
                        elevation_angle=30.0 + i * 10,  # 模擬仰角
                        azimuth_angle=(i * 120) % 360,  # 模擬方位角
                        signal_strength=0.7 + i * 0.1,  # 模擬信號強度
                        distance=alt,  # 距離
                        is_visible=True
                    )
                    all_satellites.append(sat_info)

        # 更新緩存
        self._satellite_cache = {}
        for sat_info in all_satellites:
            if sat_info.constellation not in self._satellite_cache:
                self._satellite_cache[sat_info.constellation] = []
            self._satellite_cache[sat_info.constellation].append(sat_info)

        self._cache_timestamp = timestamp
        logger.info(f"總共載入了 {len(all_satellites)} 顆衛星數據 (來源: NetStack 96分鐘預處理)")

        return all_satellites

    def _calculate_signal_strength(
        self, elevation_angle: float, distance_km: float
    ) -> float:
        """
        計算信號強度（簡化模型）

        Args:
            elevation_angle: 仰角（度）
            distance_km: 距離（公里）

        Returns:
            信號強度（0-1）
        """
        if elevation_angle <= 0:
            return 0.0

        # 基於仰角的信號強度（仰角越高信號越強）
        elevation_factor = min(elevation_angle / 90.0, 1.0)

        # 基於距離的信號衰減（自由空間路徑損耗）
        # 假設參考距離為 500km
        reference_distance = 500.0
        distance_factor = (
            reference_distance / max(distance_km, reference_distance)
        ) ** 2

        # 大氣衰減因子（仰角低時大氣衰減更嚴重）
        atmospheric_factor = 1.0 - (1.0 - elevation_factor) * 0.3

        # 綜合信號強度
        signal_strength = elevation_factor * distance_factor * atmospheric_factor

        return min(signal_strength, 1.0)

    def _is_cache_valid(self) -> bool:
        """檢查緩存是否有效"""
        if self._cache_timestamp is None:
            return False

        now = datetime.now(timezone.utc)
        return (now - self._cache_timestamp) < self._cache_duration

    def update_constellation_config(
        self, constellation: str, config: ConstellationConfig
    ) -> bool:
        """更新星座配置"""
        try:
            self.constellation_configs[constellation] = config
            logger.info(f"更新星座配置: {constellation}")

            # 清除緩存以強制重新計算
            self._satellite_cache.clear()
            self._cache_timestamp = None

            return True
        except Exception as e:
            logger.error(f"更新星座配置失敗: {e}")
            return False

    def get_constellation_configs(self) -> Dict[str, ConstellationConfig]:
        """獲取所有星座配置"""
        return self.constellation_configs.copy()

    async def get_constellation_statistics(self) -> Dict[str, Dict]:
        """獲取星座統計信息 - 使用模擬數據"""
        stats = {}

        for constellation_name, config in self.constellation_configs.items():
            if not config.enabled:
                continue

            try:
                # TLE 服務已移除，返回模擬統計數據
                mock_satellite_counts = {
                    "starlink": 4200,
                    "oneweb": 648,
                    "gps": 31,
                    "galileo": 30
                }
                
                mock_altitudes = {
                    "starlink": 550,
                    "oneweb": 1200,
                    "gps": 20200,
                    "galileo": 23200
                }

                total_sats = mock_satellite_counts.get(constellation_name, 100)
                avg_altitude = mock_altitudes.get(constellation_name, 550)

                stats[constellation_name] = {
                    "name": config.name,
                    "total_satellites": total_sats,
                    "valid_satellites": total_sats - 10,  # 假設10顆無效
                    "average_altitude": avg_altitude,
                    "inclination_range": {"min": 50, "max": 55},
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "data_source": "simulated",
                    "config": {
                        "min_elevation": config.min_elevation,
                        "max_satellites": config.max_satellites,
                        "priority": config.priority,
                        "frequency_band": config.frequency_band,
                        "enabled": config.enabled,
                    },
                }
                
                logger.info(f"返回 {constellation_name} 的模擬統計數據")
                
            except Exception as e:
                logger.error(f"生成 {constellation_name} 統計信息失敗: {e}")
                stats[constellation_name] = {
                    "name": config.name,
                    "error": str(e),
                    "config": {
                        "min_elevation": config.min_elevation,
                        "max_satellites": config.max_satellites,
                        "priority": config.priority,
                        "frequency_band": config.frequency_band,
                        "enabled": config.enabled,
                    },
                }

        return stats

    async def simulate_handover_scenario(
        self,
        observer_position: Position,
        start_time: datetime,
        duration_minutes: int = 30,
    ) -> List[Dict]:
        """
        模擬衛星切換場景

        Args:
            observer_position: 觀測者位置
            start_time: 開始時間
            duration_minutes: 模擬時長（分鐘）

        Returns:
            切換事件列表
        """
        try:
            handover_events = []
            current_time = start_time
            end_time = start_time + timedelta(minutes=duration_minutes)
            step_seconds = 30  # 30秒步長

            current_best_satellite = None

            while current_time <= end_time:
                # 獲取當前最佳衛星
                best_satellite = await self.get_best_satellite(
                    observer_position, current_time
                )

                # 檢查是否需要切換
                if best_satellite and (
                    current_best_satellite is None
                    or best_satellite.tle_data.catalog_number
                    != current_best_satellite.tle_data.catalog_number
                ):
                    handover_event = {
                        "timestamp": current_time.isoformat(),
                        "event_type": (
                            "handover"
                            if current_best_satellite
                            else "initial_acquisition"
                        ),
                        "old_satellite": (
                            {
                                "name": current_best_satellite.tle_data.satellite_name,
                                "norad_id": current_best_satellite.tle_data.catalog_number,
                                "constellation": current_best_satellite.constellation,
                                "elevation": current_best_satellite.elevation_angle,
                                "signal_strength": current_best_satellite.signal_strength,
                            }
                            if current_best_satellite
                            else None
                        ),
                        "new_satellite": {
                            "name": best_satellite.tle_data.satellite_name,
                            "norad_id": best_satellite.tle_data.catalog_number,
                            "constellation": best_satellite.constellation,
                            "elevation": best_satellite.elevation_angle,
                            "signal_strength": best_satellite.signal_strength,
                        },
                        "reason": self._determine_handover_reason(
                            current_best_satellite, best_satellite
                        ),
                    }

                    handover_events.append(handover_event)
                    current_best_satellite = best_satellite

                    logger.info(
                        f"衛星切換: {handover_event['event_type']} at {current_time}"
                    )

                current_time += timedelta(seconds=step_seconds)

            logger.info(f"模擬完成: {len(handover_events)} 次切換事件")
            return handover_events

        except Exception as e:
            logger.error(f"切換場景模擬失敗: {e}")
            return []

    def _determine_handover_reason(
        self, old_satellite: Optional[SatelliteInfo], new_satellite: SatelliteInfo
    ) -> str:
        """確定切換原因"""
        if old_satellite is None:
            return "initial_acquisition"

        if old_satellite.elevation_angle < 10:
            return "low_elevation"

        if new_satellite.signal_strength > old_satellite.signal_strength * 1.2:
            return "better_signal"

        if new_satellite.constellation != old_satellite.constellation:
            priority_old = self.constellation_configs[
                old_satellite.constellation
            ].priority
            priority_new = self.constellation_configs[
                new_satellite.constellation
            ].priority
            if priority_new < priority_old:
                return "higher_priority_constellation"

        return "optimization"

    async def get_optimal_handover_targets(
        self,
        observer_position: Position,
        current_satellite: Optional[SatelliteInfo],
        timestamp: Optional[datetime] = None,
        prediction_window_minutes: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        獲取最佳切換目標衛星

        Args:
            observer_position: 觀測者位置
            current_satellite: 當前衛星
            timestamp: 時間戳
            prediction_window_minutes: 預測窗口（分鐘）

        Returns:
            排序後的切換目標列表
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        try:
            # 獲取所有可見衛星
            visible_satellites = await self.get_visible_satellites(
                observer_position, timestamp
            )

            if not visible_satellites:
                return []

            # 排除當前衛星
            if current_satellite:
                visible_satellites = [
                    sat
                    for sat in visible_satellites
                    if sat.tle_data.catalog_number
                    != current_satellite.tle_data.catalog_number
                ]

            # 計算每個衛星的切換評分
            handover_candidates = []

            for satellite in visible_satellites:
                score = await self._calculate_handover_score(
                    observer_position,
                    satellite,
                    current_satellite,
                    timestamp,
                    prediction_window_minutes,
                )

                # 預測未來軌跡
                future_trajectory = await self._predict_satellite_trajectory(
                    satellite, timestamp, prediction_window_minutes
                )

                # 計算切換時機
                optimal_handover_time = self._calculate_optimal_handover_time(
                    observer_position,
                    current_satellite,
                    satellite,
                    timestamp,
                    prediction_window_minutes,
                )

                candidate = {
                    "satellite_info": satellite,
                    "handover_score": score,
                    "predicted_trajectory": future_trajectory,
                    "optimal_handover_time": optimal_handover_time,
                    "handover_reason": self._determine_handover_reason(
                        current_satellite, satellite
                    ),
                    "quality_metrics": {
                        "elevation_stability": self._calculate_elevation_stability(
                            future_trajectory
                        ),
                        "signal_quality": satellite.signal_strength,
                        "geometric_diversity": (
                            self._calculate_geometric_diversity(
                                current_satellite, satellite
                            )
                            if current_satellite
                            else 1.0
                        ),
                        "constellation_priority": self.constellation_configs[
                            satellite.constellation
                        ].priority,
                    },
                }

                handover_candidates.append(candidate)

            # 按切換評分排序
            handover_candidates.sort(key=lambda x: x["handover_score"], reverse=True)

            logger.info(f"找到 {len(handover_candidates)} 個切換候選目標")
            return handover_candidates[:10]  # 返回前10個最佳目標

        except Exception as e:
            logger.error(f"獲取最佳切換目標失敗: {e}")
            return []

    async def _calculate_handover_score(
        self,
        observer_position: Position,
        candidate_satellite: SatelliteInfo,
        current_satellite: Optional[SatelliteInfo],
        timestamp: datetime,
        prediction_window_minutes: int,
    ) -> float:
        """
        計算衛星切換評分

        評分因子：
        1. 信號強度 (30%)
        2. 仰角穩定性 (25%)
        3. 幾何多樣性 (20%)
        4. 星座優先級 (15%)
        5. 切換成本 (10%)
        """
        try:
            # 1. 信號強度評分 (0-1)
            signal_score = candidate_satellite.signal_strength

            # 2. 仰角穩定性評分
            future_positions = []
            current_time = timestamp
            for i in range(prediction_window_minutes):
                future_time = current_time + timedelta(minutes=i)
                future_pos = self.sgp4_calculator.propagate_orbit(
                    candidate_satellite.tle_data, future_time
                )
                if future_pos:
                    elevation = self.distance_calculator.calculate_elevation_angle(
                        observer_position, future_pos
                    )
                    future_positions.append(elevation)

            if future_positions:
                elevation_variance = sum(
                    (e - sum(future_positions) / len(future_positions)) ** 2
                    for e in future_positions
                ) / len(future_positions)
                elevation_stability_score = max(
                    0, 1 - elevation_variance / 100
                )  # 歸一化
            else:
                elevation_stability_score = 0

            # 3. 幾何多樣性評分
            if current_satellite:
                geometric_diversity_score = self._calculate_geometric_diversity(
                    current_satellite, candidate_satellite
                )
            else:
                geometric_diversity_score = 1.0

            # 4. 星座優先級評分
            constellation_config = self.constellation_configs[
                candidate_satellite.constellation
            ]
            priority_score = 1.0 / constellation_config.priority  # 優先級越高分數越高

            # 5. 切換成本評分（基於角度差異）
            if current_satellite:
                angle_diff = abs(
                    candidate_satellite.elevation_angle
                    - current_satellite.elevation_angle
                )
                handover_cost_score = max(
                    0, 1 - angle_diff / 90
                )  # 角度差異越小成本越低
            else:
                handover_cost_score = 1.0

            # 加權總分
            total_score = (
                signal_score * 0.30
                + elevation_stability_score * 0.25
                + geometric_diversity_score * 0.20
                + priority_score * 0.15
                + handover_cost_score * 0.10
            )

            return min(total_score, 1.0)

        except Exception as e:
            logger.error(f"計算切換評分失敗: {e}")
            return 0.0

    async def _predict_satellite_trajectory(
        self, satellite: SatelliteInfo, start_time: datetime, duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """預測衛星軌跡"""
        try:
            trajectory = []
            current_time = start_time

            for i in range(0, duration_minutes, 2):  # 每2分鐘一個點
                future_time = current_time + timedelta(minutes=i)
                future_pos = self.sgp4_calculator.propagate_orbit(
                    satellite.tle_data, future_time
                )

                if future_pos:
                    trajectory.append(
                        {
                            "timestamp": future_time.isoformat(),
                            "latitude": future_pos.latitude,
                            "longitude": future_pos.longitude,
                            "altitude": future_pos.altitude,
                        }
                    )

            return trajectory
        except Exception as e:
            logger.error(f"預測衛星軌跡失敗: {e}")
            return []

    def _calculate_optimal_handover_time(
        self,
        observer_position: Position,
        current_satellite: Optional[SatelliteInfo],
        candidate_satellite: SatelliteInfo,
        start_time: datetime,
        window_minutes: int,
    ) -> Optional[str]:
        """計算最佳切換時機"""
        try:
            if not current_satellite:
                return start_time.isoformat()

            best_time = start_time
            best_score = 0

            # 在預測窗口內尋找最佳切換時機
            for i in range(window_minutes):
                test_time = start_time + timedelta(minutes=i)

                # 計算當前衛星在該時間的信號強度
                current_pos = self.sgp4_calculator.propagate_orbit(
                    current_satellite.tle_data, test_time
                )
                candidate_pos = self.sgp4_calculator.propagate_orbit(
                    candidate_satellite.tle_data, test_time
                )

                if current_pos and candidate_pos:
                    current_elevation = (
                        self.distance_calculator.calculate_elevation_angle(
                            observer_position, current_pos
                        )
                    )
                    candidate_elevation = (
                        self.distance_calculator.calculate_elevation_angle(
                            observer_position, candidate_pos
                        )
                    )

                    # 切換評分：候選衛星信號強度 - 當前衛星信號強度
                    current_signal = self._calculate_signal_strength(
                        current_elevation, current_pos.altitude
                    )
                    candidate_signal = self._calculate_signal_strength(
                        candidate_elevation, candidate_pos.altitude
                    )

                    score = candidate_signal - current_signal

                    if score > best_score:
                        best_score = score
                        best_time = test_time

            return best_time.isoformat()
        except Exception as e:
            logger.error(f"計算最佳切換時機失敗: {e}")
            return start_time.isoformat()

    def _calculate_elevation_stability(self, trajectory: List[Dict[str, Any]]) -> float:
        """計算仰角穩定性"""
        if len(trajectory) < 2:
            return 0.0

        try:
            # 這裡需要重新計算仰角，因為軌跡只包含位置信息
            # 簡化處理：基於高度變化評估穩定性
            altitudes = [point["altitude"] for point in trajectory]
            altitude_variance = sum(
                (alt - sum(altitudes) / len(altitudes)) ** 2 for alt in altitudes
            ) / len(altitudes)

            # 高度變化越小，穩定性越高
            stability = max(0, 1 - altitude_variance / 10000)  # 歸一化
            return stability
        except Exception as e:
            logger.error(f"計算仰角穩定性失敗: {e}")
            return 0.0

    def _calculate_geometric_diversity(
        self, satellite1: SatelliteInfo, satellite2: SatelliteInfo
    ) -> float:
        """計算幾何多樣性"""
        try:
            # 基於方位角和仰角差異計算多樣性
            azimuth_diff = abs(satellite1.azimuth_angle - satellite2.azimuth_angle)
            elevation_diff = abs(
                satellite1.elevation_angle - satellite2.elevation_angle
            )

            # 歸一化到 0-1 範圍
            azimuth_diversity = min(azimuth_diff / 180, 1.0)
            elevation_diversity = min(elevation_diff / 90, 1.0)

            # 綜合多樣性評分
            diversity = (azimuth_diversity + elevation_diversity) / 2
            return diversity
        except Exception as e:
            logger.error(f"計算幾何多樣性失敗: {e}")
            return 0.0
