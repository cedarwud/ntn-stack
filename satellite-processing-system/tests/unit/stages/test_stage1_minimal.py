"""
Stage 1 TLE軌道計算處理器 - 簡化測試套件

針對重構後的Stage1TLEProcessor進行基本功能測試
"""

import pytest
import sys
from pathlib import Path

# 添加src路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

from stages.stage1_orbital_calculation.tle_orbital_calculation_processor import Stage1TLEProcessor


class TestStage1MinimalProcessor:
    """Stage 1處理器基本測試套件"""

    @pytest.fixture
    def processor(self):
        """創建Stage1處理器實例"""
        return Stage1TLEProcessor()

    def test_processor_initialization(self, processor):
        """測試處理器初始化"""
        # 驗證基礎屬性
        assert processor.stage_name == "tle_orbital_calculation"
        assert processor.stage_number == 1
        assert processor.logger is not None
        assert processor.output_dir is not None

    def test_processor_basic_attributes(self, processor):
        """測試處理器基本屬性"""
        # 驗證配置屬性
        assert hasattr(processor, 'sample_mode')
        assert hasattr(processor, 'sample_size')
        assert hasattr(processor, 'time_points')
        assert hasattr(processor, 'time_interval')

        # 驗證地球物理常數
        assert processor.EARTH_RADIUS == 6378.137
        assert processor.EARTH_MU == 398600.4418

    def test_processor_components_exist(self, processor):
        """測試處理器組件存在"""
        # 驗證主要組件
        assert hasattr(processor, 'tle_loader')
        assert hasattr(processor, 'orbital_calculator')
        assert hasattr(processor, 'validation_engine')
        assert hasattr(processor, 'processing_stats')

    def test_processing_stats_structure(self, processor):
        """測試處理統計結構"""
        stats = processor.processing_stats
        assert isinstance(stats, dict)
        assert "total_satellites" in stats
        assert "successfully_processed" in stats
        assert "processing_duration" in stats
        assert "calculation_base_time" in stats

    def test_output_directories_exist(self, processor):
        """測試輸出目錄存在"""
        assert processor.output_dir.exists()
        assert processor.validation_dir.exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])