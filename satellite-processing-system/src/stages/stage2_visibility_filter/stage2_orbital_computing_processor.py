#!/usr/bin/env python3
"""
Stage 2: 軌道計算層處理器 (重構版本)

重構原則：
- 專注軌道計算和可見性分析
- 整合原Stage 1的SGP4計算和Stage 2的可見性過濾
- 使用共享的預測和監控模組
- 實現統一的處理器接口

功能整合：
- ✅ 從Stage 1遷移: SGP4軌道計算、座標轉換
- ✅ 從Stage 2整合: 可見性篩選、地理過濾
- ✅ 新增: 軌道預測、時空優化基礎
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import math

# 共享模組導入
from shared.interfaces import BaseProcessor, ProcessingStatus, ProcessingResult, create_processing_result
from shared.validation_framework import ValidationEngine
from shared.prediction import TrajectoryPredictor, PredictionConfig
from shared.monitoring import PerformanceMonitor, MonitoringConfig
from shared.utils import TimeUtils, MathUtils
from shared.constants import PhysicsConstantsManager, SystemConstantsManager

# Stage 1,2專用模組
from ..stage1_orbital_calculation.orbital_calculator import OrbitalCalculator
from .simple_geographic_filter import SimpleGeographicFilter

logger = logging.getLogger(__name__)


class Stage2OrbitalComputingProcessor(BaseProcessor):
    """
    Stage 2: 軌道計算層處理器 (重構版本)

    專職責任：
    1. SGP4軌道計算和位置預測
    2. 座標系統轉換和幾何計算
    3. 可見性分析和地理過濾
    4. 軌道預測和時空關係建立
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Stage2OrbitalComputingProcessor", config or {})

        # 配置參數
        self.time_points = self.config.get('time_points', 24)
        self.time_interval = self.config.get('time_interval', 300)  # 5分鐘
        self.min_elevation = self.config.get('min_elevation_deg', 10.0)
        self.prediction_horizon_hours = self.config.get('prediction_horizon_hours', 24)

        # 觀測者位置（台灣預設）
        self.observer_config = self.config.get('observer', {
            'latitude': 24.9,
            'longitude': 121.3,
            'altitude_km': 0.035
        })

        # 初始化組件
        self.orbital_calculator = OrbitalCalculator()
        self.geographic_filter = SimpleGeographicFilter()
        self.validation_engine = ValidationEngine('stage2')

        # 初始化共享服務
        self._initialize_shared_services()

        # 處理統計
        self.processing_stats = {
            'total_satellites_processed': 0,
            'successful_calculations': 0,
            'failed_calculations': 0,
            'visible_satellites': 0,
            'prediction_cache_hits': 0
        }

        self.logger.info("Stage 2 軌道計算處理器已初始化")

    def _initialize_shared_services(self):
        """初始化共享服務"""
        # 軌道預測器
        prediction_config = PredictionConfig(
            predictor_name="orbital_predictor",
            model_type="physics_based",
            prediction_horizon=timedelta(hours=self.prediction_horizon_hours)
        )
        self.trajectory_predictor = TrajectoryPredictor(prediction_config)

        # 性能監控
        from shared.monitoring import PerformanceMonitoringConfig
        performance_monitoring_config = PerformanceMonitoringConfig(
            monitor_name="stage2_orbital_computing",
            stage_timeout_thresholds={
                'orbital_calculation': 30.0,
                'visibility_analysis': 60.0,
                'coordinate_transformation': 10.0
            }
        )
        self.performance_monitor = PerformanceMonitor(performance_monitoring_config)

        # 物理常數管理
        self.physics_constants = PhysicsConstantsManager()
        self.system_constants = SystemConstantsManager()

    def process(self, input_data: Any) -> ProcessingResult:
        """
        主要處理方法

        Args:
            input_data: Stage 1輸出的TLE數據

        Returns:
            處理結果，包含軌道計算和可見性分析結果
        """
        start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 開始Stage 2軌道計算處理...")

        try:
            # 驗證輸入數據
            if not self._validate_stage1_output(input_data):
                return create_processing_result(
                    status=ProcessingStatus.VALIDATION_FAILED,
                    data={},
                    message="Stage 1輸出數據驗證失敗"
                )

            # 提取TLE數據
            tle_data = self._extract_tle_data(input_data)
            if not tle_data:
                return create_processing_result(
                    status=ProcessingStatus.ERROR,
                    data={},
                    message="未找到有效的TLE數據"
                )

            # 執行軌道計算
            with self.performance_monitor.measure_operation("orbital_calculation"):
                orbital_results = self._perform_orbital_calculations(tle_data)

            # 執行可見性分析
            with self.performance_monitor.measure_operation("visibility_analysis"):
                visibility_results = self._perform_visibility_analysis(orbital_results)

            # 執行軌道預測
            with self.performance_monitor.measure_operation("trajectory_prediction"):
                prediction_results = self._perform_trajectory_prediction(orbital_results)

            # 整合結果
            integrated_results = self._integrate_results(
                orbital_results, visibility_results, prediction_results
            )

            # 數據驗證
            validation_result = self._validate_output_data(integrated_results)

            # 處理ValidationResult對象
            if hasattr(validation_result, 'overall_status'):
                is_valid = validation_result.overall_status == 'PASS'
                validation_dict = validation_result.to_dict()
                errors = [check['message'] for check in validation_dict['detailed_results']
                         if check['status'] == 'FAILURE']
            else:
                # 字典格式
                is_valid = validation_result.get('valid', False)
                errors = validation_result.get('errors', [])

            if not is_valid:
                return create_processing_result(
                    status=ProcessingStatus.VALIDATION_FAILED,
                    data={},
                    message=f"輸出數據驗證失敗: {errors}"
                )

            # 構建最終結果
            processing_time = datetime.now(timezone.utc) - start_time
            result_data = {
                'stage': 'stage2_orbital_computing',
                'satellites': integrated_results,
                'metadata': {
                    'processing_start_time': start_time.isoformat(),
                    'processing_end_time': datetime.now(timezone.utc).isoformat(),
                    'processing_duration_seconds': processing_time.total_seconds(),
                    'calculation_base_time': self._get_calculation_base_time(tle_data),
                    'observer_position': self.observer_config,
                    'min_elevation_deg': self.min_elevation,
                    'prediction_horizon_hours': self.prediction_horizon_hours
                },
                'processing_stats': self.processing_stats,
                'performance_metrics': self.performance_monitor.get_metrics(),
                'next_stage_ready': True
            }

            self.logger.info(
                f"✅ Stage 2軌道計算完成，處理{self.processing_stats['total_satellites_processed']}顆衛星，"
                f"可見{self.processing_stats['visible_satellites']}顆"
            )

            return create_processing_result(
                status=ProcessingStatus.SUCCESS,
                data=result_data,
                message=f"成功完成{self.processing_stats['total_satellites_processed']}顆衛星的軌道計算"
            )

        except Exception as e:
            self.logger.error(f"❌ Stage 2軌道計算失敗: {e}")
            return create_processing_result(
                status=ProcessingStatus.ERROR,
                data={},
                message=f"軌道計算錯誤: {str(e)}"
            )

    def _validate_stage1_output(self, input_data: Any) -> bool:
        """驗證Stage 1的輸出數據"""
        if not isinstance(input_data, dict):
            self.logger.error("輸入數據必須是字典格式")
            return False

        required_fields = ['stage', 'tle_data', 'metadata']
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"缺少必要字段: {field}")
                return False

        if input_data['stage'] != 'stage1_data_loading':
            self.logger.error("輸入數據不是來自Stage 1")
            return False

        return True

    def _extract_tle_data(self, input_data: Dict[str, Any]) -> List[Dict]:
        """從Stage 1輸出中提取TLE數據"""
        try:
            tle_data = input_data['tle_data']
            if not isinstance(tle_data, list):
                self.logger.error("TLE數據必須是列表格式")
                return []

            self.logger.info(f"提取到{len(tle_data)}顆衛星的TLE數據")
            return tle_data

        except Exception as e:
            self.logger.error(f"提取TLE數據失敗: {e}")
            return []

    def _get_calculation_base_time(self, tle_data: List[Dict]) -> str:
        """獲取計算基準時間（使用TLE epoch時間）"""
        if not tle_data:
            return datetime.now(timezone.utc).isoformat()

        # 使用第一個TLE的epoch時間作為基準
        first_tle = tle_data[0]
        if 'epoch_datetime' in first_tle:
            return first_tle['epoch_datetime']

        # 如果沒有標準化時間，從TLE行解析
        try:
            line1 = first_tle['line1']
            epoch_year = int(line1[18:20])
            epoch_day = float(line1[20:32])

            if epoch_year < 57:
                full_year = 2000 + epoch_year
            else:
                full_year = 1900 + epoch_year

            epoch_time = TimeUtils.parse_tle_epoch(full_year, epoch_day)
            return epoch_time.isoformat()

        except Exception as e:
            self.logger.warning(f"解析TLE時間失敗: {e}")
            return datetime.now(timezone.utc).isoformat()

    def _perform_orbital_calculations(self, tle_data: List[Dict]) -> Dict[str, Any]:
        """執行軌道計算"""
        orbital_results = {}
        calculation_base_time_str = self._get_calculation_base_time(tle_data)
        calculation_base_time = datetime.fromisoformat(calculation_base_time_str.replace('Z', '+00:00'))

        self.logger.info(f"使用計算基準時間: {calculation_base_time}")

        for tle in tle_data:
            satellite_id = tle.get('satellite_id', 'unknown')
            self.processing_stats['total_satellites_processed'] += 1

            try:
                # 生成時間序列
                time_series = TimeUtils.generate_time_series(
                    start_time=calculation_base_time,
                    end_time=calculation_base_time + timedelta(hours=self.prediction_horizon_hours),
                    step_minutes=self.time_interval // 60
                )

                # 為每個時間點計算軌道位置
                positions = []
                for time_point in time_series:
                    # 計算從epoch的時間差（分鐘）
                    if 'epoch_datetime' in tle:
                        epoch_time = datetime.fromisoformat(tle['epoch_datetime'].replace('Z', '+00:00'))
                    else:
                        epoch_time = calculation_base_time

                    time_since_epoch = (time_point - epoch_time).total_seconds() / 60.0

                    # 使用SGP4計算位置
                    position = self.orbital_calculator.calculate_position(
                        tle['line1'], tle['line2'], time_since_epoch
                    )

                    if position:
                        # 添加時間信息
                        position['timestamp'] = time_point.isoformat()
                        position['time_since_epoch_minutes'] = time_since_epoch
                        positions.append(position)

                if positions:
                    orbital_results[satellite_id] = {
                        'satellite_id': satellite_id,
                        'name': tle.get('name', ''),
                        'tle_line1': tle['line1'],
                        'tle_line2': tle['line2'],
                        'positions': positions,
                        'calculation_successful': True,
                        'calculation_base_time': calculation_base_time_str
                    }
                    self.processing_stats['successful_calculations'] += 1
                else:
                    self.logger.warning(f"衛星 {satellite_id} 軌道計算失敗")
                    self.processing_stats['failed_calculations'] += 1

            except Exception as e:
                self.logger.error(f"衛星 {satellite_id} 軌道計算異常: {e}")
                self.processing_stats['failed_calculations'] += 1

        return orbital_results

    def _perform_visibility_analysis(self, orbital_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行可見性分析"""
        visibility_results = {}

        observer_lat = self.observer_config['latitude']
        observer_lon = self.observer_config['longitude']
        observer_alt = self.observer_config['altitude_km']

        for satellite_id, orbit_data in orbital_results.items():
            try:
                visible_windows = []
                current_window = None

                for position in orbit_data['positions']:
                    # 計算仰角和方位角
                    elevation, azimuth = self._calculate_look_angles(
                        position, observer_lat, observer_lon, observer_alt
                    )

                    position['elevation_deg'] = elevation
                    position['azimuth_deg'] = azimuth
                    position['is_visible'] = elevation >= self.min_elevation

                    # 可見性窗口檢測
                    if elevation >= self.min_elevation:
                        if current_window is None:
                            current_window = {
                                'start_time': position['timestamp'],
                                'start_elevation': elevation,
                                'max_elevation': elevation,
                                'positions': []
                            }
                        else:
                            current_window['max_elevation'] = max(current_window['max_elevation'], elevation)

                        current_window['positions'].append(position)
                    else:
                        if current_window is not None:
                            current_window['end_time'] = current_window['positions'][-1]['timestamp']
                            current_window['duration_minutes'] = len(current_window['positions']) * (self.time_interval / 60)
                            visible_windows.append(current_window)
                            current_window = None

                # 處理最後一個窗口
                if current_window is not None:
                    current_window['end_time'] = current_window['positions'][-1]['timestamp']
                    current_window['duration_minutes'] = len(current_window['positions']) * (self.time_interval / 60)
                    visible_windows.append(current_window)

                visibility_results[satellite_id] = {
                    'satellite_id': satellite_id,
                    'visible_windows': visible_windows,
                    'total_visible_time_minutes': sum(w['duration_minutes'] for w in visible_windows),
                    'is_currently_visible': any(p.get('is_visible', False) for p in orbit_data['positions'][:1]),
                    'next_pass_time': visible_windows[0]['start_time'] if visible_windows else None
                }

                if visible_windows:
                    self.processing_stats['visible_satellites'] += 1

            except Exception as e:
                self.logger.error(f"衛星 {satellite_id} 可見性分析失敗: {e}")

        return visibility_results

    def _calculate_look_angles(self, satellite_pos: Dict, obs_lat: float, obs_lon: float, obs_alt: float) -> Tuple[float, float]:
        """計算觀測角度（仰角和方位角）"""
        try:
            # 衛星位置（km）
            sat_x = satellite_pos.get('x', 0)
            sat_y = satellite_pos.get('y', 0)
            sat_z = satellite_pos.get('z', 0)

            # 觀測者位置轉換為ECEF坐標
            earth_radius = 6371.0  # km
            obs_lat_rad = math.radians(obs_lat)
            obs_lon_rad = math.radians(obs_lon)

            obs_x = (earth_radius + obs_alt) * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
            obs_y = (earth_radius + obs_alt) * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
            obs_z = (earth_radius + obs_alt) * math.sin(obs_lat_rad)

            # 相對位置向量
            rel_x = sat_x - obs_x
            rel_y = sat_y - obs_y
            rel_z = sat_z - obs_z

            # 距離
            range_km = math.sqrt(rel_x**2 + rel_y**2 + rel_z**2)

            # 轉換到局部坐標系
            # 簡化的仰角計算
            elevation_rad = math.asin(rel_z / range_km) if range_km > 0 else 0
            elevation_deg = math.degrees(elevation_rad)

            # 簡化的方位角計算
            azimuth_rad = math.atan2(rel_y, rel_x)
            azimuth_deg = math.degrees(azimuth_rad)
            if azimuth_deg < 0:
                azimuth_deg += 360

            return elevation_deg, azimuth_deg

        except Exception as e:
            self.logger.warning(f"角度計算失敗: {e}")
            return 0.0, 0.0

    def _perform_trajectory_prediction(self, orbital_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行軌道預測"""
        prediction_results = {}

        for satellite_id, orbit_data in orbital_results.items():
            try:
                # 構建預測輸入數據
                if orbit_data['positions']:
                    latest_position = orbit_data['positions'][-1]

                    # 使用軌道預測器
                    prediction_input = {
                        'satellite_id': int(satellite_id) if satellite_id.isdigit() else hash(satellite_id) % 10000,
                        'current_position': latest_position,
                        'tle_data': {
                            'line1': orbit_data['tle_line1'],
                            'line2': orbit_data['tle_line2']
                        },
                        'observer_location': {
                            'latitude': self.observer_config['latitude'],
                            'longitude': self.observer_config['longitude'],
                            'altitude': self.observer_config['altitude_km']
                        },
                        'start_time': datetime.now()
                    }

                    prediction = self.trajectory_predictor.predict(prediction_input)

                    prediction_results[satellite_id] = {
                        'satellite_id': satellite_id,
                        'prediction_horizon_hours': self.prediction_horizon_hours,
                        'confidence_score': prediction.confidence_score,
                        'predicted_positions': prediction.predicted_positions,
                        'visibility_windows': prediction.visibility_windows,
                        'orbital_parameters': prediction.orbital_parameters
                    }

            except Exception as e:
                self.logger.warning(f"衛星 {satellite_id} 軌道預測失敗: {e}")

        return prediction_results

    def _integrate_results(self, orbital_results: Dict, visibility_results: Dict, prediction_results: Dict) -> Dict[str, Any]:
        """整合所有計算結果"""
        integrated_results = {}

        for satellite_id in orbital_results.keys():
            orbital_data = orbital_results.get(satellite_id, {})
            visibility_data = visibility_results.get(satellite_id, {})
            prediction_data = prediction_results.get(satellite_id, {})

            # 提取驗證所需的頂層字段
            integrated_results[satellite_id] = {
                'satellite_id': satellite_id,
                # 軌道數據 - 提取驗證所需字段到頂層
                'positions': orbital_data.get('positions', []),
                'calculation_successful': orbital_data.get('calculation_successful', False),
                # 可見性數據 - 提取驗證所需字段到頂層
                'visible_windows': visibility_data.get('visible_windows', []),
                'visibility_status': visibility_data.get('status', 'unknown'),
                # 原始數據保留
                'orbital_data': orbital_data,
                'visibility_data': visibility_data,
                'prediction_data': prediction_data,
                'integration_timestamp': datetime.now(timezone.utc).isoformat()
            }

        return integrated_results

    def _validate_output_data(self, integrated_results: Dict[str, Any]) -> Dict[str, Any]:
        """驗證輸出數據"""
        validation_rules = {
            'min_satellites': 1,
            'required_orbital_fields': ['positions', 'calculation_successful'],
            'required_visibility_fields': ['visible_windows'],
            'coordinate_range_check': True
        }

        return self.validation_engine.validate(integrated_results, validation_rules)

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """驗證輸入數據"""
        errors = []
        warnings = []

        if self._validate_stage1_output(input_data):
            return {'valid': True, 'errors': errors, 'warnings': warnings}
        else:
            errors.append("Stage 1輸出數據驗證失敗")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """驗證輸出數據"""
        errors = []
        warnings = []

        if not isinstance(output_data, dict):
            errors.append("輸出數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        required_fields = ['stage', 'visible_satellites', 'metadata']
        for field in required_fields:
            if field not in output_data:
                errors.append(f"缺少必需字段: {field}")

        if output_data.get('stage') != 'stage2_orbital_computing':
            errors.append("階段標識錯誤")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def extract_key_metrics(self) -> Dict[str, Any]:
        """提取關鍵指標"""
        return {
            'stage': 'stage2_orbital_computing',
            'satellites_processed': self.processing_stats['total_satellites_processed'],
            'successful_calculations': self.processing_stats['successful_calculations'],
            'failed_calculations': self.processing_stats['failed_calculations'],
            'visible_satellites': self.processing_stats['visible_satellites'],
            'calculation_success_rate': (
                self.processing_stats['successful_calculations'] /
                max(1, self.processing_stats['total_satellites_processed'])
            ) * 100,
            'visibility_rate': (
                self.processing_stats['visible_satellites'] /
                max(1, self.processing_stats['successful_calculations'])
            ) * 100
        }


def create_stage2_processor(config: Optional[Dict[str, Any]] = None) -> Stage2OrbitalComputingProcessor:
    """
    創建Stage 2軌道計算處理器實例

    Args:
        config: 可選配置參數

    Returns:
        Stage 2處理器實例
    """
    return Stage2OrbitalComputingProcessor(config)