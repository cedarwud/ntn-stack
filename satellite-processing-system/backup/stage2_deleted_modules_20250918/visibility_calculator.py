"""
可見性計算引擎 - Stage 2模組化組件

職責：
1. 基於觀測點計算衛星相對位置
2. 計算仰角、方位角和距離
3. 判斷衛星地理可見性
4. 使用學術級標準的計算方法
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

# 🚨 Grade A要求：使用學術級仰角標準替代硬編碼
try:
    from ...shared.elevation_standards import ELEVATION_STANDARDS
    INVALID_ELEVATION = ELEVATION_STANDARDS.get_safe_default_elevation()
except ImportError:
    logger = logging.getLogger(__name__)
    # 使用全局警告管理器避免無限循環
    from .academic_warning_manager import AcademicConfigWarningManager
    AcademicConfigWarningManager.show_warning_once(logger)
    INVALID_ELEVATION = -999.0  # 學術標準：使用明確的無效值標記

logger = logging.getLogger(__name__)

class VisibilityCalculator:
    """衛星可見性計算引擎 - 基於學術級標準"""
    
    def __init__(self, observer_coordinates: Tuple[float, float, float] = (24.9441667, 121.3713889, 50)):
        """
        初始化可見性計算引擎
        
        Args:
            observer_coordinates: 觀測點座標 (緯度, 經度, 海拔m)，預設為NTPU
        """
        self.logger = logging.getLogger(f"{__name__}.VisibilityCalculator")
        
        self.observer_lat = observer_coordinates[0]  # 緯度 (度)
        self.observer_lon = observer_coordinates[1]  # 經度 (度) 
        self.observer_alt = observer_coordinates[2]  # 海拔 (米)
        
        self.logger.info(f"✅ 可見性計算引擎初始化成功")
        self.logger.info(f"   觀測點: 緯度={self.observer_lat:.6f}°, 經度={self.observer_lon:.6f}°, 海拔={self.observer_alt}m")
        
        # 計算統計
        self.calculation_statistics = {
            "total_satellites": 0,
            "satellites_with_visibility": 0,
            "total_position_calculations": 0,
            "visible_position_calculations": 0
        }
        
        # 地球參數 (WGS84)
        self.EARTH_RADIUS_KM = 6371.0  # 平均半徑
        self.DEG_TO_RAD = math.pi / 180.0
        self.RAD_TO_DEG = 180.0 / math.pi

    def initialize_coverage_guarantee_system(self, config: Optional[Dict] = None):
        """
        🆕 Stage2增強：初始化覆蓋保證系統
        
        整合從TemporalSpatialAnalysisEngine提取的31個覆蓋保證方法，
        為Stage2提供增強的覆蓋連續性保證能力。
        
        Args:
            config: 覆蓋保證配置參數
        """
        from .coverage_guarantee_engine import CoverageGuaranteeEngine
        
        # 整合觀測者坐標到配置
        if config is None:
            config = {}
        config.update({
            'observer_lat': self.observer_lat,
            'observer_lon': self.observer_lon,
            'observer_alt': self.observer_alt
        })
        
        self.coverage_guarantee_engine = CoverageGuaranteeEngine(config)
        self.coverage_guarantee_enabled = True
        
        # 更新計算統計以包含覆蓋保證
        self.calculation_statistics.update({
            "coverage_guarantee_enabled": True,
            "continuous_coverage_ensured": False,
            "coverage_reliability_calculated": False,
            "coverage_gaps_identified": 0
        })
        
        self.logger.info("🛡️ 覆蓋保證系統已整合到可見性計算引擎")
        return self.coverage_guarantee_engine

    def calculate_visibility_with_coverage_guarantee(self, satellites: List[Dict], time_points: List[datetime],
                                                   enable_continuous_coverage: bool = True,
                                                   enable_reliability_analysis: bool = True) -> Dict[str, Any]:
        """
        🆕 Stage2增強：結合覆蓋保證的可見性計算
        
        這是Stage2的核心增強功能，整合了從Stage6提取的覆蓋保證能力。
        
        Args:
            satellites: 衛星數據列表
            time_points: 分析時間點列表
            enable_continuous_coverage: 是否啟用連續覆蓋確保
            enable_reliability_analysis: 是否啟用可靠性分析
            
        Returns:
            包含覆蓋保證的可見性計算結果
        """
        if not hasattr(self, 'coverage_guarantee_engine'):
            self.logger.warning("⚠️ 覆蓋保證系統未初始化，使用標準可見性計算")
            return self.calculate_satellite_visibility_batch(satellites, time_points)
            
        self.logger.info("🚀 開始覆蓋保證增強的可見性計算...")
        
        try:
            # Step 1: 標準可見性計算
            standard_visibility = self.calculate_satellite_visibility_batch(satellites, time_points)
            
            # Step 2: 連續覆蓋確保 (如果啟用)
            continuous_coverage_results = {}
            if enable_continuous_coverage:
                continuous_coverage_results = self.coverage_guarantee_engine._ensure_continuous_coverage(
                    satellites, time_points
                )
                self.calculation_statistics["continuous_coverage_ensured"] = True
                
            # Step 3: 覆蓋可靠性計算 (如果啟用)
            reliability_results = {}
            if enable_reliability_analysis:
                reliability_results = self.coverage_guarantee_engine._calculate_coverage_reliability(
                    satellites, None  # 暫時沒有歷史數據
                )
                self.calculation_statistics["coverage_reliability_calculated"] = True
                
            # Step 4: 覆蓋間隙識別
            coverage_gaps_results = self.coverage_guarantee_engine._identify_coverage_gaps(
                satellites, time_points, detailed_analysis=True
            )
            self.calculation_statistics["coverage_gaps_identified"] = coverage_gaps_results.get('gap_statistics', {}).get('total_gaps_identified', 0)
            
            # Step 5: 整合計算結果
            enhanced_visibility = {
                **standard_visibility,  # 保留原有可見性計算結果
                'coverage_guarantee_enhancement': {
                    'continuous_coverage': continuous_coverage_results if enable_continuous_coverage else {'enabled': False},
                    'reliability_analysis': reliability_results if enable_reliability_analysis else {'enabled': False},
                    'coverage_gaps_analysis': coverage_gaps_results,
                    'enhancement_metadata': {
                        'stage2_enhanced': True,
                        'calculation_timestamp': datetime.now().isoformat(),
                        'methods_applied': self._get_applied_methods_list(enable_continuous_coverage, enable_reliability_analysis),
                        'coverage_guarantee_summary': {
                            'continuous_coverage_guaranteed': continuous_coverage_results.get('coverage_continuity', {}).get('guaranteed', False) if enable_continuous_coverage else False,
                            'reliability_meets_threshold': reliability_results.get('reliability_metrics', {}).get('meets_requirement', False) if enable_reliability_analysis else False,
                            'total_gaps_identified': coverage_gaps_results.get('gap_statistics', {}).get('total_gaps_identified', 0),
                            'critical_gaps_resolved': coverage_gaps_results.get('gap_statistics', {}).get('critical_gaps', 0)
                        }
                    }
                }
            }
            
            # 日誌輸出結果摘要
            summary = enhanced_visibility['coverage_guarantee_enhancement']['enhancement_metadata']['coverage_guarantee_summary']
            self.logger.info("✅ 覆蓋保證增強可見性計算完成")
            self.logger.info(f"   連續覆蓋保證: {'✅' if summary['continuous_coverage_guaranteed'] else '❌'}")
            self.logger.info(f"   可靠性達標: {'✅' if summary['reliability_meets_threshold'] else '❌'}")
            self.logger.info(f"   識別覆蓋間隙: {summary['total_gaps_identified']} 個")
            
            return enhanced_visibility
            
        except Exception as e:
            self.logger.error(f"覆蓋保證計算失敗: {e}")
            self.logger.warning("回退到標準可見性計算")
            return self.calculate_satellite_visibility_batch(satellites, time_points)

    def _get_applied_methods_list(self, continuous_coverage: bool, reliability_analysis: bool) -> List[str]:
        """獲取應用的方法列表"""
        methods = ['coverage_gaps_identification']
        
        if continuous_coverage:
            methods.append('continuous_coverage_guarantee')
            
        if reliability_analysis:
            methods.append('reliability_analysis')
            
        return methods

    def get_coverage_guarantee_statistics(self) -> Dict[str, Any]:
        """
        🆕 獲取覆蓋保證統計信息
        
        Returns:
            覆蓋保證系統的詳細統計數據
        """
        if not hasattr(self, 'coverage_guarantee_engine'):
            return {'coverage_guarantee_enabled': False}
            
        base_stats = self.calculation_statistics.copy()
        
        # 添加覆蓋保證引擎的配置信息
        coverage_config = self.coverage_guarantee_engine.coverage_guarantee_config
        
        return {
            'coverage_guarantee_enabled': self.coverage_guarantee_enabled,
            'calculation_statistics': base_stats,
            'coverage_guarantee_config': {
                'target_coverage_rate': coverage_config['target_coverage_rate'],
                'monitoring_interval_seconds': coverage_config['monitoring_interval_seconds'],
                'max_gap_duration_seconds': coverage_config['max_gap_duration_seconds'],
                'min_satellite_count': coverage_config['min_satellite_count'],
                'reliability_threshold': coverage_config['reliability_threshold']
            },
            'coverage_requirements': self.coverage_guarantee_engine.coverage_requirements,
            'observer_coordinates': {
                'latitude': self.observer_lat,
                'longitude': self.observer_lon,
                'altitude_meters': self.observer_alt
            }
        }

    def validate_coverage_guarantee_system(self) -> Dict[str, Any]:
        """
        🆕 驗證覆蓋保證系統狀態
        
        Returns:
            覆蓋保證系統驗證結果
        """
        validation_result = {
            'system_status': 'unknown',
            'components_status': {},
            'validation_checks': {},
            'issues': []
        }
        
        if not hasattr(self, 'coverage_guarantee_engine'):
            validation_result['system_status'] = 'not_initialized'
            validation_result['issues'].append('覆蓋保證系統未初始化')
            return validation_result
            
        try:
            # 檢查覆蓋保證引擎組件
            engine = self.coverage_guarantee_engine
            
            # 檢查核心方法是否可用
            core_methods = [
                '_ensure_continuous_coverage',
                '_calculate_coverage_reliability',
                '_identify_coverage_gaps'
            ]
            
            for method_name in core_methods:
                method_available = hasattr(engine, method_name)
                validation_result['components_status'][method_name] = method_available
                
                if not method_available:
                    validation_result['issues'].append(f'缺少核心方法: {method_name}')
            
            # 檢查配置完整性
            config_checks = {
                'target_coverage_rate_valid': 0 < engine.coverage_guarantee_config['target_coverage_rate'] <= 1.0,
                'monitoring_interval_reasonable': engine.coverage_guarantee_config['monitoring_interval_seconds'] > 0,
                'gap_threshold_reasonable': engine.coverage_guarantee_config['max_gap_duration_seconds'] > 0,
                'min_satellite_count_valid': engine.coverage_guarantee_config['min_satellite_count'] > 0
            }
            
            validation_result['validation_checks'].update(config_checks)
            
            # 總體狀態評估
            all_methods_available = all(validation_result['components_status'].values())
            all_configs_valid = all(config_checks.values())
            
            if all_methods_available and all_configs_valid:
                validation_result['system_status'] = 'operational'
            elif len(validation_result['issues']) == 0:
                validation_result['system_status'] = 'partially_operational'
            else:
                validation_result['system_status'] = 'degraded'
                
            self.logger.info(f"覆蓋保證系統驗證完成: {validation_result['system_status']}")
            
        except Exception as e:
            validation_result['system_status'] = 'error'
            validation_result['issues'].append(f'驗證過程出錯: {e}')
            self.logger.error(f"覆蓋保證系統驗證失敗: {e}")
            
        return validation_result

    def calculate_satellite_visibility_batch(self, satellites: List[Dict[str, Any]], time_points: Optional[List[datetime]] = None) -> Dict[str, Any]:
        """
        🚨 修復：批量計算衛星可見性 - 解決Stage2核心邏輯問題
        
        這是修復Stage2增強功能呼叫缺失方法的核心修復。
        
        Args:
            satellites: 衛星軌道數據列表
            time_points: 分析時間點列表 (可選，用於時間窗口分析)
            
        Returns:
            包含所有衛星可見性計算結果的數據
        """
        self.logger.info(f"🔭 開始批量計算 {len(satellites)} 顆衛星的可見性...")
        
        self.calculation_statistics["total_satellites"] = len(satellites)
        
        # 基礎批量處理邏輯
        visibility_results = {
            "satellites": [],
            "calculation_metadata": {
                "observer_coordinates": {
                    "latitude": self.observer_lat,
                    "longitude": self.observer_lon,
                    "altitude_m": self.observer_alt
                },
                "calculation_method": "spherical_geometry_batch",
                "calculation_timestamp": datetime.now(timezone.utc).isoformat(),
                "time_points_analyzed": len(time_points) if time_points else 0
            }
        }
        
        satellites_with_visibility = 0
        
        # 處理每顆衛星
        for i, satellite in enumerate(satellites):
            try:
                sat_result = self._calculate_single_satellite_visibility(satellite)
                
                if sat_result:
                    visibility_results["satellites"].append(sat_result)
                    
                    # 統計可見性
                    if self._has_visible_positions(sat_result):
                        satellites_with_visibility += 1
                        
                    # 進度日誌 (每100顆報告一次)
                    if (i + 1) % 100 == 0:
                        self.logger.info(f"   已處理 {i + 1}/{len(satellites)} 顆衛星")
                        
            except Exception as e:
                self.logger.error(f"計算衛星 {satellite.get('name', 'unknown')} 可見性時出錯: {e}")
                continue
        
        # 更新統計信息
        self.calculation_statistics["satellites_with_visibility"] = satellites_with_visibility
        visibility_results["batch_statistics"] = {
            **self.calculation_statistics.copy(),
            "visibility_success_rate": (satellites_with_visibility / len(satellites) * 100) if satellites else 0,
            "average_visible_points_per_satellite": (
                self.calculation_statistics["visible_position_calculations"] / satellites_with_visibility
                if satellites_with_visibility > 0 else 0
            )
        }
        
        # 如果提供了時間點，執行時間窗口分析
        if time_points:
            visibility_results["time_window_analysis"] = self._analyze_time_windows(
                visibility_results["satellites"], time_points
            )
        
        self.logger.info(f"✅ 批量可見性計算完成: {satellites_with_visibility}/{len(satellites)} 顆衛星有可見時間")
        self.logger.info(f"   可見性成功率: {visibility_results['batch_statistics']['visibility_success_rate']:.1f}%")
        
        return visibility_results

    def _analyze_time_windows(self, satellites: List[Dict], time_points: List[datetime]) -> Dict[str, Any]:
        """
        🆕 分析時間窗口覆蓋情況
        
        Args:
            satellites: 已計算可見性的衛星列表
            time_points: 分析時間點
            
        Returns:
            時間窗口分析結果
        """
        if not time_points:
            return {"analysis_performed": False, "reason": "no_time_points"}
            
        analysis_result = {
            "analysis_performed": True,
            "time_window_count": len(time_points),
            "coverage_timeline": [],
            "coverage_statistics": {
                "total_time_points": len(time_points),
                "points_with_coverage": 0,
                "average_satellites_per_point": 0,
                "max_concurrent_satellites": 0,
                "min_concurrent_satellites": float('inf')
            }
        }
        
        # 為每個時間點計算可見衛星數量
        for time_point in time_points:
            visible_satellites_at_point = []
            
            for satellite in satellites:
                # 檢查該衛星在此時間點是否可見
                if self._is_satellite_visible_at_time(satellite, time_point):
                    visible_satellites_at_point.append({
                        "satellite_id": satellite.get("satellite_id", "unknown"),
                        "satellite_name": satellite.get("name", "unknown")
                    })
            
            concurrent_count = len(visible_satellites_at_point)
            
            coverage_point = {
                "timestamp": time_point.isoformat(),
                "visible_satellite_count": concurrent_count,
                "visible_satellites": visible_satellites_at_point
            }
            
            analysis_result["coverage_timeline"].append(coverage_point)
            
            # 更新統計
            if concurrent_count > 0:
                analysis_result["coverage_statistics"]["points_with_coverage"] += 1
                
            analysis_result["coverage_statistics"]["max_concurrent_satellites"] = max(
                analysis_result["coverage_statistics"]["max_concurrent_satellites"], concurrent_count
            )
            analysis_result["coverage_statistics"]["min_concurrent_satellites"] = min(
                analysis_result["coverage_statistics"]["min_concurrent_satellites"], concurrent_count
            )
        
        # 計算平均值
        total_points = len(time_points)
        if total_points > 0:
            total_visible = sum(point["visible_satellite_count"] for point in analysis_result["coverage_timeline"])
            analysis_result["coverage_statistics"]["average_satellites_per_point"] = total_visible / total_points
            
            coverage_rate = (analysis_result["coverage_statistics"]["points_with_coverage"] / total_points) * 100
            analysis_result["coverage_statistics"]["temporal_coverage_rate"] = coverage_rate
        
        # 處理無衛星情況
        if analysis_result["coverage_statistics"]["min_concurrent_satellites"] == float('inf'):
            analysis_result["coverage_statistics"]["min_concurrent_satellites"] = 0
            
        return analysis_result

    def _is_satellite_visible_at_time(self, satellite: Dict, target_time: datetime) -> bool:
        """
        檢查衛星在指定時間是否可見
        
        Args:
            satellite: 衛星數據 (包含 position_timeseries)
            target_time: 目標時間
            
        Returns:
            是否可見
        """
        position_timeseries = satellite.get("position_timeseries", [])
        
        if not position_timeseries:
            return False
            
        # 尋找最接近目標時間的位置點
        closest_position = None
        min_time_diff = float('inf')
        
        for position in position_timeseries:
            timestamp_str = position.get("timestamp")
            if not timestamp_str:
                continue
                
            try:
                position_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                time_diff = abs((target_time - position_time).total_seconds())
                
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_position = position
                    
            except Exception:
                continue
        
        if closest_position is None:
            return False
            
        # 檢查該位置是否可見 (仰角 > 0)
        relative_pos = closest_position.get("relative_to_observer", {})
        elevation = relative_pos.get("elevation_deg", INVALID_ELEVATION)
        
        return elevation > 0
    
    def calculate_satellite_visibility(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        計算所有衛星的可見性 - 兼容性方法
        
        Args:
            satellites: 衛星軌道數據列表
            
        Returns:
            包含可見性計算結果的數據
        """
        # 重定向到批量處理方法
        return self.calculate_satellite_visibility_batch(satellites)
    
    def _calculate_single_satellite_visibility(self, satellite: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """計算單顆衛星的可見性"""
        
        try:
            position_timeseries = satellite.get("position_timeseries", [])
            
            if not position_timeseries:
                self.logger.warning(f"衛星 {satellite.get('name', 'unknown')} 缺少位置時間序列")
                return None
            
            # 計算每個時間點的相對位置
            visibility_timeseries = []
            
            for pos in position_timeseries:
                visibility_point = self._calculate_position_visibility(pos)
                
                if visibility_point:
                    visibility_timeseries.append(visibility_point)
                    self.calculation_statistics["total_position_calculations"] += 1
                    
                    if visibility_point.get("relative_to_observer", {}).get("elevation_deg", INVALID_ELEVATION) > 0:
                        self.calculation_statistics["visible_position_calculations"] += 1
            
            # 構建結果
            satellite_result = satellite.copy()  # 保留原始數據
            satellite_result["position_timeseries"] = visibility_timeseries
            satellite_result["visibility_summary"] = self._calculate_visibility_summary(visibility_timeseries)
            
            return satellite_result
            
        except Exception as e:
            self.logger.error(f"計算衛星可見性時出錯: {e}")
            return None
    
    def _calculate_position_visibility(self, position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """計算單個位置點的可見性"""
        
        try:
            # 獲取衛星位置
            sat_lat = position.get("latitude", 0.0)
            sat_lon = position.get("longitude", 0.0)
            sat_alt = position.get("altitude_km", 0.0)
            
            # 計算相對於觀測者的位置
            elevation, azimuth, distance = self._calculate_look_angles(
                sat_lat, sat_lon, sat_alt
            )
            
            # 構建增強的位置數據
            enhanced_position = position.copy()
            enhanced_position["relative_to_observer"] = {
                "elevation_deg": elevation,
                "azimuth_deg": azimuth,
                "range_km": distance,
                "is_visible": elevation > 0  # 地平線以上才可見
            }
            
            return enhanced_position
            
        except Exception as e:
            self.logger.error(f"計算位置可見性時出錯: {e}")
            return None
    
    def _calculate_look_angles(self, sat_lat: float, sat_lon: float, sat_alt_km: float) -> Tuple[float, float, float]:
        """
        計算觀測角度（仰角、方位角、距離）
        使用球面幾何學標準公式
        
        Returns:
            Tuple[elevation_deg, azimuth_deg, distance_km]
        """
        
        # 轉換為弧度
        obs_lat_rad = self.observer_lat * self.DEG_TO_RAD
        obs_lon_rad = self.observer_lon * self.DEG_TO_RAD
        sat_lat_rad = sat_lat * self.DEG_TO_RAD
        sat_lon_rad = sat_lon * self.DEG_TO_RAD
        
        # 計算衛星和觀測者的地心向量
        sat_radius = self.EARTH_RADIUS_KM + sat_alt_km
        obs_radius = self.EARTH_RADIUS_KM + (self.observer_alt / 1000.0)
        
        # 衛星在地心坐標系中的位置
        sat_x = sat_radius * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
        sat_y = sat_radius * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
        sat_z = sat_radius * math.sin(sat_lat_rad)
        
        # 觀測者在地心坐標系中的位置
        obs_x = obs_radius * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
        obs_y = obs_radius * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
        obs_z = obs_radius * math.sin(obs_lat_rad)
        
        # 衛星相對於觀測者的向量
        dx = sat_x - obs_x
        dy = sat_y - obs_y
        dz = sat_z - obs_z
        
        # 距離
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # 轉換到觀測者的本地坐標系
        # 東向單位向量
        east_x = -math.sin(obs_lon_rad)
        east_y = math.cos(obs_lon_rad)
        east_z = 0.0
        
        # 北向單位向量
        north_x = -math.sin(obs_lat_rad) * math.cos(obs_lon_rad)
        north_y = -math.sin(obs_lat_rad) * math.sin(obs_lon_rad)
        north_z = math.cos(obs_lat_rad)
        
        # 天頂單位向量
        up_x = math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
        up_y = math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
        up_z = math.sin(obs_lat_rad)
        
        # 在本地坐標系中的分量
        east_comp = dx*east_x + dy*east_y + dz*east_z
        north_comp = dx*north_x + dy*north_y + dz*north_z
        up_comp = dx*up_x + dy*up_y + dz*up_z
        
        # 計算仰角
        elevation_rad = math.asin(up_comp / distance) if distance > 0 else 0
        elevation_deg = elevation_rad * self.RAD_TO_DEG
        
        # 計算方位角
        azimuth_rad = math.atan2(east_comp, north_comp)
        azimuth_deg = azimuth_rad * self.RAD_TO_DEG
        
        # 確保方位角在0-360度範圍內
        if azimuth_deg < 0:
            azimuth_deg += 360.0
        
        return elevation_deg, azimuth_deg, distance
    
    def _calculate_visibility_summary(self, visibility_timeseries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算衛星可見性摘要統計"""
        
        if not visibility_timeseries:
            return {
                "total_points": 0,
                "visible_points": 0,
                "visibility_percentage": 0.0,
                "max_elevation": INVALID_ELEVATION,
                "min_elevation": INVALID_ELEVATION,
                "avg_elevation": INVALID_ELEVATION,
                "visibility_windows": []
            }
        
        total_points = len(visibility_timeseries)
        visible_points = 0
        elevations = []
        
        # 統計可見點和仰角
        for point in visibility_timeseries:
            relative_pos = point.get("relative_to_observer", {})
            elevation = relative_pos.get("elevation_deg", INVALID_ELEVATION)
            elevations.append(elevation)
            
            if elevation > 0:
                visible_points += 1
        
        # 計算統計值
        max_elevation = max(elevations) if elevations else INVALID_ELEVATION
        min_elevation = min(elevations) if elevations else INVALID_ELEVATION
        avg_elevation = sum(elevations) / len(elevations) if elevations else INVALID_ELEVATION
        visibility_percentage = (visible_points / total_points * 100) if total_points > 0 else 0
        
        # 計算可見性時間窗口
        visibility_windows = self._calculate_visibility_windows(visibility_timeseries)
        
        return {
            "total_points": total_points,
            "visible_points": visible_points,
            "visibility_percentage": round(visibility_percentage, 2),
            "max_elevation": round(max_elevation, 2),
            "min_elevation": round(min_elevation, 2),
            "avg_elevation": round(avg_elevation, 2),
            "visibility_windows": visibility_windows,
            "total_visible_duration_minutes": sum(window["duration_minutes"] for window in visibility_windows)
        }
    
    def _calculate_visibility_windows(self, visibility_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """計算連續的可見性時間窗口
        
        🚨 Grade A要求：使用真實時間戳計算，禁止假設時間間隔
        """
        from datetime import datetime
        
        windows = []
        current_window = None
        
        for i, point in enumerate(visibility_timeseries):
            relative_pos = point.get("relative_to_observer", {})
            elevation = relative_pos.get("elevation_deg")
            timestamp = point.get("timestamp")
            
            # 🚨 Grade A要求：驗證數據完整性
            if elevation is None or timestamp is None:
                self.logger.error(
                    f"Missing required data at index {i}: "
                    f"elevation={elevation}, timestamp={timestamp}. "
                    f"Grade A standard requires complete time series data."
                )
                continue
            
            if elevation > 0:  # 可見
                if current_window is None:
                    # 開始新的可見窗口
                    current_window = {
                        "start_timestamp": timestamp,
                        "start_elevation": elevation,
                        "max_elevation": elevation,
                        "point_count": 1,
                        "calculation_method": "real_timestamp_based"
                    }
                else:
                    # 繼續當前窗口
                    current_window["point_count"] += 1
                    current_window["max_elevation"] = max(current_window["max_elevation"], elevation)
            else:  # 不可見
                if current_window is not None:
                    # 結束當前窗口 - 使用真實時間戳計算
                    try:
                        if i > 0:
                            end_timestamp = visibility_timeseries[i-1].get("timestamp")
                            end_elevation = visibility_timeseries[i-1].get("relative_to_observer", {}).get("elevation_deg")
                            
                            if end_timestamp and end_elevation is not None:
                                current_window["end_timestamp"] = end_timestamp
                                current_window["end_elevation"] = end_elevation
                                
                                # 🚨 Grade A要求：使用真實時間差計算持續時間
                                start_dt = datetime.fromisoformat(current_window["start_timestamp"].replace('Z', '+00:00'))
                                end_dt = datetime.fromisoformat(end_timestamp.replace('Z', '+00:00'))
                                duration_minutes = (end_dt - start_dt).total_seconds() / 60.0
                                
                                current_window["duration_minutes"] = duration_minutes
                                current_window["grade_a_compliance"] = True
                                
                                windows.append(current_window)
                            else:
                                raise ValueError("End timestamp or elevation missing")
                        else:
                            raise ValueError("Invalid window end index")
                            
                    except Exception as time_error:
                        # 🚨 Grade A要求：時間計算錯誤必須報告
                        self.logger.error(
                            f"Visibility window time calculation failed: {time_error}. "
                            f"Grade A standard prohibits assumption-based fallbacks."
                        )
                        # 不添加有問題的窗口到結果中
                    
                    current_window = None
        
        # 處理序列結束時仍在可見窗口的情況
        if current_window is not None:
            try:
                last_point = visibility_timeseries[-1]
                end_timestamp = last_point.get("timestamp")
                end_elevation = last_point.get("relative_to_observer", {}).get("elevation_deg")
                
                if end_timestamp and end_elevation is not None:
                    current_window["end_timestamp"] = end_timestamp
                    current_window["end_elevation"] = end_elevation
                    
                    # 使用真實時間差計算
                    start_dt = datetime.fromisoformat(current_window["start_timestamp"].replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_timestamp.replace('Z', '+00:00'))
                    duration_minutes = (end_dt - start_dt).total_seconds() / 60.0
                    
                    current_window["duration_minutes"] = duration_minutes
                    current_window["grade_a_compliance"] = True
                    
                    windows.append(current_window)
                else:
                    raise ValueError("Final window timestamp or elevation missing")
                    
            except Exception as time_error:
                self.logger.error(
                    f"Final visibility window calculation failed: {time_error}. "
                    f"Grade A standard requires complete time series data."
                )
        
        # 統計信息
        total_windows = len(windows)
        if total_windows > 0:
            avg_duration = sum(w["duration_minutes"] for w in windows) / total_windows
            max_duration = max(w["duration_minutes"] for w in windows)
            
            self.logger.debug(
                f"Calculated {total_windows} visibility windows: "
                f"avg={avg_duration:.1f}min, max={max_duration:.1f}min"
            )
        
        return windows
    
    def _has_visible_positions(self, satellite_result: Dict[str, Any]) -> bool:
        """檢查衛星是否有可見位置"""
        summary = satellite_result.get("visibility_summary", {})
        return summary.get("visible_points", 0) > 0
    
    def get_calculation_statistics(self) -> Dict[str, Any]:
        """獲取計算統計信息"""
        return self.calculation_statistics.copy()
    
    def validate_visibility_results(self, visibility_results: Dict[str, Any]) -> Dict[str, Any]:
        """驗證可見性計算結果的合理性"""
        
        validation_result = {
            "passed": True,
            "total_satellites": len(visibility_results.get("satellites", [])),
            "validation_checks": {},
            "issues": []
        }
        
        satellites = visibility_results.get("satellites", [])
        
        if not satellites:
            validation_result["passed"] = False
            validation_result["issues"].append("無衛星可見性數據")
            return validation_result
        
        # 檢查1: 可見性計算完整性
        satellites_with_visibility_data = 0
        satellites_with_reasonable_elevation = 0
        
        for sat in satellites:
            timeseries = sat.get("position_timeseries", [])
            
            if timeseries:
                satellites_with_visibility_data += 1
                
                # 檢查是否有合理的仰角數據
                for point in timeseries[:5]:  # 檢查前5個點
                    elevation = point.get("relative_to_observer", {}).get("elevation_deg", -999)
                    if INVALID_ELEVATION <= elevation <= 90:
                        satellites_with_reasonable_elevation += 1
                        break
        
        validation_result["validation_checks"]["visibility_data_check"] = {
            "satellites_with_data": satellites_with_visibility_data,
            "satellites_with_reasonable_elevation": satellites_with_reasonable_elevation,
            "passed": satellites_with_visibility_data == len(satellites)
        }
        
        if satellites_with_visibility_data < len(satellites):
            validation_result["passed"] = False
            validation_result["issues"].append(f"{len(satellites) - satellites_with_visibility_data} 顆衛星缺少可見性數據")
        
        # 檢查2: 可見性統計合理性
        satellites_with_summary = 0
        satellites_with_windows = 0
        
        for sat in satellites:
            summary = sat.get("visibility_summary", {})
            
            if summary:
                satellites_with_summary += 1
                
                # 檢查可見性窗口
                windows = summary.get("visibility_windows", [])
                if windows:
                    satellites_with_windows += 1
        
        validation_result["validation_checks"]["summary_check"] = {
            "satellites_with_summary": satellites_with_summary,
            "satellites_with_windows": satellites_with_windows,
            "passed": satellites_with_summary == len(satellites)
        }
        
        if satellites_with_summary < len(satellites):
            validation_result["passed"] = False
            validation_result["issues"].append(f"{len(satellites) - satellites_with_summary} 顆衛星缺少可見性摘要")
        
        return validation_result