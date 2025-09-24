"""
Stage 1 TLE軌道計算處理器 - 簡化測試套件

針對重構後的Stage1TLEProcessor進行基本功能測試
"""

import unittest
import pytest
import sys
from pathlib import Path

# 添加src路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

from stages.stage1_orbital_calculation.stage1_data_loading_processor import Stage1DataLoadingProcessor


class TestStage1MinimalProcessor(unittest.TestCase):
    """
    🔧 更新：使用新的Stage1DataLoadingProcessor進行基本功能測試
    
    變更說明：
    - 從Stage1TLEProcessor更新為Stage1DataLoadingProcessor
    - 測試邏輯調整為數據載入階段的驗證
    - 移除軌道計算相關的測試期待
    """

    @pytest.fixture
    def processor(self):
        """創建Stage1數據載入處理器實例"""
        return Stage1DataLoadingProcessor()

    def test_processor_initialization(self):
        """測試處理器初始化"""
        processor = Stage1DataLoadingProcessor()
        
        # 驗證基本屬性
        self.assertEqual(processor.stage_name, "data_loading")
        self.assertEqual(processor.stage_number, 1)
        self.assertIsNotNone(processor.tle_loader)
        self.assertIsNotNone(processor.data_validator)
        self.assertIsNotNone(processor.time_reference_manager)

    def test_processor_basic_attributes(self):
        """測試處理器基本屬性"""
        processor = Stage1DataLoadingProcessor()
        
        # 檢查數據載入處理器的屬性
        self.assertEqual(processor.stage_name, "data_loading")
        self.assertFalse(processor.sample_mode)  # 預設非樣本模式
        self.assertGreater(processor.sample_size, 0)  # 樣本大小大於0

    def test_processor_components_exist(self):
        """測試處理器組件存在性"""
        processor = Stage1DataLoadingProcessor()
        
        # 檢查v2.0模組化組件
        self.assertTrue(hasattr(processor, 'tle_loader'))
        self.assertTrue(hasattr(processor, 'data_validator'))
        self.assertTrue(hasattr(processor, 'time_reference_manager'))
        self.assertTrue(hasattr(processor, 'processing_stats'))

    def test_processing_stats_structure(self):
        """測試處理統計結構"""
        processor = Stage1DataLoadingProcessor()
        
        # 檢查統計字典結構
        expected_keys = [
            'total_files_scanned',
            'total_satellites_loaded', 
            'validation_failures',
            'time_reference_issues'
        ]
        
        for key in expected_keys:
            self.assertIn(key, processor.processing_stats)
            self.assertEqual(processor.processing_stats[key], 0)  # 初始值為0

    def test_output_directories_exist(self):
        """測試輸出目錄存在性（數據載入不需要輸出目錄）"""
        processor = Stage1DataLoadingProcessor()
        
        # 數據載入處理器主要進行記憶體操作，不一定需要輸出目錄
        # 檢查基本路徑配置
        self.assertTrue(hasattr(processor, 'output_dir'))
        
        # 如果有輸出目錄配置，檢查其格式
        if hasattr(processor, 'output_dir') and processor.output_dir:
            # output_dir可能是str或PosixPath
            self.assertTrue(isinstance(processor.output_dir, (str, type(None))) or hasattr(processor.output_dir, '__fspath__'))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])