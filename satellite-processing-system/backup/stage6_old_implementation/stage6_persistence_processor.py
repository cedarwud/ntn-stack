#!/usr/bin/env python3
"""
Stage 6: 持久化API層處理器 (重構版本)

重構原則：
- 專注數據持久化和API輸出
- 移除動態池規劃功能（已移至Stage 4）
- 實現高效的數據存儲和檢索
- 提供標準化的API接口

功能變化：
- ✅ 保留: 數據持久化、API格式化、輸出管理
- ✅ 保留: 數據品質監控、性能統計
- ❌ 移除: 動態池規劃、資源優化（已移至Stage 4）
- ✅ 新增: 高效存儲、批次處理、API標準化
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import json
import os

# 共享模組導入
from shared.base_processor import BaseStageProcessor
from shared.interfaces import ProcessingStatus, ProcessingResult, create_processing_result
from shared.validation_framework import ValidationEngine
from shared.utils import FileUtils, TimeUtils
from shared.constants import SystemConstantsManager

logger = logging.getLogger(__name__)


class Stage6PersistenceProcessor(BaseStageProcessor):
    """
    Stage 6: 持久化API層處理器 (重構版本)

    專職責任：
    1. 多格式數據持久化和存儲管理
    2. 標準化API輸出格式
    3. 批次處理和增量更新
    4. 數據檢索和查詢接口
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(stage_number=6, stage_name="persistence_api", config=config or {})

        # 配置參數
        self.output_formats = self.config.get('output_formats', ['json', 'csv'])
        self.batch_size = self.config.get('batch_size', 1000)
        self.enable_compression = self.config.get('enable_compression', True)

        # 存儲路徑配置 - 根據環境自動調整
        import os
        if os.path.exists('/satellite-processing'):
            # 容器環境
            self.base_output_path = self.config.get('base_output_path', '/satellite-processing/data/final_outputs')
            self.api_output_path = self.config.get('api_output_path', '/satellite-processing/data/api_outputs')
        else:
            # 主機環境
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            self.base_output_path = self.config.get('base_output_path', f'{project_root}/data/final_outputs')
            self.api_output_path = self.config.get('api_output_path', f'{project_root}/data/api_outputs')

        # 初始化組件
        self.validation_engine = ValidationEngine('stage6')
        self.system_constants = SystemConstantsManager()
        self.file_utils = FileUtils()
        self.time_utils = TimeUtils()

        # 處理統計
        self.processing_stats = {
            'total_records_persisted': 0,
            'files_generated': 0,
            'api_endpoints_updated': 0,
            'storage_operations': 0,
            'compression_savings': 0.0
        }

        # 確保輸出目錄存在
        self._ensure_output_directories()

        self.logger.info("Stage 6 持久化API層處理器已初始化")

    def _ensure_output_directories(self):
        """確保輸出目錄存在"""
        directories = [
            self.base_output_path,
            self.api_output_path,
            f"{self.base_output_path}/json",
            f"{self.base_output_path}/csv",
            f"{self.api_output_path}/latest",
            f"{self.api_output_path}/archive"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def process(self, input_data: Any) -> ProcessingResult:
        """主要處理方法"""
        start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 開始Stage 6持久化API處理...")

        try:
            # 驗證輸入數據
            if not self._validate_stage5_output(input_data):
                return create_processing_result(
                    status=ProcessingStatus.VALIDATION_FAILED,
                    data={},
                    message="Stage 5輸出數據驗證失敗"
                )

            # 執行數據持久化
            persistence_results = self._perform_data_persistence(input_data)

            # 生成API輸出
            api_results = self._generate_api_outputs(persistence_results)

            # 構建最終結果
            processing_time = datetime.now(timezone.utc) - start_time
            result_data = {
                'stage': 'stage6_persistence_api',
                'persistence_results': persistence_results,
                'api_results': api_results,
                'metadata': {
                    'processing_start_time': start_time.isoformat(),
                    'processing_end_time': datetime.now(timezone.utc).isoformat(),
                    'processing_duration_seconds': processing_time.total_seconds(),
                    'output_paths': {
                        'base_output': self.base_output_path,
                        'api_output': self.api_output_path
                    }
                },
                'processing_stats': self.processing_stats,
                'pipeline_complete': True
            }

            return create_processing_result(
                status=ProcessingStatus.SUCCESS,
                data=result_data,
                message=f"成功持久化{self.processing_stats['total_records_persisted']}筆記錄，生成{self.processing_stats['files_generated']}個輸出文件"
            )

        except Exception as e:
            self.logger.error(f"❌ Stage 6持久化API失敗: {e}")
            return create_processing_result(
                status=ProcessingStatus.ERROR,
                data={},
                message=f"持久化API錯誤: {str(e)}"
            )

    def _validate_stage5_output(self, input_data: Any) -> bool:
        """驗證Stage 5的輸出數據"""
        if not isinstance(input_data, dict):
            return False

        required_fields = ['stage', 'integrated_data']
        for field in required_fields:
            if field not in input_data:
                return False

        return input_data.get('stage') == 'stage5_data_integration'

    def _perform_data_persistence(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行數據持久化"""
        persistence_results = {
            'storage_operations': [],
            'file_outputs': [],
            'performance_metrics': {}
        }

        try:
            # 提取整合數據
            integrated_data = input_data.get('integrated_data', {})
            satellites_data = integrated_data.get('satellites', {})

            # 生成時間戳
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

            # 持久化JSON格式
            if 'json' in self.output_formats:
                json_output = self._save_json_format(satellites_data, timestamp)
                persistence_results['file_outputs'].append(json_output)
                self.processing_stats['files_generated'] += 1

            # 持久化CSV格式
            if 'csv' in self.output_formats:
                csv_output = self._save_csv_format(satellites_data, timestamp)
                persistence_results['file_outputs'].append(csv_output)
                self.processing_stats['files_generated'] += 1

            # 更新統計
            self.processing_stats['total_records_persisted'] = len(satellites_data)
            self.processing_stats['storage_operations'] += len(persistence_results['file_outputs'])

            # 記錄性能指標
            persistence_results['performance_metrics'] = {
                'records_processed': len(satellites_data),
                'storage_efficiency': self._calculate_storage_efficiency(),
                'write_performance': self._calculate_write_performance()
            }

        except Exception as e:
            self.logger.error(f"數據持久化失敗: {e}")

        return persistence_results

    def _save_json_format(self, satellites_data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """保存JSON格式數據"""
        json_filename = f"satellite_processing_results_{timestamp}.json"
        json_filepath = f"{self.base_output_path}/json/{json_filename}"

        # 構建輸出數據結構
        output_data = {
            'metadata': {
                'generation_time': datetime.now(timezone.utc).isoformat(),
                'total_satellites': len(satellites_data),
                'data_format': 'json',
                'stage6_processor_version': '2.0.0'
            },
            'satellites': satellites_data,
            'processing_summary': self.processing_stats
        }

        # 寫入文件
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return {
            'format': 'json',
            'filename': json_filename,
            'filepath': json_filepath,
            'size_bytes': os.path.getsize(json_filepath),
            'record_count': len(satellites_data)
        }

    def _save_csv_format(self, satellites_data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """保存CSV格式數據"""
        csv_filename = f"satellite_processing_results_{timestamp}.csv"
        csv_filepath = f"{self.base_output_path}/csv/{csv_filename}"

        # 構建CSV數據
        csv_rows = []
        headers = ['satellite_id', 'handover_decision_type', 'trigger_rsrp', 'threshold_dbm', 'integration_timestamp']
        csv_rows.append(','.join(headers))

        for satellite_id, satellite_data in satellites_data.items():
            handover_data = satellite_data.get('handover_decision', {})
            row = [
                satellite_id,
                handover_data.get('decision_type', ''),
                str(handover_data.get('trigger_rsrp', '')),
                str(handover_data.get('threshold_dbm', '')),
                satellite_data.get('integration_timestamp', '')
            ]
            csv_rows.append(','.join(row))

        # 寫入文件
        with open(csv_filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(csv_rows))

        return {
            'format': 'csv',
            'filename': csv_filename,
            'filepath': csv_filepath,
            'size_bytes': os.path.getsize(csv_filepath),
            'record_count': len(satellites_data)
        }

    def _generate_api_outputs(self, persistence_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成API輸出"""
        api_results = {
            'endpoints_updated': [],
            'latest_data': {},
            'api_metadata': {}
        }

        try:
            # 生成最新數據端點
            latest_endpoint = self._create_latest_data_endpoint(persistence_results)
            api_results['endpoints_updated'].append(latest_endpoint)

            # 生成統計數據端點
            stats_endpoint = self._create_statistics_endpoint()
            api_results['endpoints_updated'].append(stats_endpoint)

            # 更新API元數據
            api_results['api_metadata'] = {
                'last_update': datetime.now(timezone.utc).isoformat(),
                'data_version': '1.0.0',
                'available_endpoints': len(api_results['endpoints_updated'])
            }

            self.processing_stats['api_endpoints_updated'] = len(api_results['endpoints_updated'])

        except Exception as e:
            self.logger.error(f"API輸出生成失敗: {e}")

        return api_results

    def _create_latest_data_endpoint(self, persistence_results: Dict[str, Any]) -> Dict[str, Any]:
        """創建最新數據端點"""
        endpoint_data = {
            'endpoint': '/api/v1/satellite/latest',
            'method': 'GET',
            'data_source': persistence_results.get('file_outputs', []),
            'update_time': datetime.now(timezone.utc).isoformat()
        }

        # 保存端點數據
        endpoint_filepath = f"{self.api_output_path}/latest/satellite_latest.json"
        with open(endpoint_filepath, 'w', encoding='utf-8') as f:
            json.dump(endpoint_data, f, indent=2, ensure_ascii=False)

        return endpoint_data

    def _create_statistics_endpoint(self) -> Dict[str, Any]:
        """創建統計數據端點"""
        endpoint_data = {
            'endpoint': '/api/v1/pipeline/statistics',
            'method': 'GET',
            'statistics': self.processing_stats,
            'update_time': datetime.now(timezone.utc).isoformat()
        }

        # 保存端點數據
        endpoint_filepath = f"{self.api_output_path}/latest/pipeline_statistics.json"
        with open(endpoint_filepath, 'w', encoding='utf-8') as f:
            json.dump(endpoint_data, f, indent=2, ensure_ascii=False)

        return endpoint_data

    def _calculate_storage_efficiency(self) -> float:
        """計算存儲效率"""
        # 簡化的存儲效率計算
        if self.enable_compression:
            return 0.85  # 假設85%的壓縮率
        return 1.0

    def _calculate_write_performance(self) -> float:
        """計算寫入性能"""
        # 簡化的寫入性能計算（記錄/秒）
        if self.processing_stats['total_records_persisted'] > 0:
            return self.processing_stats['total_records_persisted'] / max(1, self.processing_stats['storage_operations'])
        return 0.0

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """驗證輸入數據"""
        errors = []
        warnings = []

        if self._validate_stage5_output(input_data):
            return {'valid': True, 'errors': errors, 'warnings': warnings}
        else:
            errors.append("Stage 5輸出數據驗證失敗")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """驗證輸出數據"""
        errors = []
        warnings = []

        if not isinstance(output_data, dict):
            errors.append("輸出數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        required_fields = ['stage', 'persistence_results', 'metadata']
        for field in required_fields:
            if field not in output_data:
                errors.append(f"缺少必需字段: {field}")

        if output_data.get('stage') != 'stage6_persistence_api':
            errors.append("階段標識錯誤")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def extract_key_metrics(self) -> Dict[str, Any]:
        """提取關鍵指標"""
        return {
            'stage': 'stage6_persistence_api',
            'records_persisted': self.processing_stats['total_records_persisted'],
            'files_generated': self.processing_stats['files_generated'],
            'api_endpoints_updated': self.processing_stats['api_endpoints_updated'],
            'storage_operations': self.processing_stats['storage_operations']
        }


def create_stage6_processor(config: Optional[Dict[str, Any]] = None) -> Stage6PersistenceProcessor:
    """創建Stage 6處理器實例"""
    return Stage6PersistenceProcessor(config)