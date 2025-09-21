"""
BaseProcessor統一接口 - TDD測試套件

測試所有重構後的處理器是否正確實現BaseProcessor接口
"""

import pytest
import sys
from pathlib import Path
from typing import Any

# 添加src路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

from shared.interfaces.processor_interface import BaseProcessor, ProcessingResult, ProcessingStatus


class TestBaseProcessorInterface:
    """BaseProcessor接口統一性測試"""

    @pytest.fixture(params=[
        'stage1_data_loading_processor',
        'stage2_orbital_computing_processor',
        'stage3_signal_analysis_processor',
        'timeseries_preprocessing_processor',
        'data_integration_processor',
        'stage6_main_processor'
    ])
    def processor(self, request):
        """創建各階段處理器實例進行統一測試"""
        stage_name = request.param

        if stage_name == 'stage1_data_loading_processor':
            from stages.stage1_orbital_calculation.stage1_data_loading_processor import create_stage1_processor
            return create_stage1_processor()
        elif stage_name == 'stage2_orbital_computing_processor':
            from stages.stage2_visibility_filter.stage2_orbital_computing_processor import create_stage2_processor
            return create_stage2_processor()
        elif stage_name == 'stage3_signal_analysis_processor':
            from stages.stage3_signal_analysis.stage3_signal_analysis_processor import create_stage3_processor
            return create_stage3_processor()
        elif stage_name == 'timeseries_preprocessing_processor':
            from stages.stage4_timeseries_preprocessing.timeseries_preprocessing_processor import create_stage4_processor
            return create_stage4_processor()
        elif stage_name == 'data_integration_processor':
            from stages.stage5_data_integration.data_integration_processor import create_stage5_processor
            return create_stage5_processor()
        elif stage_name == 'stage6_main_processor':
            from stages.stage6_dynamic_pool_planning.stage6_main_processor import create_stage6_processor
            return create_stage6_processor()

    def test_processor_is_base_processor_instance(self, processor):
        """測試處理器是BaseProcessor的實例"""
        assert isinstance(processor, BaseProcessor), f"處理器必須繼承BaseProcessor"

    def test_processor_has_required_methods(self, processor):
        """測試處理器具有必要的方法"""
        assert hasattr(processor, 'process'), "處理器必須有process()方法"
        assert hasattr(processor, 'validate_input'), "處理器必須有validate_input()方法"
        assert hasattr(processor, 'validate_output'), "處理器必須有validate_output()方法"

        # 檢查方法是可調用的
        assert callable(getattr(processor, 'process')), "process()必須是可調用的"
        assert callable(getattr(processor, 'validate_input')), "validate_input()必須是可調用的"
        assert callable(getattr(processor, 'validate_output')), "validate_output()必須是可調用的"

    def test_validate_input_method_signature(self, processor):
        """測試validate_input方法簽名"""
        import inspect
        signature = inspect.signature(processor.validate_input)

        # 檢查參數
        params = list(signature.parameters.keys())
        assert 'input_data' in params, "validate_input()必須有input_data參數"

    def test_validate_output_method_signature(self, processor):
        """測試validate_output方法簽名"""
        import inspect
        signature = inspect.signature(processor.validate_output)

        # 檢查參數
        params = list(signature.parameters.keys())
        assert 'output_data' in params, "validate_output()必須有output_data參數"

    def test_process_method_signature(self, processor):
        """測試process方法簽名"""
        import inspect
        signature = inspect.signature(processor.process)

        # 檢查參數
        params = list(signature.parameters.keys())
        assert 'input_data' in params, "process()必須有input_data參數"

        # 檢查返回類型註解
        return_annotation = signature.return_annotation
        assert return_annotation == ProcessingResult or return_annotation == 'ProcessingResult', \
            "process()必須返回ProcessingResult類型"

    def test_validate_input_returns_dict(self, processor):
        """測試validate_input返回字典格式"""
        # 使用空數據測試
        result = processor.validate_input(None)
        assert isinstance(result, dict), "validate_input()必須返回字典"
        assert 'valid' in result, "驗證結果必須包含valid字段"
        assert 'errors' in result, "驗證結果必須包含errors字段"

    def test_validate_output_returns_dict(self, processor):
        """測試validate_output返回字典格式"""
        # 使用空數據測試
        result = processor.validate_output({})
        assert isinstance(result, dict), "validate_output()必須返回字典"
        assert 'valid' in result, "驗證結果必須包含valid字段"
        assert 'errors' in result, "驗證結果必須包含errors字段"


class TestProcessingResult:
    """ProcessingResult統一格式測試"""

    def test_processing_result_structure(self):
        """測試ProcessingResult結構"""
        from shared.interfaces.processor_interface import create_processing_result

        result = create_processing_result(
            status=ProcessingStatus.SUCCESS,
            data={'test': 'data'},
            message="測試成功"
        )

        assert hasattr(result, 'status'), "ProcessingResult必須有status屬性"
        assert hasattr(result, 'data'), "ProcessingResult必須有data屬性"
        assert hasattr(result, 'metadata'), "ProcessingResult必須有metadata屬性"
        assert result.status == ProcessingStatus.SUCCESS, "狀態必須正確設置"
        assert result.data['test'] == 'data', "數據必須正確設置"

    def test_processing_status_enum(self):
        """測試ProcessingStatus枚舉值"""
        assert hasattr(ProcessingStatus, 'SUCCESS'), "必須有SUCCESS狀態"
        assert hasattr(ProcessingStatus, 'FAILED'), "必須有FAILED狀態"
        assert hasattr(ProcessingStatus, 'VALIDATION_FAILED'), "必須有VALIDATION_FAILED狀態"


if __name__ == "__main__":
    pytest.main([__file__])