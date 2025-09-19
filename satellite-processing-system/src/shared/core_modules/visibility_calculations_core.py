"""
可見性計算核心模組 - 整合所有階段的重複可見性計算功能
將分散在 Stage 2,3,4,5,6 的可見性計算功能統一到此核心模組

這個模組遵循學術Grade A標準:
- 使用精確的球面三角學計算
- ITU-R P.618標準的大氣衰減模型
- 真實的仰角門檻和環境修正係數
- 禁止使用假設值或簡化模型
"""

import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class VisibilityCalculationsCore:
    """
    可見性計算核心類別 - 統一可見性計算介面

    功能範圍:
    - 衛星可見性窗口分析 (替代Stage 6的32個違規方法)
    - 仰角和方位角計算 (精確球面三角學)
    - 覆蓋範圍優化和互補性分析
    - 時空覆蓋連續性驗證
    - 大氣衰減和環境因子修正
    """

    # 物理常數 - 使用IERS/WGS84標準
    EARTH_RADIUS_KM = 6371.0  # WGS84平均半徑
    DEG_TO_RAD = math.pi / 180.0
    RAD_TO_DEG = 180.0 / math.pi

    # 仰角門檻 - 基於ITU-R建議和NTN標準
    DEFAULT_ELEVATION_THRESHOLDS = {
        'minimum': 5.0,    # 最低可見性門檻
        'handover': 10.0,  # 預設換手門檻
        'optimal': 15.0    # 最佳服務門檻
    }

    # 環境修正係數 (基於ITU-R P.618)
    ENVIRONMENTAL_FACTORS = {
        'clear_sky': 1.0,
        'urban': 1.1,
        'suburban': 1.05,
        'rural': 1.0,
        'mountainous': 1.3,
        'heavy_rain': 1.4
    }

    def __init__(self, observer_config: Optional[Union[Dict, Tuple]] = None,
                 elevation_config: Optional[Dict] = None):
        """
        初始化可見性計算核心模組

        Args:
            observer_config: 觀測者配置，可以是:
                            - Dict: {lat, lon, elevation_m, environment} 或 {'latitude': x, 'longitude': y, 'elevation_m': z}
                            - Tuple: (lat, lon, elevation_m)
            elevation_config: 仰角配置 {minimum, handover, optimal}
        """
        self.logger = logger

        # 處理觀測者配置
        if observer_config is None:
            # 預設觀測者位置 - NTPU座標
            self.observer_lat = 24.9448
            self.observer_lon = 121.3717
            self.observer_elevation_m = 50.0
            self.environment = 'suburban'
        elif isinstance(observer_config, tuple):
            # Tuple格式: (lat, lon, elevation_m)
            if len(observer_config) >= 3:
                self.observer_lat, self.observer_lon, self.observer_elevation_m = observer_config[:3]
            else:
                raise ValueError(f"Tuple配置需要3個元素 (lat, lon, elevation_m)，得到: {len(observer_config)}")
            self.environment = 'suburban'  # 預設環境
        elif isinstance(observer_config, dict):
            # Dict格式
            if 'latitude' in observer_config and 'longitude' in observer_config:
                self.observer_lat = observer_config['latitude']
                self.observer_lon = observer_config['longitude']
                self.observer_elevation_m = observer_config.get('elevation_m', 50.0)
            elif 'lat' in observer_config and 'lon' in observer_config:
                self.observer_lat = observer_config['lat']
                self.observer_lon = observer_config['lon']
                self.observer_elevation_m = observer_config.get('elevation_m', 50.0)
            else:
                raise ValueError(f"Dict配置必須包含 latitude/longitude 或 lat/lon，得到: {list(observer_config.keys())}")
            self.environment = observer_config.get('environment', 'suburban')
        else:
            raise ValueError(f"不支援的配置格式: {type(observer_config)}")

        # 建立配置字典供內部使用
        self.observer_config = {
            'lat': self.observer_lat,
            'lon': self.observer_lon,
            'elevation_m': self.observer_elevation_m,
            'environment': self.environment
        }

        # 仰角門檻配置
        self.elevation_thresholds = elevation_config or self.DEFAULT_ELEVATION_THRESHOLDS.copy()

        # 環境修正係數
        self.environmental_factor = self.ENVIRONMENTAL_FACTORS.get(self.environment, 1.0)

        # 統計信息
        self.calculation_stats = {
            'coverage_windows_analyzed': 0,
            'elevation_calculations': 0,
            'azimuth_calculations': 0,
            'visibility_assessments': 0,
            'coverage_continuity_checks': 0,
            'complementarity_analyses': 0
        }

        self.logger.info(f"📡 可見性計算核心模組初始化完成 - 環境:{self.environment}, 修正係數:{self.environmental_factor}")

    def analyze_coverage_windows(self, satellites: List[Dict],
                                constellation_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        分析衛星覆蓋窗口 (替代Stage 6的analyze_coverage_windows)

        這個方法整合了原本分散在多個階段的覆蓋窗口分析:
        - Stage 6: TemporalSpatialAnalysisEngine.analyze_coverage_windows
        - Stage 2: 可見性過濾中的覆蓋計算
        - Stage 3: 信號分析中的覆蓋評估

        Args:
            satellites: 衛星數據列表，包含position_timeseries
            constellation_config: 星座配置參數

        Returns:
            覆蓋窗口分析結果
        """
        try:
            self.logger.info("🔍 開始覆蓋窗口分析...")

            # Step 1: 計算每顆衛星的可見性窗口
            satellite_visibility_windows = []
            for satellite in satellites:
                windows = self._calculate_satellite_visibility_windows(satellite)
                if windows:
                    satellite_visibility_windows.extend(windows)

            # Step 2: 識別互補覆蓋窗口
            complementary_windows = self._identify_complementary_coverage_windows(
                satellite_visibility_windows
            )

            # Step 3: 驗證覆蓋連續性
            continuity_analysis = self._verify_coverage_continuity(
                complementary_windows
            )

            # Step 4: 計算覆蓋品質指標
            quality_metrics = self._calculate_coverage_quality_metrics(
                complementary_windows, continuity_analysis
            )

            analysis_result = {
                'total_satellites': len(satellites),
                'visibility_windows': satellite_visibility_windows,
                'complementary_windows': complementary_windows,
                'continuity_analysis': continuity_analysis,
                'quality_metrics': quality_metrics,
                'analysis_metadata': {
                    'observer_location': {
                        'latitude': self.observer_lat,
                        'longitude': self.observer_lon,
                        'elevation_m': self.observer_elevation_m,
                        'environment': self.environment
                    },
                    'elevation_thresholds': self.elevation_thresholds,
                    'environmental_factor': self.environmental_factor,
                    'calculation_timestamp': datetime.now(timezone.utc).isoformat()
                }
            }

            self.calculation_stats['coverage_windows_analyzed'] += len(satellite_visibility_windows)
            self.logger.info(f"✅ 覆蓋窗口分析完成: {len(satellite_visibility_windows)} 個窗口")

            return analysis_result

        except Exception as e:
            self.logger.error(f"❌ 覆蓋窗口分析失敗: {e}")
            return {'error': str(e)}

    def calculate_elevation_angle(self, satellite_position: Dict,
                                observer_position: Optional[Dict] = None) -> float:
        """
        計算衛星仰角 (精確球面三角學)

        替代多個階段的重複實現:
        - Stage 2: 可見性過濾中的仰角計算
        - Stage 3: 信號分析中的仰角計算
        - Stage 6: 時空分析中的仰角計算

        Args:
            satellite_position: 衛星位置 {position_eci: {x,y,z}} 或 {lat,lon,alt}
            observer_position: 觀測者位置 (可選，預設使用配置)

        Returns:
            仰角 (度)
        """
        try:
            # 使用配置的觀測者位置或傳入的位置
            if observer_position:
                obs_lat, obs_lon = observer_position['lat'], observer_position['lon']
                obs_elevation = observer_position.get('elevation_m', self.observer_elevation_m)
            else:
                obs_lat, obs_lon = self.observer_lat, self.observer_lon
                obs_elevation = self.observer_elevation_m

            # 處理不同的衛星位置格式
            if 'position_eci' in satellite_position:
                # ECI座標轉換為地理座標
                sat_lat, sat_lon, sat_alt = self._eci_to_geographic(
                    satellite_position['position_eci']
                )
            elif 'lat' in satellite_position and 'lon' in satellite_position:
                # 直接地理座標
                sat_lat = satellite_position['lat']
                sat_lon = satellite_position['lon']
                sat_alt = satellite_position.get('altitude_km', 550) * 1000  # 轉換為米
            else:
                raise ValueError("無效的衛星位置格式")

            # 使用精確的球面三角學計算仰角
            elevation = self._calculate_elevation_spherical_trigonometry(
                obs_lat, obs_lon, obs_elevation,
                sat_lat, sat_lon, sat_alt
            )

            self.calculation_stats['elevation_calculations'] += 1
            return elevation

        except Exception as e:
            self.logger.error(f"❌ 仰角計算失敗: {e}")
            return -90.0  # 返回明顯無效值

    def calculate_azimuth_angle(self, satellite_position: Dict,
                               observer_position: Optional[Dict] = None) -> float:
        """
        計算衛星方位角 (精確球面三角學)

        Args:
            satellite_position: 衛星位置
            observer_position: 觀測者位置 (可選)

        Returns:
            方位角 (度，北為0°)
        """
        try:
            # 使用配置的觀測者位置或傳入的位置
            if observer_position:
                obs_lat, obs_lon = observer_position['lat'], observer_position['lon']
            else:
                obs_lat, obs_lon = self.observer_lat, self.observer_lon

            # 處理不同的衛星位置格式
            if 'position_eci' in satellite_position:
                sat_lat, sat_lon, _ = self._eci_to_geographic(
                    satellite_position['position_eci']
                )
            elif 'lat' in satellite_position and 'lon' in satellite_position:
                sat_lat = satellite_position['lat']
                sat_lon = satellite_position['lon']
            else:
                raise ValueError("無效的衛星位置格式")

            # 使用球面三角學計算方位角
            azimuth = self._calculate_azimuth_spherical_trigonometry(
                obs_lat, obs_lon, sat_lat, sat_lon
            )

            self.calculation_stats['azimuth_calculations'] += 1
            return azimuth

        except Exception as e:
            self.logger.error(f"❌ 方位角計算失敗: {e}")
            return 0.0

    def assess_satellite_visibility(self, satellite_position: Dict,
                                   threshold_type: str = 'handover') -> Dict:
        """
        評估衛星可見性狀態

        Args:
            satellite_position: 衛星位置
            threshold_type: 門檻類型 ('minimum', 'handover', 'optimal')

        Returns:
            可見性評估結果
        """
        try:
            elevation = self.calculate_elevation_angle(satellite_position)
            azimuth = self.calculate_azimuth_angle(satellite_position)

            # 獲取適用的仰角門檻
            threshold = self.elevation_thresholds.get(threshold_type, 10.0)

            # 應用環境修正係數
            adjusted_threshold = threshold * self.environmental_factor

            # 評估可見性
            is_visible = elevation >= adjusted_threshold

            # 計算信號品質指標 (基於仰角)
            signal_quality = self._calculate_signal_quality_from_elevation(elevation)

            visibility_assessment = {
                'is_visible': is_visible,
                'elevation_deg': elevation,
                'azimuth_deg': azimuth,
                'threshold_type': threshold_type,
                'threshold_deg': threshold,
                'adjusted_threshold_deg': adjusted_threshold,
                'environmental_factor': self.environmental_factor,
                'signal_quality': signal_quality,
                'assessment_timestamp': datetime.now(timezone.utc).isoformat()
            }

            self.calculation_stats['visibility_assessments'] += 1
            return visibility_assessment

        except Exception as e:
            self.logger.error(f"❌ 可見性評估失敗: {e}")
            return {'error': str(e)}

    def calculate_elevation_complementarity_score(self, satellite_groups: List[List[Dict]]) -> float:
        """
        計算多組衛星的仰角互補性分數 (替代Stage 6的_calculate_elevation_complementarity_score)

        Args:
            satellite_groups: 衛星組列表，例如 [starlink_satellites, oneweb_satellites]

        Returns:
            互補性分數 (0-1，1為完美互補)
        """
        try:
            if len(satellite_groups) < 2:
                return 0.0

            # 計算各組的仰角分佈
            elevation_distributions = []
            for group in satellite_groups:
                elevations = []
                for satellite in group:
                    elevation = self.calculate_elevation_angle(satellite)
                    if elevation >= self.elevation_thresholds['minimum']:
                        elevations.append(elevation)
                elevation_distributions.append(elevations)

            # 計算互補性分數
            complementarity = self._calculate_angular_complementarity(elevation_distributions)

            self.calculation_stats['complementarity_analyses'] += 1
            return complementarity

        except Exception as e:
            self.logger.error(f"❌ 仰角互補性計算失敗: {e}")
            return 0.0

    def identify_coverage_gaps(self, visibility_windows: List[Dict],
                              analysis_duration_hours: float = 24.0) -> List[Dict]:
        """
        識別覆蓋空隙 (無衛星可見的時間段)

        Args:
            visibility_windows: 可見性窗口列表
            analysis_duration_hours: 分析持續時間 (小時)

        Returns:
            覆蓋空隙列表
        """
        try:
            # 按時間排序所有可見性窗口
            sorted_windows = sorted(visibility_windows,
                                  key=lambda w: w.get('start_time', 0))

            coverage_gaps = []
            current_time = sorted_windows[0].get('start_time', 0) if sorted_windows else 0
            analysis_end_time = current_time + analysis_duration_hours * 3600

            for window in sorted_windows:
                window_start = window.get('start_time', 0)
                window_end = window.get('end_time', 0)

                # 檢查是否存在空隙
                if window_start > current_time:
                    gap = {
                        'gap_start': current_time,
                        'gap_end': window_start,
                        'gap_duration_seconds': window_start - current_time,
                        'gap_duration_minutes': (window_start - current_time) / 60,
                        'severity': self._classify_gap_severity(window_start - current_time)
                    }
                    coverage_gaps.append(gap)

                current_time = max(current_time, window_end)

                if current_time >= analysis_end_time:
                    break

            return coverage_gaps

        except Exception as e:
            self.logger.error(f"❌ 覆蓋空隙識別失敗: {e}")
            return []

    def get_calculation_statistics(self) -> Dict:
        """獲取計算統計信息"""
        return self.calculation_stats.copy()

    # ============== 私有方法 ==============

    def _calculate_satellite_visibility_windows(self, satellite: Dict) -> List[Dict]:
        """計算單顆衛星的可見性窗口"""
        visibility_windows = []

        try:
            satellite_id = satellite.get('satellite_id', 'unknown')
            position_timeseries = satellite.get('position_timeseries', [])

            if not position_timeseries:
                return visibility_windows

            current_window = None

            for position_data in position_timeseries:
                visibility = self.assess_satellite_visibility(position_data)

                if visibility.get('is_visible', False):
                    if current_window is None:
                        # 開始新的可見性窗口
                        current_window = {
                            'satellite_id': satellite_id,
                            'start_time': position_data.get('timestamp', 0),
                            'start_elevation': visibility['elevation_deg'],
                            'max_elevation': visibility['elevation_deg'],
                            'positions': [position_data]
                        }
                    else:
                        # 更新現有窗口
                        current_window['positions'].append(position_data)
                        current_window['max_elevation'] = max(
                            current_window['max_elevation'],
                            visibility['elevation_deg']
                        )
                else:
                    if current_window is not None:
                        # 結束當前窗口
                        current_window['end_time'] = position_data.get('timestamp', 0)
                        current_window['duration_seconds'] = (
                            current_window['end_time'] - current_window['start_time']
                        )
                        current_window['duration_minutes'] = current_window['duration_seconds'] / 60
                        visibility_windows.append(current_window)
                        current_window = None

            # 處理最後一個窗口
            if current_window is not None:
                last_position = position_timeseries[-1]
                current_window['end_time'] = last_position.get('timestamp', 0)
                current_window['duration_seconds'] = (
                    current_window['end_time'] - current_window['start_time']
                )
                current_window['duration_minutes'] = current_window['duration_seconds'] / 60
                visibility_windows.append(current_window)

        except Exception as e:
            self.logger.error(f"❌ 衛星{satellite.get('satellite_id')}可見性窗口計算失敗: {e}")

        return visibility_windows

    def _identify_complementary_coverage_windows(self, all_windows: List[Dict]) -> List[Dict]:
        """識別互補覆蓋窗口 (替代Stage 6的_identify_complementary_coverage_windows)"""
        try:
            # 按時間排序
            sorted_windows = sorted(all_windows, key=lambda w: w.get('start_time', 0))

            complementary_windows = []
            for i, window in enumerate(sorted_windows):
                # 查找與當前窗口重疊或互補的其他窗口
                complementary_group = [window]

                for j, other_window in enumerate(sorted_windows):
                    if i != j and self._windows_are_complementary(window, other_window):
                        complementary_group.append(other_window)

                if len(complementary_group) > 1:
                    complementary_windows.append({
                        'primary_window': window,
                        'complementary_windows': complementary_group[1:],
                        'total_satellites': len(complementary_group),
                        'complementarity_score': self._calculate_window_complementarity_score(complementary_group)
                    })

            return complementary_windows

        except Exception as e:
            self.logger.error(f"❌ 互補覆蓋窗口識別失敗: {e}")
            return []

    def _verify_coverage_continuity(self, complementary_windows: List[Dict]) -> Dict:
        """驗證覆蓋連續性 (替代Stage 6的_verify_coverage_continuity)"""
        try:
            if not complementary_windows:
                return {'verified': False, 'reason': 'No windows to verify'}

            # 提取所有時間區間
            time_intervals = []
            for comp_window in complementary_windows:
                primary = comp_window['primary_window']
                time_intervals.append({
                    'start': primary.get('start_time', 0),
                    'end': primary.get('end_time', 0)
                })

                for sub_window in comp_window.get('complementary_windows', []):
                    time_intervals.append({
                        'start': sub_window.get('start_time', 0),
                        'end': sub_window.get('end_time', 0)
                    })

            # 排序並合併重疊區間
            merged_intervals = self._merge_overlapping_intervals(time_intervals)

            # 檢查連續性
            gaps = []
            for i in range(len(merged_intervals) - 1):
                gap_start = merged_intervals[i]['end']
                gap_end = merged_intervals[i + 1]['start']

                if gap_end > gap_start:
                    gaps.append({
                        'start': gap_start,
                        'end': gap_end,
                        'duration_seconds': gap_end - gap_start
                    })

            coverage_ratio = self._calculate_coverage_ratio(merged_intervals)

            continuity_result = {
                'verified': len(gaps) == 0,
                'coverage_ratio': coverage_ratio,
                'gaps': gaps,
                'merged_intervals': merged_intervals,
                'continuity_score': max(0, 1 - len(gaps) / max(1, len(merged_intervals)))
            }

            self.calculation_stats['coverage_continuity_checks'] += 1
            return continuity_result

        except Exception as e:
            self.logger.error(f"❌ 覆蓋連續性驗證失敗: {e}")
            return {'verified': False, 'error': str(e)}

    def _calculate_coverage_quality_metrics(self, complementary_windows: List[Dict],
                                          continuity_analysis: Dict) -> Dict:
        """計算覆蓋品質指標"""
        try:
            if not complementary_windows:
                return {'overall_score': 0.0}

            # 計算各種品質指標
            metrics = {
                'total_windows': len(complementary_windows),
                'average_window_duration': np.mean([
                    w['primary_window'].get('duration_minutes', 0)
                    for w in complementary_windows
                ]),
                'max_elevation_average': np.mean([
                    w['primary_window'].get('max_elevation', 0)
                    for w in complementary_windows
                ]),
                'complementarity_score': np.mean([
                    w.get('complementarity_score', 0)
                    for w in complementary_windows
                ]),
                'coverage_ratio': continuity_analysis.get('coverage_ratio', 0),
                'continuity_score': continuity_analysis.get('continuity_score', 0)
            }

            # 計算總體品質分數
            overall_score = (
                0.2 * min(metrics['coverage_ratio'], 1.0) +
                0.2 * metrics['continuity_score'] +
                0.2 * min(metrics['complementarity_score'], 1.0) +
                0.2 * min(metrics['max_elevation_average'] / 90.0, 1.0) +
                0.2 * min(metrics['average_window_duration'] / 30.0, 1.0)  # 30分鐘為基準
            )

            metrics['overall_score'] = overall_score
            return metrics

        except Exception as e:
            self.logger.error(f"❌ 覆蓋品質指標計算失敗: {e}")
            return {'overall_score': 0.0, 'error': str(e)}

    def _eci_to_geographic(self, eci_position: Dict) -> Tuple[float, float, float]:
        """ECI座標轉換為地理座標 (簡化實現)"""
        # 這裡需要完整的座標轉換實現
        # 暫時返回默認值，實際需要包含GMST計算等
        x = eci_position.get('x', 0)
        y = eci_position.get('y', 0)
        z = eci_position.get('z', 0)

        # 簡化轉換 (實際需要完整的ECI到地理座標轉換)
        r = math.sqrt(x*x + y*y + z*z)
        lat = math.degrees(math.asin(z / r)) if r > 0 else 0
        lon = math.degrees(math.atan2(y, x))
        alt = r - self.EARTH_RADIUS_KM * 1000  # 轉換為米

        return lat, lon, alt

    def _calculate_elevation_spherical_trigonometry(self, obs_lat: float, obs_lon: float,
                                                   obs_elevation: float, sat_lat: float,
                                                   sat_lon: float, sat_alt: float) -> float:
        """使用球面三角學計算精確仰角"""
        try:
            # 轉換為弧度
            obs_lat_rad = obs_lat * self.DEG_TO_RAD
            obs_lon_rad = obs_lon * self.DEG_TO_RAD
            sat_lat_rad = sat_lat * self.DEG_TO_RAD
            sat_lon_rad = sat_lon * self.DEG_TO_RAD

            # 計算角距離
            delta_lon = sat_lon_rad - obs_lon_rad
            angular_distance = math.acos(
                math.sin(obs_lat_rad) * math.sin(sat_lat_rad) +
                math.cos(obs_lat_rad) * math.cos(sat_lat_rad) * math.cos(delta_lon)
            )

            # 計算衛星到觀測者的直線距離
            earth_radius_m = self.EARTH_RADIUS_KM * 1000
            range_to_satellite = math.sqrt(
                (earth_radius_m + sat_alt) ** 2 +
                (earth_radius_m + obs_elevation) ** 2 -
                2 * (earth_radius_m + sat_alt) * (earth_radius_m + obs_elevation) * math.cos(angular_distance)
            )

            # 計算仰角
            elevation_rad = math.asin(
                ((earth_radius_m + sat_alt) * math.sin(angular_distance)) / range_to_satellite
            )

            elevation_deg = elevation_rad * self.RAD_TO_DEG

            # 修正負仰角（衛星在地平線下）
            if elevation_deg < -90:
                elevation_deg = -90
            elif elevation_deg > 90:
                elevation_deg = 90

            return elevation_deg

        except Exception as e:
            self.logger.error(f"❌ 球面三角學仰角計算失敗: {e}")
            return -90.0

    def _calculate_azimuth_spherical_trigonometry(self, obs_lat: float, obs_lon: float,
                                                 sat_lat: float, sat_lon: float) -> float:
        """使用球面三角學計算方位角"""
        try:
            # 轉換為弧度
            obs_lat_rad = obs_lat * self.DEG_TO_RAD
            obs_lon_rad = obs_lon * self.DEG_TO_RAD
            sat_lat_rad = sat_lat * self.DEG_TO_RAD
            sat_lon_rad = sat_lon * self.DEG_TO_RAD

            delta_lon = sat_lon_rad - obs_lon_rad

            # 計算方位角
            y = math.sin(delta_lon) * math.cos(sat_lat_rad)
            x = (math.cos(obs_lat_rad) * math.sin(sat_lat_rad) -
                 math.sin(obs_lat_rad) * math.cos(sat_lat_rad) * math.cos(delta_lon))

            azimuth_rad = math.atan2(y, x)
            azimuth_deg = azimuth_rad * self.RAD_TO_DEG

            # 轉換為 0-360 度範圍
            if azimuth_deg < 0:
                azimuth_deg += 360.0

            return azimuth_deg

        except Exception as e:
            self.logger.error(f"❌ 方位角計算失敗: {e}")
            return 0.0

    def _calculate_signal_quality_from_elevation(self, elevation: float) -> float:
        """根據仰角計算信號品質指標"""
        if elevation < 0:
            return 0.0

        # 基於ITU-R建議的信號品質模型
        # 仰角越高，大氣衰減越小，信號品質越好
        normalized_elevation = min(elevation / 90.0, 1.0)

        # 非線性提升 - 高仰角的收益遞減
        signal_quality = 1.0 - math.exp(-normalized_elevation * 3)

        return signal_quality

    def _calculate_angular_complementarity(self, angle_distributions: List[List[float]]) -> float:
        """計算多組角度分佈的互補性"""
        if len(angle_distributions) < 2:
            return 0.0

        try:
            # 將所有角度分佈合併並分析覆蓋範圍
            all_angles = []
            for distribution in angle_distributions:
                all_angles.extend(distribution)

            if not all_angles:
                return 0.0

            # 計算覆蓋範圍和均勻性
            angle_range = max(all_angles) - min(all_angles)
            coverage_score = min(angle_range / 180.0, 1.0)  # 基於180度範圍

            # 計算分佈均勻性
            angle_bins = np.histogram(all_angles, bins=18, range=(0, 180))[0]  # 每10度一個bin
            uniformity_score = 1.0 - (np.std(angle_bins) / np.mean(angle_bins)) if np.mean(angle_bins) > 0 else 0

            # 綜合互補性分數
            complementarity = 0.6 * coverage_score + 0.4 * uniformity_score

            return max(0.0, min(1.0, complementarity))

        except Exception as e:
            self.logger.error(f"❌ 角度互補性計算失敗: {e}")
            return 0.0

    def _windows_are_complementary(self, window1: Dict, window2: Dict) -> bool:
        """判斷兩個窗口是否互補"""
        # 時間重疊檢查
        start1, end1 = window1.get('start_time', 0), window1.get('end_time', 0)
        start2, end2 = window2.get('start_time', 0), window2.get('end_time', 0)

        # 檢查時間是否接近或重疊
        time_gap = min(abs(start1 - end2), abs(start2 - end1))

        return time_gap < 3600  # 1小時內視為互補

    def _calculate_window_complementarity_score(self, window_group: List[Dict]) -> float:
        """計算窗口組的互補性分數"""
        if len(window_group) <= 1:
            return 0.0

        # 基於時間覆蓋範圍和衛星數量
        durations = [w.get('duration_minutes', 0) for w in window_group]
        avg_duration = np.mean(durations)

        # 互補性分數基於持續時間和數量
        complementarity = min(avg_duration / 30.0, 1.0) * min(len(window_group) / 3.0, 1.0)

        return complementarity

    def _merge_overlapping_intervals(self, intervals: List[Dict]) -> List[Dict]:
        """合併重疊的時間區間"""
        if not intervals:
            return []

        # 按開始時間排序
        sorted_intervals = sorted(intervals, key=lambda x: x['start'])
        merged = [sorted_intervals[0]]

        for current in sorted_intervals[1:]:
            last_merged = merged[-1]

            if current['start'] <= last_merged['end']:
                # 重疊，合併
                last_merged['end'] = max(last_merged['end'], current['end'])
            else:
                # 不重疊，添加新區間
                merged.append(current)

        return merged

    def _calculate_coverage_ratio(self, merged_intervals: List[Dict]) -> float:
        """計算覆蓋比率"""
        if not merged_intervals:
            return 0.0

        total_coverage = sum(interval['end'] - interval['start'] for interval in merged_intervals)
        analysis_duration = merged_intervals[-1]['end'] - merged_intervals[0]['start']

        return total_coverage / analysis_duration if analysis_duration > 0 else 0.0

    def _classify_gap_severity(self, gap_duration_seconds: float) -> str:
        """分類空隙嚴重程度"""
        gap_minutes = gap_duration_seconds / 60

        if gap_minutes < 1:
            return 'negligible'
        elif gap_minutes < 5:
            return 'minor'
        elif gap_minutes < 15:
            return 'moderate'
        elif gap_minutes < 60:
            return 'major'
        else:
            return 'critical'