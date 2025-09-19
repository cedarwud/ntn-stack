"""
統一數據載入器 - 整合多階段數據載入功能

整合 timeseries_data_loader.py 和 visibility_data_loader.py 的功能，
提供統一的數據載入接口，減少代碼重複。
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# 無效仰角常數 (從 visibility_data_loader.py 繼承)
INVALID_ELEVATION = -999.0

class UnifiedDataLoader:
    """統一數據載入器 - 支援多階段數據載入"""

    def __init__(self, config: Optional[Dict] = None):
        """初始化統一數據載入器"""
        self.logger = logging.getLogger(f"{__name__}.UnifiedDataLoader")

        # 配置參數
        self.config = config or {}

        # 自動檢測環境並設置輸入目錄
        self.stage2_input_dir = self._detect_stage2_input_dir()
        self.stage3_input_dir = self._detect_stage3_input_dir()

        # 統一載入統計
        self.load_statistics = {
            "stage2_data": {
                "files_found": 0,
                "satellites_loaded": 0,
                "constellations_found": 0,
                "visibility_windows_total": 0,
                "load_errors": 0
            },
            "stage3_data": {
                "total_satellites_loaded": 0,
                "total_timeseries_points": 0,
                "constellations_loaded": 0,
                "animation_frames_loaded": 0,
                "data_quality_score": 0.0
            },
            "unified_statistics": {
                "total_load_attempts": 0,
                "successful_loads": 0,
                "failed_loads": 0,
                "data_integration_score": 0.0
            }
        }

        self.logger.info("✅ 統一數據載入器初始化完成")
        self.logger.info(f"   Stage 2 輸入目錄: {self.stage2_input_dir}")
        self.logger.info(f"   Stage 3 輸入目錄: {self.stage3_input_dir}")

    def _detect_stage2_input_dir(self) -> Path:
        """自動檢測Stage 2輸入目錄"""
        if os.path.exists("/satellite-processing") or Path(".").exists():
            return Path("data/stage2_outputs")  # 容器環境
        else:
            return Path("/tmp/ntn-stack-dev/stage2_outputs")  # 開發環境

    def _detect_stage3_input_dir(self) -> Path:
        """自動檢測Stage 3輸入目錄"""
        # Stage 3 標準輸出路徑
        standard_paths = [
            Path("/satellite-processing/data/outputs/stage3/signal_analysis_output.json"),
            Path("data/stage3_outputs/timeseries_preprocessing_output.json"),
            Path("/app/data/stage3_signal_analysis_output.json")
        ]

        for path in standard_paths:
            if path.exists():
                return path.parent

        # 默認路徑
        return Path("data/stage3_outputs")

    def load_stage2_output(self) -> Dict[str, Any]:
        """
        載入Stage 2可見性篩選輸出 (整合自 visibility_data_loader.py)

        Returns:
            Stage 2數據，已驗證和標準化
        """
        self.logger.info("🔄 載入Stage 2可見性篩選輸出...")
        self.load_statistics["unified_statistics"]["total_load_attempts"] += 1

        try:
            # 檢查多個可能的文件名
            possible_files = [
                "visibility_filter_output.json",
                "stage2_output.json"
            ]

            stage2_data = None

            for filename in possible_files:
                file_path = self.stage2_input_dir / filename
                if file_path.exists():
                    self.logger.info(f"   找到Stage 2文件: {file_path}")

                    with open(file_path, 'r', encoding='utf-8') as f:
                        stage2_data = json.load(f)

                    self.load_statistics["stage2_data"]["files_found"] += 1
                    break

            if stage2_data is None:
                raise FileNotFoundError(f"未找到Stage 2輸出文件，檢查目錄: {self.stage2_input_dir}")

            # 驗證和標準化數據
            validated_data = self._validate_and_normalize_stage2_data(stage2_data)

            self.load_statistics["unified_statistics"]["successful_loads"] += 1
            self.logger.info("✅ Stage 2數據載入完成")

            return validated_data

        except Exception as e:
            self.logger.error(f"❌ Stage 2數據載入失敗: {e}")
            self.load_statistics["stage2_data"]["load_errors"] += 1
            self.load_statistics["unified_statistics"]["failed_loads"] += 1
            raise

    def load_stage3_output(self) -> Dict[str, Any]:
        """
        載入Stage 3信號分析輸出 (整合自 timeseries_data_loader.py)

        Returns:
            Stage 3數據，已驗證格式
        """
        self.logger.info("🔄 載入Stage 3信號分析輸出...")
        self.load_statistics["unified_statistics"]["total_load_attempts"] += 1

        try:
            # 檢查多個可能的文件路徑
            possible_paths = [
                Path("/satellite-processing/data/outputs/stage3/signal_analysis_output.json"),
                Path("data/stage3_outputs/timeseries_preprocessing_output.json"),
                Path("/app/data/stage3_signal_analysis_output.json"),
                self.stage3_input_dir / "signal_analysis_output.json",
                self.stage3_input_dir / "timeseries_preprocessing_output.json"
            ]

            stage3_data = None

            for file_path in possible_paths:
                if file_path.exists():
                    self.logger.info(f"   找到Stage 3文件: {file_path}")

                    with open(file_path, 'r', encoding='utf-8') as f:
                        stage3_data = json.load(f)
                    break

            if not stage3_data:
                raise FileNotFoundError("未找到Stage 3輸出文件")

            # 驗證數據格式
            validation_result = self.validate_timeseries_data_format(stage3_data)

            if not validation_result["format_valid"]:
                raise ValueError(f"Stage 3數據格式無效: {validation_result.get('validation_errors', [])}")

            # 更新載入統計
            self._update_stage3_load_statistics(stage3_data)

            self.load_statistics["unified_statistics"]["successful_loads"] += 1
            self.logger.info("✅ Stage 3數據載入完成")

            return stage3_data

        except Exception as e:
            self.logger.error(f"❌ Stage 3數據載入失敗: {e}")
            self.load_statistics["stage3_data"]["load_errors"] = self.load_statistics["stage3_data"].get("load_errors", 0) + 1
            self.load_statistics["unified_statistics"]["failed_loads"] += 1
            raise

    def _validate_and_normalize_stage2_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證和標準化Stage 2數據 (整合自 visibility_data_loader.py)"""

        validated_data = {
            "metadata": data.get("metadata", {}),
            "satellites": [],
            "validation_info": {
                "validated_at": datetime.now(timezone.utc).isoformat(),
                "validator": "UnifiedDataLoader",
                "stage": "stage2_visibility_filter"
            }
        }

        # 處理衛星數據
        satellites_data = data.get("satellites", data.get("filtered_satellites", []))

        if not satellites_data:
            self.logger.warning("⚠️ Stage 2數據中未找到衛星數據")
            return validated_data

        constellation_count = {}

        for sat_data in satellites_data:
            try:
                # 標準化衛星數據
                normalized_satellite = self._normalize_satellite_visibility_data(sat_data)
                validated_data["satellites"].append(normalized_satellite)

                # 統計星座信息
                constellation = normalized_satellite.get("constellation", "unknown")
                constellation_count[constellation] = constellation_count.get(constellation, 0) + 1

            except Exception as e:
                self.logger.warning(f"⚠️ 跳過無效的衛星數據: {e}")
                continue

        # 更新統計信息
        self.load_statistics["stage2_data"]["satellites_loaded"] = len(validated_data["satellites"])
        self.load_statistics["stage2_data"]["constellations_found"] = len(constellation_count)

        # 計算可見性窗口總數
        total_visibility_windows = 0
        for satellite in validated_data["satellites"]:
            timeseries = satellite.get("timeseries", [])
            visible_points = [p for p in timeseries if p.get("is_visible", False)]
            total_visibility_windows += len(visible_points)

        self.load_statistics["stage2_data"]["visibility_windows_total"] = total_visibility_windows

        self.logger.info(f"   已載入 {len(validated_data['satellites'])} 顆衛星")
        self.logger.info(f"   涵蓋 {len(constellation_count)} 個星座")

        return validated_data

    def _normalize_satellite_visibility_data(self, sat_data: Dict[str, Any]) -> Dict[str, Any]:
        """標準化單個衛星的可見性數據 (整合自 visibility_data_loader.py)"""

        normalized = {
            "name": sat_data.get("name", sat_data.get("satellite_id", "unknown")),
            "satellite_id": sat_data.get("satellite_id", sat_data.get("name", "unknown")),
            "constellation": sat_data.get("constellation", "unknown"),
            "timeseries": [],
            "stage2_metadata": sat_data.get("stage2_processing", {})
        }

        # 處理時間序列數據
        position_data = sat_data.get("position_timeseries", sat_data.get("timeseries", []))

        if position_data:
            enhanced_timeseries = self._enhance_position_timeseries(position_data)
            normalized["timeseries"] = enhanced_timeseries

        return normalized

    def _enhance_position_timeseries(self, position_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """增強位置時間序列數據 (整合自 visibility_data_loader.py)"""

        enhanced_timeseries = []

        for point in position_data:
            enhanced_point = {
                "time_offset_seconds": point.get("time_offset_seconds", 0),
                "latitude": point.get("latitude", 0.0),
                "longitude": point.get("longitude", 0.0),
                "altitude_km": point.get("altitude_km", 0.0),
                "is_visible": point.get("is_visible", False)
            }

            # 添加可見性相關數據（如果可見）
            if enhanced_point["is_visible"]:
                enhanced_point.update({
                    "elevation_deg": point.get("elevation_deg", INVALID_ELEVATION),
                    "azimuth_deg": point.get("azimuth_deg", 0.0),
                    "range_km": point.get("range_km", 0.0)
                })

            enhanced_timeseries.append(enhanced_point)

        return enhanced_timeseries

    def validate_timeseries_data_format(self, stage3_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證時間序列數據格式 (整合自 timeseries_data_loader.py)"""

        validation_result = {
            "format_valid": True,
            "validation_errors": [],
            "data_summary": {},
            "validation_timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            # 基本結構檢查
            required_fields = ["metadata", "signal_quality_data"]
            for field in required_fields:
                if field not in stage3_data:
                    validation_result["validation_errors"].append(f"缺少必要欄位: {field}")
                    validation_result["format_valid"] = False

            # 檢查衛星數據
            signal_data = stage3_data.get("signal_quality_data", [])

            if not isinstance(signal_data, list):
                validation_result["validation_errors"].append("signal_quality_data 必須是列表格式")
                validation_result["format_valid"] = False

            if len(signal_data) == 0:
                validation_result["validation_errors"].append("signal_quality_data 不能為空")
                validation_result["format_valid"] = False

            # 驗證衛星數據結構
            valid_satellites = 0
            for i, satellite in enumerate(signal_data[:5]):  # 檢查前5個衛星
                validation_issues = self._validate_satellite_timeseries(satellite, i)
                if validation_issues:
                    validation_result["validation_errors"].extend(validation_issues)
                else:
                    valid_satellites += 1

            # 數據摘要
            validation_result["data_summary"] = {
                "total_satellites": len(signal_data),
                "sample_validated": min(5, len(signal_data)),
                "valid_satellites_in_sample": valid_satellites,
                "data_quality_estimate": (valid_satellites / min(5, len(signal_data))) * 100 if signal_data else 0
            }

        except Exception as e:
            validation_result["validation_errors"].append(f"驗證過程異常: {str(e)}")
            validation_result["format_valid"] = False

        return validation_result

    def _validate_satellite_timeseries(self, satellite: Dict[str, Any], index: int) -> List[str]:
        """驗證單個衛星的時間序列數據 (整合自 timeseries_data_loader.py)"""

        errors = []

        # 檢查基本字段
        required_fields = ["satellite_id", "constellation"]
        for field in required_fields:
            if field not in satellite:
                errors.append(f"衛星 {index}: 缺少 {field}")

        # 檢查時間序列數據
        if "position_timeseries_with_signal" not in satellite:
            errors.append(f"衛星 {index}: 缺少 position_timeseries_with_signal")

        return errors

    def _update_stage3_load_statistics(self, stage3_data: Dict[str, Any]) -> None:
        """更新Stage 3載入統計 (整合自 timeseries_data_loader.py)"""

        signal_data = stage3_data.get("signal_quality_data", [])

        self.load_statistics["stage3_data"]["total_satellites_loaded"] = len(signal_data)

        # 計算總時間序列點數
        total_points = 0
        constellations = set()

        for satellite in signal_data:
            constellation = satellite.get("constellation")
            if constellation:
                constellations.add(constellation)

            timeseries = satellite.get("position_timeseries_with_signal", [])
            total_points += len(timeseries)

        self.load_statistics["stage3_data"]["total_timeseries_points"] = total_points
        self.load_statistics["stage3_data"]["constellations_loaded"] = len(constellations)

        # 計算數據質量分數
        if len(signal_data) > 0:
            avg_points_per_satellite = total_points / len(signal_data)
            quality_score = min(100, (avg_points_per_satellite / 96) * 100)  # 96點為一個軌道週期
            self.load_statistics["stage3_data"]["data_quality_score"] = round(quality_score, 2)

    def extract_signal_analysis_data(self, stage3_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取信號分析數據 (整合自 timeseries_data_loader.py)"""

        self.logger.info("🔄 提取Stage 3信號分析數據...")

        extracted_data = {
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_stage": "stage3_signal_analysis",
            "satellites": [],
            "extraction_summary": {}
        }

        # 從Stage 3數據中提取關鍵信息
        data_section = stage3_data.get("data", {})
        signal_data = stage3_data.get("signal_quality_data", [])

        for satellite in signal_data:
            satellite_analysis = {
                "satellite_id": satellite.get("satellite_id"),
                "constellation": satellite.get("constellation"),
                "position_timeseries": self._extract_position_timeseries(satellite),
                "visibility_windows": self._extract_visibility_windows(satellite),
                "signal_analysis": satellite
            }

            extracted_data["satellites"].append(satellite_analysis)

        # 提取摘要信息
        extracted_data["extraction_summary"] = {
            "satellites_extracted": len(extracted_data["satellites"]),
            "source_metadata": stage3_data.get("metadata", {}),
            "extraction_quality": "high" if len(extracted_data["satellites"]) > 0 else "low"
        }

        self.logger.info(f"✅ 已提取 {len(extracted_data['satellites'])} 顆衛星的信號分析數據")

        return extracted_data

    def _extract_position_timeseries(self, satellite: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取位置時間序列 (整合自 timeseries_data_loader.py)"""

        timeseries = satellite.get("position_timeseries_with_signal", [])
        return [
            {
                "time_offset_seconds": point.get("time_offset_seconds", 0),
                "latitude": point.get("latitude", 0.0),
                "longitude": point.get("longitude", 0.0),
                "altitude_km": point.get("altitude_km", 0.0),
                "is_visible": point.get("is_visible", False)
            }
            for point in timeseries
        ]

    def _extract_visibility_windows(self, satellite: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取可見性窗口 (整合自 timeseries_data_loader.py)"""

        timeseries = satellite.get("position_timeseries_with_signal", [])
        visibility_windows = []

        current_window = None

        for point in timeseries:
            if point.get("is_visible", False):
                if current_window is None:
                    # 開始新的可見性窗口
                    current_window = {
                        "start_time": point.get("time_offset_seconds", 0),
                        "max_elevation": point.get("elevation_deg", 0.0),
                        "max_elevation_time": point.get("time_offset_seconds", 0),
                        "visibility_points": []
                    }

                # 添加點到當前窗口
                current_window["visibility_points"].append({
                    "time": point.get("time_offset_seconds", 0),
                    "elevation": point.get("elevation_deg", 0.0),
                    "azimuth": point.get("azimuth_deg", 0.0),
                    "range_km": point.get("range_km", 0.0)
                })

                # 更新最大仰角
                elevation = point.get("elevation_deg", 0.0)
                if elevation > current_window["max_elevation"]:
                    current_window["max_elevation"] = elevation
                    current_window["max_elevation_time"] = point.get("time_offset_seconds", 0)

            else:
                # 結束當前可見性窗口
                if current_window is not None:
                    current_window["end_time"] = current_window["visibility_points"][-1]["time"] if current_window["visibility_points"] else current_window["start_time"]
                    current_window["duration_seconds"] = current_window["end_time"] - current_window["start_time"]
                    visibility_windows.append(current_window)
                    current_window = None

        # 處理最後一個窗口
        if current_window is not None:
            current_window["end_time"] = current_window["visibility_points"][-1]["time"] if current_window["visibility_points"] else current_window["start_time"]
            current_window["duration_seconds"] = current_window["end_time"] - current_window["start_time"]
            visibility_windows.append(current_window)

        return visibility_windows

    def get_load_statistics(self) -> Dict[str, Any]:
        """獲取統一載入統計"""

        # 計算統一的數據整合分數
        total_attempts = self.load_statistics["unified_statistics"]["total_load_attempts"]
        successful_loads = self.load_statistics["unified_statistics"]["successful_loads"]

        if total_attempts > 0:
            integration_score = (successful_loads / total_attempts) * 100
            self.load_statistics["unified_statistics"]["data_integration_score"] = round(integration_score, 2)

        return self.load_statistics.copy()

    def get_satellites_by_constellation(self, data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """按星座分組衛星數據 (整合自 visibility_data_loader.py)"""

        satellites = data.get("satellites", [])
        constellation_groups = {}

        for satellite in satellites:
            constellation = satellite.get("constellation", "unknown")
            if constellation not in constellation_groups:
                constellation_groups[constellation] = []
            constellation_groups[constellation].append(satellite)

        return constellation_groups

    def get_visibility_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """獲取可見性統計信息 (整合自 visibility_data_loader.py)"""

        satellites = data.get("satellites", [])

        statistics = {
            "total_satellites": len(satellites),
            "constellations": {},
            "visibility_summary": {
                "total_visibility_windows": 0,
                "average_window_duration": 0.0,
                "max_elevation_overall": 0.0,
                "satellites_with_visibility": 0
            }
        }

        total_duration = 0.0
        window_count = 0
        max_elevation = 0.0
        satellites_with_visibility = 0

        for satellite in satellites:
            constellation = satellite.get("constellation", "unknown")
            if constellation not in statistics["constellations"]:
                statistics["constellations"][constellation] = {
                    "satellite_count": 0,
                    "visibility_windows": 0,
                    "max_elevation": 0.0
                }

            statistics["constellations"][constellation]["satellite_count"] += 1

            # 分析可見性數據
            timeseries = satellite.get("timeseries", [])
            visible_points = [p for p in timeseries if p.get("is_visible", False)]

            if visible_points:
                satellites_with_visibility += 1

                # 計算可見性窗口
                windows = self._extract_visibility_windows({"position_timeseries_with_signal": timeseries})
                window_count += len(windows)
                statistics["constellations"][constellation]["visibility_windows"] += len(windows)

                for window in windows:
                    total_duration += window.get("duration_seconds", 0)
                    elevation = window.get("max_elevation", 0.0)
                    max_elevation = max(max_elevation, elevation)
                    statistics["constellations"][constellation]["max_elevation"] = max(
                        statistics["constellations"][constellation]["max_elevation"], elevation
                    )

        # 計算總體統計
        statistics["visibility_summary"]["total_visibility_windows"] = window_count
        statistics["visibility_summary"]["satellites_with_visibility"] = satellites_with_visibility
        statistics["visibility_summary"]["max_elevation_overall"] = max_elevation

        if window_count > 0:
            statistics["visibility_summary"]["average_window_duration"] = round(total_duration / window_count, 2)

        return statistics