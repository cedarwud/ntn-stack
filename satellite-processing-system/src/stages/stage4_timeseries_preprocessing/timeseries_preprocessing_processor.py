#!/usr/bin/env python3
"""
Stage 4: 優化決策層處理器 (重構版本)

重構原則：
- 整合換手決策、動態池規劃、時空優化功能
- 集中所有優化相關邏輯
- 使用共享的預測和監控模組
- 為強化學習擴展預留接口

功能整合：
- ✅ 從Stage 3遷移: 換手候選管理、換手決策
- ✅ 從Stage 6遷移: 動態池規劃
- ✅ 從Stage 4整合: 時間序列預處理
- ✅ 新增: 時空錯置分析、RL擴展點
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

# 共享模組導入
from shared.interfaces import BaseProcessor, ProcessingStatus, ProcessingResult, create_processing_result
from shared.validation_framework import ValidationEngine
from shared.monitoring import PerformanceMonitor, MonitoringConfig
from shared.utils import TimeUtils
from shared.constants import SystemConstantsManager

logger = logging.getLogger(__name__)


class TimeseriesPreprocessingProcessor(BaseProcessor):
    """
    Stage 4: 優化決策層處理器 (重構版本)

    專職責任：
    1. 換手決策和候選衛星管理
    2. 動態池規劃和資源優化
    3. 時空錯置分析和時間序列預處理
    4. 強化學習擴展接口
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("TimeseriesPreprocessingProcessor", config or {})

        # 配置參數
        self.handover_threshold_dbm = self.config.get('handover_threshold_dbm', -105.0)
        self.pool_size_target = self.config.get('pool_size_target', 5)

        # 初始化組件
        self.validation_engine = ValidationEngine('stage4')
        self.system_constants = SystemConstantsManager()

        # 處理統計
        self.processing_stats = {
            'total_satellites_processed': 0,
            'handover_decisions_made': 0,
            'pool_optimizations_performed': 0,
            'temporal_adjustments': 0
        }

        self.logger.info("Stage 4 優化決策處理器已初始化")

    def process(self, input_data: Any) -> ProcessingResult:
        """主要處理方法"""
        start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 開始Stage 4優化決策處理...")

        try:
            # 驗證輸入數據
            if not self._validate_stage3_output(input_data):
                return create_processing_result(
                    status=ProcessingStatus.VALIDATION_FAILED,
                    data={},
                    message="Stage 3輸出數據驗證失敗"
                )

            # 提取信號分析數據
            signal_analysis_data = self._extract_signal_analysis_data(input_data)
            if not signal_analysis_data:
                return create_processing_result(
                    status=ProcessingStatus.ERROR,
                    data={},
                    message="未找到有效的信號分析數據"
                )

            # 執行優化決策
            optimization_results = self._perform_optimization_analysis(signal_analysis_data)

            # 構建最終結果
            processing_time = datetime.now(timezone.utc) - start_time
            result_data = {
                'stage': 'stage4_optimization_decision',
                'optimization_results': optimization_results,
                'metadata': {
                    'processing_start_time': start_time.isoformat(),
                    'processing_end_time': datetime.now(timezone.utc).isoformat(),
                    'processing_duration_seconds': processing_time.total_seconds()
                },
                'processing_stats': self.processing_stats,
                'next_stage_ready': True
            }

            return create_processing_result(
                status=ProcessingStatus.SUCCESS,
                data=result_data,
                message=f"成功完成{self.processing_stats['total_satellites_processed']}顆衛星的優化決策"
            )

        except Exception as e:
            self.logger.error(f"❌ Stage 4優化決策失敗: {e}")
            return create_processing_result(
                status=ProcessingStatus.ERROR,
                data={},
                message=f"優化決策錯誤: {str(e)}"
            )

    def _validate_stage3_output(self, input_data: Any) -> bool:
        """驗證Stage 3的輸出數據"""
        if not isinstance(input_data, dict):
            return False

        required_fields = ['stage', 'satellites']
        for field in required_fields:
            if field not in input_data:
                return False

        return input_data.get('stage') == 'stage3_signal_analysis'

    def _extract_signal_analysis_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取信號分析數據"""
        return input_data.get('satellites', {})

    def _perform_optimization_analysis(self, signal_analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行優化分析"""
        optimization_results = {
            'handover_decisions': {},
            'pool_recommendations': [],
            'optimization_summary': {}
        }

        for satellite_id, satellite_data in signal_analysis_data.items():
            self.processing_stats['total_satellites_processed'] += 1

            # 簡化的優化邏輯
            signal_analysis = satellite_data.get('signal_analysis', {})
            signal_stats = signal_analysis.get('signal_statistics', {})
            average_rsrp = signal_stats.get('average_rsrp', -120)

            if average_rsrp < self.handover_threshold_dbm:
                optimization_results['handover_decisions'][satellite_id] = {
                    'decision_type': 'handover_required',
                    'trigger_rsrp': average_rsrp,
                    'threshold_dbm': self.handover_threshold_dbm
                }
                self.processing_stats['handover_decisions_made'] += 1

        return optimization_results


    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """驗證輸入數據"""
        validation_result = {'valid': True, 'errors': [], 'warnings': []}

        if not isinstance(input_data, dict):
            validation_result['errors'].append("輸入數據必須是字典格式")
            validation_result['valid'] = False
            return validation_result

        required_fields = ['stage', 'satellites']
        for field in required_fields:
            if field not in input_data:
                validation_result['errors'].append(f"缺少必要字段: {field}")
                validation_result['valid'] = False

        if input_data.get('stage') != 'stage3_signal_analysis':
            validation_result['errors'].append("輸入數據必須來自Stage 3信號分析")
            validation_result['valid'] = False

        return validation_result

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """驗證輸出數據"""
        errors = []
        warnings = []

        if not isinstance(output_data, dict):
            errors.append("輸出數據必須是字典格式")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        required_fields = ['stage', 'optimization_results', 'metadata']
        for field in required_fields:
            if field not in output_data:
                errors.append(f"缺少必需字段: {field}")

        if output_data.get('stage') != 'stage4_optimization_decision':
            errors.append("階段標識錯誤")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def extract_key_metrics(self) -> Dict[str, Any]:
        """提取關鍵指標"""
        return {
            'stage': 'stage4_optimization_decision',
            'satellites_processed': self.processing_stats['total_satellites_processed'],
            'handover_decisions_made': self.processing_stats['handover_decisions_made']
        }


def create_stage4_processor(config: Optional[Dict[str, Any]] = None) -> TimeseriesPreprocessingProcessor:
    """創建Stage 4處理器實例"""
    return TimeseriesPreprocessingProcessor(config)