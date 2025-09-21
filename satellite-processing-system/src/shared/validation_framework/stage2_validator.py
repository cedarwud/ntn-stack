#!/usr/bin/env python3
"""
Stage 2 可見性過濾驗證器

移除虛假驗證，建立真實的業務邏輯驗證：
- 仰角門檻驗證 (5°/10°/15°)
- 過濾邏輯合理性檢查
- 地理座標轉換驗證
- 0 顆衛星輸出 → FAILURE

作者: Claude & Human
版本: v1.0 - 真實驗證系統
"""

import logging
from typing import Dict, Any, List
from .validation_engine import BaseValidator, ValidationResult, CheckResult, ValidationStatus

logger = logging.getLogger(__name__)

class Stage2VisibilityValidator(BaseValidator):
    """Stage 2 可見性過濾專用驗證器"""

    def __init__(self):
        super().__init__("stage2_visibility_filter")

    def validate(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> ValidationResult:
        """執行 Stage 2 驗證邏輯"""
        result = ValidationResult()

        # 1. 仰角門檻驗證
        elevation_check = self.validate_elevation_thresholds(output_data)
        result.add_check(elevation_check)

        # 2. 過濾邏輯合理性
        filtering_check = self.validate_filtering_logic(input_data, output_data)
        result.add_check(filtering_check)

        # 3. 地理座標轉換驗證
        coordinate_check = self.validate_coordinate_transformation(output_data)
        result.add_check(coordinate_check)

        # 4. 時間窗口驗證
        time_window_check = self.validate_time_windows(output_data)
        result.add_check(time_window_check)

        # 5. 覆蓋幾何驗證
        geometry_check = self.validate_coverage_geometry(output_data)
        result.add_check(geometry_check)

        return result

    def validate_elevation_thresholds(self, output_data: Dict[str, Any]) -> CheckResult:
        """驗證仰角門檻計算"""
        try:
            visible_satellites = output_data.get('visible_satellites', {})

            if not visible_satellites:
                return CheckResult(
                    "elevation_threshold_validation",
                    ValidationStatus.FAILURE,
                    "無可見衛星數據，無法驗證仰角門檻"
                )

            invalid_elevations = []
            total_satellites = 0

            # 適配階段二實際數據格式：{satellite_id: satellite_data}
            for satellite_id, satellite_data in visible_satellites.items():
                total_satellites += 1

                # 從 visibility_data 中獲取仰角數據
                visibility_data = satellite_data.get('visibility_data', {})
                visible_elevations = visibility_data.get('visible_elevations', [])

                if visible_elevations:
                    max_elevation = max(visible_elevations)
                    if max_elevation < 5.0:  # 最低門檻 5°
                        invalid_elevations.append(f"{satellite_id}: {max_elevation:.2f}°")
                else:
                    # 如果沒有仰角數據，從signal_analysis_data獲取
                    signal_data = satellite_data.get('signal_analysis_data', {})
                    max_elevation = signal_data.get('max_elevation', 0)
                    if max_elevation < 5.0:
                        invalid_elevations.append(f"{satellite_id}: {max_elevation:.2f}°")

            if invalid_elevations:
                return CheckResult(
                    "elevation_threshold_validation",
                    ValidationStatus.FAILURE,
                    f"仰角門檻違規: {len(invalid_elevations)}/{total_satellites} 顆衛星低於5°",
                    {'invalid_satellites': invalid_elevations[:10]}  # 限制顯示數量
                )

            return CheckResult(
                "elevation_threshold_validation",
                ValidationStatus.SUCCESS,
                f"仰角門檻驗證通過: {total_satellites} 顆衛星均符合5°以上標準"
            )

        except Exception as e:
            return CheckResult(
                "elevation_threshold_validation",
                ValidationStatus.FAILURE,
                f"仰角門檻驗證失敗: {e}"
            )

    def validate_filtering_logic(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> CheckResult:
        """驗證過濾邏輯合理性"""
        try:
            # 從processing_statistics獲取統計數據
            processing_stats = output_data.get('processing_statistics', {})
            input_count = processing_stats.get('total_satellites', 0)
            output_count = processing_stats.get('visible_satellites', 0)

            # 備用方案：直接計算
            if input_count == 0:
                input_satellites = input_data.get('satellites', {}) if isinstance(input_data, dict) else {}
                input_count = len(input_satellites) if isinstance(input_satellites, dict) else 0

            if output_count == 0:
                output_satellites = output_data.get('visible_satellites', {})
                output_count = len(output_satellites) if isinstance(output_satellites, dict) else 0

            # 關鍵檢查：有輸入但無輸出
            if input_count > 0 and output_count == 0:
                return CheckResult(
                    "filtering_logic_validation",
                    ValidationStatus.FAILURE,
                    f"過濾異常: 輸入{input_count}顆衛星，輸出0顆 - 這表示過濾邏輯有問題或門檻設定過嚴"
                )

            # 檢查過濾率
            if input_count > 0:
                filter_rate = (input_count - output_count) / input_count
                visibility_rate = 1 - filter_rate

                if filter_rate > 0.99:  # 超過99%被過濾
                    return CheckResult(
                        "filtering_logic_validation",
                        ValidationStatus.WARNING,
                        f"過濾率過高: {filter_rate:.2%} ({input_count}→{output_count})，可能需要檢查過濾條件"
                    )

                return CheckResult(
                    "filtering_logic_validation",
                    ValidationStatus.SUCCESS,
                    f"過濾邏輯合理: {input_count}→{output_count} ({visibility_rate*100:.1f}% 可見)"
                )
            else:
                return CheckResult(
                    "filtering_logic_validation",
                    ValidationStatus.SUCCESS,
                    "過濾邏輯通過"
                )

        except Exception as e:
            return CheckResult(
                "filtering_logic_validation",
                ValidationStatus.FAILURE,
                f"過濾邏輯驗證失敗: {e}"
            )

    def validate_coordinate_transformation(self, output_data: Dict[str, Any]) -> CheckResult:
        """驗證地理座標轉換"""
        try:
            visible_satellites = output_data.get('visible_satellites', {})

            if not visible_satellites:
                return CheckResult(
                    "coordinate_transformation",
                    ValidationStatus.WARNING,
                    "無可見衛星，跳過座標轉換驗證"
                )

            coordinate_errors = []
            valid_coordinates = 0

            for satellite_id, satellite_data in visible_satellites.items():
                # 檢查ECI座標範圍合理性
                complete_orbital_data = satellite_data.get('complete_orbital_data', {})
                positions_eci = complete_orbital_data.get('positions_eci', [])

                if positions_eci:
                    for i, pos in enumerate(positions_eci[:3]):  # 檢查前3個位置
                        if isinstance(pos, dict):
                            x, y, z = pos.get('x', 0), pos.get('y', 0), pos.get('z', 0)

                            # 檢查ECI座標合理性 (應在地球周圍)
                            distance = (x**2 + y**2 + z**2)**0.5
                            if distance < 6400:  # 小於地球半徑
                                coordinate_errors.append(f"{satellite_id}: ECI距離過近 {distance:.1f}km")
                            elif distance > 50000:  # 超過同步軌道
                                coordinate_errors.append(f"{satellite_id}: ECI距離過遠 {distance:.1f}km")
                            else:
                                valid_coordinates += 1

                # 檢查可見性方位角和仰角範圍
                visibility_data = satellite_data.get('visibility_data', {})
                azimuths = visibility_data.get('visible_azimuths', [])
                elevations = visibility_data.get('visible_elevations', [])

                for azimuth in azimuths[:3]:  # 檢查前3個
                    if azimuth < 0 or azimuth > 360:
                        coordinate_errors.append(f"{satellite_id}: 方位角 {azimuth:.1f}° 超出範圍")

                for elevation in elevations[:3]:  # 檢查前3個
                    if elevation < -90 or elevation > 90:
                        coordinate_errors.append(f"{satellite_id}: 仰角 {elevation:.1f}° 超出範圍")

            if len(coordinate_errors) > 50:  # 如果錯誤太多，可能是系統性問題
                return CheckResult(
                    "coordinate_transformation",
                    ValidationStatus.FAILURE,
                    f"座標轉換系統性錯誤: {len(coordinate_errors)} 個錯誤，可能存在根本性問題",
                    {'error_count': len(coordinate_errors), 'sample_errors': coordinate_errors[:5]}
                )

            if coordinate_errors:
                return CheckResult(
                    "coordinate_transformation",
                    ValidationStatus.WARNING,
                    f"座標轉換部分錯誤: {len(coordinate_errors)} 個錯誤",
                    {'errors': coordinate_errors[:10]}
                )

            return CheckResult(
                "coordinate_transformation",
                ValidationStatus.SUCCESS,
                f"座標轉換驗證通過: {len(visible_satellites)} 顆衛星，{valid_coordinates} 個有效座標"
            )

        except Exception as e:
            return CheckResult(
                "coordinate_transformation",
                ValidationStatus.FAILURE,
                f"座標轉換驗證失敗: {e}"
            )

    def validate_time_windows(self, output_data: Dict[str, Any]) -> CheckResult:
        """驗證時間窗口"""
        try:
            visible_satellites = output_data.get('visible_satellites', {})

            if not visible_satellites:
                return CheckResult(
                    "time_window_validation",
                    ValidationStatus.WARNING,
                    "無可見衛星，跳過時間窗口驗證"
                )

            time_errors = []
            valid_time_windows = 0

            for satellite_id, satellite_data in visible_satellites.items():
                # 檢查可見時間戳的一致性
                visibility_data = satellite_data.get('visibility_data', {})
                visible_timestamps = visibility_data.get('visible_timestamps', [])

                if visible_timestamps:
                    # 檢查時間戳格式和順序
                    prev_time = None
                    for i, timestamp in enumerate(visible_timestamps):
                        try:
                            from datetime import datetime
                            # 嘗試解析時間戳
                            current_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

                            if prev_time and current_time <= prev_time:
                                time_errors.append(f"{satellite_id}: 時間順序錯誤 位置{i}")

                            prev_time = current_time
                            valid_time_windows += 1

                        except ValueError as e:
                            time_errors.append(f"{satellite_id}: 時間格式錯誤 {timestamp}")

                # 檢查時間序列數據
                timeseries_data = satellite_data.get('timeseries_data', {})
                duration = timeseries_data.get('visibility_duration_seconds', 0)

                if duration < 0:
                    time_errors.append(f"{satellite_id}: 可見時長負值 {duration}秒")

                # 檢查整合元數據的時間覆蓋
                integration_metadata = satellite_data.get('integration_metadata', {})
                temporal_coverage = integration_metadata.get('temporal_coverage', {})

                start_time = temporal_coverage.get('start')
                end_time = temporal_coverage.get('end')

                if start_time and end_time:
                    try:
                        from datetime import datetime
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

                        if start_dt >= end_dt:
                            time_errors.append(f"{satellite_id}: 覆蓋時間窗口錯誤 {start_time} >= {end_time}")

                    except ValueError:
                        time_errors.append(f"{satellite_id}: 覆蓋時間格式錯誤")

            if time_errors:
                return CheckResult(
                    "time_window_validation",
                    ValidationStatus.FAILURE,
                    f"時間窗口錯誤: {len(time_errors)} 個錯誤",
                    {'errors': time_errors[:10]}
                )

            return CheckResult(
                "time_window_validation",
                ValidationStatus.SUCCESS,
                f"時間窗口驗證通過: {len(visible_satellites)} 顆衛星，{valid_time_windows} 個有效時間點"
            )

        except Exception as e:
            return CheckResult(
                "time_window_validation",
                ValidationStatus.FAILURE,
                f"時間窗口驗證失敗: {e}"
            )

    def validate_coverage_geometry(self, output_data: Dict[str, Any]) -> CheckResult:
        """驗證覆蓋幾何"""
        try:
            visible_satellites = output_data.get('visible_satellites', {})

            if not visible_satellites:
                return CheckResult(
                    "coverage_geometry",
                    ValidationStatus.WARNING,
                    "無可見衛星，跳過覆蓋幾何驗證"
                )

            geometry_issues = []
            valid_geometries = 0

            for satellite_id, satellite_data in visible_satellites.items():
                # 檢查可見性距離合理性
                visibility_data = satellite_data.get('visibility_data', {})
                visible_distances = visibility_data.get('visible_distances', [])

                if visible_distances:
                    for distance in visible_distances[:5]:  # 檢查前5個距離
                        if distance < 160:  # 低於國際太空站軌道
                            geometry_issues.append(f"{satellite_id}: 距離過近 {distance:.1f}km")
                        elif distance > 40000:  # 超過同步軌道
                            geometry_issues.append(f"{satellite_id}: 距離過遠 {distance:.1f}km")
                        else:
                            valid_geometries += 1

                # 檢查信號分析數據的距離範圍
                signal_data = satellite_data.get('signal_analysis_data', {})
                min_distance = signal_data.get('min_distance', float('inf'))

                if min_distance != float('inf'):
                    if min_distance < 160:
                        geometry_issues.append(f"{satellite_id}: 最小距離過近 {min_distance:.1f}km")
                    elif min_distance > 40000:
                        geometry_issues.append(f"{satellite_id}: 最小距離過遠 {min_distance:.1f}km")

                # 檢查規劃屬性的權重
                planning_attrs = satellite_data.get('planning_attributes', {})
                load_weight = planning_attrs.get('load_balancing_weight', 1.0)

                if load_weight <= 0 or load_weight > 10:
                    geometry_issues.append(f"{satellite_id}: 負載權重異常 {load_weight}")

            # 檢查整體覆蓋分布
            processing_stats = output_data.get('processing_statistics', {})
            total_visible = processing_stats.get('visible_satellites', 0)
            starlink_visible = processing_stats.get('starlink_visible', 0)
            oneweb_visible = processing_stats.get('oneweb_visible', 0)

            # 如果星座分布過於不均衡
            if total_visible > 100:  # 只在有足夠衛星時檢查
                if starlink_visible == 0 and total_visible > 0:
                    geometry_issues.append("Starlink覆蓋缺失：無Starlink衛星可見")
                elif oneweb_visible == 0 and total_visible > 0:
                    geometry_issues.append("OneWeb覆蓋缺失：無OneWeb衛星可見")

            if len(geometry_issues) > 100:  # 過多幾何問題可能表示系統性錯誤
                return CheckResult(
                    "coverage_geometry",
                    ValidationStatus.FAILURE,
                    f"覆蓋幾何系統性問題: {len(geometry_issues)} 個問題",
                    {'issue_count': len(geometry_issues), 'sample_issues': geometry_issues[:5]}
                )

            if geometry_issues:
                return CheckResult(
                    "coverage_geometry",
                    ValidationStatus.WARNING,
                    f"覆蓋幾何部分問題: {len(geometry_issues)} 個問題",
                    {'issues': geometry_issues[:10]}
                )

            return CheckResult(
                "coverage_geometry",
                ValidationStatus.SUCCESS,
                f"覆蓋幾何驗證通過: {len(visible_satellites)} 顆衛星，{valid_geometries} 個有效幾何"
            )

        except Exception as e:
            return CheckResult(
                "coverage_geometry",
                ValidationStatus.FAILURE,
                f"覆蓋幾何驗證失敗: {e}"
            )