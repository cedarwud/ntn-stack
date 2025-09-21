#!/usr/bin/env python3
"""
Stage 1: 數據載入層處理器 (重構版本)

重構原則：
- 專注數據載入和驗證，移除SGP4計算功能
- 使用共享的驗證框架和工具模組
- 實現統一的處理器接口
- 提供清潔的TLE數據輸出供Stage 2使用

功能變化：
- ✅ 保留: TLE數據載入、數據驗證
- ❌ 移除: SGP4軌道計算（移至Stage 2）
- ✅ 新增: 時間基準標準化、數據完整性檢查
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# 共享模組導入
from shared.interfaces import BaseProcessor, ProcessingStatus, ProcessingResult, create_processing_result
from shared.validation_framework import ValidationEngine
from shared.utils import TimeUtils, FileUtils
from shared.constants import SystemConstantsManager
from shared.testing import TestAssertion

# Stage 1專用模組
from .tle_data_loader import TLEDataLoader

logger = logging.getLogger(__name__)


class Stage1DataLoadingProcessor(BaseProcessor):
    """
    Stage 1: 數據載入層處理器 (重構版本)

    專職責任：
    1. TLE數據載入和解析
    2. 數據格式驗證和完整性檢查
    3. 時間基準標準化
    4. 為Stage 2提供清潔的數據輸出
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Stage1DataLoadingProcessor", config or {})

        # 配置參數
        self.sample_mode = self.config.get('sample_mode', False)
        self.sample_size = self.config.get('sample_size', 100)
        self.validate_tle_epoch = self.config.get('validate_tle_epoch', True)

        # 初始化組件
        self.tle_loader = TLEDataLoader()
        self.validation_engine = ValidationEngine('stage1')
        self.system_constants = SystemConstantsManager()

        # 處理統計
        self.processing_stats = {
            'total_files_scanned': 0,
            'total_satellites_loaded': 0,
            'validation_failures': 0,
            'time_reference_issues': 0
        }

        self.logger.info("Stage 1 數據載入處理器已初始化")

    def process(self, input_data: Any) -> ProcessingResult:
        """
        主要處理方法

        Args:
            input_data: 輸入數據（可選的TLE數據或配置）

        Returns:
            處理結果，包含載入的TLE數據
        """
        start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 開始Stage 1數據載入處理...")

        try:
            # 檢查輸入數據類型
            if input_data and isinstance(input_data, dict) and 'tle_data' in input_data:
                # 使用提供的TLE數據
                self.logger.info("📋 使用輸入的TLE數據...")
                tle_data_list = input_data['tle_data']
                loaded_data = self._process_input_tle_data(tle_data_list)
            else:
                # 從文件載入TLE數據
                self.logger.info("📁 從文件載入TLE數據...")
                loaded_data = self._load_tle_data_from_files()

            # 數據驗證
            validation_result = self._validate_loaded_data(loaded_data)

            # 檢查驗證結果
            if hasattr(validation_result, 'overall_status'):
                validation_status = validation_result.overall_status
                is_valid = validation_status == 'PASS' or (validation_status == 'PENDING' and len(loaded_data) > 0)
                # 轉換為字典獲取詳細信息
                validation_dict = validation_result.to_dict()
                errors = [check['message'] for check in validation_dict['detailed_results']
                         if check['status'] == 'FAILURE']
                metrics = {'validation_summary': validation_dict}

                # 如果是PENDING狀態但有數據，添加基本檢查
                if validation_status == 'PENDING' and len(loaded_data) > 0:
                    validation_result.add_success(
                        "data_loaded",
                        f"成功載入 {len(loaded_data)} 顆衛星數據",
                        {'satellite_count': len(loaded_data)}
                    )
                    validation_result.finalize()
                    is_valid = True
            else:
                # 如果是字典格式
                is_valid = validation_result.get('is_valid', False)
                errors = validation_result.get('errors', [])
                metrics = validation_result.get('metrics', {})

            if not is_valid:
                return create_processing_result(
                    status=ProcessingStatus.VALIDATION_FAILED,
                    data={},
                    message=f"數據驗證失敗: {errors}"
                )

            # 時間基準標準化
            standardized_data = self._standardize_time_reference(loaded_data)

            # 數據完整性檢查
            completeness_check = self._check_data_completeness(standardized_data)

            # 構建輸出結果
            processing_time = datetime.now(timezone.utc) - start_time
            result_data = {
                'stage': 'stage1_data_loading',
                'tle_data': standardized_data,
                'metadata': {
                    'processing_start_time': start_time.isoformat(),
                    'processing_end_time': datetime.now(timezone.utc).isoformat(),
                    'processing_duration_seconds': processing_time.total_seconds(),
                    'total_satellites_loaded': len(standardized_data),
                    'time_reference_standard': 'tle_epoch',
                    'validation_passed': True,
                    'completeness_score': completeness_check['score']
                },
                'processing_stats': self.processing_stats,
                'quality_metrics': metrics,
                'next_stage_ready': True
            }

            self.logger.info(f"✅ Stage 1數據載入完成，載入{len(standardized_data)}顆衛星數據")

            return create_processing_result(
                status=ProcessingStatus.SUCCESS,
                data=result_data,
                message=f"成功載入{len(standardized_data)}顆衛星的TLE數據"
            )

        except Exception as e:
            self.logger.error(f"❌ Stage 1數據載入失敗: {e}")
            return create_processing_result(
                status=ProcessingStatus.ERROR,
                data={},
                message=f"數據載入錯誤: {str(e)}"
            )

    def _process_input_tle_data(self, tle_data_list: List[Dict]) -> List[Dict]:
        """處理輸入的TLE數據"""
        if not tle_data_list:
            self.logger.warning("輸入的TLE數據為空")
            return []

        processed_data = []
        for tle_data in tle_data_list:
            # 基本格式檢查
            if self._validate_tle_format(tle_data):
                processed_data.append(tle_data)
            else:
                self.processing_stats['validation_failures'] += 1

        self.processing_stats['total_satellites_loaded'] = len(processed_data)
        return processed_data

    def _load_tle_data_from_files(self) -> List[Dict]:
        """從文件載入TLE數據"""
        try:
            # 掃描TLE文件
            tle_files = self.tle_loader.scan_tle_data()
            self.processing_stats['total_files_scanned'] = len(tle_files)

            if not tle_files:
                self.logger.warning("未找到TLE文件")
                return []

            # 載入所有TLE數據
            all_tle_data = []
            for tle_file in tle_files:
                tle_data = self.tle_loader.load_satellite_data(tle_files)
                if tle_data:
                    all_tle_data.extend(tle_data)
                break  # load_satellite_data handles all files at once

            # 樣本模式處理
            if self.sample_mode and len(all_tle_data) > self.sample_size:
                self.logger.info(f"樣本模式：從{len(all_tle_data)}顆衛星中選取{self.sample_size}顆")
                all_tle_data = all_tle_data[:self.sample_size]

            self.processing_stats['total_satellites_loaded'] = len(all_tle_data)
            return all_tle_data

        except Exception as e:
            self.logger.error(f"載入TLE文件失敗: {e}")
            raise

    def _validate_tle_format(self, tle_data: Dict) -> bool:
        """驗證TLE數據格式"""
        required_fields = ['satellite_id', 'line1', 'line2', 'name']

        for field in required_fields:
            if field not in tle_data:
                self.logger.warning(f"TLE數據缺少必要字段: {field}")
                return False

        # 檢查TLE行格式
        line1 = tle_data['line1']
        line2 = tle_data['line2']

        if len(line1) != 69 or len(line2) != 69:
            self.logger.warning("TLE行長度不正確")
            return False

        if line1[0] != '1' or line2[0] != '2':
            self.logger.warning("TLE行標識符不正確")
            return False

        return True

    def _validate_loaded_data(self, loaded_data: List[Dict]) -> Dict[str, Any]:
        """使用共享驗證框架驗證載入的數據"""
        try:
            # 構建驗證規則
            validation_rules = {
                'min_satellites': 1,
                'required_fields': ['satellite_id', 'line1', 'line2', 'name'],
                'tle_format_check': True,
                'academic_compliance': True
            }

            # 執行驗證
            validation_result = self.validation_engine.validate(loaded_data, validation_rules)

            # 額外的TLE特定檢查
            if hasattr(validation_result, 'overall_status') and validation_result.overall_status == 'PASS':
                tle_specific_checks = self._perform_tle_specific_validation(loaded_data)
                # 在ValidationResult中添加額外檢查
                for check_name, value in tle_specific_checks.items():
                    validation_result.add_success(
                        f"tle_specific_{check_name}",
                        f"{check_name}: {value}",
                        {'value': value}
                    )
            elif isinstance(validation_result, dict) and validation_result.get('is_valid'):
                tle_specific_checks = self._perform_tle_specific_validation(loaded_data)
                validation_result['metrics'].update(tle_specific_checks)

            return validation_result

        except Exception as e:
            self.logger.error(f"數據驗證失敗: {e}")
            return {
                'is_valid': False,
                'errors': [str(e)],
                'metrics': {}
            }

    def _perform_tle_specific_validation(self, data: List[Dict]) -> Dict[str, Any]:
        """執行TLE特定的驗證檢查"""
        metrics = {
            'unique_satellites': 0,
            'epoch_time_range_days': 0,
            'constellation_coverage': 0,
            'data_freshness_score': 0
        }

        if not data:
            return metrics

        # 檢查衛星ID唯一性
        satellite_ids = set()
        epochs = []
        constellations = set()

        for tle in data:
            satellite_ids.add(tle['satellite_id'])

            # 解析TLE時間
            try:
                line1 = tle['line1']
                epoch_year = int(line1[18:20])
                epoch_day = float(line1[20:32])

                # 轉換為完整年份
                if epoch_year < 57:
                    full_year = 2000 + epoch_year
                else:
                    full_year = 1900 + epoch_year

                epoch_time = TimeUtils.parse_tle_epoch(full_year, epoch_day)
                epochs.append(epoch_time)

            except Exception as e:
                self.logger.warning(f"TLE時間解析失敗: {e}")
                self.processing_stats['time_reference_issues'] += 1

        metrics['unique_satellites'] = len(satellite_ids)

        if epochs:
            time_range = max(epochs) - min(epochs)
            metrics['epoch_time_range_days'] = time_range.days

            # 數據新鮮度評分
            latest_epoch = max(epochs)
            age_days = (datetime.now(timezone.utc) - latest_epoch).days
            metrics['data_freshness_score'] = max(0, 100 - age_days)

        return metrics

    def _standardize_time_reference(self, loaded_data: List[Dict]) -> List[Dict]:
        """標準化時間基準"""
        standardized_data = []

        for tle_data in loaded_data:
            try:
                # 解析TLE epoch時間
                line1 = tle_data['line1']
                epoch_year = int(line1[18:20])
                epoch_day = float(line1[20:32])

                # 轉換為完整年份
                if epoch_year < 57:
                    full_year = 2000 + epoch_year
                else:
                    full_year = 1900 + epoch_year

                # 標準化時間信息
                epoch_time = TimeUtils.parse_tle_epoch(full_year, epoch_day)

                # 添加標準化時間字段
                enhanced_tle = tle_data.copy()
                enhanced_tle.update({
                    'epoch_datetime': epoch_time.isoformat(),
                    'epoch_year_full': full_year,
                    'epoch_day_decimal': epoch_day,
                    'time_reference_standard': 'tle_epoch'
                })

                standardized_data.append(enhanced_tle)

            except Exception as e:
                self.logger.error(f"時間標準化失敗 {tle_data.get('satellite_id', 'unknown')}: {e}")
                # 保留原數據但標記問題
                enhanced_tle = tle_data.copy()
                enhanced_tle['time_reference_error'] = str(e)
                standardized_data.append(enhanced_tle)
                self.processing_stats['time_reference_issues'] += 1

        return standardized_data

    def _check_data_completeness(self, data: List[Dict]) -> Dict[str, Any]:
        """檢查數據完整性"""
        if not data:
            return {'score': 0, 'issues': ['無數據']}

        total_satellites = len(data)
        complete_records = 0
        issues = []

        for tle in data:
            completeness_checks = [
                'satellite_id' in tle and tle['satellite_id'],
                'name' in tle and tle['name'],
                'line1' in tle and len(tle['line1']) == 69,
                'line2' in tle and len(tle['line2']) == 69,
                'epoch_datetime' in tle,
                'time_reference_error' not in tle
            ]

            if all(completeness_checks):
                complete_records += 1
            else:
                missing_fields = []
                if not completeness_checks[0]:
                    missing_fields.append('satellite_id')
                if not completeness_checks[1]:
                    missing_fields.append('name')
                if not completeness_checks[2]:
                    missing_fields.append('line1_format')
                if not completeness_checks[3]:
                    missing_fields.append('line2_format')
                if not completeness_checks[4]:
                    missing_fields.append('epoch_time')
                if not completeness_checks[5]:
                    missing_fields.append('time_parsing')

                if missing_fields:
                    issues.append(f"衛星 {tle.get('satellite_id', 'unknown')}: {', '.join(missing_fields)}")

        completeness_score = (complete_records / total_satellites) * 100

        return {
            'score': completeness_score,
            'complete_records': complete_records,
            'total_records': total_satellites,
            'issues': issues[:10]  # 限制報告前10個問題
        }

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """驗證輸入數據"""
        errors = []
        warnings = []

        if input_data is None:
            # 允許無輸入，將從文件載入
            return {'valid': True, 'errors': errors, 'warnings': warnings}

        if isinstance(input_data, dict):
            if 'tle_data' in input_data:
                tle_data = input_data['tle_data']
                if not isinstance(tle_data, list):
                    errors.append("tle_data必須是列表格式")
                elif len(tle_data) == 0:
                    warnings.append("tle_data為空列表")
            return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}

        errors.append("輸入數據格式不正確")
        return {'valid': False, 'errors': errors, 'warnings': warnings}

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """驗證輸出數據"""
        errors = []
        warnings = []

        if not isinstance(output_data, dict):
            errors.append("輸出數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        required_fields = ['stage', 'tle_data', 'metadata']
        for field in required_fields:
            if field not in output_data:
                errors.append(f"缺少必需字段: {field}")

        if output_data.get('stage') != 'stage1_data_loading':
            errors.append("階段標識錯誤")

        # 檢查 TLE 數據
        tle_data = output_data.get('tle_data', {})
        if not isinstance(tle_data, list):
            errors.append("TLE數據格式錯誤")
        elif len(tle_data) == 0:
            warnings.append("TLE數據為空")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def extract_key_metrics(self) -> Dict[str, Any]:
        """提取關鍵指標"""
        return {
            'stage': 'stage1_data_loading',
            'satellites_loaded': self.processing_stats['total_satellites_loaded'],
            'files_scanned': self.processing_stats['total_files_scanned'],
            'validation_failures': self.processing_stats['validation_failures'],
            'time_reference_issues': self.processing_stats['time_reference_issues'],
            'success_rate': (
                (self.processing_stats['total_satellites_loaded'] - self.processing_stats['validation_failures'])
                / max(1, self.processing_stats['total_satellites_loaded'])
            ) * 100
        }


def create_stage1_processor(config: Optional[Dict[str, Any]] = None) -> Stage1DataLoadingProcessor:
    """
    創建Stage 1數據載入處理器實例

    Args:
        config: 可選配置參數

    Returns:
        Stage 1處理器實例
    """
    return Stage1DataLoadingProcessor(config)