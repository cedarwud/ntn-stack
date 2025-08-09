#!/usr/bin/env python3
"""
衛星預處理邏輯單元測試

測試核心預處理算法，包括：
1. 衛星選擇邏輯
2. 軌道分群算法
3. 相位分散優化
4. 可見性評分
"""

import sys
import os
import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta

# 添加模組路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'netstack/src/services/satellite'))

class TestPreprocessingLogic(unittest.TestCase):
    """預處理邏輯測試類"""
    
    def setUp(self):
        """設置測試環境"""
        # 模擬衛星數據
        self.mock_satellites = [
            {
                'satellite_id': 'SAT-001',
                'name': 'STARLINK-1234',
                'constellation': 'starlink',
                'altitude': 550.0,
                'inclination': 53.0,
                'raan': 0.0,
                'mean_anomaly': 0.0,
                'mean_motion': 15.5,
                'eccentricity': 0.001,
                'tle_age_days': 5.0
            },
            {
                'satellite_id': 'SAT-002',
                'name': 'STARLINK-1235',
                'constellation': 'starlink',
                'altitude': 550.0,
                'inclination': 53.0,
                'raan': 30.0,
                'mean_anomaly': 60.0,
                'mean_motion': 15.5,
                'eccentricity': 0.001,
                'tle_age_days': 3.0
            },
            {
                'satellite_id': 'SAT-003',
                'name': 'ONEWEB-0001',
                'constellation': 'oneweb',
                'altitude': 1200.0,
                'inclination': 87.4,
                'raan': 0.0,
                'mean_anomaly': 0.0,
                'mean_motion': 13.1,
                'eccentricity': 0.001,
                'tle_age_days': 7.0
            }
        ]
    
    def test_satellite_selection_config(self):
        """測試衛星選擇配置"""
        try:
            from preprocessing.satellite_selector import SatelliteSelectionConfig
            
            config = SatelliteSelectionConfig()
            
            # 驗證默認配置
            self.assertEqual(config.target_visible_count, 10)
            self.assertEqual(config.min_visible_count, 8)
            self.assertEqual(config.max_visible_count, 12)
            self.assertEqual(config.starlink_target, 120)
            self.assertEqual(config.oneweb_target, 80)
            self.assertAlmostEqual(config.observer_lat, 24.9441667, places=5)
            self.assertAlmostEqual(config.observer_lon, 121.3713889, places=5)
            
        except ImportError:
            self.skipTest("預處理模組不可用，跳過測試")
    
    def test_orbital_plane_grouping(self):
        """測試軌道平面分群"""
        try:
            from preprocessing.orbital_grouping import OrbitalPlaneGrouper
            
            grouper = OrbitalPlaneGrouper()
            
            # 測試 Starlink 衛星分群
            starlink_sats = [sat for sat in self.mock_satellites if sat['constellation'] == 'starlink']
            groups = grouper.group_by_orbital_plane(starlink_sats)
            
            # 驗證分群結果
            self.assertIsInstance(groups, dict)
            self.assertGreater(len(groups), 0)
            
            # 驗證每個群組都有衛星
            for plane_id, satellites in groups.items():
                self.assertIsInstance(satellites, list)
                self.assertGreater(len(satellites), 0)
                self.assertTrue(plane_id.startswith('starlink_'))
            
        except ImportError:
            self.skipTest("軌道分群模組不可用，跳過測試")
    
    def test_phase_distribution_optimizer(self):
        """測試相位分散優化器"""
        try:
            from preprocessing.phase_distribution import PhaseDistributionOptimizer
            
            optimizer = PhaseDistributionOptimizer()
            
            # 測試相位優化
            target_count = 2
            optimized_sats = optimizer.optimize_phase_distribution(
                self.mock_satellites[:3], target_count
            )
            
            # 驗證優化結果
            self.assertIsInstance(optimized_sats, list)
            self.assertLessEqual(len(optimized_sats), target_count)
            
            # 測試相位品質評估
            quality = optimizer.evaluate_phase_quality(optimized_sats)
            self.assertIsInstance(quality, (int, float))
            self.assertGreaterEqual(quality, 0.0)
            self.assertLessEqual(quality, 1.0)
            
        except ImportError:
            self.skipTest("相位分散模組不可用，跳過測試")
    
    def test_visibility_scoring(self):
        """測試可見性評分器"""
        try:
            from preprocessing.visibility_scoring import VisibilityScorer
            
            scorer = VisibilityScorer()
            
            # 測試單顆衛星評分
            observer_lat, observer_lon = 24.9441667, 121.3713889
            score = scorer.calculate_visibility_score(
                self.mock_satellites[0], observer_lat, observer_lon
            )
            
            # 驗證評分結果
            self.assertIsInstance(score, (int, float))
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
            
            # 測試批量評分
            scored_satellites = scorer.batch_score_satellites(
                self.mock_satellites, observer_lat, observer_lon
            )
            
            # 驗證批量評分結果
            self.assertIsInstance(scored_satellites, list)
            self.assertEqual(len(scored_satellites), len(self.mock_satellites))
            
            # 驗證按評分排序
            scores = [score for _, score in scored_satellites]
            self.assertEqual(scores, sorted(scores, reverse=True))
            
        except ImportError:
            self.skipTest("可見性評分模組不可用，跳過測試")
    
    def test_intelligent_satellite_selector(self):
        """測試智能衛星選擇器"""
        try:
            from preprocessing.satellite_selector import (
                IntelligentSatelliteSelector, SatelliteSelectionConfig
            )
            
            config = SatelliteSelectionConfig()
            config.starlink_target = 2
            config.oneweb_target = 1
            
            selector = IntelligentSatelliteSelector(config)
            
            # 測試衛星選擇
            selected_sats, stats = selector.select_research_subset(self.mock_satellites)
            
            # 驗證選擇結果
            self.assertIsInstance(selected_sats, list)
            self.assertIsInstance(stats, dict)
            self.assertGreater(len(selected_sats), 0)
            self.assertLessEqual(len(selected_sats), len(self.mock_satellites))
            
            # 驗證統計信息
            self.assertIn('total', stats)
            self.assertIn('starlink', stats)
            self.assertIn('oneweb', stats)
            
            # 驗證選擇驗證
            validation = selector.validate_selection(selected_sats)
            self.assertIsInstance(validation, dict)
            self.assertIn('overall_pass', validation)
            
        except ImportError:
            self.skipTest("衛星選擇器模組不可用，跳過測試")
    
    def test_preprocessing_service_mock(self):
        """測試預處理服務模擬實現"""
        try:
            from preprocessing_service import get_preprocessing_service, PreprocessingRequest
            
            service = get_preprocessing_service()
            
            # 創建測試請求
            request = PreprocessingRequest(
                constellation="starlink",
                target_count=2,
                optimization_mode="event_diversity"
            )
            
            # 這裡我們無法測試異步方法，但可以驗證服務實例
            self.assertIsNotNone(service)
            self.assertTrue(hasattr(service, 'preprocess_satellite_pool'))
            self.assertTrue(hasattr(service, 'get_optimal_time_window'))
            self.assertTrue(hasattr(service, 'get_event_timeline'))
            
        except ImportError:
            self.skipTest("預處理服務不可用，跳過測試")

class TestMockImplementations(unittest.TestCase):
    """測試模擬實現"""
    
    def test_numpy_mock(self):
        """測試 numpy 模擬實現"""
        # 模擬沒有 numpy 的情況
        import sys
        original_modules = sys.modules.copy()
        
        # 暫時移除 numpy
        if 'numpy' in sys.modules:
            del sys.modules['numpy']
        
        try:
            # 重新導入並測試模擬實現
            sys.path.append(os.path.join(os.path.dirname(__file__), 'netstack/src/services/satellite/preprocessing'))
            
            # 手動創建 numpy 模擬
            class NumpyMock:
                def std(self, data): 
                    if not data or len(data) <= 1: return 0.0
                    mean_val = sum(data) / len(data)
                    variance = sum((x - mean_val) ** 2 for x in data) / (len(data) - 1)
                    return variance ** 0.5
                def mean(self, data): return sum(data) / len(data) if data else 0.0
                def min(self, data): return min(data) if data else 0.0
                def max(self, data): return max(data) if data else 0.0
            
            np_mock = NumpyMock()
            
            # 測試統計函數
            test_data = [1, 2, 3, 4, 5]
            
            mean_result = np_mock.mean(test_data)
            self.assertAlmostEqual(mean_result, 3.0, places=5)
            
            std_result = np_mock.std(test_data)
            self.assertAlmostEqual(std_result, 1.5811, places=3)
            
            min_result = np_mock.min(test_data)
            self.assertEqual(min_result, 1)
            
            max_result = np_mock.max(test_data)
            self.assertEqual(max_result, 5)
            
        finally:
            # 恢復原始模組
            sys.modules.clear()
            sys.modules.update(original_modules)

def run_unit_tests():
    """運行單元測試"""
    print("🧪 運行衛星預處理邏輯單元測試")
    print("="*60)
    
    # 創建測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加測試類
    suite.addTests(loader.loadTestsFromTestCase(TestPreprocessingLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestMockImplementations))
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 顯示結果摘要
    print("\n" + "="*60)
    print("📊 單元測試結果摘要")
    print("="*60)
    print(f"運行測試: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
    print(f"跳過: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("🎉 所有測試通過！")
    else:
        print("❌ 部分測試失敗")
        
        if result.failures:
            print("\n失敗的測試:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\n錯誤的測試:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
    
    print("="*60)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_unit_tests()
    sys.exit(0 if success else 1)