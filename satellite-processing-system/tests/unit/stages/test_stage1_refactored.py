"""
Stage 1 TLE軌道計算處理器 - 重構後TDD測試套件

重構變更:
- 移除所有觀測者計算功能 (6個方法, 202行代碼)
- 專注純軌道計算，符合單一職責原則
- 使用TLE epoch時間作為計算基準
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# 添加src路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

from stages.stage1_orbital_calculation.stage1_data_loading_processor import create_stage1_processor
from shared.interfaces.processor_interface import ProcessingStatus, ProcessingResult


class TestStage1RefactoredProcessor:
    """重構後Stage 1處理器測試套件"""

    @pytest.fixture
    def processor(self):
        """創建Stage1處理器實例"""
        return create_stage1_processor()

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_processor_initialization_refactored(self, processor):
        """測試重構後的處理器初始化"""
        # 驗證BaseProcessor接口
        from shared.interfaces.processor_interface import BaseProcessor
        assert isinstance(processor, BaseProcessor)

        # 驗證必要方法存在
        assert hasattr(processor, 'process')
        assert hasattr(processor, 'validate_input')
        assert hasattr(processor, 'validate_output')

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_removed_observer_methods(self, processor):
        """驗證觀測者計算方法已被移除"""
        # 確認這些方法不再存在
        removed_methods = [
            '_add_observer_geometry',
            '_calculate_observer_geometry',
            '_validate_observer_coordinates',
            '_calculate_elevation_azimuth',
            '_check_visibility_constraints',
            '_format_observer_results'
        ]

        for method_name in removed_methods:
            assert not hasattr(processor, method_name), f"方法 {method_name} 應該已被移除"

    @pytest.mark.unit
    @pytest.mark.stage1
    @pytest.mark.sgp4
    def test_tle_data_loading_process(self, processor):
        """測試TLE數據載入處理功能"""
        # 執行處理
        result = processor.process(None)

        # 驗證返回ProcessingResult
        assert isinstance(result, ProcessingResult)
        assert hasattr(result, 'status')
        assert hasattr(result, 'data')
        assert hasattr(result, 'metadata')

        # 檢查成功狀態
        assert result.status == ProcessingStatus.SUCCESS

        # 驗證數據結構
        assert 'tle_data' in result.data
        assert isinstance(result.data['tle_data'], list)
        assert len(result.data['tle_data']) > 1000  # 應該有大量衛星數據

        # 檢查TLE數據結構
        if result.data['tle_data']:
            sample_tle = result.data['tle_data'][0]
            required_fields = ['satellite_id', 'line1', 'line2']
            for field in required_fields:
                assert field in sample_tle, f"缺少必要字段: {field}"

    @pytest.mark.unit
    @pytest.mark.stage1
    @pytest.mark.critical
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
    def test_stage_responsibility_compliance(self, processor):
        """驗證Stage 1嚴格遵循職責邊界"""
        # Stage 1應該只處理軌道計算，不應該有其他階段的功能

        # 確認沒有Stage 2功能 (可見性過濾)
        stage2_methods = ['filter_by_elevation', 'check_visibility', 'apply_geographic_filter']
        for method in stage2_methods:
            assert not hasattr(processor, method)

        # 確認沒有Stage 3功能 (信號分析)
        stage3_methods = ['calculate_rsrp', 'analyze_signal_quality', 'compute_path_loss']
        for method in stage3_methods:
            assert not hasattr(processor, method)

        # 確認只有核心處理方法
        core_methods = ['process', 'validate_input', 'validate_output']
        for method in core_methods:
            assert hasattr(processor, method), f"核心方法 {method} 應該存在"

    @pytest.mark.integration
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

    @pytest.mark.performance
    @pytest.mark.stage1
    def test_next_stage_readiness(self, processor):
        """測試為下一階段準備的數據格式"""
        result = processor.process(None)

        if result.status == ProcessingStatus.SUCCESS:
            # 檢查輸出格式適合Stage 2消費
            assert 'tle_data' in result.data
            assert 'next_stage_ready' in result.data
            assert result.data['next_stage_ready'] is True


# 重構後快照標記
@pytest.mark.refactored
@pytest.mark.snapshot
class TestStage1RefactoringSnapshot:
    """重構效果快照測試"""

    def test_refactoring_completeness(self):
        """驗證重構完整性"""
        processor = create_stage1_processor()

        # 確認BaseProcessor接口實現
        from shared.interfaces.processor_interface import BaseProcessor
        assert isinstance(processor, BaseProcessor)

        # 確認核心方法保留
        essential_methods = ['process', 'validate_input', 'validate_output']
        for method in essential_methods:
            assert hasattr(processor, method), f"核心方法 {method} 應該保留"