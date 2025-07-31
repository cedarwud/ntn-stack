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
    
    @property
    def mean_motion(self) -> float:
        """從 TLE 第二行提取平均角速度 (每日轉數)"""
        try:
            return float(self.line2[52:63])
        except (ValueError, IndexError):
            return 15.5  # LEO 衛星典型值 (約90分鐘軌道週期)
    
    @property
    def inclination(self) -> float:
        """從 TLE 第二行提取軌道傾角 (度)"""
        try:
            return float(self.line2[8:16])
        except (ValueError, IndexError):
            return 53.0  # Starlink 典型傾角


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
        """
        計算所有衛星的當前位置 - 使用本地 Docker Volume 統一時間序列數據
        優先級: 本地統一時間序列 > NetStack API > 模擬數據
        """
        satellites = []
        
        try:
            # 方案 A: 優先使用本地 Docker Volume 統一時間序列數據
            from .local_volume_data_service import get_local_volume_service
            
            volume_service = get_local_volume_service()
            
            for constellation in constellations:
                logger.info(f"🛰️ 使用本地統一時間序列數據處理星座: {constellation}")
                
                # 生成當前時間的統一時間序列數據
                unified_data = await volume_service.generate_120min_timeseries(
                    constellation=constellation,
                    reference_location={
                        "latitude": 24.9441,   # NTPU 位置
                        "longitude": 121.3714,
                        "altitude": 0.0
                    }
                )
                
                if unified_data and unified_data.get("satellites"):
                    logger.info(f"✅ 成功載入 {constellation} 統一時間序列數據: {len(unified_data['satellites'])} 顆衛星")
                    
                    # 找到最接近當前時間的時間點
                    current_time_point = self._find_closest_time_point(unified_data, timestamp)
                    
                    # 轉換為 SatelliteInfo 格式
                    for sat_data in unified_data["satellites"]:
                        if current_time_point < len(sat_data["time_series"]):
                            time_point = sat_data["time_series"][current_time_point]
                            
                            # 構建 TLE 數據 (用於兼容性)
                            tle_data = TLEData(
                                name=sat_data["name"],
                                line1="",  # 統一時間序列不需要原始 TLE
                                line2="",
                                epoch=timestamp.isoformat()
                            )
                            
                            # 構建位置信息
                            current_position = Position(
                                latitude=time_point["position"]["latitude"],
                                longitude=time_point["position"]["longitude"],
                                altitude=time_point["position"]["altitude"]
                            )
                            
                            # 構建衛星信息
                            satellite_info = SatelliteInfo(
                                tle_data=tle_data,
                                constellation=constellation,
                                current_position=current_position,
                                last_updated=timestamp,
                                is_visible=time_point["observation"]["is_visible"],
                                elevation=time_point["observation"]["elevation_deg"],
                                azimuth=time_point["observation"]["azimuth_deg"],
                                range_km=time_point["observation"]["range_km"]
                            )
                            
                            satellites.append(satellite_info)
                    
                    logger.info(f"✅ {constellation} 處理完成: {len([s for s in satellites if s.constellation == constellation])} 顆衛星")
                    continue  # 成功處理此星座，繼續下一個
            
            if satellites:
                logger.info(f"🎯 本地統一時間序列數據成功: 總共 {len(satellites)} 顆衛星")
                return satellites
            
            logger.warning("⚠️ 本地統一時間序列數據不可用，嘗試 NetStack API")
            
        except Exception as e:
            logger.error(f"❌ 本地統一時間序列處理失敗: {e}")
            logger.info("🔄 回退到 NetStack API 方案")
        
        # 方案 B: NetStack API 備用方案 (現有代碼)
        try:
            import aiohttp
            
            for constellation in constellations:
                logger.info(f"🌐 使用 NetStack API 處理星座: {constellation}")
                
                async with aiohttp.ClientSession() as session:
                    url = f"http://netstack-api:8080/api/v1/satellites/precomputed/ntpu"
                    params = {"constellation": constellation}
                    
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"✅ NetStack API 成功獲取 {constellation} 數據")
                            
                            # 處理 NetStack API 響應數據
                            api_satellites = await self._process_netstack_api_response(data, constellation, timestamp)
                            satellites.extend(api_satellites)
                            
                        else:
                            logger.warning(f"⚠️ NetStack API 響應異常: {response.status}")
                            
        except Exception as e:
            logger.error(f"❌ NetStack API 調用失敗: {e}")
        
        # 方案 C: 模擬數據最後備用方案
        if not satellites:
            logger.warning("🔄 回退到模擬數據備用方案")
            satellites = await self._generate_fallback_satellites(constellations, timestamp)
        
        logger.info(f"🎯 最終結果: {len(satellites)} 顆衛星位置已計算")
        return satellites

    def _find_closest_time_point(self, unified_data: Dict[str, Any], target_timestamp: datetime) -> int:
        """找到最接近目標時間的時間點索引"""
        try:
            start_time_str = unified_data["metadata"]["computation_time"]
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            
            # 計算時間差（秒）
            time_diff_seconds = (target_timestamp - start_time).total_seconds()
            
            # 計算對應的時間點索引
            time_point_index = int(time_diff_seconds / unified_data["metadata"]["time_interval_seconds"])
            
            # 限制在有效範圍內
            time_point_index = max(0, min(time_point_index, unified_data["metadata"]["total_time_points"] - 1))
            
            logger.debug(f"目標時間: {target_timestamp}, 對應時間點索引: {time_point_index}")
            return time_point_index
            
        except Exception as e:
            logger.warning(f"計算時間點索引失敗: {e}, 使用預設索引 0")
            return 0
    
    async def _process_netstack_api_response(
        self, data: Dict[str, Any], constellation: str, timestamp: datetime
    ) -> List[SatelliteInfo]:
        """處理 NetStack API 響應數據"""
        satellites = []
        
        try:
            # 處理 NetStack API 格式的數據
            positions = data.get("positions", [])
            
            for i, position_data in enumerate(positions[:10]):  # 限制處理前10個
                # 構建 TLE 數據 (模擬)
                tle_data = TLEData(
                    name=f"{constellation.upper()}-SAT-{i+1}",
                    line1="",
                    line2="",
                    epoch=timestamp.isoformat()
                )
                
                # 構建位置信息 (NetStack API 數據可能沒有實際的緯經度)
                current_position = Position(
                    latitude=position_data.get("latitude", 25.0 + i * 0.1),
                    longitude=position_data.get("longitude", 121.0 + i * 0.1),
                    altitude=position_data.get("altitude_km", 550) * 1000  # 轉換為米
                )
                
                # 構建衛星信息
                satellite_info = SatelliteInfo(
                    tle_data=tle_data,
                    constellation=constellation,
                    current_position=current_position,
                    last_updated=timestamp,
                    is_visible=position_data.get("is_visible", True),
                    elevation=position_data.get("elevation_deg", 15.0),
                    azimuth=position_data.get("azimuth_deg", 180.0),
                    range_km=position_data.get("range_km", 1000.0)
                )
                
                satellites.append(satellite_info)
            
            logger.info(f"成功處理 NetStack API 響應: {len(satellites)} 顆衛星")
            return satellites
            
        except Exception as e:
            logger.error(f"處理 NetStack API 響應失敗: {e}")
            return []
    
    async def _generate_fallback_satellites(
        self, constellations: List[str], timestamp: datetime
    ) -> List[SatelliteInfo]:
        """生成備用模擬衛星數據"""
        satellites = []
        
        try:
            logger.info("🔄 生成備用模擬衛星數據")
            
            for constellation in constellations:
                constellation_sats = []
                
                # 每個星座生成5顆模擬衛星
                for i in range(5):
                    # 模擬 TLE 數據
                    tle_data = TLEData(
                        name=f"{constellation.upper()}-FALLBACK-{i+1}",
                        line1="",
                        line2="",
                        epoch=timestamp.isoformat()
                    )
                    
                    # 模擬位置 (分散在不同象限)
                    lat_offset = (i - 2) * 10  # -20 到 20 度變化
                    lon_offset = (i - 2) * 15  # -30 到 30 度變化
                    
                    current_position = Position(
                        latitude=24.9441 + lat_offset,
                        longitude=121.3714 + lon_offset,
                        altitude=550000.0  # 550km 高度
                    )
                    
                    # 模擬觀測數據
                    elevation = 15.0 + i * 10  # 15-55度仰角
                    azimuth = i * 72  # 0, 72, 144, 216, 288度方位角
                    range_km = 1000 + i * 200  # 1000-1800km距離
                    
                    satellite_info = SatelliteInfo(
                        tle_data=tle_data,
                        constellation=constellation,
                        current_position=current_position,
                        last_updated=timestamp,
                        is_visible=True,
                        elevation=elevation,
                        azimuth=azimuth,
                        range_km=range_km
                    )
                    
                    # 計算信號強度
                    satellite_info.signal_strength = self._calculate_signal_strength(
                        elevation, range_km
                    )
                    
                    constellation_sats.append(satellite_info)
                
                satellites.extend(constellation_sats)
                logger.info(f"✅ 生成 {constellation} 備用數據: {len(constellation_sats)} 顆衛星")
            
            logger.info(f"🎯 備用模擬數據生成完成: 總共 {len(satellites)} 顆衛星")
            return satellites
            
        except Exception as e:
            logger.error(f"❌ 生成備用衛星數據失敗: {e}")
            return []

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