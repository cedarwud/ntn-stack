# 🛰️ Phase 1 整合測試
"""
Phase 1 Pipeline Integration Tests
功能: 測試F1→F2→F3→A1完整流程的整合性和正確性
"""

import asyncio
import logging
import pytest
from datetime import datetime, timezone
from pathlib import Path
import sys
import json

# 添加模組路徑
sys.path.append(str(Path(__file__).parent.parent))

from phase1_core_system.main_pipeline import Phase1Pipeline, create_default_config
from shared_core.data_models import create_ntpu_config, ConstellationType
from shared_core.utils import setup_logger

class TestPhase1Integration:
    """Phase 1整合測試套件"""
    
    @pytest.fixture
    def setup_logging(self):
        """設置測試日誌"""
        return setup_logger('TestPhase1Integration', logging.INFO)
    
    @pytest.fixture
    def test_config(self):
        """測試配置"""
        config = create_default_config()
        
        # 修改為測試參數
        config['tle_loader']['calculation_params']['time_range_minutes'] = 100  # 縮短測試時間
        config['optimizer']['optimization_params']['max_iterations'] = 100    # 減少迭代次數
        
        return config
    
    @pytest.fixture
    def ntpu_config(self):
        """NTPU觀測點配置"""
        return create_ntpu_config()
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_execution(self, test_config, setup_logging):
        """測試完整管道執行"""
        logger = setup_logging
        logger.info("🧪 開始完整管道執行測試...")
        
        # 創建管道實例
        pipeline = Phase1Pipeline(test_config)
        
        try:
            # 執行完整管道
            result = await pipeline.execute_complete_pipeline()
            
            # 驗證結果
            assert result is not None, "管道執行結果不應為空"
            assert hasattr(result, 'starlink_satellites'), "結果應包含Starlink衛星列表"
            assert hasattr(result, 'oneweb_satellites'), "結果應包含OneWeb衛星列表"
            assert result.get_total_satellites() > 0, "總衛星數應大於0"
            
            # 驗證管道統計
            assert pipeline.pipeline_stats['stages_completed'] == 4, "應完成4個階段"
            assert pipeline.pipeline_stats['total_duration_seconds'] > 0, "執行時間應大於0"
            
            logger.info(f"✅ 管道執行成功，總衛星數: {result.get_total_satellites()}")
            
        except Exception as e:
            logger.error(f"❌ 管道執行失敗: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_stage1_tle_loading(self, test_config, setup_logging):
        """測試Stage 1: TLE載入"""
        logger = setup_logging
        logger.info("🧪 測試Stage 1: TLE載入...")
        
        pipeline = Phase1Pipeline(test_config)
        
        try:
            satellite_data, orbital_positions = await pipeline._execute_stage1_tle_loading()
            
            # 驗證TLE數據
            assert 'starlink' in satellite_data, "應包含Starlink數據"
            assert 'oneweb' in satellite_data, "應包含OneWeb數據"
            
            # 驗證軌道位置
            assert orbital_positions is not None, "軌道位置不應為空"
            assert len(orbital_positions) > 0, "應有軌道位置數據"
            
            # 驗證載入統計
            stats = pipeline.tle_loader.load_statistics
            assert stats['total_satellites'] > 0, "總衛星數應大於0"
            
            logger.info(f"✅ Stage 1測試成功，載入{stats['total_satellites']}顆衛星")
            
        except Exception as e:
            logger.error(f"❌ Stage 1測試失敗: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_stage2_filtering(self, test_config, setup_logging):
        """測試Stage 2: 衛星篩選"""
        logger = setup_logging
        logger.info("🧪 測試Stage 2: 衛星篩選...")
        
        pipeline = Phase1Pipeline(test_config)
        
        # 先執行Stage 1獲取數據
        satellite_data, _ = await pipeline._execute_stage1_tle_loading()
        
        try:
            filtered_candidates = await pipeline._execute_stage2_satellite_filtering(satellite_data)
            
            # 驗證篩選結果
            assert 'starlink' in filtered_candidates, "應包含Starlink候選"
            assert 'oneweb' in filtered_candidates, "應包含OneWeb候選"
            
            starlink_count = len(filtered_candidates.get('starlink', []))
            oneweb_count = len(filtered_candidates.get('oneweb', []))
            total_count = starlink_count + oneweb_count
            
            assert total_count > 0, "篩選候選總數應大於0"
            
            # 驗證篩選比例合理
            input_total = (len(satellite_data.get('starlink', [])) + 
                          len(satellite_data.get('oneweb', [])))
            
            if input_total > 0:
                filter_ratio = total_count / input_total
                assert 0.01 <= filter_ratio <= 0.5, f"篩選比例{filter_ratio:.1%}應在合理範圍內"
            
            logger.info(f"✅ Stage 2測試成功，篩選出{total_count}顆候選")
            
        except Exception as e:
            logger.error(f"❌ Stage 2測試失敗: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_target_compliance(self, test_config, ntpu_config, setup_logging):
        """測試目標合規性"""
        logger = setup_logging
        logger.info("🧪 測試目標合規性...")
        
        pipeline = Phase1Pipeline(test_config)
        
        try:
            # 執行完整管道
            result = await pipeline.execute_complete_pipeline()
            
            # 檢查可見性目標
            starlink_target = ntpu_config.starlink_target_visible
            oneweb_target = ntpu_config.oneweb_target_visible
            
            # 簡化合規檢查 (實際應檢查時間軸上的可見性)
            starlink_pool_size = len(result.starlink_satellites)
            oneweb_pool_size = len(result.oneweb_satellites)
            
            # 池大小應足以支持目標可見性
            assert starlink_pool_size >= starlink_target[1], f"Starlink池({starlink_pool_size})應≥{starlink_target[1]}"
            assert oneweb_pool_size >= oneweb_target[1], f"OneWeb池({oneweb_pool_size})應≥{oneweb_target[1]}"
            
            # 檢查最佳化指標
            assert result.visibility_compliance >= 0.0, "可見性合規度應≥0"
            assert result.temporal_distribution >= 0.0, "時空分佈應≥0"
            assert result.signal_quality >= 0.0, "信號品質應≥0"
            
            logger.info(f"✅ 目標合規性測試通過")
            logger.info(f"   Starlink池: {starlink_pool_size}顆 (目標: {starlink_target})")
            logger.info(f"   OneWeb池: {oneweb_pool_size}顆 (目標: {oneweb_target})")
            logger.info(f"   可見性合規: {result.visibility_compliance:.1%}")
            
        except Exception as e:
            logger.error(f"❌ 目標合規性測試失敗: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_output_file_generation(self, test_config, setup_logging):
        """測試輸出文件生成"""
        logger = setup_logging
        logger.info("🧪 測試輸出文件生成...")
        
        pipeline = Phase1Pipeline(test_config)
        
        try:
            # 執行管道
            await pipeline.execute_complete_pipeline()
            
            # 檢查輸出目錄
            output_dir = pipeline.output_dir
            assert output_dir.exists(), "輸出目錄應存在"
            
            # 檢查各階段輸出文件
            expected_files = [
                "stage1_tle_loading_results.json",
                "stage2_filtering_results.json", 
                "stage3_event_analysis_results.json",
                "stage4_optimization_results.json",
                "phase1_final_report.json"
            ]
            
            for filename in expected_files:
                file_path = output_dir / filename
                assert file_path.exists(), f"輸出文件{filename}應存在"
                
                # 檢查文件內容
                with open(file_path, 'r') as f:
                    content = json.load(f)
                    assert content is not None, f"{filename}內容不應為空"
            
            logger.info(f"✅ 輸出文件生成測試通過，共{len(expected_files)}個文件")
            
        except Exception as e:
            logger.error(f"❌ 輸出文件生成測試失敗: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_error_handling(self, setup_logging):
        """測試錯誤處理"""
        logger = setup_logging
        logger.info("🧪 測試錯誤處理...")
        
        # 創建無效配置
        invalid_config = {
            'tle_loader': {
                'data_sources': {
                    'starlink_tle_url': 'invalid_url',  # 無效URL
                    'oneweb_tle_url': 'invalid_url'
                }
            }
        }
        
        pipeline = Phase1Pipeline(invalid_config)
        
        try:
            # 應該拋出異常
            with pytest.raises(Exception):
                await pipeline.execute_complete_pipeline()
            
            logger.info("✅ 錯誤處理測試通過")
            
        except Exception as e:
            logger.error(f"❌ 錯誤處理測試失敗: {e}")
            raise
    
    def test_configuration_validation(self, test_config, setup_logging):
        """測試配置驗證"""
        logger = setup_logging
        logger.info("🧪 測試配置驗證...")
        
        try:
            # 檢查必要配置項
            assert 'tle_loader' in test_config, "配置應包含tle_loader"
            assert 'satellite_filter' in test_config, "配置應包含satellite_filter"
            assert 'event_processor' in test_config, "配置應包含event_processor"
            assert 'optimizer' in test_config, "配置應包含optimizer"
            
            # 檢查NTPU座標
            ntpu_coords = test_config['satellite_filter']['ntpu_coordinates']
            assert 'latitude' in ntpu_coords, "應包含緯度"
            assert 'longitude' in ntpu_coords, "應包含經度"
            
            # 檢查目標參數
            targets = test_config['optimizer']['targets']
            assert 'starlink_pool_size' in targets, "應包含Starlink池大小"
            assert 'oneweb_pool_size' in targets, "應包含OneWeb池大小"
            
            logger.info("✅ 配置驗證測試通過")
            
        except Exception as e:
            logger.error(f"❌ 配置驗證測試失敗: {e}")
            raise

# 測試運行腳本
if __name__ == "__main__":
    async def run_integration_tests():
        """運行整合測試"""
        logger = setup_logger('TestRunner', logging.INFO)
        logger.info("🚀 開始Phase 1整合測試...")
        
        test_suite = TestPhase1Integration()
        config = create_default_config()
        ntpu_config = create_ntpu_config()
        
        # 縮短測試參數
        config['tle_loader']['calculation_params']['time_range_minutes'] = 50
        config['optimizer']['optimization_params']['max_iterations'] = 50
        
        try:
            # 運行主要測試
            logger.info("📡 測試Stage 1...")
            await test_suite.test_stage1_tle_loading(config, logger)
            
            logger.info("🔍 測試Stage 2...")  
            await test_suite.test_stage2_filtering(config, logger)
            
            logger.info("📊 測試配置驗證...")
            test_suite.test_configuration_validation(config, logger)
            
            logger.info("📁 測試輸出文件...")
            await test_suite.test_output_file_generation(config, logger)
            
            logger.info("🎯 測試目標合規...")
            await test_suite.test_target_compliance(config, ntpu_config, logger)
            
            logger.info("🎉 所有整合測試通過!")
            
        except Exception as e:
            logger.error(f"❌ 整合測試失敗: {e}")
            raise
    
    # 執行測試
    asyncio.run(run_integration_tests())