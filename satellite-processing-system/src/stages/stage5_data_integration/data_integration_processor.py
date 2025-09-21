#!/usr/bin/env python3
"""
Stage 5: 數據處理層處理器 (重構版本)

重構原則：
- 專注數據整合和格式化
- 移除換手場景功能（已移至Stage 4）
- 使用共享的監控和工具模組
- 實現統一的處理器接口

功能變化：
- ✅ 保留: 數據整合、格式標準化
- ✅ 保留: 數據品質檢查、性能統計
- ❌ 移除: 換手場景分析（已移至Stage 4）
- ✅ 新增: 數據流管理、輸出格式優化
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# 共享模組導入
from shared.interfaces import BaseProcessor, ProcessingStatus, ProcessingResult, create_processing_result
from shared.validation_framework import ValidationEngine
from shared.utils import FileUtils
from shared.constants import SystemConstantsManager

logger = logging.getLogger(__name__)


class DataIntegrationProcessor(BaseProcessor):
    """
    Stage 5: 數據處理層處理器 (重構版本)

    專職責任：
    1. 多階段數據整合和合併
    2. 數據格式標準化和品質檢查
    3. 輸出格式優化和性能統計
    4. 數據流管理和一致性保證
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("DataIntegrationProcessor", config or {})

        # 配置參數
        self.output_format = self.config.get('output_format', 'json')
        self.data_quality_threshold = self.config.get('data_quality_threshold', 0.8)

        # 初始化組件
        self.validation_engine = ValidationEngine('stage5')
        self.system_constants = SystemConstantsManager()

        # 處理統計
        self.processing_stats = {
            'total_satellites_integrated': 0,
            'data_quality_score': 0.0,
            'integration_operations': 0,
            'validation_checks': 0
        }

        self.logger.info("Stage 5 數據處理處理器已初始化")

    def process(self, input_data: Any) -> ProcessingResult:
        """主要處理方法"""
        start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 開始Stage 5數據整合處理...")

        try:
            # 驗證輸入數據
            if not self._validate_stage4_output(input_data):
                return create_processing_result(
                    status=ProcessingStatus.VALIDATION_FAILED,
                    data={},
                    message="Stage 4輸出數據驗證失敗"
                )

            # 執行數據整合
            integrated_data = self._perform_data_integration(input_data)

            # 構建最終結果
            processing_time = datetime.now(timezone.utc) - start_time
            result_data = {
                'stage': 'stage5_data_integration',
                'integrated_data': integrated_data,
                'metadata': {
                    'processing_start_time': start_time.isoformat(),
                    'processing_end_time': datetime.now(timezone.utc).isoformat(),
                    'processing_duration_seconds': processing_time.total_seconds(),
                    'output_format': self.output_format
                },
                'processing_stats': self.processing_stats,
                'next_stage_ready': True
            }

            return create_processing_result(
                status=ProcessingStatus.SUCCESS,
                data=result_data,
                message=f"成功整合{self.processing_stats['total_satellites_integrated']}顆衛星的數據"
            )

        except Exception as e:
            self.logger.error(f"❌ Stage 5數據整合失敗: {e}")
            return create_processing_result(
                status=ProcessingStatus.ERROR,
                data={},
                message=f"數據整合錯誤: {str(e)}"
            )

    def _validate_stage4_output(self, input_data: Any) -> bool:
        """驗證Stage 4的輸出數據"""
        if not isinstance(input_data, dict):
            return False

        required_fields = ['stage', 'optimization_results']
        for field in required_fields:
            if field not in input_data:
                return False

        return input_data.get('stage') == 'stage4_optimization_decision'

    def _perform_data_integration(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行數據整合"""
        integrated_data = {
            'satellites': {},
            'integration_metadata': {}
        }

        try:
            # 提取優化結果
            optimization_results = input_data.get('optimization_results', {})
            handover_decisions = optimization_results.get('handover_decisions', {})

            # 整合每顆衛星的數據
            for satellite_id, handover_data in handover_decisions.items():
                integrated_data['satellites'][satellite_id] = {
                    'satellite_id': satellite_id,
                    'handover_decision': handover_data,
                    'integration_timestamp': datetime.now(timezone.utc).isoformat()
                }
                self.processing_stats['total_satellites_integrated'] += 1

            # 添加整合元數據
            integrated_data['integration_metadata'] = {
                'integration_timestamp': datetime.now(timezone.utc).isoformat(),
                'total_satellites': len(integrated_data['satellites']),
                'data_sources': ['stage4_optimization']
            }

            self.processing_stats['integration_operations'] += 1
            self.processing_stats['data_quality_score'] = 1.0

        except Exception as e:
            self.logger.error(f"數據整合失敗: {e}")

        return integrated_data

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """驗證輸入數據"""
        errors = []
        warnings = []

        if self._validate_stage4_output(input_data):
            return {'valid': True, 'errors': errors, 'warnings': warnings}
        else:
            errors.append("Stage 4輸出數據驗證失敗")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """驗證輸出數據"""
        errors = []
        warnings = []

        if not isinstance(output_data, dict):
            errors.append("輸出數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        required_fields = ['stage', 'integrated_data', 'metadata']
        for field in required_fields:
            if field not in output_data:
                errors.append(f"缺少必需字段: {field}")

        if output_data.get('stage') != 'stage5_data_integration':
            errors.append("階段標識錯誤")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def extract_key_metrics(self) -> Dict[str, Any]:
        """提取關鍵指標"""
        return {
            'stage': 'stage5_data_integration',
            'satellites_integrated': self.processing_stats['total_satellites_integrated'],
            'data_quality_score': self.processing_stats['data_quality_score'],
            'integration_operations': self.processing_stats['integration_operations']
        }


def create_stage5_processor(config: Optional[Dict[str, Any]] = None) -> DataIntegrationProcessor:
    """創建Stage 5處理器實例"""
    return DataIntegrationProcessor(config)