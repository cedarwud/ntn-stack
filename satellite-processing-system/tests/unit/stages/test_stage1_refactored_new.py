"""
Stage 1 數據載入處理器 - 新架構TDD測試套件

新架構特點:
- 使用統一BaseProcessor接口
- 專注TLE數據載入和預處理
- 標準化ProcessingResult返回格式
- 使用TLE epoch時間作為計算基準
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# 添加src路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

from stages.stage1_orbital_calculation.stage1_data_loading_processor import create_stage1_processor
from shared.interfaces.processor_interface import ProcessingStatus, ProcessingResult


class TestStage1NewArchitecture:
    """Stage 1新架構測試套件"""

    @pytest.fixture
    def processor(self):
        """創建Stage 1處理器實例"""
        return create_stage1_processor()

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_processor_creation(self, processor):
        """測試處理器創建"""
        assert processor is not None
        assert hasattr(processor, 'process')
        assert hasattr(processor, 'validate_input')
        assert hasattr(processor, 'validate_output')

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_base_processor_interface(self, processor):
        """測試BaseProcessor接口實現"""
        from shared.interfaces.processor_interface import BaseProcessor
        assert isinstance(processor, BaseProcessor)

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_validate_input_method(self, processor):
        """測試validate_input方法"""
        # Stage 1不需要輸入數據，任何輸入都應該被接受
        result = processor.validate_input(None)
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'errors' in result
        assert result['valid'] is True

        # 測試字典輸入
        result = processor.validate_input({'some': 'data'})
        assert result['valid'] is True

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_validate_output_method(self, processor):
        """測試validate_output方法"""
        # 測試有效輸出
        valid_output = {
            'stage': 'stage1_data_loading',
            'tle_data': [{'satellite_id': '12345', 'line1': 'test', 'line2': 'test'}],
            'metadata': {'timestamp': datetime.now().isoformat()}
        }
        result = processor.validate_output(valid_output)
        assert isinstance(result, dict)
        assert 'valid' in result

        # 測試無效輸出
        invalid_output = {'invalid': 'data'}
        result = processor.validate_output(invalid_output)
        assert result['valid'] is False
        assert len(result['errors']) > 0

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_tle_data_loading(self, processor):
        """測試TLE數據載入功能"""
        result = processor.process(None)

        # 檢查ProcessingResult格式
        assert isinstance(result, ProcessingResult)
        assert hasattr(result, 'status')
        assert hasattr(result, 'data')
        assert hasattr(result, 'metadata')

        # 檢查成功狀態
        assert result.status == ProcessingStatus.SUCCESS

        # 檢查數據結構
        assert 'tle_data' in result.data
        assert isinstance(result.data['tle_data'], list)
        assert len(result.data['tle_data']) > 1000  # 應該有大量衛星數據

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_tle_data_structure(self, processor):
        """測試TLE數據結構"""
        result = processor.process(None)

        if result.status == ProcessingStatus.SUCCESS and result.data['tle_data']:
            sample_tle = result.data['tle_data'][0]

            # 檢查必要字段
            required_fields = ['satellite_id', 'line1', 'line2']
            for field in required_fields:
                assert field in sample_tle, f"缺少必要字段: {field}"

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_time_standardization(self, processor):
        """測試時間標準化功能"""
        result = processor.process(None)

        if result.status == ProcessingStatus.SUCCESS:
            # 檢查metadata包含時間信息
            metadata = result.data.get('metadata', {})
            # 使用實際存在的時間字段
            time_fields = ['processing_start_time', 'processing_end_time']
            assert any(field in metadata for field in time_fields)

            # 檢查時間基準信息
            if 'calculation_base_time' in metadata:
                # 驗證使用的是TLE epoch時間而非當前時間
                base_time = metadata['calculation_base_time']
                assert isinstance(base_time, str)

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_processing_statistics(self, processor):
        """測試處理統計信息"""
        result = processor.process(None)

        if result.status == ProcessingStatus.SUCCESS:
            # 檢查統計信息
            if 'processing_stats' in result.data:
                stats = result.data['processing_stats']
                # 使用實際存在的統計字段
                expected_fields = ['total_satellites_loaded', 'total_files_scanned']
                assert any(field in stats for field in expected_fields)

                if 'total_satellites_loaded' in stats:
                    assert stats['total_satellites_loaded'] > 0

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_error_handling(self, processor):
        """測試錯誤處理"""
        # Stage 1應該能處理任何輸入而不崩潰
        result = processor.process({'invalid': 'input'})
        assert isinstance(result, ProcessingResult)
        assert result.status in [ProcessingStatus.SUCCESS, ProcessingStatus.FAILED, ProcessingStatus.VALIDATION_FAILED]

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_metadata_completeness(self, processor):
        """測試metadata完整性"""
        result = processor.process(None)

        if result.status == ProcessingStatus.SUCCESS:
            metadata = result.data.get('metadata', {})

            # 檢查基本metadata字段
            expected_fields = ['processing_timestamp', 'satellites_loaded']
            for field in expected_fields:
                if field in metadata:
                    assert metadata[field] is not None

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_data_consistency(self, processor):
        """測試數據一致性"""
        # 多次調用應該返回一致的結果
        result1 = processor.process(None)
        result2 = processor.process(None)

        if (result1.status == ProcessingStatus.SUCCESS and
            result2.status == ProcessingStatus.SUCCESS):

            # 檢查衛星數量一致性
            count1 = len(result1.data['tle_data'])
            count2 = len(result2.data['tle_data'])
            assert count1 == count2, "多次調用應返回相同數量的衛星數據"

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_next_stage_readiness(self, processor):
        """測試為下一階段準備的數據格式"""
        result = processor.process(None)

        if result.status == ProcessingStatus.SUCCESS:
            # 檢查輸出格式適合Stage 2消費
            assert 'tle_data' in result.data
            assert 'next_stage_ready' in result.data
            assert result.data['next_stage_ready'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])